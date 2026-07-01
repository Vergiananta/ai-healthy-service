from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from app.core.llm import get_llm
from app.services.bmi_service import calculate_bmi, get_bmi_kategori, calculate_berat_ideal


# ── Tools ─────────────────────────────────────────────────────────────────────

@tool
def tool_calculate_bmi(berat_badan: float, tinggi_badan: float) -> dict:
    """
    Menghitung BMI berdasarkan berat badan (kg) dan tinggi badan (cm).
    Mengembalikan nilai BMI, kategori, berat ideal, dan selisih berat.
    """
    bmi = calculate_bmi(berat_badan, tinggi_badan)
    kategori = get_bmi_kategori(bmi)
    berat_ideal = calculate_berat_ideal(tinggi_badan)
    selisih = round(berat_badan - berat_ideal, 2)

    return {
        "berat_badan": berat_badan,
        "tinggi_badan": tinggi_badan,
        "bmi": bmi,
        "bmi_kategori": kategori,
        "berat_ideal": berat_ideal,
        "selisih_berat": selisih,
        "status_selisih": "kelebihan" if selisih > 0 else ("kekurangan" if selisih < 0 else "ideal"),
    }


@tool
def tool_get_health_risk(bmi_kategori: str) -> dict:
    """
    Mendapatkan informasi risiko kesehatan dan rekomendasi berdasarkan kategori BMI.
    Kategori valid: Underweight, Normal, Overweight, Obese
    """
    risk_map = {
        "Underweight": {
            "risiko": [
                "Kekurangan nutrisi dan vitamin",
                "Anemia dan kelelahan kronis",
                "Osteoporosis dan tulang rapuh",
                "Sistem imun melemah",
                "Gangguan hormon",
            ],
            "rekomendasi": [
                "Tingkatkan asupan kalori 300-500 kkal/hari",
                "Konsumsi protein tinggi: telur, daging, kacang-kacangan",
                "Makan 5-6 kali sehari dengan porsi kecil",
                "Konsultasi dengan ahli gizi",
                "Lakukan latihan kekuatan (strength training)",
            ],
            "target_kalori": "Surplus 300-500 kkal dari kebutuhan harian",
        },
        "Normal": {
            "risiko": [
                "Risiko penyakit kronis rendah",
                "Kondisi kesehatan optimal",
            ],
            "rekomendasi": [
                "Pertahankan pola makan seimbang",
                "Olahraga rutin 150 menit/minggu",
                "Cukup tidur 7-9 jam/malam",
                "Kelola stres dengan baik",
                "Lakukan pemeriksaan kesehatan rutin",
            ],
            "target_kalori": "Sesuai kebutuhan harian (maintenance)",
        },
        "Overweight": {
            "risiko": [
                "Peningkatan risiko diabetes tipe 2",
                "Hipertensi dan penyakit jantung",
                "Sleep apnea",
                "Nyeri sendi",
                "Kolesterol tinggi",
            ],
            "rekomendasi": [
                "Kurangi asupan kalori 300-500 kkal/hari",
                "Hindari makanan olahan dan tinggi gula",
                "Olahraga kardio 200-300 menit/minggu",
                "Perbanyak konsumsi sayur dan buah",
                "Minum air putih minimal 2 liter/hari",
            ],
            "target_kalori": "Defisit 300-500 kkal dari kebutuhan harian",
        },
        "Obese": {
            "risiko": [
                "Risiko tinggi diabetes tipe 2",
                "Penyakit jantung koroner",
                "Stroke",
                "Beberapa jenis kanker",
                "Gangguan pernapasan serius",
                "Masalah psikologis",
            ],
            "rekomendasi": [
                "Konsultasi segera dengan dokter",
                "Program penurunan berat badan terstruktur",
                "Defisit kalori terkontrol di bawah pengawasan medis",
                "Olahraga bertahap sesuai kemampuan",
                "Pertimbangkan terapi perilaku kognitif",
            ],
            "target_kalori": "Defisit 500-750 kkal, di bawah pengawasan medis",
        },
    }

    info = risk_map.get(bmi_kategori, risk_map["Normal"])
    return {"bmi_kategori": bmi_kategori, **info}


# ── Agent ─────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Kamu adalah agent ahli kesehatan yang bertugas menganalisis BMI (Body Mass Index) pengguna.

Tugasmu:
1. Gunakan tool `tool_calculate_bmi` untuk menghitung BMI dari data yang diberikan
2. Gunakan tool `tool_get_health_risk` untuk mendapatkan detail risiko dan rekomendasi
3. Susun hasil analisis yang lengkap dan akurat dalam format terstruktur

Output akhirmu HARUS berupa JSON dengan format:
{
  "bmi_data": { ...hasil tool_calculate_bmi },
  "health_info": { ...hasil tool_get_health_risk },
  "summary": "ringkasan singkat kondisi kesehatan user dalam 1-2 kalimat"
}

Jangan tambahkan teks di luar JSON tersebut."""


def create_bmi_calculator_agent():
    llm = get_llm(temperature=0.1)
    tools = [tool_calculate_bmi, tool_get_health_risk]
    return create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)


def run_bmi_calculator_agent(nama: str, berat_badan: float, tinggi_badan: float) -> str:
    """
    Jalankan agent BMI calculator dan kembalikan hasil analisis sebagai string JSON.
    """
    agent = create_bmi_calculator_agent()
    user_message = (
        f"Hitung dan analisis BMI untuk:\n"
        f"- Nama: {nama}\n"
        f"- Berat badan: {berat_badan} kg\n"
        f"- Tinggi badan: {tinggi_badan} cm\n\n"
        f"Gunakan tools yang tersedia dan berikan hasil lengkap."
    )
    result = agent.invoke({"messages": [HumanMessage(content=user_message)]})
    # Ambil pesan terakhir dari agent
    return result["messages"][-1].content
