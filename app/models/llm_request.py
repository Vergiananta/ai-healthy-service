import uuid
from datetime import date
from sqlalchemy import Column, Date, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class LLMRequest(Base):
    __tablename__ = "llm_request"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_user_id = Column(UUID(as_uuid=True), ForeignKey('account_user.id'), nullable=False)
    request_date = Column(Date, nullable=False, default=date.today)

