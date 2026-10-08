"""Unit tests for the export utility service (JSON, CSV, Excel, PDF)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.schemas.estimate import (
    ComponentDetail,
    CostBreakdown,
    EstimateResponse,
    UncertaintyResult,
)
from app.utils.export import (
    export_estimate_csv,
    export_estimate_excel,
    export_estimate_json,
    export_estimate_pdf,
)


@pytest.fixture
def mock_estimate_response() -> EstimateResponse:
    return EstimateResponse(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        version=1,
        status="completed",
        cost_breakdown=CostBreakdown(
            personnel=Decimal("85000.00"),
            tooling=Decimal("4200.00"),
            cloud=Decimal("3800.00"),
            other=Decimal("0.00"),
            contingency=Decimal("13950.00"),
            total=Decimal("106950.00"),
        ),
        total_effort_hours=1020.0,
        estimated_duration_weeks=14.5,
        uncertainty=UncertaintyResult(
            p10=Decimal("92000.00"),
            p50=Decimal("106000.00"),
            p80=Decimal("118500.00"),
            p90=Decimal("126000.00"),
            method="monte_carlo",
            simulation_count=10000,
        ),
        components=[
            ComponentDetail(
                category="personnel",
                subcategory="backend",
                name="Backend Developer Effort",
                quantity=420.0,
                unit="hours",
                unit_cost=Decimal("95.00"),
                total_amount=Decimal("39900.00"),
                source="COCOMO-II & Expert Rate",
                formula="420 hrs * $95/hr",
            ),
            ComponentDetail(
                category="cloud",
                subcategory="aws",
                name="Cloud Hosting Infrastructure",
                quantity=3.5,
                unit="months",
                unit_cost=Decimal("1000.00"),
                total_amount=Decimal("3500.00"),
                source="Standard Production Tier",
                formula="3.5 mos * $1000/mo",
            ),
        ],
        cost_drivers=[],
        estimation_method="Hybrid Ensemble",
        created_at=datetime.now(timezone.utc),
    )


def test_export_estimate_json(mock_estimate_response: EstimateResponse):
    result = export_estimate_json(mock_estimate_response, project_name="Test FinTech App")
    data = json.loads(result)

    assert data["project_name"] == "Test FinTech App"
    assert "estimate" in data
    assert float(data["estimate"]["cost_breakdown"]["total"]) == 106950.00
    assert len(data["estimate"]["components"]) == 2


def test_export_estimate_csv(mock_estimate_response: EstimateResponse):
    result = export_estimate_csv(mock_estimate_response, project_name="=HYPERLINK('evil')")

    # Verify formula was prefixed with single quote so spreadsheet engines do not execute it
    lines = [line for line in result.splitlines() if line]
    data_lines = lines[1:]  # Skip header
    for line in data_lines:
        assert line.startswith("'=HYPERLINK") or not line.startswith("=")
    assert "'=HYPERLINK" in result
    assert "Backend Developer Effort" in result
    assert "39900.00" in result


def test_export_estimate_excel(mock_estimate_response: EstimateResponse):
    excel_bytes = export_estimate_excel(mock_estimate_response, project_name="Test Enterprise Cloud")

    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 1000
    # ZIP magic bytes for .xlsx
    assert excel_bytes[:4] == b"PK\x03\x04"


def test_export_estimate_pdf(mock_estimate_response: EstimateResponse):
    pdf_bytes = export_estimate_pdf(mock_estimate_response, project_name="Test Enterprise Cloud")

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    # PDF magic bytes
    assert pdf_bytes.startswith(b"%PDF")
