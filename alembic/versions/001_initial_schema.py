"""Initial schema — all 15 tables

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), server_default="user"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("is_verified", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token", sa.Text, nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("revoked", sa.Boolean, server_default="false"),
    )

    op.create_table(
        "login_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("success", sa.Boolean, nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_login_attempts_user_id", "login_attempts", ["user_id"])

    op.create_table(
        "br_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True)),
        sa.Column("budget_min", sa.Float),
        sa.Column("budget_max", sa.Float),
        sa.Column("is_deleted", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_br_projects_created_by", "br_projects", ["created_by"])
    op.create_index("ix_br_projects_status", "br_projects", ["status"])

    op.create_table(
        "br_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("br_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("mime_type", sa.String(100)),
        sa.Column("extracted_text", sa.Text),
        sa.Column("upload_status", sa.String(50), server_default="processing"),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "br_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("br_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("priority", sa.String(50), server_default="medium"),
        sa.Column("embedding", postgresql.JSONB),
        sa.Column("source", sa.String(50), server_default="extracted"),
        sa.Column("is_deleted", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_br_requirements_project_id", "br_requirements", ["project_id"])
    op.create_index("ix_br_requirements_category", "br_requirements", ["category"])

    op.create_table(
        "proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("br_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vendor_name", sa.String(500), nullable=False),
        sa.Column("vendor_contact", sa.String(255)),
        sa.Column("vendor_email", sa.String(255)),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("extracted_text", sa.Text),
        sa.Column("proposed_cost", sa.Float),
        sa.Column("proposed_timeline_months", sa.Integer),
        sa.Column("status", sa.String(50), server_default="uploaded"),
        sa.Column("is_deleted", sa.Boolean, server_default="false"),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_proposals_project_id", "proposals", ["project_id"])
    op.create_index("ix_proposals_status", "proposals", ["status"])

    op.create_table(
        "proposal_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("category", sa.String(50)),
        sa.Column("embedding", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_proposal_requirements_proposal_id", "proposal_requirements", ["proposal_id"])

    op.create_table(
        "matching_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("overall_score", sa.Float, nullable=False),
        sa.Column("functional_score", sa.Float),
        sa.Column("technical_score", sa.Float),
        sa.Column("compliance_score", sa.Float),
        sa.Column("security_score", sa.Float),
        sa.Column("timeline_score", sa.Float),
        sa.Column("resource_score", sa.Float),
        sa.Column("deliverables_score", sa.Float),
        sa.Column("executive_summary", sa.Text),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("version", sa.Integer, server_default="1"),
    )

    op.create_table(
        "requirement_matchings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("result_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("matching_results.id", ondelete="CASCADE"), nullable=False),
        sa.Column("br_requirement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("br_requirements.id"), nullable=False),
        sa.Column("proposal_requirement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proposal_requirements.id")),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("label", sa.String(50), nullable=False),
        sa.Column("explanation", sa.Text),
        sa.Column("embedding_score", sa.Float),
        sa.Column("reranker_score", sa.Float),
    )
    op.create_index("ix_req_matchings_result_id", "requirement_matchings", ["result_id"])
    op.create_index("ix_req_matchings_label", "requirement_matchings", ["label"])

    op.create_table(
        "match_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("result_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("matching_results.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("risks", postgresql.JSONB),
        sa.Column("recommendations", postgresql.JSONB),
        sa.Column("strengths", postgresql.JSONB),
        sa.Column("gaps", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "match_histories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("result_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("matching_results.id"), nullable=False),
        sa.Column("overall_score", sa.Float, nullable=False),
        sa.Column("scores_snapshot", postgresql.JSONB, nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("recalculated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("triggered_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
    )

    op.create_table(
        "feedbacks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("feedback_type", sa.String(50), nullable=False),
        sa.Column("rating", sa.Integer),
        sa.Column("comment", sa.Text),
        sa.Column("corrected_score", sa.Float),
        sa.Column("original_score", sa.Float),
        sa.Column("is_useful", sa.Boolean),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "ai_learning_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("feedback_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("feedbacks.id"), nullable=False),
        sa.Column("original_score", sa.Float, nullable=False),
        sa.Column("corrected_score", sa.Float, nullable=False),
        sa.Column("delta", sa.Float, nullable=False),
        sa.Column("applied_to_model", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100)),
        sa.Column("resource_id", sa.String(255)),
        sa.Column("detail", postgresql.JSONB),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    for table in [
        "audit_logs", "ai_learning_logs", "feedbacks", "match_histories",
        "match_analyses", "requirement_matchings", "matching_results",
        "proposal_requirements", "proposals", "br_requirements",
        "br_documents", "br_projects", "login_attempts", "sessions", "users",
    ]:
        op.drop_table(table)
