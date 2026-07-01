import uuid
from sqlalchemy import Column, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.associations import user_type_food, user_alergen_food, user_type_dessert


class UserInformation(Base):
    """
    Stores personal and health information for a user.
    OneToOne with AccountUser, ManyToMany with food/dessert/allergen masters.
    """
    __tablename__ = "user_information"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    account_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("account_user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Personal info
    nama = Column(String(150), nullable=False)
    tanggal_lahir = Column(Date, nullable=False)

    # Health metrics
    tinggi_badan = Column(Float, nullable=False, comment="Tinggi badan dalam cm")
    berat_badan = Column(Float, nullable=False, comment="Berat badan dalam kg")
    bmi = Column(Float, nullable=True, comment="Body Mass Index (auto-calculated)")
    berat_ideal = Column(Float, nullable=True, comment="Berat ideal dalam kg (auto-calculated)")
    bmi_kategori = Column(String(50), nullable=True, comment="Kategori BMI: Underweight, Normal, Overweight, Obese")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # OneToOne back-reference to AccountUser
    account_user = relationship("AccountUser", back_populates="user_information")

    # ManyToMany: tipe makanan yang disukai
    type_foods = relationship(
        "MstTypeFood",
        secondary=user_type_food,
        back_populates="user_informations",
    )

    # ManyToMany: alergi makanan
    alergen_foods = relationship(
        "MstAlergenFood",
        secondary=user_alergen_food,
        back_populates="user_informations",
    )

    # ManyToMany: tipe dessert yang disukai
    type_desserts = relationship(
        "MstTypeDessert",
        secondary=user_type_dessert,
        back_populates="user_informations",
    )

    # OneToMany: riwayat berat badan
    weight_histories = relationship(
        "WeightHistories",
        back_populates="user_information",
        cascade="all, delete-orphan",
        order_by="WeightHistories.recorded_at.desc()",
    )

    # OneToMany: riwayat makanan yang dikonsumsi
    food_histories = relationship(
        "FoodHistories",
        back_populates="user_information",
        cascade="all, delete-orphan",
        order_by="FoodHistories.recorded_at.desc()",
    )
