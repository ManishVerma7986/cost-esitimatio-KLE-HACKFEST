"""Unit tests for the AuditLog system and WBS audit logging."""

from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog
from app.db.models.project import Project
from app.db.models.user import User
from app.schemas.wbs import WorkItemCreate, WorkItemUpdate
from app.services.wbs import create_work_item, update_work_item
from streamlit_app.components.api_client import get_audit_logs


def test_wbs_actions_generate_audit_logs(db_session: Session, test_user: User):
    # 1. Create project
    proj = Project(
        id=uuid.uuid4(),
        owner_id=test_user.id,
        name="Audited Architecture Project",
        description="Verifying compliance logs.",
    )
    db_session.add(proj)
    db_session.commit()

    # 2. Create work item
    item_in = WorkItemCreate(
        project_id=proj.id,
        name="Setup Secure Database Cluster",
        phase="Infrastructure",
        complexity="high",
        role="DevOps Engineer",
        estimated_hours=40.0,
    )
    item = create_work_item(db_session, item_in, user_id=test_user.id)

    # Verify create_work_item audit log exists
    audit_logs = db_session.execute(
        select(AuditLog).where(AuditLog.action == "create_work_item")
    ).scalars().all()

    assert len(audit_logs) >= 1
    create_log = audit_logs[0]
    assert create_log.entity_id == str(item.id)
    assert create_log.user_id == test_user.id

    # 3. Update work item
    update_in = WorkItemUpdate(
        estimated_hours=60.0,
        complexity="very_high",
    )
    update_work_item(db_session, item.id, update_in, user_id=test_user.id)

    # 4. Check get_audit_logs retrieval
    all_logs = get_audit_logs(db_session, limit=10)
    assert len(all_logs) >= 2

    actions = [log.action for log in all_logs]
    assert "create_work_item" in actions
    assert "update_work_item" in actions
