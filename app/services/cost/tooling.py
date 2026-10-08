"""Tooling, software licenses, and development SaaS cost calculation."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Tuple


def calculate_tooling_cost(
    duration_weeks: float,
    team_size: int = 4,
    custom_tooling: List[Dict[str, Any]] | None = None,
) -> Tuple[Decimal, List[Dict[str, Any]]]:
    """Calculate tooling & license costs over project duration.

    Standard dev stack: GitHub Enterprise, Jira/Linear, Figma, CI/CD runners, IDE licenses.
    """
    months = max(1.0, duration_weeks / 4.33)
    line_items: List[Dict[str, Any]] = []
    total = Decimal("0.00")

    if custom_tooling:
        for tool in custom_tooling:
            cost = Decimal(str(tool.get("amount", "0.00")))
            total += cost
            line_items.append({
                "category": "tooling",
                "subcategory": tool.get("name", "Software License"),
                "name": tool.get("name", "Software License"),
                "total_amount": cost,
                "source": "User Configuration",
                "formula": tool.get("formula", "Manual specification"),
            })
        return total, line_items

    # Standard industry monthly tooling profile per developer: ~$120/dev/month
    per_dev_monthly = Decimal("125.00")
    dev_tool_cost = Decimal(str(round(team_size * float(per_dev_monthly) * months, 2)))
    total += dev_tool_cost

    line_items.append({
        "category": "tooling",
        "subcategory": "Developer Tooling",
        "name": "Developer Licenses (GitHub, JetBrains/Copilot, Linear, Figma)",
        "quantity": team_size,
        "unit": "seats",
        "unit_cost": per_dev_monthly,
        "total_amount": dev_tool_cost,
        "source": "Market Rate Baseline ($125/seat/month)",
        "formula": f"{team_size} seats × ${per_dev_monthly}/mo × {months:.1f} months",
    })

    # CI/CD & Build Compute: ~$150/month
    cicd_monthly = Decimal("150.00")
    cicd_cost = Decimal(str(round(float(cicd_monthly) * months, 2)))
    total += cicd_cost

    line_items.append({
        "category": "tooling",
        "subcategory": "CI/CD & Testing Infrastructure",
        "name": "Continuous Integration Build Minutes & Test Automation Runners",
        "quantity": round(months, 1),
        "unit": "months",
        "unit_cost": cicd_monthly,
        "total_amount": cicd_cost,
        "source": "Cloud CI/CD Pricing Tier",
        "formula": f"${cicd_monthly}/mo × {months:.1f} months",
    })

    return total, line_items
