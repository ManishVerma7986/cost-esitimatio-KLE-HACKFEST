"""Cloud infrastructure hosting, database, and operational cost calculation."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Tuple


def calculate_cloud_cost(
    duration_weeks: float,
    scale_tier: str = "medium",  # small, medium, enterprise
    custom_monthly_budget: Decimal | None = None,
) -> Tuple[Decimal, List[Dict[str, Any]]]:
    """Calculate cloud infrastructure expenses across staging and development environments."""
    months = max(1.0, duration_weeks / 4.33)
    line_items: List[Dict[str, Any]] = []
    total = Decimal("0.00")

    if custom_monthly_budget is not None:
        cost = Decimal(str(round(float(custom_monthly_budget) * months, 2)))
        line_items.append({
            "category": "cloud",
            "subcategory": "Cloud Infrastructure",
            "name": "Custom Cloud Hosting Allocation",
            "total_amount": cost,
            "source": "User Budget Specification",
            "formula": f"${custom_monthly_budget}/mo × {months:.1f} months",
        })
        return cost, line_items

    # Standard architecture profile (Compute, Managed DB, Storage/CDN, Observability)
    tiers = {
        "small": {
            "compute": Decimal("180.00"),
            "db": Decimal("120.00"),
            "storage_cdn": Decimal("60.00"),
            "observability": Decimal("50.00"),
        },
        "medium": {
            "compute": Decimal("450.00"),
            "db": Decimal("320.00"),
            "storage_cdn": Decimal("150.00"),
            "observability": Decimal("120.00"),
        },
        "enterprise": {
            "compute": Decimal("1200.00"),
            "db": Decimal("850.00"),
            "storage_cdn": Decimal("400.00"),
            "observability": Decimal("350.00"),
        },
    }

    profile = tiers.get(scale_tier.lower(), tiers["medium"])

    for service_name, monthly_rate in profile.items():
        service_cost = Decimal(str(round(float(monthly_rate) * months, 2)))
        total += service_cost
        line_items.append({
            "category": "cloud",
            "subcategory": service_name.replace("_", " ").title(),
            "name": f"Cloud {service_name.replace('_', ' ').title()} Tier",
            "quantity": round(months, 1),
            "unit": "months",
            "unit_cost": monthly_rate,
            "total_amount": service_cost,
            "source": "Standard AWS / GCP Public Pricing Benchmark",
            "formula": f"${monthly_rate}/mo × {months:.1f} months",
        })

    return total, line_items
