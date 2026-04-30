from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import date
from uuid import UUID


class RegisterRequest(BaseModel):
    # Account credentials
    username: str
    password: str

    # Personal information
    nama: str
    tanggal_lahir: date

    # Health metrics
    tinggi_badan: float  # cm
    berat_badan: float   # kg

    # Preferences (list of master UUIDs)
    type_food_ids: List[UUID]       # ManyToMany: tipe makanan yang disukai
    type_dessert_ids: List[UUID]    # ManyToMany: tipe dessert yang disukai
    alergen_food_ids: List[UUID]    # ManyToMany: alergi makanan (bisa kosong)

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Username tidak boleh kosong")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password minimal 6 karakter")
        return v

    @field_validator("tinggi_badan")
    @classmethod
    def tinggi_badan_valid(cls, v: float) -> float:
        if v <= 0 or v > 300:
            raise ValueError("Tinggi badan tidak valid (harus antara 1-300 cm)")
        return v

    @field_validator("berat_badan")
    @classmethod
    def berat_badan_valid(cls, v: float) -> float:
        if v <= 0 or v > 500:
            raise ValueError("Berat badan tidak valid (harus antara 1-500 kg)")
        return v


class UserInfoResponse(BaseModel):
    nama: str
    tanggal_lahir: date
    tinggi_badan: float
    berat_badan: float
    bmi: float
    bmi_kategori: str
    berat_ideal: float
    type_foods: List[str]
    type_desserts: List[str]
    alergen_foods: List[str]

    class Config:
        from_attributes = True


class RegisterResponse(BaseModel):
    message: str
    username: str
    user_information: UserInfoResponse


# ── Login ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Username tidak boleh kosong")
        return v.strip()


class LoginResponse(BaseModel):
    message: str
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    username: str
