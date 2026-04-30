import redis as redis_lib
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.models.account_user import AccountUser
from app.schemas.auth import LoginRequest, LoginResponse
from app.core.jwt_utils import (
    create_access_token,
    get_token_ttl_seconds,
    REDIS_TOKEN_PREFIX,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def login_user(db: Session, redis: redis_lib.Redis, payload: LoginRequest) -> LoginResponse:
    # 1. Cari user berdasarkan username
    account = db.query(AccountUser).filter(AccountUser.username == payload.username).first()

    if not account or not verify_password(payload.password, account.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not account.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun tidak aktif, hubungi administrator",
        )

    # 2. Buat JWT token — user_id di-cast ke string karena UUID tidak JSON-serializable
    token = create_access_token(data={"sub": account.username, "user_id": str(account.id)})
    ttl = get_token_ttl_seconds()

    # 3. Simpan token ke Redis dengan TTL 1 minggu
    #    Key  : "token:<username>"
    #    Value: token string
    #    EX   : TTL dalam detik
    redis_key = f"{REDIS_TOKEN_PREFIX}{account.username}"
    redis.setex(redis_key, ttl, token)

    return LoginResponse(
        message="Login berhasil",
        access_token=token,
        token_type="bearer",
        expires_in_seconds=ttl,
        username=account.username,
    )
