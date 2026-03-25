from datetime import datetime

from pydantic import BaseModel, Field


class GuestUserCreate(BaseModel):
    nickname: str = Field(min_length=2, max_length=30)


class UserResponse(BaseModel):
    id: int
    nickname: str
    created_at: datetime

    model_config = {"from_attributes": True}
