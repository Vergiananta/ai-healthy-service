from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.account_user import AccountUser
from app.schemas.food import (
    CreateScheduleMenuRequest,
    FoodPlanResponse,
    MenuByDateItemResponse,
    MenuByDateListResponse,
)
from app.services.schedule_menu_service import create_schedule_menu_for_user, find_menus_by_date

router = APIRouter(prefix="/schedule-menu", tags=["Schedule Menu"])


@router.post(
    "",
    response_model=FoodPlanResponse,
    status_code=200,
    summary="Create meal schedule and menu by date",
    description=(
        "Alur agent: agent_bmi_calculator -> agent_calorie_calculator -> "
        "agent_schedule -> agent_food."
    ),
)
async def create_schedule_menu(
    payload: CreateScheduleMenuRequest,
    current_user: AccountUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FoodPlanResponse:
    try:
        result = create_schedule_menu_for_user(
            db=db,
            current_user=current_user,
            tinggi_badan=payload.tinggi_badan,
            berat_badan=payload.berat_badan,
            tanggal=payload.tanggal,
            gender=payload.gender,
            activity_level=payload.activity_level,
        )
        return FoodPlanResponse(
            ideal_weight=result["ideal_weight"],
            bmi_category=result["bmi_category"],
            total_daily_calories=result["total_daily_calories"],
            schedule=result["schedule"],
            foods=result["foods"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create schedule menu: {str(e)}",
        )

def _parse_tanggal_param(tanggal: str):
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(tanggal, fmt).date()
        except ValueError:
            continue
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Format tanggal harus DD-MM-YYYY atau YYYY-MM-DD",
    )


@router.get("", response_model=MenuByDateListResponse, status_code=200)
async def get_menus_by_date(
    tanggal: str,
    current_user: AccountUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MenuByDateListResponse:
    try:
        tanggal_date = _parse_tanggal_param(tanggal)
        result = find_menus_by_date(db=db, current_user=current_user, tanggal=tanggal_date)
        return MenuByDateListResponse(
            data=[MenuByDateItemResponse(**item) for item in result]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get menus by date: {str(e)}",
        )
