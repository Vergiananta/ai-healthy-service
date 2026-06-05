import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

_ENV_LOADED = False


def load_app_env() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return

    root_dir = Path(__file__).resolve().parents[2]

    explicit_dotenv_file = os.getenv("DOTENV_FILE", "").strip()
    if explicit_dotenv_file:
        dotenv_path = Path(explicit_dotenv_file)
        if not dotenv_path.is_absolute():
            dotenv_path = root_dir / dotenv_path
    else:
        env_name = (os.getenv("APP_ENV") or os.getenv("ENV") or "dev").strip().lower()
        if env_name in {"prod", "production"}:
            dotenv_path = root_dir / ".env.prod"
        else:
            dotenv_path = root_dir / ".env.dev"

        if not dotenv_path.exists():
            fallback = root_dir / ".env"
            if fallback.exists():
                dotenv_path = fallback

    load_dotenv(dotenv_path=dotenv_path, override=False)
    _ENV_LOADED = True
