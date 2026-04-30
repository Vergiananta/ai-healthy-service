from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from app.core.llm import get_llm


SYSTEM_PROMPT = """Kamu adalah agent komunikasi kesehatan yang bertugas menulis pesan personal dan motivasi kepada pengguna.

Tugasmu:
1. Terima hasil analisis BMI dari agent sebelumnya
2. Tulis pesan yang:
   - Personal dan ramah (gunakan nama user)
   - Mudah dipahami (hindari istilah medis yang rumit)
   - Motivasi dan supportif (bukan menakut-nakuti)
   - Actionable (berikan langkah konkret)
   - Empati (pahami kondisi emosional user)

Format output:
{
  "greeting": "sapaan personal",
  "bmi_explanation": "penjelasan BMI dengan bahasa sederhana",
  "health_status": "kondisi kesehatan saat ini",
  "recommendations": ["rekomendasi 1", "rekomendasi 2", ...],
  "motivation": "pesan motivasi penutup",
  "next_steps": "langkah konkret yang bisa dilakukan hari ini"
}

Gunakan bahasa Indonesia yang hangat dan supportif."""


def create_messaging_agent():
    llm = get_llm(temperature=0.7)  # Lebih kreatif untuk messaging
    return create_react_agent(llm, [], state_modifier=SystemMessage(content=SYSTEM_PROMPT))


def run_messaging_agent(nama: str, bmi_analysis: str) -> str:
    """
    Jalankan agent messaging untuk membuat pesan personal berdasarkan hasil analisis BMI.
    """
    agent = create_messaging_agent()
    user_message = (
        f"Buatkan pesan personal untuk user bernama {nama} berdasarkan hasil analisis BMI berikut:\n\n"
        f"{bmi_analysis}\n\n"
        f"Tulis pesan yang ramah, mudah dipahami, dan memotivasi."
    )
    result = agent.invoke({"messages": [HumanMessage(content=user_message)]})
    return result["messages"][-1].content
