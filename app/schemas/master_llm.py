from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID
from decimal import Decimal


class MstModelLlmCreateRequest(BaseModel):
    name: str
    input_price: Decimal
    output_price: Decimal

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Nama model tidak boleh kosong")
        return v.strip()

    @field_validator("input_price", "output_price")
    @classmethod
    def price_non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Harga tidak boleh negatif")
        return v


class MstModelLlmUpdateRequest(BaseModel):
    name: Optional[str] = None
    input_price: Optional[Decimal] = None
    output_price: Optional[Decimal] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Nama model tidak boleh kosong")
        return v.strip() if v else v

    @field_validator("input_price", "output_price")
    @classmethod
    def price_non_negative(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError("Harga tidak boleh negatif")
        return v


class MstModelLlmResponse(BaseModel):
    id: UUID
    name: str
    input_price: Decimal
    output_price: Decimal

    class Config:
        from_attributes = True
