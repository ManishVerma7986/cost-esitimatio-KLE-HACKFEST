"""Full end-to-end estimation generation service."""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models.assumption import Assumption
from app.db.models.audit_log import AuditLog
from app.db.models.estimate import Estimate, EstimateComponent
from app.db.models.project import Project, ProjectScope
from app.db.models.risk import Risk
from app.db.models.work_item import WorkItem
from app.schemas.estimate import (
    ComponentDetail,
    CostBreakdown,
    CostDriverItem,
    EstimateResponse,
    UncertaintyResult,
)
from app.services.cost.engine import get_cost_engine
from app.services.estimation.engine import get_estimation_engine
from app.services.explainability import get_cost_drivers
from app.services.llm.provider import get_llm_service
from app.services.risk import analyze_project_risks
from app.services.uncertainty.monte_carlo import run_monte_carlo_simulation
from app.utils.errors import AppException, EntityNotFoundError
from app.utils.logging import get_logger

logger = get_logger("services.estimate")


def generate_estimate_for_project(
    db: Session,
    project_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
) -> EstimateResponse:
    """Execute end-to-end multi-model estimation, cost calculation, and uncertainty analysis."""
    start_time = time.time()
    now = datetime.now(timezone.utc)
    settings = get_settings()

    project = db.execute(select(Project).where(Project.id == project_id)).scalar_one_or_none()
    if not project:
        raise EntityNotFoundError("Project", project_id)

    work_items = db.execute(
        select(WorkItem).where(WorkItem.project_id == project_id).order_by(WorkItem.sort_order.asc())
    ).scalars().all()

    if not work_items:
        raise AppException(
            "Cannot calculate estimate: Project has no WBS tasks. Run AI decomposition or add tasks first."
        )

    # 1. Prepare tasks for estimation engine
    tasks_input = [
        {
            "id": str(item.id),
            "name": item.name,
            "phase": item.phase,
            "complexity": item.complexity,
            "role": item.role,
            "estimated_hours": item.estimated_hours,
            "is_user_modified": item.is_user_modified,
        }
        for item in work_items
    ]

    # 2. Run Hybrid Estimation Engine
    est_engine = get_estimation_engine()
    est_res = est_engine.estimate(tasks_input)

    total_hours = est_res["total_effort_hours"]
    duration_weeks = est_res["duration_weeks"]
    allocations = est_res["task_allocations"]

    # 3. Update task records with allocated hours in DB
    for item in work_items:
        key = str(item.id)
        if key in allocations:
            alloc = allocations[key]
            if not item.is_user_modified or item.estimated_hours is None:
                item.estimated_hours = alloc["likely_hours"]
                item.estimated_hours_optimistic = alloc["optimistic_hours"]
                item.estimated_hours_pessimistic = alloc["pessimistic_hours"]
    db.flush()

    # 4. Run Cost Engine
    cost_engine = get_cost_engine()
    cost_breakdown, component_dicts = cost_engine.calculate_project_cost(
        tasks=tasks_input,
        task_allocations=allocations,
        duration_weeks=duration_weeks,
        team_size=4,
        scale_tier="medium",
        contingency_percentage=15.0,
    )

    # 5. Run Monte Carlo Uncertainty Engine (10,000 simulations)
    sim_res = run_monte_carlo_simulation(
        task_allocations=allocations,
        hourly_rate_mean=85.0,
        cloud_monthly_budget=float(cost_breakdown.cloud) / max(1.0, duration_weeks / 4.33),
        duration_months=duration_weeks / 4.33,
        tooling_monthly_budget=float(cost_breakdown.tooling) / max(1.0, duration_weeks / 4.33),
        contingency_pct=15.0,
    )
    unc: UncertaintyResult = sim_res["uncertainty_result"]

    # 6. Run Explainability
    drivers = get_cost_drivers(
        tasks=tasks_input,
        ksloc=est_res.get("ksloc", 5.0),
        total_hours=total_hours,
        integrations_count=2,
    )

    # 7. Next version number
    prev_estimate = db.execute(
        select(Estimate)
        .where(Estimate.project_id == project_id)
        .order_by(desc(Estimate.version))
    ).scalars().first()
    next_version = (prev_estimate.version + 1) if prev_estimate else 1

    # 8. Create Estimate Record
    estimate = Estimate(
        id=uuid.uuid4(),
        project_id=project_id,
        version=next_version,
        status="completed",
        personnel_cost=cost_breakdown.personnel,
        tooling_cost=cost_breakdown.tooling,
        cloud_cost=cost_breakdown.cloud,
        other_cost=cost_breakdown.other,
        contingency_cost=cost_breakdown.contingency,
        total_cost=cost_breakdown.total,
        total_effort_hours=total_hours,
        estimated_duration_weeks=duration_weeks,
        p10=unc.p10,
        p25=unc.p25,
        p50=unc.p50,
        p75=unc.p75,
        p80=unc.p80,
        p90=unc.p90,
        confidence_level=unc.confidence_level,
        estimation_method=est_res["method"],
        cost_drivers_json=json.dumps([d.model_dump() for d in drivers]),
        estimation_started_at=now,
        estimation_completed_at=datetime.now(timezone.utc),
        app_version=settings.app_version,
    )
    db.add(estimate)
    db.flush()

    # 9. Save Line-item Components
    for c in component_dicts:
        comp = EstimateComponent(
            id=uuid.uuid4(),
            estimate_id=estimate.id,
            category=c["category"],
            subcategory=c.get("subcategory"),
            name=c["name"],
            quantity=c.get("quantity"),
            unit=c.get("unit"),
            unit_cost=c.get("unit_cost"),
            total_amount=c["total_amount"],
            source=c.get("source", "calculation"),
            formula=c.get("formula"),
        )
        db.add(comp)

    # 10. Run Risk Engine
    analyze_project_risks(
        db=db,
        estimate_id=estimate.id,
        project_id=project_id,
        total_effort_hours=total_hours,
        duration_weeks=duration_weeks,
    )

    # 11. Initial Assumptions
    default_assumptions = [
        ("contingency_pct", "15.0", "contingency", "Industry standard nominal risk reserve"),
        ("work_week_hours", "40.0", "personnel", "Full-time equivalent work week"),
        ("developer_productivity_factor", "0.75", "productivity", "Productive coding factor (excluding meetings/admin)"),
        ("cloud_environment", "AWS / GCP Medium Tier", "cloud", "Managed container cluster + HA PostgreSQL database"),
    ]
    for key, val, cat, desc_text in default_assumptions:
        assump = Assumption(
            id=uuid.uuid4(),
            estimate_id=estimate.id,
            key=key,
            value=val,
            category=cat,
            source="system_default",
            description=desc_text,
        )
        db.add(assump)

    # 12. Generate LLM Narrative Recommendation
    llm = get_llm_service()
    rec_obj = llm.generate_recommendation(
        project_name=project.name,
        total_cost=float(cost_breakdown.total),
        effort_hours=total_hours,
        duration_weeks=duration_weeks,
        personnel_cost=float(cost_breakdown.personnel),
        tooling_cost=float(cost_breakdown.tooling),
        cloud_cost=float(cost_breakdown.cloud),
        contingency_cost=float(cost_breakdown.contingency),
        p50=float(unc.p50 or cost_breakdown.total),
        p80=float(unc.p80 or cost_breakdown.total),
    )
    estimate.recommendation_text = rec_obj.summary

    # 13. Audit Log
    cycle_time = round(time.time() - start_time, 2)
    audit = AuditLog(
        id=uuid.uuid4(),
        user_id=user_id or project.owner_id,
        action="calculate_estimate",
        entity_type="estimate",
        entity_id=str(estimate.id),
        new_value=json.dumps({
            "total_cost": str(cost_breakdown.total),
            "hours": total_hours,
            "version": estimate.version,
            "cycle_time_sec": cycle_time,
        }),
    )
    db.add(audit)

    project.status = "estimated"
    db.commit()
    db.refresh(estimate)

    logger.info(
        "Estimate calculated successfully",
        estimate_id=str(estimate.id),
        total_cost=float(estimate.total_cost),
        cycle_time=cycle_time,
    )

    return build_estimate_response(estimate, drivers, unc, component_dicts, cycle_time)


