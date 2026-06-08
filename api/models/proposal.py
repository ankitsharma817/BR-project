import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class Proposal(Base):
    __tablename__ = "proposals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("br_projects.id", ondelete="CASCADE"))
    vendor_name: Mapped[str] = mapped_column(String(500), nullable=False)
    vendor_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vendor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    proposed_timeline_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="uploaded")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project: Mapped["BRProject"] = relationship("BRProject", back_populates="proposals")
    requirements: Mapped[list["ProposalRequirement"]] = relationship("ProposalRequirement", back_populates="proposal", cascade="all, delete-orphan")
    matching_result: Mapped["MatchingResult | None"] = relationship("MatchingResult", back_populates="proposal", uselist=False)
    feedbacks: Mapped[list["Feedback"]] = relationship("Feedback", back_populates="proposal")


class ProposalRequirement(Base):
    __tablename__ = "proposal_requirements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("proposals.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=True)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    proposal: Mapped["Proposal"] = relationship("Proposal", back_populates="requirements")
    matchings: Mapped[list["RequirementMatching"]] = relationship("RequirementMatching", back_populates="proposal_requirement")
