"""Project Pydantic schemas for request/response validation."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str = Field(..., min_length=1, max_length=500, description="Project name")
    description: str = Field(
        ..., min_length=10, max_length=10000,
        description="Natural language project description"
    )
    product_type: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    target_platform: Optional[str] = Field(None, max_length=200)
    expected_users: Optional[str] = Field(None, max_length=100)
    geography: Optional[str] = Field(None, max_length=200)
    required_deadline: Optional[date] = None
    technology_constraints: Optional[str] = Field(None, max_length=2000)
    required_integrations: Optional[str] = Field(None, max_length=2000)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Project name cannot be blank")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Description cannot be blank")
        return v.strip()


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, min_length=10, max_length=10000)
    product_type: Optional[str] = None
    industry: Optional[str] = None
    target_platform: Optional[str] = None
    expected_users: Optional[str] = None
    geography: Optional[str] = None
    required_deadline: Optional[date] = None
    technology_constraints: Optional[str] = None
    required_integrations: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(BaseModel):
    """Schema for project API responses."""

    id: uuid.UUID
    name: str
    description: str
    product_type: Optional[str] = None
    industry: Optional[str] = None
    target_platform: Optional[str] = None
    expected_users: Optional[str] = None
    geography: Optional[str] = None
    required_deadline: Optional[date] = None
    technology_constraints: Optional[str] = None
    required_integrations: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
