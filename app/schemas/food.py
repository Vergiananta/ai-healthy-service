from pydantic import BaseModel, field_validator
from datetime import date
from typing import List, Dict, Any

class FoodPlanRequest(BaseModel):
    tanggal: date  # tanggal rencana
    gender: str = "neutral"





class FoodPlanResponse(BaseModel):
    ideal_weight: float
    bmi_category: str
    schedule: List[str]
    foods: List[Dict[str, Any]]