def build_estimate_response(
    estimate: Estimate,
    drivers: List[CostDriverItem],
    unc: UncertaintyResult,
    component_dicts: List[Dict[str, Any]],
    cycle_time: float,
) -> EstimateResponse:
    """Helper to convert ORM model to API response schema."""
    breakdown = CostBreakdown(
        personnel=estimate.personnel_cost or Decimal("0.00"),
        tooling=estimate.tooling_cost or Decimal("0.00"),
        cloud=estimate.cloud_cost or Decimal("0.00"),
        other=estimate.other_cost or Decimal("0.00"),
        contingency=estimate.contingency_cost or Decimal("0.00"),
        total=estimate.total_cost or Decimal("0.00"),
    )

    comp_details = [
        ComponentDetail(
            category=c["category"],
            subcategory=c.get("subcategory"),
            name=c["name"],
            quantity=c.get("quantity"),
            unit=c.get("unit"),
            unit_cost=c.get("unit_cost"),
            total_amount=c["total_amount"],
            source=c.get("source", "calculation"),
            formula=c.get("formula"),
        )
        for c in component_dicts
    ]

    return EstimateResponse(
        id=estimate.id,
        project_id=estimate.project_id,
        version=estimate.version,
        status=estimate.status,
        cost_breakdown=breakdown,
        total_effort_hours=estimate.total_effort_hours,
        estimated_duration_weeks=estimate.estimated_duration_weeks,
        uncertainty=unc,
        components=comp_details,
        cost_drivers=drivers,
        estimation_method=estimate.estimation_method,
        recommendation=estimate.recommendation_text,
        app_version=estimate.app_version,
        estimation_cycle_time_seconds=cycle_time,
        created_at=estimate.created_at,
    )


def get_estimate_response(db: Session, estimate_id: uuid.UUID) -> EstimateResponse:
    """Retrieve an existing estimate and serialize as full EstimateResponse."""
    estimate = db.execute(select(Estimate).where(Estimate.id == estimate_id)).scalar_one_or_none()
    if not estimate:
        raise EntityNotFoundError("Estimate", estimate_id)

    # Load components
    components = db.execute(
        select(EstimateComponent).where(EstimateComponent.estimate_id == estimate_id)
    ).scalars().all()

    comp_dicts = [
        {
            "category": c.category,
            "subcategory": c.subcategory,
            "name": c.name,
            "quantity": c.quantity,
            "unit": c.unit,
            "unit_cost": c.unit_cost,
            "total_amount": c.total_amount,
            "source": c.source,
            "formula": c.formula,
        }
        for c in components
    ]

    drivers = []
    if estimate.cost_drivers_json:
        try:
            drivers = [CostDriverItem.model_validate(d) for d in json.loads(estimate.cost_drivers_json)]
        except Exception:
            pass

    unc = UncertaintyResult(
        p10=estimate.p10,
        p25=estimate.p25,
        p50=estimate.p50,
        p75=estimate.p75,
        p80=estimate.p80,
        p90=estimate.p90,
        confidence_level=estimate.confidence_level or 0.80,
        method="monte_carlo",
        simulation_count=10000,
        is_calibrated=True,
    )

    return build_estimate_response(estimate, drivers, unc, comp_dicts, 0.0)
