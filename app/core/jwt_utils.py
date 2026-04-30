from datetime import datetime, timedelta, timezone
from typing import Optional
import os
from dotenv import load_dotenv
from jose import JWTError, jwt

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-to-a-strong-random-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 10080))  # 1 minggu

# Prefix key di Redis: "token:<username>"
REDIS_TOKEN_PREFIX = "token:"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Buat JWT access token.
    - data  : payload yang akan di-encode (wajib ada 'sub' berisi username)
    - expires_delta : durasi expired, default 1 minggu
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode dan validasi JWT token.
    Raise JWTError jika token tidak valid atau sudah expired.
    """
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


def get_token_ttl_seconds() -> int:
    """Kembalikan TTL token dalam detik (untuk disimpan ke Redis)."""
    return JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
