"""Scenario ORM model for what-if planning."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import String, DateTime, ForeignKey, Text, Numeric, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Scenario(Base):
    """A what-if scenario attached to an estimate."""

    __tablename__ = "scenarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    estimate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("estimates.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Modifications (JSON: list of changes applied)
    parameters_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    # Recalculated results
    personnel_cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    tooling_cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    cloud_cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    other_cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    contingency_cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    total_effort_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_duration_weeks: Mapped[float | None] = mapped_column(Float, nullable=True)
    p50: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    p80: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Delta from baseline
    cost_delta: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    effort_delta_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_delta_weeks: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Relationships
    estimate: Mapped["Estimate"] = relationship("Estimate", back_populates="scenarios")  # noqa: F821
