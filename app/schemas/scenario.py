"""Scenario planning Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field


class ScenarioModification(BaseModel):
    """Specific modifications to apply to an estimate for a what-if scenario."""

    team_size_multiplier: Optional[float] = Field(
        None, ge=0.1, le=10.0, description="Multiplier on team capacity / size"
    )
    rate_multiplier: Optional[float] = Field(
        None, ge=0.1, le=10.0, description="Multiplier on hourly billing/labor rates"
    )
    contingency_percentage: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Explicit contingency percentage override"
    )
    deadline_weeks: Optional[float] = Field(
        None, ge=1.0, description="Target compressed or relaxed duration in weeks"
    )
    cloud_monthly_override: Optional[Decimal] = Field(
        None, ge=0, description="Override monthly cloud infrastructure budget"
    )
    tooling_cost_override: Optional[Decimal] = Field(
        None, ge=0, description="Override tooling/software licensing cost"
    )
    exclude_work_item_ids: list[str] = Field(
        default_factory=list, description="IDs of work items to omit (scope descoping)"
    )
    additional_work_item_hours: Optional[float] = Field(
        None, ge=0, description="Additional scope buffer in hours"
    )
    custom_parameters: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary custom what-if parameters"
    )


class ScenarioCreate(BaseModel):
    """Schema for creating a new what-if scenario."""

    estimate_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    modifications: ScenarioModification


class ScenarioResponse(BaseModel):
    """Full scenario response with recalculated figures and deltas."""

    id: uuid.UUID
    estimate_id: uuid.UUID
    name: str
    description: Optional[str] = None
    parameters_json: str

    personnel_cost: Optional[Decimal] = None
    tooling_cost: Optional[Decimal] = None
    cloud_cost: Optional[Decimal] = None
    other_cost: Optional[Decimal] = None
    contingency_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    total_effort_hours: Optional[float] = None
    estimated_duration_weeks: Optional[float] = None
    p50: Optional[Decimal] = None
    p80: Optional[Decimal] = None

    cost_delta: Optional[Decimal] = None
    effort_delta_hours: Optional[float] = None
    duration_delta_weeks: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScenarioComparison(BaseModel):
    """Side-by-side comparison of baseline estimate and scenarios."""

    baseline_estimate_id: uuid.UUID
    baseline_total_cost: Decimal
    baseline_effort_hours: float
    baseline_duration_weeks: float
    baseline_p50: Optional[Decimal] = None
    baseline_p80: Optional[Decimal] = None
    scenarios: list[ScenarioResponse]
