"""Contingency buffer calculation service."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Tuple


def calculate_contingency(
    subtotal: Decimal,
    contingency_percentage: float = 15.0,
) -> Tuple[Decimal, Dict[str, Any]]:
    """Calculate risk contingency buffer based on baseline subtotal."""
    pct = Decimal(str(contingency_percentage)) / Decimal("100.0")
    amount = Decimal(str(round(float(subtotal * pct), 2)))

    line_item = {
        "category": "contingency",
        "subcategory": "Risk Reserve",
        "name": f"Project Contingency & Scope Buffer ({contingency_percentage:.1f}%)",
        "total_amount": amount,
        "source": "Standard PMI / Software Engineering Contingency Guideline",
        "formula": f"${subtotal:,.2f} × {contingency_percentage:.1f}%",
    }

    return amount, line_item
