import uuid
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

# Association table: UserInformation <-> MstTypeFood
user_type_food = Table(
    "user_type_food",
    Base.metadata,
    Column("user_information_id", UUID(as_uuid=True), ForeignKey("user_information.id"), primary_key=True),
    Column("mst_type_food_id", UUID(as_uuid=True), ForeignKey("mst_type_food.id"), primary_key=True),
)

# Association table: UserInformation <-> MstAlergenFood
user_alergen_food = Table(
    "user_alergen_food",
    Base.metadata,
    Column("user_information_id", UUID(as_uuid=True), ForeignKey("user_information.id"), primary_key=True),
    Column("mst_alergen_food_id", UUID(as_uuid=True), ForeignKey("mst_alergen_food.id"), primary_key=True),
)

# Association table: UserInformation <-> MstTypeDessert
user_type_dessert = Table(
    "user_type_dessert",
    Base.metadata,
    Column("user_information_id", UUID(as_uuid=True), ForeignKey("user_information.id"), primary_key=True),
    Column("mst_type_dessert_id", UUID(as_uuid=True), ForeignKey("mst_type_dessert.id"), primary_key=True),
)
