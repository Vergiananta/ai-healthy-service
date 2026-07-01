from sqlalchemy.orm import Session
from app.models.app_version import AppVersion
from app.schemas.version import AppVersionCreate, AppVersionResponse

def get_latest_version(db: Session, platform: str = "android") -> AppVersionResponse:
    latest = (
        db.query(AppVersion)
        .filter(AppVersion.platform == platform)
        .order_by(AppVersion.created_at.desc())
        .first()
    )
    if latest:
        return AppVersionResponse(
            latest_version=latest.latest_version,
            force_update=latest.force_update,
            update_url=latest.update_url or "",
            release_notes=latest.release_notes or "",
        )
    
    # Fallback default version if no record exists in db
    return AppVersionResponse(
        latest_version="1.0.0",
        force_update=False,
        update_url="https://play.google.com/store/apps/details?id=com.nutrimatch.app",
        release_notes="• Desain antarmuka baru yang lebih premium\n• Optimasi performa dan perbaikan bug\n• Pelacakan BMI harian yang lebih interaktif"
    )

def create_app_version(db: Session, payload: AppVersionCreate) -> AppVersion:
    db_version = AppVersion(
        platform=payload.platform,
        latest_version=payload.latest_version,
        force_update=payload.force_update,
        update_url=payload.update_url,
        release_notes=payload.release_notes,
    )
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version