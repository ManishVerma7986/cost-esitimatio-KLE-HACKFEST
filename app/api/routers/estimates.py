"""Estimates, Scope Decomposition, and WBS endpoints."""

from __future__ import annotations

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models.estimate import Estimate
from app.db.models.project import Project, ProjectScope
from app.db.models.user import User
from app.db.models.work_item import WorkItem
from app.schemas.estimate import EstimateResponse
from app.schemas.wbs import WorkItemCreate, WorkItemResponse, WorkItemUpdate
from app.services.decomposition import decompose_project
from app.services.estimate_service import generate_estimate_for_project, get_estimate_response
from app.services.wbs import (
    create_work_item,
    delete_work_item,
    get_project_work_items,
    update_work_item,
)
from app.utils.errors import EntityNotFoundError

router = APIRouter(tags=["Estimates & WBS"])


# ── AI Scope Decomposition ──────────────────────────────────────────

@router.post("/projects/{project_id}/decompose")
def trigger_scope_decomposition(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger AI Scope Decomposition to generate requirements, phases, and initial WBS."""
    scope, work_items = decompose_project(db=db, project_id=project_id, user_id=current_user.id)
    return {
        "project_id": str(project_id),
        "status": "decomposed",
        "provider_used": scope.llm_provider_used,
        "model_used": scope.llm_model_used,
        "tasks_generated": len(work_items),
    }


# ── WBS CRUD ────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/wbs", response_model=List[WorkItemResponse])
def get_wbs(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all WBS items for a project."""
    items = get_project_work_items(db, project_id)
    return [WorkItemResponse.model_validate(item) for item in items]


@router.post("/projects/{project_id}/wbs", response_model=WorkItemResponse, status_code=status.HTTP_201_CREATED)
def add_wbs_item(
    project_id: uuid.UUID,
    item_in: WorkItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new manual task in the project WBS."""
    if item_in.project_id != project_id:
        item_in.project_id = project_id
    item = create_work_item(db, item_in, user_id=current_user.id)
    return WorkItemResponse.model_validate(item)


@router.put("/projects/{project_id}/wbs/{item_id}", response_model=WorkItemResponse)
def modify_wbs_item(
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    item_in: WorkItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a specific work item (complexity, hours override, role, priority)."""
    item = update_work_item(db, item_id, item_in, user_id=current_user.id)
    return WorkItemResponse.model_validate(item)


@router.delete("/projects/{project_id}/wbs/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_wbs_item(
    project_id: uuid.UUID,
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a work item from the WBS."""
    delete_work_item(db, item_id, user_id=current_user.id)


# ── Estimation Engine Execution ─────────────────────────────────────

@router.post("/projects/{project_id}/estimate", response_model=EstimateResponse, status_code=status.HTTP_201_CREATED)
def calculate_estimate(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute hybrid estimation: COCOMO baseline + ML + Analogy + Cost Engine + Monte Carlo."""
    return generate_estimate_for_project(db=db, project_id=project_id, user_id=current_user.id)


@router.get("/estimates/{estimate_id}", response_model=EstimateResponse)
def get_estimate(
    estimate_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full estimate details by estimate ID."""
    return get_estimate_response(db, estimate_id)


@router.get("/projects/{project_id}/estimates", response_model=List[EstimateResponse])
def list_project_estimates(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all estimate versions created for this project."""
    estimates = db.execute(
        select(Estimate)
        .where(Estimate.project_id == project_id)
        .order_by(desc(Estimate.version))
    ).scalars().all()

    return [get_estimate_response(db, e.id) for e in estimates]
