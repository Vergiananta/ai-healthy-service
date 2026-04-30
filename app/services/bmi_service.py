def calculate_bmi(berat_badan: float, tinggi_badan: float) -> float:
    """
    Hitung BMI berdasarkan berat badan (kg) dan tinggi badan (cm).
    Formula: BMI = berat (kg) / (tinggi (m))^2
    """
    tinggi_meter = tinggi_badan / 100
    bmi = berat_badan / (tinggi_meter ** 2)
    return round(bmi, 2)


def get_bmi_kategori(bmi: float) -> str:
    """
    Klasifikasi BMI berdasarkan standar WHO:
    - < 18.5  : Underweight
    - 18.5-24.9: Normal
    - 25.0-29.9: Overweight
    - >= 30   : Obese
    """
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25.0:
        return "Normal"
    elif bmi < 30.0:
        return "Overweight"
    else:
        return "Obese"


def calculate_berat_ideal(tinggi_badan: float, gender: str = "neutral") -> float:
    """
    Hitung berat ideal menggunakan rumus Devine (modifikasi netral).
    Rumus: Berat Ideal = (Tinggi (cm) - 100) * 0.9
    Ini adalah pendekatan umum yang tidak memerlukan data gender.
    """
    berat_ideal = (tinggi_badan - 100) * 0.9
    return round(berat_ideal, 2)
