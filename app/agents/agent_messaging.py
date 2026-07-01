from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from app.core.llm import get_llm


SYSTEM_PROMPT = """Kamu adalah agent komunikasi kesehatan yang bertugas menulis pesan personal dan motivasi kepada pengguna.

Tugasmu:
1. Terima hasil analisis BMI dari agent sebelumnya
2. Tulis pesan yang:
   - Tidak mengulang menyebut angka hasil BMI dan tidak mengulang menyebut username
   - Mudah dipahami (hindari istilah medis yang rumit)
   - Langsung ke kesimpulan dan ajakan untuk menggunakan aplikasi Nutri Track agar bisa membantu dalam mencapai berat badan ideal.
Format output JSON:
{
  "bmi_explanation": "penjelasan kategori hasil BMI dengan bahasa sederhana dan singkat maksimal 200 karakter",
}

Gunakan bahasa Indonesia yang hangat dan supportif."""


def create_messaging_agent():
    llm = get_llm(temperature=0.7)  # Lebih kreatif untuk messaging
    return create_react_agent(llm, [], prompt=SYSTEM_PROMPT)


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
