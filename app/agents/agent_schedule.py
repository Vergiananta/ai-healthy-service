import json
from datetime import datetime
from typing import Dict, List, Optional
import logging
from zoneinfo import ZoneInfo

from app.core.llm import get_llm
from app.services.bmi_service import get_bmi_kategori

logger = logging.getLogger(__name__)
JAKARTA_TZ = ZoneInfo("Asia/Jakarta")

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


def _generate_schedule_with_llm(
    total_daily_calories: int,
    bmi_category: str,
    goal: str,
) -> Optional[List[Dict]]:
    last_error = None
    for _ in range(2):
        try:
            llm = get_llm(temperature=0.4)
            prompt = (
                "Kamu adalah ahli nutrisi.")
            prompt += (
                " Buat jadwal makan harian dalam format JSON array valid saja (tanpa markdown).\n"
                "Setiap item WAJIB punya key: label, time, calories.\n"
                "time harus format HH:MM:SS (24 jam).\n"
                "Jumlah item 3 atau 4 slot makan.\n"
                "Total calories seluruh item harus sama persis dengan total_daily_calories.\n"
                "Gunakan konteks timezone Asia/Jakarta (WIB).\n"
                "Hindari start jadwal makan di jam subuh.\n"
                "Gunakan label makan natural seperti Breakfast/Lunch/Dinner/Snack.\n\n"
                f"BMI Category: {bmi_category}\n"
                f"Goal: {goal}\n"
                f"Total Daily Calories: {total_daily_calories}\n"
                f"Waktu saat ini (WIB): {datetime.now(JAKARTA_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
            )

            response = llm.invoke(prompt)
            content = getattr(response, "content", "") or ""
            payload = _extract_json_payload(content)
            parsed = json.loads(payload)
            if not isinstance(parsed, list) or len(parsed) < 3:
                last_error = "response jadwal bukan JSON array valid (min 3 item)"
                continue

            schedule: List[Dict] = []
            for item in parsed:
                if not isinstance(item, dict):
                    last_error = "item jadwal bukan object"
                    break
                label = str(item.get("label", "")).strip()
                t = str(item.get("time", "")).strip()
                if len(t) == 5:
                    t = f"{t}:00"
                calories = int(item.get("calories", 0))
                datetime.strptime(t, "%H:%M:%S")
                if not label or calories <= 0:
                    last_error = "label kosong atau calories <= 0"
                    break
                schedule.append({"label": label, "time": t, "calories": calories})

            if len(schedule) not in {3, 4}:
                last_error = "jumlah slot makan bukan 3/4"
                continue

            total_generated = sum(x["calories"] for x in schedule)
            if total_generated != total_daily_calories:
                delta = total_daily_calories - total_generated
                schedule[len(schedule) // 2]["calories"] += delta
                if schedule[len(schedule) // 2]["calories"] <= 0:
                    last_error = "normalisasi total kalori menghasilkan nilai <= 0"
                    continue

            return schedule
        except Exception as e:
            last_error = str(e)
            continue

    logger.warning("agent_schedule LLM output invalid: %s", last_error)
    return None


def run_schedule_agent(calorie_data: Dict, bmi: float) -> Dict:
    """
    Agent_schedule:
    Menyusun jadwal jam makan berbasis output LLM.
    """
    kategori = get_bmi_kategori(bmi)
    total_daily_calories = calorie_data["total_daily_calories"]
    goal = calorie_data.get("goal", "maintenance")

    schedule = _generate_schedule_with_llm(
        total_daily_calories=total_daily_calories,
        bmi_category=kategori,
        goal=goal,
    )
    if not schedule:
        raise ValueError("LLM gagal menghasilkan jadwal makan yang valid.")

    return {
        "bmi_category": kategori,
        "total_daily_calories": total_daily_calories,
        "schedule": schedule,
    }
