"""Estimate and EstimateComponent ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import String, DateTime, ForeignKey, Text, Integer, Numeric, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Estimate(Base):
    """A complete cost estimate for a project."""

    __tablename__ = "estimates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default="draft")

    # Cost totals (Decimal for financial precision)
    personnel_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    tooling_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    cloud_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    other_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    contingency_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    total_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )

    # Effort
    total_effort_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_duration_weeks: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Uncertainty
    p10: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    p25: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    p50: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    p75: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    p80: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    p90: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    confidence_level: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Traceability
    model_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("model_versions.id"), nullable=True
    )
    dataset_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dataset_versions.id"), nullable=True
    )
    estimation_method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    calculation_path_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_drivers_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    shap_values_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Recommendation (LLM-generated, references computed values only)
    recommendation_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    estimation_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    estimation_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    app_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="estimates")  # noqa: F821
    components: Mapped[list[EstimateComponent]] = relationship(
        "EstimateComponent", back_populates="estimate", cascade="all, delete-orphan"
    )
    scenarios: Mapped[list["Scenario"]] = relationship(  # noqa: F821
        "Scenario", back_populates="estimate", cascade="all, delete-orphan"
    )
    assumptions: Mapped[list["Assumption"]] = relationship(  # noqa: F821
        "Assumption", back_populates="estimate", cascade="all, delete-orphan"
    )
    risks: Mapped[list["Risk"]] = relationship(  # noqa: F821
        "Risk", back_populates="estimate", cascade="all, delete-orphan"
    )


class EstimateComponent(Base):
    """Individual line item in an estimate (e.g., one role's cost, one tool)."""

    __tablename__ = "estimate_components"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    estimate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("estimates.id"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # personnel, tooling, cloud, other, contingency
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    source: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # user_input, assumption, model, calculation
    formula: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Relationships
    estimate: Mapped[Estimate] = relationship(
        "Estimate", back_populates="components"
    )
