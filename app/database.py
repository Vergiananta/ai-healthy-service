from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import urllib.parse

from app.core import load_app_env

load_app_env()

def _build_postgres_url(
    *,
    user: str,
    password: str,
    host: str,
    port: str,
    database: str,
    query: dict[str, str] | None = None,
) -> str:
    safe_user = urllib.parse.quote_plus(user or "")
    safe_password = urllib.parse.quote_plus(password or "")
    safe_host = host or "localhost"
    safe_port = str(port or "5432")
    safe_db = urllib.parse.quote_plus(database or "")

    base = f"postgresql://{safe_user}:{safe_password}@{safe_host}:{safe_port}/{safe_db}"
    if not query:
        return base
    return f"{base}?{urllib.parse.urlencode(query)}"


def _normalize_postgres_url(raw_url: str) -> str:
    raw_url = (raw_url or "").strip()
    if not raw_url:
        return ""

    scheme_split = raw_url.split("://", 1)
    if len(scheme_split) != 2:
        return raw_url

    scheme, rest = scheme_split
    if scheme not in {"postgresql", "postgres"}:
        return raw_url

    if "@" not in rest:
        return raw_url

    userinfo, host_and_path = rest.rsplit("@", 1)
    if ":" in userinfo:
        user, password = userinfo.split(":", 1)
    else:
        user, password = userinfo, ""

    if "/" in host_and_path:
        hostport, path_and_query = host_and_path.split("/", 1)
    else:
        hostport, path_and_query = host_and_path, ""

    if "?" in path_and_query:
        database, query_string = path_and_query.split("?", 1)
    else:
        database, query_string = path_and_query, ""

    host = hostport
    port = ""
    if ":" in hostport:
        host, port = hostport.rsplit(":", 1)

    query = dict(urllib.parse.parse_qsl(query_string, keep_blank_values=True)) if query_string else None
    port_value = port or os.getenv("DB_PORT", "5432")
    normalized = _build_postgres_url(
        user=user,
        password=password,
        host=host,
        port=port_value,
        database=database,
        query=query,
    )
    return normalized


def _ensure_sslmode_require(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return url
    split = urllib.parse.urlsplit(url)
    query = dict(urllib.parse.parse_qsl(split.query, keep_blank_values=True))
    if "sslmode" in query and query["sslmode"]:
        return url
    query["sslmode"] = "require"
    return urllib.parse.urlunsplit(
        (split.scheme, split.netloc, split.path, urllib.parse.urlencode(query), split.fragment)
    )


APP_ENV = (os.getenv("APP_ENV") or os.getenv("ENV") or "dev").strip().lower()

DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip()
if not DATABASE_URL:
    if APP_ENV in {"prod", "production"}:
        DATABASE_URL = (os.getenv("SUPABASE_DB") or "").strip()

if DATABASE_URL:
    DATABASE_URL = _normalize_postgres_url(DATABASE_URL)
else:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "healthy-ai")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DATABASE_URL = _build_postgres_url(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
    )

if APP_ENV in {"prod", "production"}:
    DATABASE_URL = _ensure_sslmode_require(DATABASE_URL)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
