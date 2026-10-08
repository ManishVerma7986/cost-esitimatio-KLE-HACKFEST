"""WBS Service for managing Work Breakdown Structure items and dependencies."""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog
from app.db.models.work_item import Dependency, WorkItem
from app.schemas.wbs import DependencyCreate, WorkItemCreate, WorkItemUpdate
from app.utils.errors import EntityNotFoundError
from app.utils.logging import get_logger

logger = get_logger("services.wbs")


def get_project_work_items(db: Session, project_id: uuid.UUID) -> list[WorkItem]:
    """Retrieve all work items for a project sorted by sort_order."""
    return db.execute(
        select(WorkItem)
        .where(WorkItem.project_id == project_id)
        .order_by(WorkItem.sort_order.asc(), WorkItem.created_at.asc())
    ).scalars().all()


def get_work_item(db: Session, item_id: uuid.UUID) -> WorkItem:
    """Retrieve a single work item by ID."""
    item = db.execute(select(WorkItem).where(WorkItem.id == item_id)).scalar_one_or_none()
    if not item:
        raise EntityNotFoundError("WorkItem", item_id)
    return item


def create_work_item(
    db: Session, item_in: WorkItemCreate, user_id: Optional[uuid.UUID] = None
) -> WorkItem:
    """Create a new WBS work item with audit logging."""
    item = WorkItem(
        id=uuid.uuid4(),
        project_id=item_in.project_id,
        parent_id=item_in.parent_id,
        name=item_in.name,
        description=item_in.description,
        phase=item_in.phase,
        complexity=item_in.complexity,
        priority=item_in.priority,
        role=item_in.role,
        estimated_hours=item_in.estimated_hours,
        estimated_hours_optimistic=item_in.estimated_hours_optimistic,
        estimated_hours_pessimistic=item_in.estimated_hours_pessimistic,
        sort_order=item_in.sort_order,
        is_user_modified=True,
        modification_note="Manually created item",
    )
    db.add(item)

    if user_id:
        audit = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action="create_work_item",
            entity_type="work_item",
            entity_id=str(item.id),
            new_value=json.dumps({"name": item.name, "phase": item.phase}),
        )
        db.add(audit)

    db.commit()
    db.refresh(item)
    return item


def update_work_item(
    db: Session,
    item_id: uuid.UUID,
    item_in: WorkItemUpdate,
    user_id: Optional[uuid.UUID] = None,
) -> WorkItem:
    """Update a work item and record modified state in audit log."""
    item = get_work_item(db, item_id)

    old_state = {
        "name": item.name,
        "complexity": item.complexity,
        "role": item.role,
        "estimated_hours": item.estimated_hours,
        "phase": item.phase,
    }

    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    item.is_user_modified = True

    if user_id:
        audit = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action="update_work_item",
            entity_type="work_item",
            entity_id=str(item.id),
            previous_value=json.dumps(old_state),
            new_value=json.dumps(update_data),
        )
        db.add(audit)

    db.commit()
    db.refresh(item)
    return item


def delete_work_item(
    db: Session, item_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
) -> None:
    """Delete a work item and remove associated dependencies."""
    item = get_work_item(db, item_id)

    if user_id:
        audit = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action="delete_work_item",
            entity_type="work_item",
            entity_id=str(item.id),
            previous_value=json.dumps({"name": item.name, "phase": item.phase}),
        )
        db.add(audit)

    db.delete(item)
    db.commit()


def add_dependency(db: Session, dep_in: DependencyCreate) -> Dependency:
    """Link two work items with a dependency."""
    # Verify both exist
    get_work_item(db, dep_in.source_item_id)
    get_work_item(db, dep_in.target_item_id)

    dep = Dependency(
        id=uuid.uuid4(),
        source_item_id=dep_in.source_item_id,
        target_item_id=dep_in.target_item_id,
        dependency_type=dep_in.dependency_type,
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep


def delete_dependency(db: Session, dep_id: uuid.UUID) -> None:
    """Remove a dependency between work items."""
    dep = db.execute(select(Dependency).where(Dependency.id == dep_id)).scalar_one_or_none()
    if not dep:
        raise EntityNotFoundError("Dependency", dep_id)
    db.delete(dep)
    db.commit()
