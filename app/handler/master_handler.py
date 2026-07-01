from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.master import MstTypeFood, MstAlergenFood, MstTypeDessert
from app.schemas.master import MstTypeFoodSchema, MstAlergenFoodSchema, MstTypeDessertSchema

router = APIRouter(prefix="/master", tags=["Master Data"])
class TypeFoodResponse(BaseModel):
    data: List[MstTypeFoodSchema]

@router.get("/type-food", response_model=TypeFoodResponse, summary="List tipe makanan")
def get_type_food(db: Session = Depends(get_db)):
    data = db.query(MstTypeFood).all()
    return {"data": data}

class TypeAlergenFood(BaseModel):
    data: List[MstAlergenFoodSchema]
@router.get("/alergen-food", response_model=TypeAlergenFood, summary="List alergen makanan")
def get_alergen_food(db: Session = Depends(get_db)):
    data = db.query(MstAlergenFood).all()
    return {"data": data}

class TypeDessert(BaseModel):
    data: List[MstTypeDessertSchema]
@router.get("/type-dessert", response_model=TypeDessert, summary="List tipe dessert")
def get_type_dessert(db: Session = Depends(get_db)):
    data = db.query(MstTypeDessert).all()
    return {"data": data}
