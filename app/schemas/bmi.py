from pydantic import BaseModel, field_validator
from typing import Any, Dict, List, Optional


class BMICalculateRequest(BaseModel):
    nama: str
    berat_badan: float   # kg
    tinggi_badan: float  # cm

    @field_validator("berat_badan")
    @classmethod
    def validate_berat(cls, v: float) -> float:
        if v <= 0 or v > 500:
            raise ValueError("Berat badan tidak valid (1-500 kg)")
        return v

    @field_validator("tinggi_badan")
    @classmethod
    def validate_tinggi(cls, v: float) -> float:
        if v <= 0 or v > 300:
            raise ValueError("Tinggi badan tidak valid (1-300 cm)")
        return v

    @field_validator("nama")
    @classmethod
    def validate_nama(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Nama tidak boleh kosong")
        return v.strip()


class BMICalculateResponse(BaseModel):
    message: str
    nama: str
    bmi_analysis: Dict[str, Any]      # Hasil dari agent_bmi_calculator
    personal_message: Dict[str, Any]  # Hasil dari agent_messaging
    iterations: int                   # Jumlah iterasi supervisor
