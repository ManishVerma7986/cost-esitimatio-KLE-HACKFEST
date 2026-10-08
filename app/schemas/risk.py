"""Risk analysis Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class RiskBase(BaseModel):
    """Base schema for a detected or identified risk."""

    category: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=500)
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    evidence: str = Field(..., min_length=1, description="Quantitative or factual reason")
    impact: str = Field(..., min_length=1, description="Estimated impact on cost, timeline, or quality")
    mitigation: str = Field(..., min_length=1, description="Recommended mitigation strategy")
    source: Literal["system", "model", "user"] = "system"


class RiskCreate(RiskBase):
    """Schema for creating a risk entry."""

    estimate_id: uuid.UUID


class RiskResponse(RiskBase):
    """Full risk response schema."""

    id: uuid.UUID
    estimate_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
