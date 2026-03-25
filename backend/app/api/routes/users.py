from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import GuestUserCreate, UserResponse

router = APIRouter()


@router.post("/guest", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_guest_user(payload: GuestUserCreate, db: Session = Depends(get_db)) -> User:
    existing_user = db.scalar(select(User).where(User.nickname == payload.nickname))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nickname already exists")

    user = User(nickname=payload.nickname)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
