from app.core.dependencies import require_basic_plan
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.account_user import AccountUser
from app.schemas.bmi import BMICalculateRequest, BMICalculateResponse
from app.agents.agent_supervisor import run_supervisor

router = APIRouter(prefix="/bmi", tags=["BMI & Health Analysis"])


@router.post(
    "/calculate",
    response_model=BMICalculateResponse,
    status_code=200,
    summary="Hitung dan analisis BMI dengan AI",
    description=(
        "Menghitung BMI menggunakan multi-agent system (LangChain + OpenRouter).\n\n"
        "**Alur agent:**\n"
        "1. `agent_supervisor` menerima request dan mengkoordinasikan agent lain\n"
        "2. `agent_bmi_calculator` menghitung BMI, kategori, berat ideal, dan risiko kesehatan\n"
        "3. `agent_supervisor` mereview hasil dan mengarahkan ke agent berikutnya\n"
        "4. `agent_messaging` menulis pesan personal dan motivasi untuk user\n"
        "5. `agent_supervisor` memverifikasi semua selesai dan mengembalikan hasil akhir"
    ),
)
async def calculate_bmi(
    payload: BMICalculateRequest,
    _: AccountUser = Depends(require_basic_plan),
):
    try:
        result = run_supervisor(
            nama=payload.nama,
            berat_badan=payload.berat_badan,
            tinggi_badan=payload.tinggi_badan,
        )
        return BMICalculateResponse(
            message="Analisis BMI berhasil",
            nama=result["nama"],
            bmi_analysis=result["bmi_analysis"],
            personal_message=result["personal_message"],
            iterations=result["iterations"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal menjalankan analisis BMI: {str(e)}",
        )


@router.post(
    "/calculate/guest",
    response_model=BMICalculateResponse,
    status_code=200,
    summary="Hitung BMI tanpa login (guest)",
    description="Endpoint publik untuk menghitung BMI tanpa autentikasi.",
)
async def calculate_bmi_guest(payload: BMICalculateRequest):
    try:
        result = run_supervisor(
            nama=payload.nama,
            berat_badan=payload.berat_badan,
            tinggi_badan=payload.tinggi_badan,
        )
        return BMICalculateResponse(
            message="Analisis BMI berhasil",
            nama=result["nama"],
            bmi_analysis=result["bmi_analysis"],
            personal_message=result["personal_message"],
            iterations=result["iterations"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal menjalankan analisis BMI: {str(e)}",
        )
