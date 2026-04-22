from datetime import datetime

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
    smarts: int
    activity: int
    status: str
    life_stage: str
    character_type: int
    evolution_form: str
    poop_count: int
    feed_tally: int
    play_tally: int
    study_tally: int
    train_tally: int
    hatched_at: datetime | None = None
    last_decay_at: datetime
    created_at: datetime
    updated_at: datetime | None = None
    cached: bool = False

    model_config = {"from_attributes": True}


class PetActionResponse(BaseModel):
    action_type: str
    pet: PetStateResponse
    message: str
