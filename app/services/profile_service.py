from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.account_user import AccountUser
from app.models.weight_histories import WeightHistories
from app.schemas.auth import UserInfoResponse

def get_user_profile(db: Session, current_user_id: str) -> UserInfoResponse:
    # Fetch the target user account
    target_account = db.query(AccountUser).filter(AccountUser.id == current_user_id).first()
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
        "plan": target_account.plan,
    }
    return UserInfoResponse(**response_data)
