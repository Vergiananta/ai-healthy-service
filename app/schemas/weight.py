from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from typing import List

class WeightHistoryRequest(BaseModel):
    @validator('tanggal', pre=True)
    def parse_tanggal(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%d-%m-%Y").date()
            except ValueError:
                raise ValueError("tanggal must be in format DD-MM-YYYY")
        return v
    tanggal: date = Field(..., description="Tanggal pencatatan berat dan tinggi badan")
    berat_badan: float = Field(..., gt=0, lt=500, description="Berat badan dalam kg")
    tinggi_badan: float = Field(..., gt=0, lt=300, description="Tinggi badan dalam cm")



class WeightHistoryResponse(BaseModel):
    id: str
    tanggal: date
    berat_badan: float
    tinggi_badan: float | None = None
    bmi: float | None = None
    bmi_kategori: str | None = None

    class Config:
        orm_mode = True

class WeightHistoryListResponse(BaseModel):
    data: List[WeightHistoryResponse]
