from fastapi import APIRouter, Depends, HTTPException, status

from app.agents.agent_food import run_food_agent
from app.core.dependencies import get_current_user
from app.models.account_user import AccountUser
from app.schemas.food import FoodPlanRequest, FoodPlanResponse

router = APIRouter(prefix="/food", tags=["Food Planning"])


@router.post(
    "/plan",
    response_model=FoodPlanResponse,
    status_code=200,
    summary="Generate food plan based on BMI and schedule",
    description="Rantai agent: calorie calculator -> schedule -> food recommendation.",
)
async def generate_food_plan(
    payload: FoodPlanRequest,
    current_user: AccountUser = Depends(get_current_user),
) -> FoodPlanResponse:
    try:
        result = run_food_agent(
            account_user_id=current_user.id,
            plan_date=payload.tanggal,
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate food plan: {str(e)}",
        )
