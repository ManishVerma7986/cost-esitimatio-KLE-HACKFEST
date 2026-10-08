"""Service for AI scope decomposition and automatic WBS generation."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog
from app.db.models.project import Project, ProjectScope
from app.db.models.work_item import Dependency, WorkItem
from app.schemas.llm_responses import ScopeDecomposition
from app.services.llm.provider import get_llm_service
from app.utils.errors import EntityNotFoundError
from app.utils.logging import get_logger

logger = get_logger("services.decomposition")


def decompose_project(
    db: Session, project_id: uuid.UUID, user_id: uuid.UUID | None = None
) -> Tuple[ProjectScope, list[WorkItem]]:
    """Run AI scope decomposition for a project and populate initial WBS work items."""
    project = db.execute(
        select(Project).where(Project.id == project_id)
    ).scalar_one_or_none()

    if not project:
        raise EntityNotFoundError("Project", project_id)

    llm = get_llm_service()
    decomposition, provider_used, model_used = llm.decompose_project_scope(
        name=project.name,
        description=project.description,
        product_type=project.product_type,
        industry=project.industry,
        target_platform=project.target_platform,
        expected_users=project.expected_users,
        geography=project.geography,
        technology_constraints=project.technology_constraints,
        required_integrations=project.required_integrations,
    )

    # 1. Update or create ProjectScope
    now = datetime.now(timezone.utc)
    scope = db.execute(
        select(ProjectScope).where(ProjectScope.project_id == project_id)
    ).scalar_one_or_none()

    if not scope:
        scope = ProjectScope(
            id=uuid.uuid4(),
            project_id=project_id,
        )
        db.add(scope)

    scope.requirements_json = json.dumps([r.model_dump() for r in decomposition.requirements])
    scope.technology_components_json = json.dumps(decomposition.technology_components)
    scope.integrations_json = json.dumps([i.model_dump() for i in decomposition.integrations])
    scope.clarification_questions_json = json.dumps(decomposition.clarification_questions)
    scope.identified_risks_json = json.dumps(decomposition.identified_risks)
    scope.assumptions_json = json.dumps(decomposition.assumptions_made)
    scope.llm_provider_used = provider_used
    scope.llm_model_used = model_used
    scope.decomposition_timestamp = now

    # 2. Clear previous draft work items if re-decomposing
    existing_items = db.execute(
        select(WorkItem).where(WorkItem.project_id == project_id)
    ).scalars().all()
    for item in existing_items:
        db.delete(item)
    db.flush()

    # 3. Create WBS WorkItems and track dependencies
    created_items: list[WorkItem] = []
    task_name_to_item: dict[str, WorkItem] = {}
    pending_dependencies: list[Tuple[str, list[str]]] = []

    sort_counter = 1
    for phase_idx, phase in enumerate(decomposition.work_phases):
        # Create Phase Container WorkItem
        phase_item = WorkItem(
            id=uuid.uuid4(),
            project_id=project_id,
            parent_id=None,
            name=phase.name,
            description=phase.description,
            phase=phase.name,
            complexity="medium",
            priority="medium",
            role="Technical Lead",
            sort_order=sort_counter,
        )
        db.add(phase_item)
        created_items.append(phase_item)
        task_name_to_item[phase.name] = phase_item
        sort_counter += 1

        # Create Child Tasks
        for task in phase.tasks:
            child_item = WorkItem(
                id=uuid.uuid4(),
                project_id=project_id,
                parent_id=phase_item.id,
                name=task.name,
                description=task.description,
                phase=phase.name,
                complexity=task.complexity,
                priority="medium",
                role=task.suggested_role,
                sort_order=sort_counter,
            )
            db.add(child_item)
            created_items.append(child_item)
            task_name_to_item[task.name] = child_item
            if task.dependencies:
                pending_dependencies.append((task.name, task.dependencies))
            sort_counter += 1

    db.flush()

    # 4. Resolve task dependencies
    for target_name, source_names in pending_dependencies:
        target_item = task_name_to_item.get(target_name)
        if not target_item:
            continue
        for source_name in source_names:
            source_item = task_name_to_item.get(source_name)
            if source_item and source_item.id != target_item.id:
                dep = Dependency(
                    id=uuid.uuid4(),
                    source_item_id=source_item.id,
                    target_item_id=target_item.id,
                    dependency_type="finish_to_start",
                )
                db.add(dep)

    # 5. Audit log
    audit = AuditLog(
        id=uuid.uuid4(),
        user_id=user_id or project.owner_id,
        action="scope_decomposition",
        entity_type="project",
        entity_id=str(project_id),
        new_value=json.dumps({
            "phases_count": len(decomposition.work_phases),
            "tasks_count": len(created_items),
            "provider": provider_used,
        }),
    )
    db.add(audit)

    project.status = "decomposed"
    db.commit()
    db.refresh(scope)

    logger.info(
        "Scope decomposed successfully",
        project_id=str(project_id),
        work_items_created=len(created_items),
        provider=provider_used,
    )
    return scope, created_items
