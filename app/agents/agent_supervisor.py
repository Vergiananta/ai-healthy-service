import json
from typing import TypedDict, Literal, Annotated
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from app.core.llm import get_llm
from app.agents.agent_bmi_calculator import run_bmi_calculator_agent
from app.agents.agent_messaging import run_messaging_agent


# ── State ─────────────────────────────────────────────────────────────────────

class SupervisorState(TypedDict):
    # Input awal
    nama: str
    berat_badan: float
    tinggi_badan: float

    # Hasil dari masing-masing agent
    bmi_analysis: str           # Output dari agent_bmi_calculator
    personal_message: str       # Output dari agent_messaging

    # Routing control
    next_agent: str             # Agent mana yang harus dipanggil berikutnya
    iteration: int              # Jumlah iterasi untuk mencegah infinite loop
    is_complete: bool           # Flag selesai

    # Conversation log
    messages: Annotated[list[BaseMessage], add_messages]


# ── Supervisor Node ───────────────────────────────────────────────────────────

SUPERVISOR_SYSTEM = """Kamu adalah supervisor agent kesehatan. Tugasmu adalah mengkoordinasikan agent-agent lain.

Agent yang tersedia:
- "bmi_calculator" : Menghitung dan menganalisis BMI pengguna
- "messaging"      : Menulis pesan personal berdasarkan hasil analisis BMI
- "FINISH"         : Semua tugas selesai, kembalikan hasil akhir

Aturan routing:
1. Jika belum ada hasil BMI → arahkan ke "bmi_calculator"
2. Jika sudah ada hasil BMI tapi belum ada pesan → arahkan ke "messaging"
3. Jika sudah ada hasil BMI DAN pesan personal → arahkan ke "FINISH"

Balas HANYA dengan satu kata: bmi_calculator, messaging, atau FINISH"""


def supervisor_node(state: SupervisorState) -> SupervisorState:
    """
    Supervisor memutuskan agent mana yang dipanggil berikutnya
    berdasarkan state saat ini.
    """
    llm = get_llm(temperature=0.0)

    # Susun konteks untuk supervisor
    context_parts = [f"Nama user: {state['nama']}"]

    if state.get("bmi_analysis"):
        context_parts.append(f"Status BMI: SUDAH dihitung ✓\nHasil: {state['bmi_analysis'][:200]}...")
    else:
        context_parts.append("Status BMI: BELUM dihitung")

    if state.get("personal_message"):
        context_parts.append(f"Status Pesan: SUDAH dibuat ✓\nPesan: {state['personal_message'][:100]}...")
    else:
        context_parts.append("Status Pesan: BELUM dibuat")

    context = "\n".join(context_parts)

    messages = [
        SystemMessage(content=SUPERVISOR_SYSTEM),
        HumanMessage(content=f"Kondisi saat ini:\n{context}\n\nAgent mana yang harus dipanggil?"),
    ]

    response = llm.invoke(messages)
    decision = response.content.strip()

    # Validasi decision
    valid_decisions = {"bmi_calculator", "messaging", "FINISH"}
    if decision not in valid_decisions:
        # Fallback logic jika LLM tidak patuh format
        if not state.get("bmi_analysis"):
            decision = "bmi_calculator"
        elif not state.get("personal_message"):
            decision = "messaging"
        else:
            decision = "FINISH"

    print(f"[Supervisor] Iterasi {state.get('iteration', 0) + 1} → Routing ke: {decision}")

    return {
        **state,
        "next_agent": decision,
        "iteration": state.get("iteration", 0) + 1,
        "messages": [AIMessage(content=f"[Supervisor] Routing ke agent: {decision}")],
    }


# ── Agent Nodes ───────────────────────────────────────────────────────────────

