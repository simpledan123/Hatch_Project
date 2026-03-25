from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PetActionLog(Base):
    __tablename__ = "pet_action_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)
    before_state_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    after_state_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    request_id: Mapped[str] = mapped_column(String(100), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    pet = relationship("Pet", back_populates="action_logs")
