"""Estimate and cost-related Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class EstimateCreate(BaseModel):
    """Request to generate a new estimate for a project."""

    project_id: uuid.UUID


class CostBreakdown(BaseModel):
    """Cost breakdown by category."""

    personnel: Decimal = Field(default=Decimal("0"))
    tooling: Decimal = Field(default=Decimal("0"))
    cloud: Decimal = Field(default=Decimal("0"))
    other: Decimal = Field(default=Decimal("0"))
    contingency: Decimal = Field(default=Decimal("0"))
    total: Decimal = Field(default=Decimal("0"))


class UncertaintyResult(BaseModel):
    """Uncertainty analysis result with percentiles."""

    p10: Optional[Decimal] = None
    p25: Optional[Decimal] = None
    p50: Optional[Decimal] = None
    p75: Optional[Decimal] = None
    p80: Optional[Decimal] = None
    p90: Optional[Decimal] = None
    confidence_level: Optional[float] = None
    method: str = Field(
        ..., description="Method used: monte_carlo, conformal, parametric"
    )
    simulation_count: Optional[int] = None
    is_calibrated: Optional[bool] = None
    calibration_coverage: Optional[float] = None


class CostDriverItem(BaseModel):
    """A single cost driver with its contribution."""

    feature_name: str
    contribution_pct: float = Field(
        ..., description="Percentage contribution from SHAP analysis"
    )
    direction: str = Field(..., description="increase or decrease")
    explanation: str


class ComponentDetail(BaseModel):
    """Detail of an estimate component (line item)."""

    category: str
    subcategory: Optional[str] = None
    name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_cost: Optional[Decimal] = None
    total_amount: Decimal
    source: str
    formula: Optional[str] = None


class EstimateResponse(BaseModel):
    """Full estimate response."""

    id: uuid.UUID
    project_id: uuid.UUID
    version: int
    status: str

    # Costs
    cost_breakdown: CostBreakdown
    total_effort_hours: Optional[float] = None
    estimated_duration_weeks: Optional[float] = None

    # Uncertainty
    uncertainty: Optional[UncertaintyResult] = None

    # Components
    components: list[ComponentDetail] = []

    # Explainability
    cost_drivers: list[CostDriverItem] = []
    estimation_method: Optional[str] = None
    recommendation: Optional[str] = None

    # Traceability
    model_version: Optional[str] = None
    dataset_version: Optional[str] = None
    app_version: Optional[str] = None
    estimation_cycle_time_seconds: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CalculationStep(BaseModel):
    """A single step in the calculation audit trail."""

    step: int
    label: str
    value: str
    source: str
    formula: Optional[str] = None


class EstimateExplanation(BaseModel):
    """Complete audit trail / explanation for an estimate."""

    estimate_id: uuid.UUID
    calculation_path: list[CalculationStep]
    assumptions_used: list[dict]
    risks_identified: list[dict]
    model_info: Optional[dict] = None
    data_sources: list[str]
