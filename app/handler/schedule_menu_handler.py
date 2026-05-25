from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.account_user import AccountUser
from app.schemas.food import CreateScheduleMenuRequest, FoodPlanResponse
from app.services.schedule_menu_service import create_schedule_menu_for_user

router = APIRouter(tags=["Schedule Menu"])


@router.post(
    "/create-schedule-menu",
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
