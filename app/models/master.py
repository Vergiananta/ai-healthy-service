import uuid
from sqlalchemy import Column, String, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.associations import user_type_food, user_alergen_food, user_type_dessert


class MstTypeFood(Base):
    """
    Master table for food types.
    Examples: Western, Southeast Asia, Middle East, East Asia, Latin America, Other
    """
    __tablename__ = "mst_type_food"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    user_informations = relationship(
        "UserInformation",
        secondary=user_type_food,
        back_populates="type_foods",
    )


class MstAlergenFood(Base):
    """
    Master table for food allergens.
    Examples: Gluten, Dairy, Nuts, Seafood, Eggs, Soy, etc.
    """
    __tablename__ = "mst_alergen_food"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    user_informations = relationship(
        "UserInformation",
        secondary=user_alergen_food,
        back_populates="alergen_foods",
    )


class MstTypeDessert(Base):
    """
    Master table for dessert types.
    Examples: Buah, Kue Manis, Kue Asin, Es Krim, etc.
    """
    __tablename__ = "mst_type_dessert"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    user_informations = relationship(
        "UserInformation",
        secondary=user_type_dessert,
        back_populates="type_desserts",
    )


class MstModelLlm(Base):
    """Master table for LLM models."""
    __tablename__ = "mst_model_llm"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    input_price = Column(Numeric(precision=10, scale=4), nullable=False, comment="Harga per 1K input token (USD)")
    output_price = Column(Numeric(precision=10, scale=4), nullable=False, comment="Harga per 1K output token (USD)")

    # OneToMany: riwayat penggunaan model ini
    usage_histories = relationship(
        "HistoryLlmUsage",
        back_populates="mst_model_llm",
        cascade="all, delete-orphan",
    )
