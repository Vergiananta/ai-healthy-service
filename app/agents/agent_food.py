from datetime import date, datetime, time
from typing import Dict, List, Optional, Sequence
from uuid import UUID
import json
import logging
from zoneinfo import ZoneInfo

from app.agents.agent_calorie_calculator import run_calorie_calculator_agent
from app.agents.agent_schedule import run_schedule_agent
from app.core.llm import get_llm
from app.database import SessionLocal
from app.models.food_histories import FoodHistories
from app.models.user_information import UserInformation
from app.models.weight_histories import WeightHistories
from app.services.bmi_service import calculate_bmi
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
JAKARTA_TZ = ZoneInfo("Asia/Jakarta")

def generate_food_suggestions(
    schedule: List[Dict],
    preferred_type_food_names: Sequence[str],
    preferred_dessert_names: Sequence[str],
    allergen_food_names: Sequence[str],
    total_daily_calories: Optional[int] = None,
    bmi_category: str = "",
) -> List[Dict]:
    """
    Agent_food:
    Membuat saran menu berdasarkan jadwal dan pembagian kalori per waktu makan.
    """
    llm_foods = _generate_food_suggestions_with_llm(
        schedule=schedule,
        preferred_type_food_names=list(preferred_type_food_names),
        preferred_dessert_names=list(preferred_dessert_names),
        allergen_food_names=list(allergen_food_names),
        total_daily_calories=total_daily_calories,
        bmi_category=bmi_category,
    )
    if llm_foods:
        return llm_foods

    raise ValueError("LLM gagal menghasilkan menu makanan yang valid.")


