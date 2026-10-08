"""Strict Pydantic schemas for LLM structured outputs.

Every LLM response MUST be validated against these schemas.
If validation fails, the response is rejected and retried.
The LLM NEVER provides numerical estimates — only structural decomposition.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class Requirement(BaseModel):
    """A single identified requirement from the project description."""

    name: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1, max_length=2000)
    category: str = Field(
        ..., description="functional, non_functional, integration, data, security"
    )
    priority: Literal["low", "medium", "high", "critical"] = "medium"


class TaskDecomposition(BaseModel):
    """A single task in the work breakdown."""

    name: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1, max_length=2000)
    complexity: Literal["low", "medium", "high", "very_high"] = "medium"
    suggested_role: str = Field(
        ..., min_length=1, max_length=100,
        description="Role best suited for this task"
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="Names of other tasks this depends on"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()


class WorkPhaseDecomposition(BaseModel):
    """A phase of work containing multiple tasks."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    tasks: list[TaskDecomposition] = Field(
        ..., min_length=1, description="Tasks in this phase"
    )


class IntegrationIdentified(BaseModel):
    """An integration point identified from the description."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    complexity: Literal["low", "medium", "high"] = "medium"


class ScopeDecomposition(BaseModel):
    """Complete structured scope decomposition from LLM.

    This is the PRIMARY output schema for AI scope decomposition.
    The LLM fills in structure and categorization.
    It does NOT fill in numerical estimates.
    """

    requirements: list[Requirement] = Field(
        ..., min_length=1,
        description="Identified requirements from the project description"
    )
    work_phases: list[WorkPhaseDecomposition] = Field(
        ..., min_length=1,
        description="Work phases with tasks"
    )
    technology_components: list[str] = Field(
        default_factory=list,
        description="Technology stack components identified"
    )
    integrations: list[IntegrationIdentified] = Field(
        default_factory=list,
        description="External integrations identified"
    )
    clarification_questions: list[str] = Field(
        default_factory=list,
        description="Questions the PM should answer for better estimation"
    )
    assumptions_made: list[str] = Field(
        default_factory=list,
        description="Assumptions made during decomposition"
    )
    identified_risks: list[str] = Field(
        default_factory=list,
        description="Potential risks identified"
    )


class RecommendationResponse(BaseModel):
    """LLM-generated recommendation that REFERENCES computed values.

    The LLM explains and recommends — it does NOT generate numbers.
    All numbers referenced must come from the estimation engine.
    """

    summary: str = Field(
        ..., min_length=10, max_length=3000,
        description="Executive summary of the estimate"
    )
    key_findings: list[str] = Field(
        default_factory=list,
        description="Key findings from the analysis"
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actionable recommendations"
    )
    risk_commentary: Optional[str] = Field(
        None, max_length=2000,
        description="Commentary on identified risks"
    )
    confidence_commentary: Optional[str] = Field(
        None, max_length=1000,
        description="Commentary on confidence level and uncertainty"
    )
