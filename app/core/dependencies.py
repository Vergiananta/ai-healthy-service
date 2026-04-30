import redis as redis_lib
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.redis_client import get_redis
from app.core.jwt_utils import decode_access_token, REDIS_TOKEN_PREFIX
from app.models.account_user import AccountUser

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    redis: redis_lib.Redis = Depends(get_redis),
) -> AccountUser:
    """
    Dependency untuk endpoint yang membutuhkan autentikasi.
    1. Decode JWT dan ambil username
    2. Cek token masih ada di Redis (belum logout / belum expired)
    3. Return AccountUser yang sedang login
    """
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau sudah expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Validasi token di Redis
    redis_key = f"{REDIS_TOKEN_PREFIX}{username}"
    stored_token = redis.get(redis_key)
    if stored_token != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi tidak ditemukan atau sudah logout",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Ambil user dari DB
    account = db.query(AccountUser).filter(AccountUser.username == username).first()
    if not account or not account.is_active:
        raise credentials_exception

    return account
