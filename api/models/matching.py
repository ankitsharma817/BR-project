import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class MatchingResult(Base):
    __tablename__ = "matching_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("proposals.id", ondelete="CASCADE"), unique=True)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    functional_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    technical_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    compliance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    security_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    timeline_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    resource_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    deliverables_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    version: Mapped[int] = mapped_column(Integer, default=1)

    proposal: Mapped["Proposal"] = relationship("Proposal", back_populates="matching_result")
    requirement_matchings: Mapped[list["RequirementMatching"]] = relationship("RequirementMatching", back_populates="result", cascade="all, delete-orphan")
    analysis: Mapped["MatchAnalysis | None"] = relationship("MatchAnalysis", back_populates="result", uselist=False)
    history: Mapped[list["MatchHistory"]] = relationship("MatchHistory", back_populates="result")


class RequirementMatching(Base):
    __tablename__ = "requirement_matchings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matching_results.id", ondelete="CASCADE"))
    br_requirement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("br_requirements.id"))
    proposal_requirement_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("proposal_requirements.id"), nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reranker_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    result: Mapped["MatchingResult"] = relationship("MatchingResult", back_populates="requirement_matchings")
    br_requirement: Mapped["BRRequirement"] = relationship("BRRequirement", back_populates="matchings")
    proposal_requirement: Mapped["ProposalRequirement | None"] = relationship("ProposalRequirement", back_populates="matchings")


class MatchAnalysis(Base):
    __tablename__ = "match_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matching_results.id", ondelete="CASCADE"), unique=True)
    risks: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    strengths: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    gaps: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    result: Mapped["MatchingResult"] = relationship("MatchingResult", back_populates="analysis")


class MatchHistory(Base):
    __tablename__ = "match_histories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matching_results.id"))
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    scores_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    recalculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    triggered_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    result: Mapped["MatchingResult"] = relationship("MatchingResult", back_populates="history")
