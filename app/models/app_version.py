import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class AppVersion(Base):
    __tablename__ = "app_version"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    platform = Column(String(50), nullable=False, default="android", index=True)
    latest_version = Column(String(50), nullable=False)
    force_update = Column(Boolean, default=False, nullable=False)
    update_url = Column(String(512), nullable=True)
    release_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
