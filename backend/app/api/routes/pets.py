from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.pet import Pet
from app.models.user import User
from app.schemas.pet import PetActionResponse, PetCreate, PetStateResponse
from app.services.pet_service import get_pet_state, perform_action
from app.utils.request_id import get_request_id

router = APIRouter()


@router.post("", response_model=PetStateResponse, status_code=status.HTTP_201_CREATED)
def create_pet(payload: PetCreate, db: Session = Depends(get_db)) -> PetStateResponse:
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    pet = Pet(
        user_id=payload.user_id,
        name=payload.name,
        species=payload.species,
    )
    db.add(pet)
    db.commit()
    db.refresh(pet)

    return PetStateResponse.model_validate(pet).model_copy(update={"cached": False})


@router.get("/{pet_id}", response_model=PetStateResponse)
def read_pet_state(pet_id: int, db: Session = Depends(get_db)) -> PetStateResponse:
    return get_pet_state(db, pet_id)


@router.post("/{pet_id}/actions/{action_type}", response_model=PetActionResponse)
def run_pet_action(
    pet_id: int,
    action_type: Literal["feed", "clean", "play", "sleep"],
    request: Request,
    db: Session = Depends(get_db),
) -> PetActionResponse:
    pet_response = perform_action(
        db=db,
        pet_id=pet_id,
        action_type=action_type,
        request_id=get_request_id(request),
    )
    return PetActionResponse(
        action_type=action_type,
        pet=pet_response,
        message=f"Action '{action_type}' completed successfully.",
    )
