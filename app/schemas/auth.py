"""User and authentication Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Schema for registering a new user."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    organization_name: Optional[str] = Field(None, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserLogin(BaseModel):
    """Schema for user login credentials."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT access token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class UserResponse(BaseModel):
    """Public user response schema."""

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    organization_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}
