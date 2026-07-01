from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_basic_plan
from app.database import get_db
from app.models.account_user import AccountUser
from app.schemas.auth import UserInfoResponse
from app.services import profile_service

router = APIRouter(prefix="/profile", tags=["User Profile"])

@router.get("", response_model=UserInfoResponse, summary="Get user profile by user ID", description="Returns full user information, including latest BMI, weight, and height, for the specified user ID. Requires authentication.")
async def get_user_profile_by_id(current_user: AccountUser = Depends(require_basic_plan), db: Session = Depends(get_db)) -> UserInfoResponse:
    return profile_service.get_user_profile(db, current_user.id)
