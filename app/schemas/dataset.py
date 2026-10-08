"""Dataset and ML model benchmark Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class DataQualityReport(BaseModel):
    """Quantitative summary of dataset quality."""

    total_rows: int
    total_columns: int
    missing_cells: int
    missing_percentage: float
    duplicate_rows: int
    constant_columns: list[str]
    outlier_counts: dict[str, int]
    column_types: dict[str, str]
    quality_score: float = Field(..., ge=0.0, le=100.0, description="Overall quality score 0-100")


class DatasetResponse(BaseModel):
    """Dataset metadata response schema."""

    id: uuid.UUID
    name: str
    source: str
    description: Optional[str] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    is_active: bool = True
    created_at: datetime
    quality_score: Optional[float] = None

    model_config = {"from_attributes": True}


class ModelBenchmarkMetrics(BaseModel):
    """Standard software estimation benchmark metrics (MMRE, MdMRE, PRED(25), etc.)."""

    model_name: str
    model_version: str
    dataset_name: str
    sample_count: int
    mmre: float = Field(..., description="Mean Magnitude of Relative Error")
    mdmre: float = Field(..., description="Median Magnitude of Relative Error")
    pred25: float = Field(..., description="Percentage of predictions within 25% of actual")
    mae: float = Field(..., description="Mean Absolute Error in person-months or hours")
    rmse: float = Field(..., description="Root Mean Squared Error")
    bias: float = Field(..., description="Mean prediction bias (positive = overestimation)")
    prediction_interval_coverage_80: Optional[float] = Field(
        None, description="Actual coverage percentage for 80% prediction interval"
    )
    trained_at: datetime
