import redis as redis_lib
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.redis_client import get_redis
from app.core.dependencies import get_current_user
from app.core.jwt_utils import REDIS_TOKEN_PREFIX
from app.models.account_user import AccountUser
from app.schemas.auth import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse
from app.services.auth_service import register_user
from app.services.login_service import login_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=201,
    summary="Register pengguna baru",
    description=(
        "Mendaftarkan pengguna baru dengan informasi akun dan data kesehatan. "
        "BMI dan berat ideal akan dihitung otomatis dari tinggi dan berat badan."
    ),
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    return register_user(db, payload)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=200,
    summary="Login pengguna",
    description=(
        "Login dengan username dan password. "
        "Mengembalikan JWT access token yang disimpan di Redis dengan TTL 1 minggu."
    ),
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
    redis: redis_lib.Redis = Depends(get_redis),
):
    return login_user(db, redis, payload)


@router.post(
    "/logout",
    status_code=200,
    summary="Logout pengguna",
    description="Menghapus token dari Redis sehingga sesi langsung tidak valid.",
)
def logout(
    current_user: AccountUser = Depends(get_current_user),
    redis: redis_lib.Redis = Depends(get_redis),
):
    redis_key = f"{REDIS_TOKEN_PREFIX}{current_user.username}"
    redis.delete(redis_key)
    return {"message": f"Logout berhasil. Sampai jumpa, {current_user.username}!"}
