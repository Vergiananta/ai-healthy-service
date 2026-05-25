from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_user
from app.models.account_user import AccountUser
from app.schemas.food import FoodPlanRequest, FoodPlanResponse
from app.agents.agent_food import run_food_agent

router = APIRouter(prefix="/food", tags=["Food Planning"])

@router.post(
    "/plan",
    response_model=FoodPlanResponse,
    status_code=200,
    summary="Generate food plan based on BMI and schedule",
    description="Calculate ideal weight, BMI category, meal schedule, and suggest foods. Records each food entry into FoodHistories.",
)
async def generate_food_plan(
    payload: FoodPlanRequest,
    current_user: AccountUser = Depends(get_current_user),
) -> FoodPlanResponse:
    try:
        result = run_food_agent(
            user_id=current_user.id,
            gender=payload.gender,
        )
        return FoodPlanResponse(
            ideal_weight=result["ideal_weight"],
            bmi_category=result["bmi_category"],
            schedule=result["schedule"],
            foods=result["foods"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate food plan: {str(e)}",
        )
