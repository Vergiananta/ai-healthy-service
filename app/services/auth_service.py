from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from passlib.context import CryptContext
from zoneinfo import ZoneInfo

from app.models.account_user import AccountUser
from app.models.user_information import UserInformation
from app.models.weight_histories import WeightHistories
from app.models.master import MstTypeFood, MstAlergenFood, MstTypeDessert
from app.schemas.auth import RegisterRequest, RegisterResponse, UserInfoResponse
from app.agents.agent_food import generate_registration_food_plan
from app.services.bmi_service import calculate_bmi, get_bmi_kategori, calculate_berat_ideal
from app.models.llm_request import LLMRequest

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JAKARTA_TZ = ZoneInfo("Asia/Jakarta")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def register_user(db: Session, payload: RegisterRequest) -> RegisterResponse:
    # 1. Cek apakah username sudah dipakai
    existing = db.query(AccountUser).filter(AccountUser.username == payload.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{payload.username}' sudah digunakan",
        )

    # 2. Validasi master data: type_food_ids (UUID)
    type_foods = db.query(MstTypeFood).filter(MstTypeFood.id.in_(payload.type_food_ids)).all()
    if len(type_foods) != len(payload.type_food_ids):
        found_ids = {f.id for f in type_foods}
        missing = set(payload.type_food_ids) - found_ids
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Type food ID tidak ditemukan: {missing}",
        )

    # 3. Validasi master data: type_dessert_ids (UUID)
    type_desserts = db.query(MstTypeDessert).filter(MstTypeDessert.id.in_(payload.type_dessert_ids)).all()
    if len(type_desserts) != len(payload.type_dessert_ids):
        found_ids = {d.id for d in type_desserts}
        missing = set(payload.type_dessert_ids) - found_ids
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Type dessert ID tidak ditemukan: {missing}",
        )

    # 4. Validasi master data: alergen_food_ids (UUID, boleh kosong)
    alergen_foods = []
    if payload.alergen_food_ids:
        alergen_foods = db.query(MstAlergenFood).filter(MstAlergenFood.id.in_(payload.alergen_food_ids)).all()
        if len(alergen_foods) != len(payload.alergen_food_ids):
            found_ids = {a.id for a in alergen_foods}
            missing = set(payload.alergen_food_ids) - found_ids
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Alergen food ID tidak ditemukan: {missing}",
            )

    # 5. Hitung BMI dan berat ideal
    bmi = calculate_bmi(payload.berat_badan, payload.tinggi_badan)
    bmi_kategori = get_bmi_kategori(bmi)
    berat_ideal = calculate_berat_ideal(payload.tinggi_badan)

    # 6. Buat AccountUser (UUID auto-generated via model default)
    account_user = AccountUser(
        username=payload.username,
        password_hash=hash_password(payload.password),
        plan="BASIC",
    )
    db.add(account_user)
    db.flush()

    # 7. Buat UserInformation (UUID auto-generated via model default)
    user_info = UserInformation(
        account_user_id=account_user.id,
        nama=payload.nama,
        tanggal_lahir=payload.tanggal_lahir,
        tinggi_badan=payload.tinggi_badan,
        berat_badan=payload.berat_badan,
        bmi=bmi,
        bmi_kategori=bmi_kategori,
        berat_ideal=berat_ideal,
        type_foods=type_foods,
        type_desserts=type_desserts,
        alergen_foods=alergen_foods,
    )
    db.add(user_info)
    db.flush()

    # 8. Catat berat awal di weight_histories (snapshot saat register)
    initial_weight = WeightHistories(
        user_information_id=user_info.id,
        berat_badan=payload.berat_badan,
        tinggi_badan=payload.tinggi_badan,
        bmi=bmi,
        bmi_kategori=bmi_kategori,
        catatan="Berat badan awal saat registrasi",
    )
    db.add(initial_weight)

    # 9. Generate food plan otomatis saat register:
    # calorie agent -> schedule agent -> food agent (dengan preferensi/alergi user).
    generate_registration_food_plan(
        db=db,
        user_info=user_info,
        plan_date=datetime.now(JAKARTA_TZ).date(),
    )

    db.commit()
    db.refresh(user_info)

    # 10. Jalankan agent_messaging untuk memberi pesan motivasi personal terkait BMI
    suggest = None
    try:
        from app.agents.agent_supervisor import run_supervisor
        supervisor_result = run_supervisor(
            nama=payload.nama,
            berat_badan=payload.berat_badan,
            tinggi_badan=payload.tinggi_badan
        )
        suggest = supervisor_result.get("personal_message", {})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Gagal menjalankan agent_messaging saat registrasi: {e}", exc_info=True)
        suggest = {
            "greeting": f"Halo {payload.nama}!",
            "bmi_explanation": f"BMI Anda adalah {bmi} ({bmi_kategori}).",
            "health_status": "Analisis personal AI saat ini sedang tidak tersedia secara real-time.",
            "recommendations": ["Jaga pola makan sehat dan olahraga teratur secara rutin."],
            "motivation": "Semangat untuk memulai perjalanan hidup sehat Anda!",
            "next_steps": "Gunakan aplikasi Healthy AI untuk melacak berat badan dan makanan harian Anda."
        }

    # Catat penggunaan LLM saat registrasi secara keseluruhan untuk 1 kali hit API
    try:
        llm_req = LLMRequest(
            account_user_id=account_user.id,
            request_date=datetime.now(JAKARTA_TZ).date(),
        )
        db.add(llm_req)
        db.commit()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Gagal mencatat LLMRequest saat registrasi: {e}", exc_info=True)

    # 11. Susun response
    return RegisterResponse(
        message="Registrasi berhasil",
        username=account_user.username,
        plan="BASIC",
        user_information=UserInfoResponse(
            nama=user_info.nama,
            tanggal_lahir=user_info.tanggal_lahir,
            tinggi_badan=user_info.tinggi_badan,
            berat_badan=user_info.berat_badan,
            bmi=user_info.bmi,
            bmi_kategori=user_info.bmi_kategori,
            berat_ideal=user_info.berat_ideal,
            type_foods=[f.name for f in user_info.type_foods],
            type_desserts=[d.name for d in user_info.type_desserts],
            alergen_foods=[a.name for a in user_info.alergen_foods],
            plan=account_user.plan,
        ),
        suggest=suggest,
    )
