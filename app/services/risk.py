"""Automated project risk detection engine grounded in actual project metrics."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.project import Project, ProjectScope
from app.db.models.risk import Risk
from app.db.models.work_item import WorkItem


def analyze_project_risks(
    db: Session,
    estimate_id: uuid.UUID,
    project_id: uuid.UUID,
    total_effort_hours: float,
    duration_weeks: float,
    team_size: int = 4,
) -> List[Risk]:
    """Detect architectural, schedule, and technical risks from computed project properties."""
    risks: List[Risk] = []

    project = db.execute(select(Project).where(Project.id == project_id)).scalar_one_or_none()
    work_items = db.execute(select(WorkItem).where(WorkItem.project_id == project_id)).scalars().all()
    scope = db.execute(select(ProjectScope).where(ProjectScope.project_id == project_id)).scalar_one_or_none()

    # 1. Schedule vs Capacity Risk (Brooks' Law / Over-allocation)
    available_hours = duration_weeks * 40.0 * team_size * 0.75  # 75% productive factor
    if total_effort_hours > available_hours * 1.15:
        severity = "critical" if total_effort_hours > available_hours * 1.4 else "high"
        risks.append(
            Risk(
                id=uuid.uuid4(),
                estimate_id=estimate_id,
                category="Schedule & Capacity",
                title="Engineering Effort Exceeds Available Team Capacity",
                severity=severity,
                evidence=(
                    f"Estimated effort is {total_effort_hours:,.0f} hrs, but nominal capacity for {team_size} engineers "
                    f"over {duration_weeks:.1f} weeks is only {available_hours:,.0f} productive hours."
                ),
                impact="High likelihood of missed milestones, developer burnout, and schedule slip.",
                mitigation="Expand team capacity by 1-2 engineers or descope non-critical WBS work items.",
                source="system",
            )
        )

    # 2. High Complexity Concentration Risk
    high_complex_count = sum(1 for item in work_items if item.complexity in ("high", "very_high"))
    total_items = max(1, len(work_items))
    high_complex_pct = (high_complex_count / total_items) * 100.0

    if high_complex_pct > 35.0:
        risks.append(
            Risk(
                id=uuid.uuid4(),
                estimate_id=estimate_id,
                category="Technical Complexity",
                title="Dense Concentration of High-Complexity Work Items",
                severity="high" if high_complex_pct > 50.0 else "medium",
                evidence=f"{high_complex_count} of {total_items} tasks ({high_complex_pct:.1f}%) are classified as high or very high complexity.",
                impact="Elevated variance in task duration estimates and increased defect injection rates.",
                mitigation="Conduct spike investigations / prototypes for critical tasks before full sprint planning.",
                source="system",
            )
        )

    # 3. Third-party Integration Risk
    if project and project.required_integrations:
        integrations = [i.strip() for i in project.required_integrations.split(",") if i.strip()]
        if len(integrations) >= 3:
            risks.append(
                Risk(
                    id=uuid.uuid4(),
                    estimate_id=estimate_id,
                    category="External Dependency",
                    title="Multiple External API & Service Integrations",
                    severity="medium",
                    evidence=f"Project specifies {len(integrations)} external integrations: {', '.join(integrations[:4])}.",
                    impact="Dependency on third-party API availability, rate limits, sandbox fidelity, and breaking changes.",
                    mitigation="Implement contract testing and mock adapter layers for all external dependencies.",
                    source="system",
                )
            )

    # 4. Scope Ambiguity / Clarification Questions Risk
    if scope and scope.clarification_questions_json:
        import json
        try:
            questions = json.loads(scope.clarification_questions_json)
            if len(questions) >= 4:
                risks.append(
                    Risk(
                        id=uuid.uuid4(),
                        estimate_id=estimate_id,
                        category="Scope Clarity",
                        title="Unresolved Scope Clarification Items",
                        severity="medium",
                        evidence=f"{len(questions)} open architectural clarification questions remain unresolved.",
                        impact="Uncertainty range remains broad until key non-functional constraints are formalized.",
                        mitigation="Review and answer clarification questions in the project workspace with stakeholders.",
                        source="system",
                    )
                )
        except Exception:
            pass

    # Save to database
    for r in risks:
        db.add(r)
    db.flush()

    return risks
