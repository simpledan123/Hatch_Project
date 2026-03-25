from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    species: Mapped[str] = mapped_column(String(30), nullable=False, default="tama")

    hunger: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    cleanliness: Mapped[int] = mapped_column(Integer, nullable=False, default=80)
    happiness: Mapped[int] = mapped_column(Integer, nullable=False, default=70)
    energy: Mapped[int] = mapped_column(Integer, nullable=False, default=70)
    health: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="alive")

    last_decay_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="pets")
    action_logs = relationship("PetActionLog", back_populates="pet", cascade="all, delete-orphan")
