"""Internal client bridging Streamlit UI with the core services and database."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog
from app.db.models.dataset import Dataset
from app.db.models.estimate import Estimate
from app.db.models.model_registry import ModelVersion
from app.db.models.project import Project, ProjectScope
from app.db.models.risk import Risk
from app.db.models.user import User
from app.db.models.work_item import WorkItem
from app.db.session import SessionLocal
from app.schemas.estimate import EstimateResponse
from app.schemas.project import ProjectCreate
from app.services.decomposition import decompose_project
from app.services.estimate_service import generate_estimate_for_project, get_estimate_response
from app.services.scenario import create_scenario, get_scenario_comparison
from app.services.wbs import (
    create_work_item,
    delete_work_item,
    get_project_work_items,
    update_work_item,
)


def get_db_session() -> Session:
    """Return a fresh database session."""
    return SessionLocal()


def get_default_user(db: Session) -> User:
    """Retrieve or initialize default demo user."""
    user = db.execute(select(User).limit(1)).scalar_one_or_none()
    if not user:
        from app.config import get_settings
        from app.security.auth import get_password_hash
        settings = get_settings()
        user = User(
            id=uuid.uuid4(),
            email=settings.dev_user_email,
            full_name="Lead Project Architect",
            hashed_password=get_password_hash(settings.dev_user_password),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def list_all_projects(db: Session) -> List[Project]:
    """Retrieve all projects sorted by creation date."""
    return db.execute(select(Project).order_by(desc(Project.created_at))).scalars().all()


def get_project_by_id(db: Session, project_id: uuid.UUID) -> Optional[Project]:
    return db.execute(select(Project).where(Project.id == project_id)).scalar_one_or_none()


def create_new_project(db: Session, data: dict, user_id: uuid.UUID) -> Project:
    project = Project(
        id=uuid.uuid4(),
        owner_id=user_id,
        name=data["name"],
        description=data["description"],
        product_type=data.get("product_type"),
        industry=data.get("industry"),
        target_platform=data.get("target_platform"),
        expected_users=data.get("expected_users"),
        geography=data.get("geography"),
        technology_constraints=data.get("technology_constraints"),
        required_integrations=data.get("required_integrations"),
        status="draft",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def run_ai_decomposition(db: Session, project_id: uuid.UUID, user_id: uuid.UUID):
    return decompose_project(db=db, project_id=project_id, user_id=user_id)


def run_project_estimate(db: Session, project_id: uuid.UUID, user_id: uuid.UUID) -> EstimateResponse:
    return generate_estimate_for_project(db=db, project_id=project_id, user_id=user_id)


def get_latest_estimate(db: Session, project_id: uuid.UUID) -> Optional[EstimateResponse]:
    est = db.execute(
        select(Estimate)
        .where(Estimate.project_id == project_id)
        .order_by(desc(Estimate.version))
    ).scalars().first()
    if est:
        return get_estimate_response(db, est.id)
    return None


def get_audit_logs(
    db: Session,
    limit: int = 200,
    action_filter: Optional[str] = None,
    source_filter: Optional[str] = None,
) -> List[AuditLog]:
    """Retrieve audit trail logs with optional filters."""
    query = select(AuditLog).order_by(desc(AuditLog.timestamp))
    if action_filter and action_filter != "All":
        query = query.where(AuditLog.action == action_filter)
    if source_filter and source_filter != "All":
        query = query.where(AuditLog.source == source_filter)
    return db.execute(query.limit(limit)).scalars().all()

