from langchain_core.tools import tool
from app.services.bmi_service import calculate_bmi, get_bmi_kategori, calculate_berat_ideal


@tool
def tool_calculate_bmi(berat_badan: float, tinggi_badan: float) -> dict:
    """
    Menghitung BMI (Body Mass Index) berdasarkan berat badan dan tinggi badan.

    Args:
        berat_badan: Berat badan dalam kilogram (kg)
        tinggi_badan: Tinggi badan dalam sentimeter (cm)

    Returns:
        dict berisi bmi, kategori, dan berat ideal
    """
    bmi = calculate_bmi(berat_badan, tinggi_badan)
    kategori = get_bmi_kategori(bmi)
    berat_ideal = calculate_berat_ideal(tinggi_badan)

    return {
        "berat_badan": berat_badan,
        "tinggi_badan": tinggi_badan,
        "bmi": bmi,
        "bmi_kategori": kategori,
        "berat_ideal": berat_ideal,
        "selisih_berat": round(berat_badan - berat_ideal, 2),
    }


@tool
def tool_get_bmi_detail(bmi: float) -> dict:
    """
    Mendapatkan detail informasi medis berdasarkan nilai BMI.

    Args:
        bmi: Nilai BMI yang sudah dihitung

    Returns:
        dict berisi kategori, risiko kesehatan, dan rekomendasi umum
    """
    kategori = get_bmi_kategori(bmi)

    detail_map = {
        "Underweight": {
            "risiko": "Kekurangan nutrisi, anemia, osteoporosis, sistem imun lemah",
            "rekomendasi_umum": "Tingkatkan asupan kalori dengan makanan bergizi, konsultasi dengan ahli gizi",
        },
        "Normal": {
            "risiko": "Risiko penyakit kronis rendah",
            "rekomendasi_umum": "Pertahankan pola makan sehat dan aktivitas fisik rutin",
        },
        "Overweight": {
            "risiko": "Peningkatan risiko diabetes tipe 2, hipertensi, dan penyakit jantung",
            "rekomendasi_umum": "Kurangi asupan kalori, tingkatkan aktivitas fisik minimal 150 menit per minggu",
        },
        "Obese": {
            "risiko": "Risiko tinggi diabetes, penyakit jantung, stroke, sleep apnea, dan beberapa jenis kanker",
            "rekomendasi_umum": "Konsultasi dengan dokter, program penurunan berat badan terstruktur",
        },
    }

    info = detail_map.get(kategori, {})
    return {
        "bmi": bmi,
        "kategori": kategori,
        "risiko_kesehatan": info.get("risiko", "-"),
        "rekomendasi_umum": info.get("rekomendasi_umum", "-"),
    }
