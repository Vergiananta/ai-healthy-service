import uuid
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class AccountUser(Base):
    """
    Stores authentication credentials for a user.
    Has a OneToOne relationship with UserInformation.
    """
    __tablename__ = "account_user"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # OneToOne relationship with UserInformation
    user_information = relationship(
        "UserInformation",
        back_populates="account_user",
        uselist=False,
        cascade="all, delete-orphan",
    )
