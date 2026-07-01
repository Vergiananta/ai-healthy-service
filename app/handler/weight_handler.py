from app.core.dependencies import require_basic_plan
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.account_user import AccountUser
from app.models.weight_histories import WeightHistories
from app.schemas.weight import WeightHistoryRequest, WeightHistoryResponse
from pydantic import BaseModel

router = APIRouter(prefix="/weight", tags=["Weight History"])

class WeightHistoryListResponse(BaseModel):
    data: List[WeightHistoryResponse]

    # Existing GET endpoint omitted for brevity

@router.post("/record", response_model=WeightHistoryResponse, summary="Create weight/height record", description="Accepts height and weight, calculates BMI and category, stores the record for the authenticated user.")
async def create_weight_record(payload: WeightHistoryRequest, current_user: AccountUser = Depends(require_basic_plan), db: Session = Depends(get_db)) -> WeightHistoryResponse:
    # Calculate BMI (height in cm -> meters)
    height_m = payload.tinggi_badan / 100.0
    bmi = round(payload.berat_badan / (height_m ** 2), 2) if height_m > 0 else None
    # Determine BMI category
    if bmi is None:
        bmi_category = None
    elif bmi < 18.5:
        bmi_category = "Underweight"
    elif bmi < 25:
        bmi_category = "Normal"
    elif bmi < 30:
        bmi_category = "Overweight"
    else:
        bmi_category = "Obese"
    # Create record linked to user's UserInformation
    if not current_user.user_information:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User profile not found")
    new_entry = WeightHistories(
        user_information_id=current_user.user_information.id,
        berat_badan=payload.berat_badan,
        tinggi_badan=payload.tinggi_badan,
        bmi=bmi,
        bmi_kategori=bmi_category,
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return WeightHistoryResponse(
        id=str(new_entry.id),
        tanggal=new_entry.recorded_at.date(),
        berat_badan=new_entry.berat_badan,
        tinggi_badan=new_entry.tinggi_badan,
        bmi=new_entry.bmi,
        bmi_kategori=new_entry.bmi_kategori,
    )

# Existing GET endpoint
@router.get("/histories", response_model=WeightHistoryListResponse, summary="Get all weight histories", description="Returns all recorded weight and height entries for the authenticated user, ordered by most recent.")
async def get_weight_histories(current_user: AccountUser = Depends(require_basic_plan), db: Session = Depends(get_db)) -> WeightHistoryListResponse:
    histories = (
        db.query(WeightHistories)
        .join(WeightHistories.user_information)
        .filter(WeightHistories.user_information_id == current_user.user_information.id)
        .order_by(WeightHistories.recorded_at.desc())
        .all()
    )
    # Convert ORM objects to response models
    resp = [
        WeightHistoryResponse(
            id=str(h.id),
            tanggal=h.recorded_at.date(),
            berat_badan=h.berat_badan,
            tinggi_badan=h.tinggi_badan,
            bmi=h.bmi,
            bmi_kategori=h.bmi_kategori,
        )
        for h in histories
    ]
    return WeightHistoryListResponse(data=resp)
