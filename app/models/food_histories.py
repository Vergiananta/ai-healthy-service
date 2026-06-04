import uuid
from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class FoodHistories(Base):
    """
    Menyimpan riwayat makanan yang dikonsumsi pengguna.
    Relasi: UserInformation OneToMany FoodHistories
    """
    __tablename__ = "food_histories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_information_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_information.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String(100), nullable=False, comment="Nama makanan")
    composition = Column(String(255), nullable=True, comment="Komposisi / bahan makanan")
    total_calories = Column(Float, nullable=True, comment="Total kalori (kkal)")
    catatan = Column(String(255), nullable=True, comment="Catatan tambahan opsional")

    recorded_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Waktu pencatatan konsumsi makanan",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Waktu pembuatan record",
    )
    # ManyToOne back-reference ke UserInformation
    user_information = relationship("UserInformation", back_populates="food_histories")
