import redis
import os

from app.core import load_app_env

load_app_env()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None) or None
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Connection pool agar koneksi efisien dan reusable
_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=REDIS_DB,
    decode_responses=True,  # semua value otomatis string
)


def get_redis() -> redis.Redis:
    """Mengembalikan Redis client dari connection pool."""
    return redis.Redis(connection_pool=_pool)


def test_redis_connection() -> bool:
    """
    Test koneksi Redis dan return True jika berhasil.
    Digunakan saat startup aplikasi.
    """
    try:
        client = get_redis()
        client.ping()
        return True
    except Exception as e:
        print(f"[Redis] ❌ Gagal terhubung ke Redis: {e}")
        return False

