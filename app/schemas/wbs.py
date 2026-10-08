"""Work Breakdown Structure (WBS) Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class WorkItemBase(BaseModel):
    """Base schema for a work item."""

    name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    phase: str = Field(..., min_length=1, max_length=100)
    complexity: Literal["low", "medium", "high", "very_high"] = "medium"
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    role: Optional[str] = Field(None, max_length=100)
    estimated_hours: Optional[float] = Field(None, ge=0)
    estimated_hours_optimistic: Optional[float] = Field(None, ge=0)
    estimated_hours_pessimistic: Optional[float] = Field(None, ge=0)
    sort_order: int = Field(0, ge=0)


class WorkItemCreate(WorkItemBase):
    """Schema for creating a new work item."""

    project_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Item name cannot be blank")
        return v.strip()


class WorkItemUpdate(BaseModel):
    """Schema for updating an existing work item."""

    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    phase: Optional[str] = Field(None, min_length=1, max_length=100)
    complexity: Optional[Literal["low", "medium", "high", "very_high"]] = None
    priority: Optional[Literal["low", "medium", "high", "critical"]] = None
    role: Optional[str] = Field(None, max_length=100)
    estimated_hours: Optional[float] = Field(None, ge=0)
    estimated_hours_optimistic: Optional[float] = Field(None, ge=0)
    estimated_hours_pessimistic: Optional[float] = Field(None, ge=0)
    sort_order: Optional[int] = Field(None, ge=0)
    modification_note: Optional[str] = Field(None, max_length=1000)


class DependencyCreate(BaseModel):
    """Schema for creating a dependency between tasks."""

    source_item_id: uuid.UUID
    target_item_id: uuid.UUID
    dependency_type: Literal[
        "finish_to_start", "start_to_start", "finish_to_finish", "start_to_finish"
    ] = "finish_to_start"


class DependencyResponse(BaseModel):
    """Schema for dependency responses."""

    id: uuid.UUID
    source_item_id: uuid.UUID
    target_item_id: uuid.UUID
    dependency_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkItemResponse(WorkItemBase):
    """Full work item response."""

    id: uuid.UUID
    project_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    is_user_modified: bool = False
    modification_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    dependencies: list[uuid.UUID] = []

    model_config = {"from_attributes": True}


class WBSBatchUpdateRequest(BaseModel):
    """Batch update schema for WBS editor grid."""

    project_id: uuid.UUID
    items: list[WorkItemResponse]
