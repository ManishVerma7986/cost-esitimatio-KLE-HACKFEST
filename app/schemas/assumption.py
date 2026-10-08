"""Assumption tracking Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AssumptionBase(BaseModel):
    """Base schema for an assumption."""

    key: str = Field(..., min_length=1, max_length=255)
    value: str = Field(..., min_length=1)
    category: str = Field("general", max_length=100)
    source: str = Field("default", max_length=100)
    description: Optional[str] = Field(None, max_length=2000)


class AssumptionCreate(AssumptionBase):
    """Schema for adding an assumption to an estimate."""

    estimate_id: uuid.UUID


class AssumptionUpdate(BaseModel):
    """Schema for user overriding an assumption."""

    value: str = Field(..., min_length=1)
    description: Optional[str] = None


class AssumptionResponse(AssumptionBase):
    """Full assumption response schema."""

    id: uuid.UUID
    estimate_id: uuid.UUID
    is_user_modified: bool = False
    previous_value: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
