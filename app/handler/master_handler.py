from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.master import MstTypeFood, MstAlergenFood, MstTypeDessert
from app.schemas.master import MstTypeFoodSchema, MstAlergenFoodSchema, MstTypeDessertSchema

router = APIRouter(prefix="/master", tags=["Master Data"])


@router.get("/type-food", response_model=List[MstTypeFoodSchema], summary="List tipe makanan")
def get_type_food(db: Session = Depends(get_db)):
    return db.query(MstTypeFood).all()


@router.get("/alergen-food", response_model=List[MstAlergenFoodSchema], summary="List alergen makanan")
def get_alergen_food(db: Session = Depends(get_db)):
    return db.query(MstAlergenFood).all()


@router.get("/type-dessert", response_model=List[MstTypeDessertSchema], summary="List tipe dessert")
def get_type_dessert(db: Session = Depends(get_db)):
    return db.query(MstTypeDessert).all()
