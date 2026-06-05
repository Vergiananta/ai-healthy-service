from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.weight_histories import WeightHistories

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.account_user import AccountUser
from app.schemas.auth import UserInfoResponse

router = APIRouter(prefix="/profile", tags=["User Profile"])

@router.get("", response_model=UserInfoResponse, summary="Get user profile by user ID", description="Returns full user information, including latest BMI, weight, and height, for the specified user ID. Requires authentication.")
async def get_user_profile_by_id(current_user: AccountUser = Depends(get_current_user), db: Session = Depends(get_db)) -> UserInfoResponse:
    # Fetch the target user account
    target_account = db.query(AccountUser).filter(AccountUser.id == current_user.id).first()
    if not target_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user_info = target_account.user_information
    if not user_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
    # Fetch latest weight history for this user
    latest_weight = (
        db.query(WeightHistories)
        .filter(WeightHistories.user_information_id == user_info.id)
        .order_by(WeightHistories.recorded_at.desc())
        .first()
    )
    # Use latest weight if available, otherwise fall back to stored info
    if latest_weight:
        berat = latest_weight.berat_badan
        tinggi = latest_weight.tinggi_badan
        bmi = round(berat / ((tinggi / 100) ** 2), 2) if tinggi else None
    else:
        berat = user_info.berat_badan
        tinggi = user_info.tinggi_badan
        bmi = user_info.bmi
    # Build response data matching UserInfoResponse schema
    response_data = {
        "nama": user_info.nama,
        "tanggal_lahir": user_info.tanggal_lahir,
        "tinggi_badan": tinggi,
        "berat_badan": berat,
        "bmi": bmi,
        "bmi_kategori": user_info.bmi_kategori,
        "berat_ideal": user_info.berat_ideal,
        "type_foods": [t.name for t in user_info.type_foods],
        "type_desserts": [d.name for d in user_info.type_desserts],
        "alergen_foods": [a.name for a in user_info.alergen_foods],
    }
    return UserInfoResponse(**response_data)
