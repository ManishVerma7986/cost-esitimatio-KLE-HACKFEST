"""Unit tests for Cost Engine."""

from decimal import Decimal
from app.services.cost.engine import CostEngine
from app.services.cost.personnel import calculate_personnel_cost, get_role_rate


def test_role_rate_resolution():
    """Verify role name matches resolve to correct market rates."""
    assert get_role_rate("Software Architect") == Decimal("125.00")
    assert get_role_rate("Frontend Developer") == Decimal("80.00")
    assert get_role_rate("Senior Backend Developer") == Decimal("100.00")
    assert get_role_rate("QA Engineer") == Decimal("65.00")
    assert get_role_rate("Unknown Role") == Decimal("85.00")


def test_personnel_cost_calculation():
    """Verify personnel cost equals hours times rate for all roles."""
    tasks = [
        {"id": "1", "name": "Task 1", "role": "Frontend Developer"},
        {"id": "2", "name": "Task 2", "role": "QA Engineer"},
    ]
    allocations = {
        "1": {"likely_hours": 100.0},
        "2": {"likely_hours": 50.0},
    }

    cost, items = calculate_personnel_cost(tasks, allocations)
    # 100 * 80 + 50 * 65 = 8000 + 3250 = 11250
    assert cost == Decimal("11250.00")
    assert len(items) == 2


def test_cost_breakdown_sums_to_total():
    """Verify total cost is the exact sum of personnel, tooling, cloud, and contingency."""
    engine = CostEngine()
    tasks = [
        {"id": "1", "name": "API Service", "role": "Backend Developer", "complexity": "medium"},
    ]
    allocations = {"1": {"likely_hours": 120.0}}

    breakdown, items = engine.calculate_project_cost(
        tasks=tasks,
        task_allocations=allocations,
        duration_weeks=8.0,
        contingency_percentage=15.0,
    )

    subtotal = breakdown.personnel + breakdown.tooling + breakdown.cloud + breakdown.other
    expected_contingency = subtotal * Decimal("0.15")

    assert breakdown.total == subtotal + breakdown.contingency
    assert abs(breakdown.contingency - expected_contingency) < Decimal("0.02")
    assert breakdown.total > Decimal("0.00")
