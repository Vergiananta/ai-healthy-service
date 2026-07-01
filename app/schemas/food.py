from pydantic import BaseModel
from datetime import date
from typing import List, Dict, Any
from pydantic import field_validator

class FoodPlanRequest(BaseModel):
    tanggal: date
    gender: str = "neutral"
    activity_level: str = "sedentary"


class FoodPlanResponse(BaseModel):
    ideal_weight: float
    bmi_category: str
    total_daily_calories: int
    schedule: List[Dict[str, Any]]
    foods: List[Dict[str, Any]]


class CreateScheduleMenuRequest(BaseModel):
    tinggi_badan: float
    berat_badan: float
    tanggal: date
    gender: str = "neutral"
    activity_level: str = "sedentary"

    @field_validator("tanggal", mode="before")
    @classmethod
    def parse_tanggal(cls, v):
        if isinstance(v, str):
            from datetime import datetime
            for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            raise ValueError("Format tanggal harus DD-MM-YYYY atau YYYY-MM-DD")
        return v


class MenuByDateItemResponse(BaseModel):
    name: str
    composition: str | None = None
    calories: float | None = None
    recorded_at: str


class MenuByDateListResponse(BaseModel):
    data: List[MenuByDateItemResponse]
