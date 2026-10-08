"""Personnel labor cost calculation service."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Tuple

# Default standard market hourly rates ($ USD)
DEFAULT_HOURLY_RATES: Dict[str, Decimal] = {
    "software architect": Decimal("125.00"),
    "lead architect": Decimal("125.00"),
    "technical lead": Decimal("115.00"),
    "senior backend developer": Decimal("100.00"),
    "backend developer": Decimal("85.00"),
    "frontend developer": Decimal("80.00"),
    "mobile developer": Decimal("90.00"),
    "full-stack developer": Decimal("90.00"),
    "devops engineer": Decimal("100.00"),
    "cloud engineer": Decimal("105.00"),
    "security engineer": Decimal("110.00"),
    "database administrator": Decimal("95.00"),
    "qa engineer": Decimal("65.00"),
    "ui/ux designer": Decimal("75.00"),
    "project manager": Decimal("85.00"),
    "scrum master": Decimal("80.00"),
    "general engineer": Decimal("85.00"),
}


def get_role_rate(role_name: str | None, custom_rates: Dict[str, Decimal] | None = None) -> Decimal:
    """Resolve hourly billing rate for a given role name."""
    rates = custom_rates or DEFAULT_HOURLY_RATES
    if not role_name:
        return Decimal("85.00")

    role_key = role_name.strip().lower()

    # Exact match
    if role_key in rates:
        return rates[role_key]

    # Partial substring match
    for key, rate in rates.items():
        if key in role_key or role_key in key:
            return rate

    return Decimal("85.00")


def calculate_personnel_cost(
    tasks: List[Dict[str, Any]],
    task_allocations: Dict[str, Dict[str, float]],
    custom_rates: Dict[str, Decimal] | None = None,
) -> Tuple[Decimal, List[Dict[str, Any]]]:
    """Calculate total personnel cost and itemized role breakdowns.

    Returns:
        Tuple of (total_personnel_cost, line_items)
    """
    total_cost = Decimal("0.00")
    line_items: List[Dict[str, Any]] = []

    # Aggregate by role
    role_hours: Dict[str, float] = {}

    for task in tasks:
        key = str(task.get("id") or task.get("name"))
        alloc = task_allocations.get(key, {})
        hours = alloc.get("likely_hours") or float(task.get("estimated_hours") or 0.0)
        role = task.get("role") or "General Engineer"

        role_hours[role] = role_hours.get(role, 0.0) + hours

    for role, hours in sorted(role_hours.items(), key=lambda x: x[0]):
        rate = get_role_rate(role, custom_rates)
        cost = Decimal(str(round(hours * float(rate), 2)))
        total_cost += cost

        line_items.append({
            "category": "personnel",
            "subcategory": role,
            "name": f"Labor - {role}",
            "quantity": round(hours, 1),
            "unit": "hours",
            "unit_cost": rate,
            "total_amount": cost,
            "source": "Standard Market Baseline / Configured Rate",
            "formula": f"{hours:.1f} hrs @ ${rate:.2f}/hr",
        })

    return total_cost, line_items
