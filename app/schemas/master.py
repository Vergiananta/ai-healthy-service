from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class MstTypeFoodSchema(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class MstAlergenFoodSchema(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class MstTypeDessertSchema(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True
