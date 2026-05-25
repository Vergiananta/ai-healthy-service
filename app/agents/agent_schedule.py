from datetime import time, datetime
from typing import List, Dict

from app.services.bmi_service import calculate_berat_ideal, calculate_bmi, get_bmi_kategori


def determine_meal_schedule() -> List[time]:
    """Return a static meal schedule (breakfast, lunch, dinner)."""
    return [time(hour=8, minute=0), time(hour=13, minute=0), time(hour=19, minute=0)]


def run_schedule_agent(berat_badan: float, tinggi_badan: float, gender: str = "neutral") -> Dict:
    """Calculate ideal weight and provide a meal schedule.

    Returns a dict with keys:
    - ideal_weight: float
    - bmi_category: str
    - schedule: list of ISO time strings
    """
    bmi = calculate_bmi(berat_badan, tinggi_badan)
    kategori = get_bmi_kategori(bmi)
    ideal_weight = calculate_berat_ideal(tinggi_badan, gender)
    schedule_times = determine_meal_schedule()
    schedule_iso = [t.isoformat() for t in schedule_times]
    return {
        "ideal_weight": ideal_weight,
        "bmi_category": kategori,
        "schedule": schedule_iso,
    }