import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("proposals.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    original_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_useful: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    proposal: Mapped["Proposal"] = relationship("Proposal", back_populates="feedbacks")
    learning_logs: Mapped[list["AILearningLog"]] = relationship("AILearningLog", back_populates="feedback")


class AILearningLog(Base):
    __tablename__ = "ai_learning_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feedback_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("feedbacks.id"))
    original_score: Mapped[float] = mapped_column(Float, nullable=False)
    corrected_score: Mapped[float] = mapped_column(Float, nullable=False)
    delta: Mapped[float] = mapped_column(Float, nullable=False)
    applied_to_model: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    feedback: Mapped["Feedback"] = relationship("Feedback", back_populates="learning_logs")
