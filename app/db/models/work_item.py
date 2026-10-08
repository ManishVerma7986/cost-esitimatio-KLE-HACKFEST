"""WorkItem and Dependency ORM models for Work Breakdown Structure."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WorkItem(Base):
    """A single task/item in the Work Breakdown Structure."""

    __tablename__ = "work_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_items.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    phase: Mapped[str] = mapped_column(String(100), nullable=False)
    complexity: Mapped[str] = mapped_column(
        String(20), default="medium"
    )  # low, medium, high, very_high
    priority: Mapped[str] = mapped_column(
        String(20), default="medium"
    )  # low, medium, high, critical
    role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estimated_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_hours_optimistic: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_hours_pessimistic: Mapped[float | None] = mapped_column(Float, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_user_modified: Mapped[bool] = mapped_column(default=False)
    modification_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="work_items")  # noqa: F821
    children: Mapped[list[WorkItem]] = relationship(
        "WorkItem", back_populates="parent", cascade="all, delete-orphan"
    )
    parent: Mapped[WorkItem | None] = relationship(
        "WorkItem", back_populates="children", remote_side=[id]
    )
    dependencies_as_source: Mapped[list[Dependency]] = relationship(
        "Dependency",
        foreign_keys="Dependency.source_item_id",
        back_populates="source_item",
        cascade="all, delete-orphan",
    )
    dependencies_as_target: Mapped[list[Dependency]] = relationship(
        "Dependency",
        foreign_keys="Dependency.target_item_id",
        back_populates="target_item",
        cascade="all, delete-orphan",
    )


class Dependency(Base):
    """Dependency between two WorkItems."""

    __tablename__ = "dependencies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_items.id"), nullable=False
    )
    target_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_items.id"), nullable=False
    )
    dependency_type: Mapped[str] = mapped_column(
        String(50), default="finish_to_start"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    source_item: Mapped[WorkItem] = relationship(
        "WorkItem", foreign_keys=[source_item_id], back_populates="dependencies_as_source"
    )
    target_item: Mapped[WorkItem] = relationship(
        "WorkItem", foreign_keys=[target_item_id], back_populates="dependencies_as_target"
    )
