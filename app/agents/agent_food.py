from datetime import datetime
from typing import List, Dict

from app.agents.agent_schedule import run_schedule_agent
from app.models.food_histories import FoodHistories
from app.models.weight_histories import WeightHistories
from app.database import SessionLocal


def generate_food_suggestions(ideal_weight: float, schedule: List[str]) -> List[Dict]:
    """Generate simple food suggestions for each meal.

    For demonstration, we create placeholder foods with equal calories.
    """
    # Approximate daily caloric need: 30 kcal per kg of ideal weight
    total_calories = round(ideal_weight * 30)
    per_meal_cal = round(total_calories / len(schedule))
    foods = []
    for idx, meal_time in enumerate(schedule, start=1):
        foods.append({
            "name": f"Meal {idx}",
            "composition": "Placeholder food composition",
            "calories": per_meal_cal,
            "scheduled_at": meal_time,
        })
    return foods


def run_food_agent(user_id: int, gender: str = "neutral") -> Dict:
    """Run the food planning agent.

    Returns a dict with schedule, ideal weight, bmi category, and food suggestions.
    Also records each food entry into FoodHistories.
    """
    # Retrieve latest weight and height for user
    db = SessionLocal()
    try:
        latest = db.query(WeightHistories).filter(WeightHistories.user_information_id == user_id).order_by(WeightHistories.recorded_at.desc()).first()
        if not latest:
            raise ValueError("No weight history found for user")
        berat_badan = latest.berat_badan
        tinggi_badan = latest.tinggi_badan
    finally:
        db.close()

    # Get schedule and BMI info using retrieved measurements
    schedule_info = run_schedule_agent(berat_badan, tinggi_badan, gender)
    schedule_iso = schedule_info["schedule"]
    ideal_weight = schedule_info["ideal_weight"]
    bmi_category = schedule_info["bmi_category"]

    # Generate food suggestions
    suggestions = generate_food_suggestions(ideal_weight, schedule_iso)

    # Persist to DB
    db = SessionLocal()
    try:
        for sug in suggestions:
            fh = FoodHistories(
                user_information_id=user_id,
                name=sug["name"],
                composition=sug["composition"],
                total_calories=sug["calories"],
                recorded_at=datetime.fromisoformat(sug["scheduled_at"]),
            )
            db.add(fh)
        db.commit()
    finally:
        db.close()

    return {
        "ideal_weight": ideal_weight,
        "bmi_category": bmi_category,
        "schedule": schedule_iso,
        "foods": suggestions,
    }
