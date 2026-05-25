import json
from datetime import date, datetime, time
from typing import Dict
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.agents.agent_bmi_calculator import run_bmi_calculator_agent
from app.agents.agent_calorie_calculator import run_calorie_calculator_agent
from app.agents.agent_food import generate_food_suggestions
from app.agents.agent_schedule import run_schedule_agent
from app.models.account_user import AccountUser
from app.models.food_histories import FoodHistories
from app.models.user_information import UserInformation


JAKARTA_TZ = ZoneInfo("Asia/Jakarta")


def _extract_json_object(raw_text: str) -> str:
    text = (raw_text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            text = text.split("\n", 1)[1]
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def _parse_bmi_agent_output(raw_result: str) -> Dict:
    payload = _extract_json_object(raw_result)
    parsed = json.loads(payload)
    bmi_data = parsed.get("bmi_data") if isinstance(parsed, dict) else None
    if not isinstance(bmi_data, dict):
        raise ValueError("Output agent_bmi_calculator tidak valid")
    return bmi_data


def create_schedule_menu_for_user(
    db: Session,
    current_user: AccountUser,
    tinggi_badan: float,
    berat_badan: float,
    tanggal: date,
    gender: str = "neutral",
    activity_level: str = "sedentary",
) -> Dict:
    user_info = (
        db.query(UserInformation)
        .filter(UserInformation.account_user_id == current_user.id)
        .first()
    )
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )

    raw_bmi = run_bmi_calculator_agent(
        nama=user_info.nama,
        berat_badan=berat_badan,
        tinggi_badan=tinggi_badan,
    )
    bmi_result = _parse_bmi_agent_output(raw_bmi)
    bmi = float(bmi_result["bmi"])

    calorie_data = run_calorie_calculator_agent(
        bmi=bmi,
        tinggi_badan=tinggi_badan,
        gender=gender,
        activity_level=activity_level,
    )

    schedule_data = run_schedule_agent(calorie_data=calorie_data, bmi=bmi)

    foods = generate_food_suggestions(
        schedule=schedule_data["schedule"],
        preferred_type_food_names=[x.name for x in user_info.type_foods],
        preferred_dessert_names=[x.name for x in user_info.type_desserts],
        allergen_food_names=[x.name for x in user_info.alergen_foods],
        total_daily_calories=calorie_data["total_daily_calories"],
        bmi_category=schedule_data["bmi_category"],
    )

    for item in foods:
        scheduled_dt = datetime.combine(
            tanggal,
            time.fromisoformat(item["scheduled_at"]),
            tzinfo=JAKARTA_TZ,
        )
        db.add(
            FoodHistories(
                user_information_id=user_info.id,
                name=item["name"],
                composition=item["composition"],
                total_calories=item["calories"],
                recorded_at=scheduled_dt,
            )
        )

    db.commit()

    return {
        "ideal_weight": calorie_data["ideal_weight"],
        "bmi_category": schedule_data["bmi_category"],
        "total_daily_calories": calorie_data["total_daily_calories"],
        "schedule": schedule_data["schedule"],
        "foods": foods,
    }
