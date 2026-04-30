import asyncio
import httpx
import requests 
import os 
from dotenv import load_dotenv
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

from app.database import SessionLocal
from app.models.master import MstModelLlm
from app.models.history_llm_usage import HistoryLlmUsage


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
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
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

            if json_schema:
                parsed = response["parsed"]
                reply = json.dumps(parsed)
                
                raw_response = response["raw"]
                usage = raw_response.response_metadata.get("token_usage", {})
                input_tokens = raw_response.usage_metadata.get("input_tokens", 0)
                output_tokens = raw_response.usage_metadata.get("output_tokens", 0)
            else:
                reply = response.content
                usage = response.response_metadata.get("token_usage", {})
                input_tokens = response.usage_metadata.get("input_tokens", 0)
                output_tokens = response.usage_metadata.get("output_tokens", 0)
                
            api_duration = time.perf_counter() - api_start
            
            # 5. Async logging
            asyncio.create_task(
                self._async_db_logger(
                    run_id=run_id,
                    prompt=final_prompt,
                    reply=reply,
                    usage=usage,
                    model=model,
                    params=params
                )
            )
            logging.info(f"Model: {model}")
            model_detail = get_detail_model_llm(model)
            create_log_llm(usage.get("total_tokens", 0), api_duration, model_detail.get("id", None) if model_detail else None, input_tokens, output_tokens)

            return reply

        except Exception as e:
            logging.error(f"Bedrock LangChain Error: {e}")
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, send_message_to_teams, str(e))
            except Exception as teams_err:
                logging.error(f"Failed to send to teams: {teams_err}")
            return "Something went wrong"
    
    async def _async_db_logger(self, run_id, prompt, reply, usage, model, params):
        """
        Menangani logging database di background agar tidak memperlambat respons utama.
        """
        try:
            # Menjalankan fungsi blocking (psycopg2) di thread terpisah
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._sync_db_insert, run_id, prompt, reply, usage, model, params)
        except Exception as e:
            logging.error(f"Background DB Logging Error: {e}")


    def _sync_db_insert(self, run_id, prompt, reply, usage, model, params):
        """
        Fungsi internal untuk eksekusi query SQL (Synchronous).
        """
        mode = params.get("mode") 
        trigger_service = params.get("trigger_service", None)
        module = params.get("module", None)
        
        try:
            with get_db_cursor(commit=True) as cursor:
                # Insert ke tabel shorts jika mode short
                if mode == "short":
                    cursor.execute(
                        """
                        INSERT INTO public.shorts (uuid, name, prompt, result, template_id, height, width, module, trigger_service)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (str(run_id), f"Project {run_id}", prompt, reply, 
                        params.get("template"), params.get("height", 1024), params.get("width", 1024), module, trigger_service)
                    )

                # Log ke generate_ai
                if trigger_service != 'product-service':
                    cursor.execute(
                        """ 
                        INSERT INTO public.generate_ai (uuid, prompt, type, model, usage, module, trigger_service)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (str(uuid.uuid4()), prompt, "text", model, json.dumps(usage), module, trigger_service)
                    )
        except Exception as e:
            raise e
