import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from ..database import Base


class BRProject(Base):
    __tablename__ = "br_projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    budget_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    budget_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    documents: Mapped[list["BRDocument"]] = relationship("BRDocument", back_populates="project", cascade="all, delete-orphan")
    requirements: Mapped[list["BRRequirement"]] = relationship("BRRequirement", back_populates="project", cascade="all, delete-orphan")
    proposals: Mapped[list["Proposal"]] = relationship("Proposal", back_populates="project", cascade="all, delete-orphan")


class BRDocument(Base):
    __tablename__ = "br_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("br_projects.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    upload_status: Mapped[str] = mapped_column(String(50), default="processing")
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    project: Mapped["BRProject"] = relationship("BRProject", back_populates="documents")


class BRRequirement(Base):
    __tablename__ = "br_requirements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("br_projects.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[str] = mapped_column(String(50), default="medium")
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="extracted")  # extracted | manual
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    project: Mapped["BRProject"] = relationship("BRProject", back_populates="requirements")
    matchings: Mapped[list["RequirementMatching"]] = relationship("RequirementMatching", back_populates="br_requirement")
