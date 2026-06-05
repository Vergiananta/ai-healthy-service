import asyncio
import httpx
import requests 
import os 
import json
import datetime
from decimal import Decimal
from langchain.memory.buffer import ConversationBufferMemory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader  
from langchain_community.vectorstores import FAISS 
from langchain.docstore.document import Document
from langchain_community.embeddings import OpenAIEmbeddings 
import uuid
import logging
import time
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from zoneinfo import ZoneInfo

from app.core import load_app_env
from app.database import SessionLocal
from app.models.master import MstModelLlm
from app.models.history_llm_usage import HistoryLlmUsage

load_app_env()


# ── Helper Functions ──────────────────────────────────────────────────────────

def get_detail_model_llm(model_name: str) -> dict | None:
    """
    Ambil detail model LLM dari tabel mst_model_llm berdasarkan model_name.

    Args:
        model_name: Nama model, contoh "openai/gpt-4o-mini"

    Returns:
        dict dengan field id, name, input_price, output_price
        atau None jika model tidak ditemukan di master.
    """
    db = SessionLocal()
    try:
        model = db.query(MstModelLlm).filter(MstModelLlm.name == model_name).first()
        if not model:
            logging.warning(f"[LLM] Model '{model_name}' tidak ditemukan di mst_model_llm")
            return None
        return {
            "id": model.id,
            "name": model.name,
            "input_price": float(model.input_price),
            "output_price": float(model.output_price),
        }
    except Exception as e:
        logging.error(f"[LLM] Gagal query mst_model_llm: {e}")
        return None
    finally:
        db.close()


def create_log_llm(
    total_tokens: int,
    duration_seconds: float,
    mst_model_llm_id,
    input_tokens: int,
    output_tokens: int,
    model_name: str = "",
    agent_name: str = "",
    run_id: str = None,
    module: str = None,
    input_price: float = 0.0,
    output_price: float = 0.0,
) -> None:
    """
    Catat aktivitas penggunaan LLM ke tabel history_llm_usage.

    Estimasi biaya dihitung dengan rumus:
        cost = (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)

    Args:
        total_tokens     : Total token yang digunakan
        duration_seconds : Durasi pemanggilan API (detik)
        mst_model_llm_id : UUID dari mst_model_llm (boleh None)
        input_tokens     : Jumlah token input
        output_tokens    : Jumlah token output
        model_name       : Nama model (untuk log langsung)
        agent_name       : Nama agent pemanggil
        run_id           : ID sesi / run untuk tracing
        module           : Nama modul / fitur
        input_price      : Harga per 1K input token (USD)
        output_price     : Harga per 1K output token (USD)
    """
    estimated_cost = None
    if input_price or output_price:
        estimated_cost = Decimal(str(
            (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)
        )).quantize(Decimal("0.000001"))

    db = SessionLocal()
    try:
        log = HistoryLlmUsage(
            mst_model_llm_id=mst_model_llm_id,
            model_name=model_name,
            total_tokens=total_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=estimated_cost,
            duration_seconds=round(duration_seconds, 4),
            agent_name=agent_name or None,
            run_id=str(run_id) if run_id else None,
            module=module,
        )
        db.add(log)
        db.commit()
        logging.info(
            f"[LLM Log] model={model_name} | tokens={total_tokens} "
            f"(in={input_tokens}, out={output_tokens}) | "
            f"duration={duration_seconds:.2f}s | cost=${estimated_cost}"
        )
    except Exception as e:
        db.rollback()
        logging.error(f"[LLM Log] Gagal menyimpan log: {e}")
    finally:
        db.close()


# ── LLM Connection Class ──────────────────────────────────────────────────────

class LlmConnection:
    openai_api_key: str = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    openai_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    url: str = "https://openrouter.ai/api/v1/chat/completions"

    async def generate_openai_async(
        self,
        prompt: str = "",
        user_prompt: str = "",
        run_id: str = None,
        agent_name: str = "",
        data: str = "",
        data_history: str = "",
        model: str = "openai/gpt-4o-mini",  # contoh model OpenRouter
        params: dict = {},
        system_prompt: str = "",
        json_schema=None,
        temperature: float = 1.0
    ) -> str:
        api_start = time.perf_counter()
        # 1. Inisialisasi LLM via Bedrock (OpenAI-compatible)
        llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=self.openai_api_key,
            base_url=self.openai_base_url,
            default_headers={
                "HTTP-Referer": "https://ai.stg.friendsure.io",  # WAJIB (bebas isi)
                "X-Title": "Gen AI"                  # optional tapi disarankan
            },
            timeout=10000,
            max_retries=4, 
        )
        
        if json_schema:
            llm = llm.with_structured_output(json_schema, include_raw=True)

        # 2. Prompt Construction
        final_prompt = user_prompt if user_prompt else prompt
        if data := params.get("data"):
            final_prompt += f"\nData: {data}"

        messages = [
            SystemMessage(content=system_prompt or "You are a helpful assistant."),
            HumanMessage(content=final_prompt)
        ]

        # 3. Multimodal (Image) – OpenRouter support GPT-4o / Claude
        image_url = params.get("image_url")
        if image_url:
            messages = [
                SystemMessage(content=system_prompt or "You are a helpful assistant."),
                HumanMessage(content=[
                    {"type": "text", "text": final_prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ])
            ]

        try:
            response = await llm.ainvoke(messages)

            # Ambil token usage
            input_tokens = 0
            output_tokens = 0
            if json_schema:
                parsed = response["parsed"]
                reply = json.dumps(parsed)
                raw_msg = response["raw"]
            else:
                reply = response.content
                raw_msg = response

            if hasattr(raw_msg, "usage_metadata") and raw_msg.usage_metadata:
                input_tokens = raw_msg.usage_metadata.get("input_tokens", 0)
                output_tokens = raw_msg.usage_metadata.get("output_tokens", 0)
            
            # Fallback ke response_metadata jika usage_metadata kosong / tidak ada
            if (not input_tokens or not output_tokens) and hasattr(raw_msg, "response_metadata") and raw_msg.response_metadata:
                token_usage = raw_msg.response_metadata.get("token_usage", {})
                if token_usage:
                    input_tokens = token_usage.get("prompt_tokens", 0)
                    output_tokens = token_usage.get("completion_tokens", 0)

            # Hitung durasi dan catat log penggunaan LLM
            duration_seconds = time.perf_counter() - api_start
            total_tokens = input_tokens + output_tokens
            
            # Cari data model di master untuk mendapatkan pricing
            model_detail = get_detail_model_llm(model)
            mst_model_llm_id = None
            input_price = 0.0
            output_price = 0.0
            if model_detail:
                mst_model_llm_id = model_detail["id"]
                input_price = model_detail["input_price"]
                output_price = model_detail["output_price"]

            create_log_llm(
                total_tokens=total_tokens,
                duration_seconds=duration_seconds,
                mst_model_llm_id=mst_model_llm_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model_name=model,
                agent_name=agent_name,
                run_id=run_id,
                module=params.get("module"),
                input_price=input_price,
                output_price=output_price,
            )

            return reply

        except Exception as e:
            logging.error(f"Bedrock LangChain Error: {e}")
            return "Something went wrong"    
