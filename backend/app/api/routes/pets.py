import random

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.pet import Pet
from app.models.user import User
from app.schemas.pet import PetActionResponse, PetCreate, PetStateResponse
from app.services.pet_service import get_pet_state, invalidate_pet_cache, perform_action
from app.utils.request_id import get_request_id


class PetRename(BaseModel):
    name: str = Field(min_length=1, max_length=30)


router = APIRouter()

VALID_ACTIONS: set[str] = {
    "feed", "clean", "play", "sleep",
    "study", "train", "medicine", "clean_poop",
    "hatch", "graduate",
}


@router.post("", response_model=PetStateResponse, status_code=status.HTTP_201_CREATED)
def create_pet(payload: PetCreate, db: Session = Depends(get_db)) -> PetStateResponse:
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    pet = Pet(
        user_id=payload.user_id,
        name=payload.name,
        species=payload.species,
        life_stage="egg",
        status="alive",
        character_type=random.randint(0, 2),
    )
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return PetStateResponse.model_validate(pet).model_copy(update={"cached": False})


@router.get("/{pet_id}", response_model=PetStateResponse)
def read_pet_state(pet_id: int, db: Session = Depends(get_db)) -> PetStateResponse:
    return get_pet_state(db, pet_id)


@router.patch("/{pet_id}/name", response_model=PetStateResponse)
def rename_pet(pet_id: int, payload: PetRename, db: Session = Depends(get_db)) -> PetStateResponse:
    pet = db.get(Pet, pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    pet.name = payload.name
    db.add(pet)
    db.commit()
    db.refresh(pet)
    invalidate_pet_cache(pet_id)
    return PetStateResponse.model_validate(pet).model_copy(update={"cached": False})


@router.post("/{pet_id}/actions/{action_type}", response_model=PetActionResponse)
def run_pet_action(
    pet_id: int, action_type: str, request: Request, db: Session = Depends(get_db),
) -> PetActionResponse:
    if action_type not in VALID_ACTIONS:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action_type}")
    pet_response, message = perform_action(
        db=db, pet_id=pet_id, action_type=action_type, request_id=get_request_id(request),
    )
    return PetActionResponse(action_type=action_type, pet=pet_response, message=message)
