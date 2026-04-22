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

    # Core stats (0-100)
    hunger: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    cleanliness: Mapped[int] = mapped_column(Integer, nullable=False, default=80)
    happiness: Mapped[int] = mapped_column(Integer, nullable=False, default=70)
    energy: Mapped[int] = mapped_column(Integer, nullable=False, default=70)
    health: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    smarts: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    activity: Mapped[int] = mapped_column(Integer, nullable=False, default=50)

    # Status and lifecycle
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="alive")
    life_stage: Mapped[str] = mapped_column(String(20), nullable=False, default="egg")

    # Character identity
    character_type: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 0=blob, 1=ghost, 2=dino
    evolution_form: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")  # normal/studious/athletic/wild

    # Poop mechanic
    poop_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Care tallies for evolution determination
    feed_tally: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    play_tally: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    study_tally: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    train_tally: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Timestamps
    hatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_decay_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="pets")
    action_logs = relationship("PetActionLog", back_populates="pet", cascade="all, delete-orphan")
