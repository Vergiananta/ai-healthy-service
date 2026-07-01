from typing import Dict

from app.services.bmi_service import calculate_berat_ideal


def _get_activity_factor(activity_level: str) -> float:
    factors = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }
    return factors.get(activity_level, 1.2)


def run_calorie_calculator_agent(
    bmi: float,
    tinggi_badan: float,
    gender: str = "neutral",
    activity_level: str = "sedentary",
) -> Dict:
    """
    Agent_calorie_calculator:
    Menghitung total kebutuhan kalori harian berdasarkan data BMI
    untuk diteruskan ke agent_schedule.
    """
    ideal_weight = calculate_berat_ideal(tinggi_badan, gender)
    activity_factor = _get_activity_factor(activity_level)
    maintenance_calories = ideal_weight * 30
    maintenance_with_activity = maintenance_calories * activity_factor

    if bmi < 18.5:
        goal = "weight_gain"
        # surplus konservatif
        total_daily_calories = round(maintenance_with_activity + 300)
    elif bmi >= 25:
        goal = "weight_loss"
        # defisit adaptif: overweight vs obese
        deficit = 500 if bmi < 30 else 700
        total_daily_calories = round(maintenance_with_activity - deficit)
        # jaga batas bawah aman umum
        total_daily_calories = max(total_daily_calories, 1200)
    else:
        goal = "maintenance"
        total_daily_calories = round(maintenance_with_activity)

    return {
        "bmi": bmi,
        "goal": goal,
        "ideal_weight": ideal_weight,
        "activity_level": activity_level,
        "activity_factor": activity_factor,
        "maintenance_calories": round(maintenance_with_activity),
        "total_daily_calories": total_daily_calories,
    }
