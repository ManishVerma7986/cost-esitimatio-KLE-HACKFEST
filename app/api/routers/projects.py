"""Project management endpoints."""

from __future__ import annotations

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models.project import Project
from app.db.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.security.input_sanitizer import sanitize_text
from app.utils.errors import EntityNotFoundError

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new software project."""
    project = Project(
        id=uuid.uuid4(),
        owner_id=current_user.id,
        name=sanitize_text(project_in.name),
        description=sanitize_text(project_in.description),
        product_type=project_in.product_type,
        industry=project_in.industry,
        target_platform=project_in.target_platform,
        expected_users=project_in.expected_users,
        geography=project_in.geography,
        required_deadline=project_in.required_deadline,
        technology_constraints=project_in.technology_constraints,
        required_integrations=project_in.required_integrations,
        status="draft",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=List[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all projects owned by the user or organization."""
    projects = db.execute(
        select(Project)
        .where(Project.owner_id == current_user.id)
        .order_by(desc(Project.created_at))
    ).scalars().all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve project by ID."""
    project = db.execute(select(Project).where(Project.id == project_id)).scalar_one_or_none()
    if not project:
        raise EntityNotFoundError("Project", project_id)
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: uuid.UUID,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update project details."""
    project = db.execute(select(Project).where(Project.id == project_id)).scalar_one_or_none()
    if not project:
        raise EntityNotFoundError("Project", project_id)

    update_data = project_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if isinstance(val, str):
            val = sanitize_text(val)
        setattr(project, field, val)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a project and cascade delete all child tasks, estimates, and scopes."""
    project = db.execute(select(Project).where(Project.id == project_id)).scalar_one_or_none()
    if not project:
        raise EntityNotFoundError("Project", project_id)

    db.delete(project)
    db.commit()
