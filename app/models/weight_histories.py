import uuid
from sqlalchemy import Column, Float, ForeignKey, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class WeightHistories(Base):
    """
    Menyimpan riwayat berat badan pengguna.
    Relasi: UserInformation OneToMany WeightHistories
    """
    __tablename__ = "weight_histories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_information_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_information.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    berat_badan = Column(Float, nullable=False, comment="Berat badan dalam kg")
    bmi = Column(Float, nullable=True, comment="BMI saat pencatatan")
    bmi_kategori = Column(String(50), nullable=True, comment="Kategori BMI saat pencatatan")
    catatan = Column(String(255), nullable=True, comment="Catatan tambahan opsional")

    recorded_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Waktu pencatatan berat badan",
    )

    # ManyToOne back-reference ke UserInformation
    user_information = relationship("UserInformation", back_populates="weight_histories")
