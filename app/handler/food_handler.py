from app.core.dependencies import require_basic_plan
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from zoneinfo import ZoneInfo

from app.agents.agent_food import run_food_agent
from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.account_user import AccountUser
from app.models.llm_request import LLMRequest
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
    current_user: AccountUser = Depends(require_basic_plan),
    db: Session = Depends(get_db),
) -> FoodPlanResponse:
    JAKARTA_TZ = ZoneInfo("Asia/Jakarta")
    today = datetime.now(JAKARTA_TZ).date()

    if current_user.plan == "BASIC":
        llm_request_count = db.query(LLMRequest).filter(
            LLMRequest.account_user_id == current_user.id,
            LLMRequest.request_date == today
        ).count()

        if llm_request_count >= 2:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="anda telah melebihi batas kuota request per hari untuk plan BASIC",
            )

    try:
        result = run_food_agent(
            account_user_id=current_user.id,
            plan_date=payload.tanggal,
            gender=payload.gender,
            activity_level=payload.activity_level,
        )
        response = FoodPlanResponse(
            ideal_weight=result["ideal_weight"],
            bmi_category=result["bmi_category"],
            total_daily_calories=result["total_daily_calories"],
            schedule=result["schedule"],
            foods=result["foods"],
        )
        
        llm_req = LLMRequest(
            account_user_id=current_user.id,
            request_date=today,
        )
        db.add(llm_req)
        db.commit()
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate food plan: {str(e)}",
        )
