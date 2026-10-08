"""Property and mathematical invariant tests."""

from decimal import Decimal
from app.services.cost.engine import CostEngine
from app.services.estimation.engine import HybridEstimationEngine


def test_invariant_cost_non_negative():
    """Invariant: Software costs must always be strictly non-negative."""
    engine = CostEngine()
    breakdown, _ = engine.calculate_project_cost(
        tasks=[],
        task_allocations={},
        duration_weeks=4.0,
    )
    assert breakdown.personnel >= Decimal("0.00")
    assert breakdown.total >= Decimal("0.00")


def test_invariant_scope_reduction_reduces_or_maintains_effort():
    """Invariant: Removing tasks from scope must never increase total estimated effort."""
    engine = HybridEstimationEngine()
    full_tasks = [
        {"id": "1", "name": "Feature A", "complexity": "medium"},
        {"id": "2", "name": "Feature B", "complexity": "high"},
        {"id": "3", "name": "Feature C", "complexity": "low"},
    ]
    reduced_tasks = [
        {"id": "1", "name": "Feature A", "complexity": "medium"},
        {"id": "3", "name": "Feature C", "complexity": "low"},
    ]

    res_full = engine.estimate(full_tasks)
    res_reduced = engine.estimate(reduced_tasks)

    assert res_reduced["total_effort_hours"] <= res_full["total_effort_hours"]


def test_invariant_complexity_ordering():
    """Invariant: Higher complexity tasks should be allocated more hours than lower complexity."""
    engine = HybridEstimationEngine()
    tasks = [
        {"id": "low_task", "name": "Low Task", "complexity": "low"},
        {"id": "high_task", "name": "High Task", "complexity": "high"},
    ]
    res = engine.estimate(tasks)
    low_hrs = res["task_allocations"]["low_task"]["likely_hours"]
    high_hrs = res["task_allocations"]["high_task"]["likely_hours"]

    assert high_hrs > low_hrs
