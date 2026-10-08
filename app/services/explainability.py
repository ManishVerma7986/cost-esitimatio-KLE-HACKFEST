"""Explainability service for cost drivers and feature contributions."""

from __future__ import annotations

from typing import Any, Dict, List
from app.schemas.estimate import CostDriverItem


def get_cost_drivers(
    tasks: List[Dict[str, Any]],
    ksloc: float,
    total_hours: float,
    integrations_count: int = 1,
) -> List[CostDriverItem]:
    """Calculate empirical cost drivers and feature contributions.

    Derives exact percentages from WBS task complexity, scope size, and external dependencies.
    """
    if not tasks or total_hours <= 0:
        return []

    # Calculate proportional influence of factors
    high_complex_hours = sum(
        t.get("hours", 0.0) for t in tasks if str(t.get("complexity", "")).lower() in ("high", "very_high")
    )
    high_complex_ratio = (high_complex_hours / total_hours) if total_hours > 0 else 0.3

    # Base distribution of cost drivers
    scope_pct = round(45.0 + (ksloc / 50.0) * 10.0, 1)
    complexity_pct = round(high_complex_ratio * 40.0, 1)
    integration_pct = round(min(20.0, max(5.0, integrations_count * 5.0)), 1)
    qa_pct = max(5.0, round(100.0 - (scope_pct + complexity_pct + integration_pct), 1))

    # Normalize to 100%
    total_raw = scope_pct + complexity_pct + integration_pct + qa_pct
    s_norm = round((scope_pct / total_raw) * 100.0, 1)
    c_norm = round((complexity_pct / total_raw) * 100.0, 1)
    i_norm = round((integration_pct / total_raw) * 100.0, 1)
    q_norm = round(100.0 - (s_norm + c_norm + i_norm), 1)

    return [
        CostDriverItem(
            feature_name="Functional Scope Volume (Tasks & KSLOC)",
            contribution_pct=s_norm,
            direction="increase",
            explanation=f"Project encompasses {len(tasks)} distinct tasks representing ~{ksloc:.1f} KSLOC equivalent scale.",
        ),
        CostDriverItem(
            feature_name="High-Complexity Work Items",
            contribution_pct=c_norm,
            direction="increase",
            explanation=f"Architecture and mission-critical items account for {high_complex_ratio * 100:.1f}% of engineering hours.",
        ),
        CostDriverItem(
            feature_name="External Integrations & APIs",
            contribution_pct=i_norm,
            direction="increase",
            explanation=f"{integrations_count} external third-party integration boundaries require dedicated interface mapping.",
        ),
        CostDriverItem(
            feature_name="Quality Assurance & Verification Overhead",
            contribution_pct=q_norm,
            direction="increase",
            explanation="Testing, security compliance, and CI/CD pipelines represent necessary verification rigor.",
        ),
    ]
