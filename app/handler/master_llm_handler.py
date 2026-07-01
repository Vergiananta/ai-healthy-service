from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.account_user import AccountUser
from app.schemas.master_llm import (
    MstModelLlmCreateRequest,
    MstModelLlmUpdateRequest,
    MstModelLlmResponse,
)
from app.services.master_llm_service import (
    create_model_llm,
    get_all_model_llm,
    get_model_llm_by_id,
    update_model_llm,
    delete_model_llm,
)

router = APIRouter(prefix="/master/model-llm", tags=["Master Model LLM"])


@router.post(
    "",
    response_model=MstModelLlmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tambah model LLM baru",
)
def create(
    payload: MstModelLlmCreateRequest,
    db: Session = Depends(get_db),
    _: AccountUser = Depends(get_current_user),
):
    return create_model_llm(db, payload)


@router.get(
    "",
    response_model=List[MstModelLlmResponse],
    status_code=status.HTTP_200_OK,
    summary="List semua model LLM",
)
def get_all(db: Session = Depends(get_db)):
    return get_all_model_llm(db)


@router.get(
    "/{model_id}",
    response_model=MstModelLlmResponse,
    status_code=status.HTTP_200_OK,
    summary="Detail model LLM by ID",
)
def get_by_id(model_id: UUID, db: Session = Depends(get_db)):
    return get_model_llm_by_id(db, model_id)


@router.put(
    "/{model_id}",
    response_model=MstModelLlmResponse,
    status_code=status.HTTP_200_OK,
    summary="Update model LLM",
)
def update(
    model_id: UUID,
    payload: MstModelLlmUpdateRequest,
    db: Session = Depends(get_db),
    _: AccountUser = Depends(get_current_user),
):
    return update_model_llm(db, model_id, payload)


@router.delete(
    "/{model_id}",
    status_code=status.HTTP_200_OK,
    summary="Hapus model LLM",
)
def delete(
    model_id: UUID,
    db: Session = Depends(get_db),
    _: AccountUser = Depends(get_current_user),
):
    return delete_model_llm(db, model_id)
