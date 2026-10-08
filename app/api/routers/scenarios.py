"""What-if scenario planning endpoints."""

from __future__ import annotations

import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.schemas.scenario import (
    ScenarioComparison,
    ScenarioCreate,
    ScenarioResponse,
)
from app.services.scenario import create_scenario, get_scenario_comparison

router = APIRouter(prefix="/estimates/{estimate_id}/scenarios", tags=["Scenarios"])


@router.post("", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
def add_scenario(
    estimate_id: uuid.UUID,
    scenario_in: ScenarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compute and persist a what-if scenario based on modified parameters."""
    if scenario_in.estimate_id != estimate_id:
        scenario_in.estimate_id = estimate_id
    scenario = create_scenario(db=db, scenario_in=scenario_in, user_id=current_user.id)
    return ScenarioResponse.model_validate(scenario)


@router.get("/compare", response_model=ScenarioComparison)
def compare_all_scenarios(
    estimate_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Side-by-side comparison of baseline estimate vs all calculated scenarios."""
    return get_scenario_comparison(db=db, estimate_id=estimate_id)