def _extract_json_payload(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            text = text.split("\n", 1)[1]
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def _generate_food_suggestions_with_llm(
    schedule: List[Dict],
    preferred_type_food_names: List[str],
    preferred_dessert_names: List[str],
    allergen_food_names: List[str],
    total_daily_calories: Optional[int],
    bmi_category: str,
) -> Optional[List[Dict]]:
    last_error = None
    for _ in range(2):
        try:
            llm = get_llm(temperature=0.6)
            prompt = (
                "Kamu adalah nutrition planner.\n"
                "Buat menu makan harian dalam format JSON array valid saja (tanpa markdown).\n"
                "Setiap item WAJIB punya key: meal, name, composition, calories, scheduled_at.\n"
                "scheduled_at harus sama persis dengan time dari schedule input.\n"
                "calories harus sama persis dengan calories dari schedule input.\n"
                "Gunakan konteks timezone Asia/Jakarta (WIB).\n"
                "Hindari seluruh alergen user.\n"
                "Prioritaskan type_food dan dessert preference user.\n"
                "Gunakan bahasa Indonesia.\n\n"
                f"BMI Category: {bmi_category}\n"
                f"Total Daily Calories: {total_daily_calories}\n"
                f"Waktu saat ini (WIB): {datetime.now(JAKARTA_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                f"Schedule: {json.dumps(schedule, ensure_ascii=False)}\n"
                f"Preferred Type Food: {json.dumps(preferred_type_food_names, ensure_ascii=False)}\n"
                f"Preferred Dessert: {json.dumps(preferred_dessert_names, ensure_ascii=False)}\n"
                f"Allergens: {json.dumps(allergen_food_names, ensure_ascii=False)}\n"
            )
            response = llm.invoke(prompt)
            content = getattr(response, "content", "") or ""
            payload = _extract_json_payload(content)
            parsed = json.loads(payload)
            if not isinstance(parsed, list):
                last_error = "response bukan JSON array"
                continue

            allowed_slots = {slot["time"]: slot for slot in schedule}
            normalized_by_slot: Dict[str, Dict] = {}
            for idx, item in enumerate(parsed):
                if not isinstance(item, dict):
                    last_error = "item response bukan object"
                    break

                scheduled_at = str(item.get("scheduled_at", "")).strip()
                if len(scheduled_at) == 5:
                    scheduled_at = f"{scheduled_at}:00"

                slot = allowed_slots.get(scheduled_at)
                if not slot and idx < len(schedule):
                    slot = schedule[idx]
                    scheduled_at = slot["time"]
                if not slot:
                    continue

                # Pastikan 1 menu per slot waktu; duplikat akan menimpa item sebelumnya.
                normalized_by_slot[scheduled_at] = {
                    "meal": str(item.get("meal", slot["label"])).strip() or slot["label"],
                    "name": str(item.get("name", "")).strip() or "Menu sehat seimbang",
                    "composition": str(item.get("composition", "")).strip() or "Protein, karbohidrat kompleks, sayur",
                    "calories": slot["calories"],
                    "scheduled_at": scheduled_at,
                }

            # Lengkapi slot yang tidak terisi agar jumlah item selalu sinkron dengan jadwal.
            normalized: List[Dict] = []
            for slot in schedule:
                slot_time = slot["time"]
                existing = normalized_by_slot.get(slot_time)
                if existing:
                    normalized.append(existing)
                    continue
                normalized.append(
                    {
                        "meal": slot["label"],
                        "name": f"Menu sehat {slot['label']}",
                        "composition": "Protein, karbohidrat kompleks, sayur",
                        "calories": slot["calories"],
                        "scheduled_at": slot_time,
                    }
                )

            if len(normalized) != len(schedule):
                if not last_error:
                    last_error = "jumlah item menu tidak sama dengan jumlah slot jadwal setelah normalisasi"
                continue
            return normalized
        except Exception as e:
            last_error = str(e)
            continue

    logger.warning("agent_food LLM output invalid: %s", last_error)
    return None


def _build_food_plan_for_user(
    db: Session,
    user_info: UserInformation,
    plan_date: date,
    gender: str = "neutral",
    activity_level: str = "sedentary",
) -> Dict:
    latest = (
        db.query(WeightHistories)
        .filter(WeightHistories.user_information_id == user_info.id)
        .order_by(WeightHistories.recorded_at.desc())
        .first()
    )

    if latest:
        berat_badan = latest.berat_badan
        tinggi_badan = latest.tinggi_badan
    else:
        berat_badan = user_info.berat_badan
        tinggi_badan = user_info.tinggi_badan

    bmi = calculate_bmi(berat_badan, tinggi_badan)

    calorie_data = run_calorie_calculator_agent(
        bmi=bmi,
        tinggi_badan=tinggi_badan,
        gender=gender,
        activity_level=activity_level,
    )
    schedule_data = run_schedule_agent(calorie_data=calorie_data, bmi=bmi)
    food_suggestions = generate_food_suggestions(
        schedule=schedule_data["schedule"],
        preferred_type_food_names=[x.name for x in user_info.type_foods],
        preferred_dessert_names=[x.name for x in user_info.type_desserts],
        allergen_food_names=[x.name for x in user_info.alergen_foods],
        total_daily_calories=calorie_data["total_daily_calories"],
        bmi_category=schedule_data["bmi_category"],
    )

    for item in food_suggestions:
        scheduled_dt = datetime.combine(
            plan_date,
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

    return {
        "ideal_weight": calorie_data["ideal_weight"],
        "bmi_category": schedule_data["bmi_category"],
        "total_daily_calories": calorie_data["total_daily_calories"],
        "schedule": schedule_data["schedule"],
        "foods": food_suggestions,
    }


def generate_registration_food_plan(
    db: Session,
    user_info: UserInformation,
    plan_date: Optional[date] = None,
    gender: str = "neutral",
    activity_level: str = "sedentary",
) -> Dict:
    return _build_food_plan_for_user(
        db=db,
        user_info=user_info,
        plan_date=plan_date or datetime.now(JAKARTA_TZ).date(),
        gender=gender,
        activity_level=activity_level,
    )


def run_food_agent(
    account_user_id: UUID,
    plan_date: date,
    gender: str = "neutral",
    activity_level: str = "sedentary",
) -> Dict:
    """
    Orkestrasi alur:
    agent_calorie_calculator -> agent_schedule -> agent_food
    """
    db = SessionLocal()
    try:
        user_info = (
            db.query(UserInformation)
            .filter(UserInformation.account_user_id == account_user_id)
            .first()
        )
        if not user_info:
            raise ValueError("User profile not found")

        result = _build_food_plan_for_user(
            db=db,
            user_info=user_info,
            plan_date=plan_date,
            gender=gender,
            activity_level=activity_level,
        )
        db.commit()
        return result
    finally:
        db.close()
