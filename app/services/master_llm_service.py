from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.master import MstModelLlm
from app.schemas.master_llm import MstModelLlmCreateRequest, MstModelLlmUpdateRequest, MstModelLlmResponse


def create_model_llm(db: Session, payload: MstModelLlmCreateRequest) -> MstModelLlmResponse:
    # Cek duplikat nama
    existing = db.query(MstModelLlm).filter(MstModelLlm.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Model LLM dengan nama '{payload.name}' sudah ada",
        )

    model = MstModelLlm(
        name=payload.name,
        input_price=payload.input_price,
        output_price=payload.output_price,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def get_all_model_llm(db: Session) -> list[MstModelLlmResponse]:
    return db.query(MstModelLlm).order_by(MstModelLlm.name).all()


def get_model_llm_by_id(db: Session, model_id: UUID) -> MstModelLlmResponse:
    model = db.query(MstModelLlm).filter(MstModelLlm.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model LLM dengan ID '{model_id}' tidak ditemukan",
        )
    return model


def update_model_llm(db: Session, model_id: UUID, payload: MstModelLlmUpdateRequest) -> MstModelLlmResponse:
    model = get_model_llm_by_id(db, model_id)

    # Cek duplikat nama jika nama diubah
    if payload.name and payload.name != model.name:
        existing = db.query(MstModelLlm).filter(MstModelLlm.name == payload.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Model LLM dengan nama '{payload.name}' sudah ada",
            )

    if payload.name is not None:
        model.name = payload.name
    if payload.input_price is not None:
        model.input_price = payload.input_price
    if payload.output_price is not None:
        model.output_price = payload.output_price

    db.commit()
    db.refresh(model)
    return model


def delete_model_llm(db: Session, model_id: UUID) -> dict:
    model = get_model_llm_by_id(db, model_id)
    db.delete(model)
    db.commit()
    return {"message": f"Model LLM '{model.name}' berhasil dihapus"}
