from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.version import AppVersionResponse, AppVersionCreate
from app.services import version_service

router = APIRouter(prefix="/app", tags=["App Version"])

@router.get("/version-check", response_model=AppVersionResponse, summary="Check app version and update requirements")
async def check_app_version(
    platform: str = Query("android", description="Platform name, e.g., android or ios"),
    db: Session = Depends(get_db)
) -> AppVersionResponse:
    return version_service.get_latest_version(db, platform)

@router.post("/create-version", response_model=AppVersionResponse, summary="Create app version")
async def create_app_version(
    payload: AppVersionCreate,
    db: Session = Depends(get_db)
) -> AppVersionResponse:
    db_version = version_service.create_app_version(db, payload)
    return AppVersionResponse(
        latest_version=db_version.latest_version,
        force_update=db_version.force_update,
        update_url=db_version.update_url or "",
        release_notes=db_version.release_notes or ""
    )