def bmi_calculator_node(state: SupervisorState) -> SupervisorState:
    """Node yang menjalankan agent_bmi_calculator."""
    print(f"[BMI Calculator] Menghitung BMI untuk {state['nama']}...")

    result = run_bmi_calculator_agent(
        nama=state["nama"],
        berat_badan=state["berat_badan"],
        tinggi_badan=state["tinggi_badan"],
    )

    print(f"[BMI Calculator] Selesai.")
    return {
        **state,
        "bmi_analysis": result,
        "messages": [AIMessage(content=f"[BMI Calculator] Analisis selesai: {result[:150]}...")],
    }


def messaging_node(state: SupervisorState) -> SupervisorState:
    """Node yang menjalankan agent_messaging."""
    print(f"[Messaging] Membuat pesan personal untuk {state['nama']}...")

    result = run_messaging_agent(
        nama=state["nama"],
        bmi_analysis=state["bmi_analysis"],
    )

    print(f"[Messaging] Pesan selesai dibuat.")
    return {
        **state,
        "personal_message": result,
        "is_complete": True,
        "messages": [AIMessage(content=f"[Messaging] Pesan dibuat: {result[:150]}...")],
    }


# ── Router Function ───────────────────────────────────────────────────────────

def route_next(state: SupervisorState) -> Literal["bmi_calculator", "messaging", "__end__"]:
    """
    Fungsi routing LangGraph — menentukan edge berikutnya berdasarkan keputusan supervisor.
    """
    next_agent = state.get("next_agent", "")
    iteration = state.get("iteration", 0)

    # Safety: maksimal 10 iterasi untuk mencegah infinite loop
    if iteration >= 10 or next_agent == "FINISH":
        return END

    if next_agent == "bmi_calculator":
        return "bmi_calculator"
    elif next_agent == "messaging":
        return "messaging"
    else:
        return END


# ── Build Graph ───────────────────────────────────────────────────────────────

def build_supervisor_graph() -> StateGraph:
    graph = StateGraph(SupervisorState)

    # Tambahkan nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("bmi_calculator", bmi_calculator_node)
    graph.add_node("messaging", messaging_node)

    # Entry point
    graph.set_entry_point("supervisor")

    # Supervisor memutuskan ke mana pergi
    graph.add_conditional_edges(
        "supervisor",
        route_next,
        {
            "bmi_calculator": "bmi_calculator",
            "messaging": "messaging",
            END: END,
        },
    )

    # Setelah agent selesai, selalu kembali ke supervisor
    graph.add_edge("bmi_calculator", "supervisor")
    graph.add_edge("messaging", "supervisor")

    return graph.compile()


# ── Public Runner ─────────────────────────────────────────────────────────────

def run_supervisor(nama: str, berat_badan: float, tinggi_badan: float) -> dict:
    """
    Entry point utama. Jalankan supervisor graph dan kembalikan hasil akhir.
    """
    graph = build_supervisor_graph()

    initial_state: SupervisorState = {
        "nama": nama,
        "berat_badan": berat_badan,
        "tinggi_badan": tinggi_badan,
        "bmi_analysis": "",
        "personal_message": "",
        "next_agent": "",
        "iteration": 0,
        "is_complete": False,
        "messages": [
            HumanMessage(
                content=f"Analisis BMI untuk {nama}, BB={berat_badan}kg, TB={tinggi_badan}cm"
            )
        ],
    }

    final_state = graph.invoke(initial_state)

    # Parse bmi_analysis jika berupa JSON string
    bmi_data = {}
    try:
        raw = final_state.get("bmi_analysis", "{}")
        # Bersihkan markdown code block jika ada
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        bmi_data = json.loads(raw.strip())
    except (json.JSONDecodeError, IndexError):
        bmi_data = {"raw": final_state.get("bmi_analysis", "")}

    # Parse personal_message jika berupa JSON string
    message_data = {}
    try:
        raw = final_state.get("personal_message", "{}")
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        message_data = json.loads(raw.strip())
    except (json.JSONDecodeError, IndexError):
        message_data = {"raw": final_state.get("personal_message", "")}

    return {
        "nama": nama,
        "bmi_analysis": bmi_data,
        "personal_message": message_data,
        "iterations": final_state.get("iteration", 0),
    }
