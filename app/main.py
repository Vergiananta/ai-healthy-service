import datetime
import logging
import traceback
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# ── Setup logging PERTAMA sebelum import lain ─────────────────────────────────
from app.core.logger import setup_logging, LOG_FORMAT, DATE_FORMAT

# Gunakan timezone Jakarta untuk semua log timestamp
_JAKARTA_TZ = ZoneInfo("Asia/Jakarta")
logging.Formatter.converter = staticmethod(
    lambda secs: datetime.datetime.fromtimestamp(secs, _JAKARTA_TZ).timetuple()
)
setup_logging()

# ── App imports ───────────────────────────────────────────────────────────────
from app.database import engine, SessionLocal, Base
from app.models import (  # noqa: F401
    AccountUser,
    UserInformation,
    MstTypeFood,
    MstAlergenFood,
    MstTypeDessert,
    MstModelLlm,
    WeightHistories,
    FoodHistories,
    HistoryLlmUsage,
    AppVersion,
    user_type_food,
    user_alergen_food,
    user_type_dessert,
)
from app.handler.auth_handler import router as auth_router
from app.handler.master_handler import router as master_router
from app.handler.bmi_handler import router as bmi_router
from app.handler.food_handler import router as food_router
from app.handler.schedule_menu_handler import router as schedule_menu_router
from app.handler.profile_handler import router as profile_router
from app.handler.weight_handler import router as weight_router
from app.handler.master_llm_handler import router as master_llm_router
from app.handler.version_handler import router as version_router
from app.utils.seeder import seed_master_data
from app.core.redis_client import test_redis_connection, REDIS_HOST, REDIS_PORT, REDIS_DB
import logging
import datetime
from zoneinfo import ZoneInfo
_JAKARTA_TZ = ZoneInfo("Asia/Jakarta")
logging.Formatter.converter = staticmethod(
    lambda secs: datetime.datetime.fromtimestamp(secs, _JAKARTA_TZ).timetuple()
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("[Startup] Membuat tabel jika belum ada...")
    Base.metadata.create_all(bind=engine)
    logger.info("[Startup] Tabel berhasil dibuat / sudah ada.")

    db = SessionLocal()
    try:
        seed_master_data(db)
    finally:
        db.close()

    logger.info(f"[Redis] Menghubungkan ke {REDIS_HOST}:{REDIS_PORT} (db={REDIS_DB})...")
    if test_redis_connection():
        logger.info(f"[Redis] ✅ Connected — {REDIS_HOST}:{REDIS_PORT} (db={REDIS_DB})")
    else:
        logger.warning("[Redis] ⚠️  Aplikasi tetap berjalan, namun fitur login/logout tidak akan berfungsi.")

    yield

    # Shutdown
    logger.info("[Shutdown] Aplikasi berhenti.")


# ── App instance ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Healthy AI API",
    description="API untuk aplikasi kesehatan dengan fitur register, BMI, dan preferensi makanan.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global Exception Handlers ─────────────────────────────────────────────────

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Tangani semua HTTPException (4xx, 5xx).
    Error 5xx dicatat ke error.log, 4xx hanya di app.log.
    """
    if exc.status_code >= 500:
        logger.error(
            f"[HTTP {exc.status_code}] {request.method} {request.url} — {exc.detail}"
        )
    else:
        logger.warning(
            f"[HTTP {exc.status_code}] {request.method} {request.url} — {exc.detail}"
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Tangani error validasi Pydantic (422 Unprocessable Entity).
    Dicatat ke app.log sebagai WARNING.
    """
    errors = exc.errors()
    logger.warning(
        f"[Validation Error] {request.method} {request.url} — {errors}"
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Tangani semua exception yang tidak tertangkap (500 Internal Server Error).
    Selalu dicatat ke error.log beserta full traceback.
    """
    tb = traceback.format_exc()
    logger.error(
        f"[Unhandled Exception] {request.method} {request.url}\n"
        f"Exception: {type(exc).__name__}: {exc}\n"
        f"Traceback:\n{tb}"
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Terjadi kesalahan internal pada server. Silakan coba beberapa saat lagi."},
    )


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth_router, prefix="/api/v1")
app.include_router(master_router, prefix="/api/v1")
app.include_router(bmi_router, prefix="/api/v1")
app.include_router(food_router, prefix="/api/v1")
app.include_router(schedule_menu_router, prefix="/api/v1")
app.include_router(profile_router, prefix="/api/v1")
app.include_router(weight_router, prefix="/api/v1")
app.include_router(master_llm_router, prefix="/api/v1")
app.include_router(version_router)


@app.get("/", tags=["Health Check"])
def root():
    return {"status": "ok", "message": "Healthy AI API is running"}
