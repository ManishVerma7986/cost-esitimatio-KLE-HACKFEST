"""What-if scenario modeling and side-by-side comparison service."""

from __future__ import annotations

import json
import uuid
from decimal import Decimal
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.estimate import Estimate
from app.db.models.scenario import Scenario
from app.db.models.work_item import WorkItem
from app.schemas.scenario import (
    ScenarioComparison,
    ScenarioCreate,
    ScenarioModification,
    ScenarioResponse,
)
from app.services.cost.engine import get_cost_engine
from app.services.estimation.engine import get_estimation_engine
from app.services.uncertainty.monte_carlo import run_monte_carlo_simulation
from app.utils.errors import EntityNotFoundError
from app.utils.logging import get_logger

logger = get_logger("services.scenario")


def create_scenario(
    db: Session,
    scenario_in: ScenarioCreate,
    user_id: uuid.UUID | None = None,
) -> Scenario:
    """Calculate and persist a what-if scenario based on parameter modifications."""
    base_estimate = db.execute(
        select(Estimate).where(Estimate.id == scenario_in.estimate_id)
    ).scalar_one_or_none()

    if not base_estimate:
        raise EntityNotFoundError("Estimate", scenario_in.estimate_id)

    # 1. Fetch work items for the project
    work_items = db.execute(
        select(WorkItem).where(WorkItem.project_id == base_estimate.project_id)
    ).scalars().all()

    mods = scenario_in.modifications
    excluded_ids = set(mods.exclude_work_item_ids)

    # 2. Filter tasks based on scope exclusions
    active_tasks = [
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
        if str(item.id) not in excluded_ids
    ]

    # 3. Recalculate Estimation Engine with active tasks
    est_engine = get_estimation_engine()
    est_res = est_engine.estimate(active_tasks)

    base_hours = est_res["total_effort_hours"]
    if mods.additional_work_item_hours:
        base_hours += mods.additional_work_item_hours

    # Brooks' Law / schedule compression penalty
    duration_weeks = est_res["duration_weeks"]
    if mods.deadline_weeks and mods.deadline_weeks < duration_weeks:
        compression_ratio = duration_weeks / mods.deadline_weeks
        # Schedule compression introduces communication overhead (quadratic or power curve)
        overhead_factor = 1.0 + 0.25 * (compression_ratio - 1.0)
        base_hours *= overhead_factor
        duration_weeks = mods.deadline_weeks

    # 4. Prepare rate adjustments
    custom_rates = None
    if mods.rate_multiplier and mods.rate_multiplier != 1.0:
        from app.services.cost.personnel import DEFAULT_HOURLY_RATES
        custom_rates = {
            role: rate * Decimal(str(mods.rate_multiplier))
            for role, rate in DEFAULT_HOURLY_RATES.items()
        }

    contingency_pct = (
        mods.contingency_percentage
        if mods.contingency_percentage is not None
        else 15.0
    )

    # 5. Recalculate Cost Engine
    cost_engine = get_cost_engine()
    cost_breakdown, _ = cost_engine.calculate_project_cost(
        tasks=active_tasks,
        task_allocations=est_res["task_allocations"],
        duration_weeks=duration_weeks,
        team_size=int(4 * (mods.team_size_multiplier or 1.0)),
        custom_rates=custom_rates,
        custom_cloud_budget=mods.cloud_monthly_override,
        contingency_percentage=contingency_pct,
    )

    # 6. Recalculate Monte Carlo Uncertainty for scenario
    sim_res = run_monte_carlo_simulation(
        task_allocations=est_res["task_allocations"],
        hourly_rate_mean=85.0 * (mods.rate_multiplier or 1.0),
        cloud_monthly_budget=float(cost_breakdown.cloud) / max(1.0, duration_weeks / 4.33),
        duration_months=duration_weeks / 4.33,
        tooling_monthly_budget=float(cost_breakdown.tooling) / max(1.0, duration_weeks / 4.33),
        contingency_pct=contingency_pct,
        n_simulations=2000,
    )
    unc = sim_res["uncertainty_result"]

    # 7. Compute Deltas against baseline estimate
    cost_delta = cost_breakdown.total - (base_estimate.total_cost or Decimal("0.00"))
    effort_delta = base_hours - (base_estimate.total_effort_hours or 0.0)
    duration_delta = duration_weeks - (base_estimate.estimated_duration_weeks or 0.0)

    # 8. Save Scenario Record
    scenario = Scenario(
        id=uuid.uuid4(),
        estimate_id=scenario_in.estimate_id,
        name=scenario_in.name,
        description=scenario_in.description,
        parameters_json=json.dumps(mods.model_dump()),
        personnel_cost=cost_breakdown.personnel,
        tooling_cost=cost_breakdown.tooling,
        cloud_cost=cost_breakdown.cloud,
        other_cost=cost_breakdown.other,
        contingency_cost=cost_breakdown.contingency,
        total_cost=cost_breakdown.total,
        total_effort_hours=round(base_hours, 1),
        estimated_duration_weeks=round(duration_weeks, 1),
        p50=unc.p50,
        p80=unc.p80,
        cost_delta=cost_delta,
        effort_delta_hours=round(effort_delta, 1),
        duration_delta_weeks=round(duration_delta, 1),
    )

    db.add(scenario)
    db.commit()
    db.refresh(scenario)

    logger.info(
        "Created what-if scenario",
        scenario_id=str(scenario.id),
        name=scenario.name,
        total_cost=float(scenario.total_cost),
    )
    return scenario


def get_scenario_comparison(db: Session, estimate_id: uuid.UUID) -> ScenarioComparison:
    """Retrieve baseline estimate and all associated scenarios for side-by-side comparison."""
    estimate = db.execute(select(Estimate).where(Estimate.id == estimate_id)).scalar_one_or_none()
    if not estimate:
        raise EntityNotFoundError("Estimate", estimate_id)

    scenarios = db.execute(
        select(Scenario).where(Scenario.estimate_id == estimate_id).order_by(Scenario.created_at.asc())
    ).scalars().all()

    return ScenarioComparison(
        baseline_estimate_id=estimate.id,
        baseline_total_cost=estimate.total_cost or Decimal("0.00"),
        baseline_effort_hours=estimate.total_effort_hours or 0.0,
        baseline_duration_weeks=estimate.estimated_duration_weeks or 0.0,
        baseline_p50=estimate.p50,
        baseline_p80=estimate.p80,
        scenarios=[ScenarioResponse.model_validate(s) for s in scenarios],
    )
