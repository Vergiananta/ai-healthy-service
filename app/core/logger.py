import logging
import os
from logging.handlers import TimedRotatingFileHandler

# ── Direktori log ─────────────────────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logging")
os.makedirs(LOG_DIR, exist_ok=True)

ERROR_LOG_PATH = os.path.join(LOG_DIR, "error.log")
APP_LOG_PATH   = os.path.join(LOG_DIR, "app.log")

# ── Format ────────────────────────────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)


def _make_rotating_handler(path: str, level: int) -> TimedRotatingFileHandler:
    """
    File handler yang rotate setiap tengah malam,
    menyimpan 30 hari backup, dan encode UTF-8.
    """
    handler = TimedRotatingFileHandler(
        filename=path,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler


def setup_logging() -> None:
    """
    Konfigurasi root logger:
    - Console  : INFO ke atas
    - app.log  : INFO ke atas  (semua aktivitas)
    - error.log: ERROR ke atas (hanya error & critical)

    Dipanggil sekali saat startup di main.py.
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Hindari duplikasi handler jika setup dipanggil lebih dari sekali
    if root.handlers:
        return

    # 1. Console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    root.addHandler(console)

    # 2. app.log — semua level INFO ke atas
    root.addHandler(_make_rotating_handler(APP_LOG_PATH, logging.INFO))

    # 3. error.log — hanya ERROR dan CRITICAL
    root.addHandler(_make_rotating_handler(ERROR_LOG_PATH, logging.ERROR))

    logging.info(f"[Logger] Logging aktif → app: {APP_LOG_PATH} | error: {ERROR_LOG_PATH}")
