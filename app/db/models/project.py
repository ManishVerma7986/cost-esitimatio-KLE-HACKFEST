"""Project and ProjectScope ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, date

from sqlalchemy import String, DateTime, ForeignKey, Text, Date, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    product_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_platform: Mapped[str | None] = mapped_column(String(200), nullable=True)
    expected_users: Mapped[str | None] = mapped_column(String(100), nullable=True)
    geography: Mapped[str | None] = mapped_column(String(200), nullable=True)
    required_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    technology_constraints: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_integrations: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="projects")  # noqa: F821
    scope: Mapped[ProjectScope | None] = relationship(
        "ProjectScope", back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    work_items: Mapped[list["WorkItem"]] = relationship(  # noqa: F821
        "WorkItem", back_populates="project", cascade="all, delete-orphan"
    )
    estimates: Mapped[list["Estimate"]] = relationship(  # noqa: F821
        "Estimate", back_populates="project", cascade="all, delete-orphan"
    )


class ProjectScope(Base):
    """Structured scope derived from AI decomposition of the project description."""

    __tablename__ = "project_scopes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), unique=True, nullable=False
    )
    # Structured decomposition stored as JSON text
    requirements_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    technology_components_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    integrations_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    clarification_questions_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    identified_risks_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    assumptions_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_provider_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_model_used: Mapped[str | None] = mapped_column(String(200), nullable=True)
    decomposition_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    estimated_complexity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Relationships
    project: Mapped[Project] = relationship("Project", back_populates="scope")
