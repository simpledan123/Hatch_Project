from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PetCreate(BaseModel):
    user_id: int
    name: str = Field(min_length=1, max_length=30)
    species: str = Field(default="tama", min_length=1, max_length=30)


class PetStateResponse(BaseModel):
    id: int
    user_id: int
    name: str
    species: str
    hunger: int
    cleanliness: int
    happiness: int
    energy: int
    health: int
    status: str
    last_decay_at: datetime
    created_at: datetime
    updated_at: datetime | None = None
    cached: bool = False

    model_config = {"from_attributes": True}


class PetActionResponse(BaseModel):
    action_type: Literal["feed", "clean", "play", "sleep"]
    pet: PetStateResponse
    message: str
