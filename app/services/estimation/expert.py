"""Expert and user adjustment handler for software estimation."""

from __future__ import annotations

from typing import Any, Dict, List


def apply_expert_adjustments(
    base_hours: float,
    task_allocations: Dict[str, Dict[str, float]],
    user_adjusted_tasks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Incorporate manual user task overrides into the estimate while preserving audit trail."""
    adjusted_allocations = dict(task_allocations)
    total_adjusted_hours = 0.0
    adjustment_count = 0

    # Map overrides
    override_map = {
        str(t.get("id")): t.get("estimated_hours")
        for t in user_adjusted_tasks
        if t.get("is_user_modified") and t.get("estimated_hours") is not None
    }

    for key, alloc in adjusted_allocations.items():
        if key in override_map and override_map[key] is not None:
            override_val = float(override_map[key])
            adjusted_allocations[key] = {
                "likely_hours": override_val,
                "optimistic_hours": round(override_val * 0.8, 1),
                "pessimistic_hours": round(override_val * 1.35, 1),
                "is_override": True,
            }
            total_adjusted_hours += override_val
            adjustment_count += 1
        else:
            total_adjusted_hours += alloc["likely_hours"]

    delta_hours = total_adjusted_hours - base_hours

    return {
        "final_effort_hours": round(total_adjusted_hours, 1),
        "final_person_months": round(total_adjusted_hours / 152.0, 2),
        "adjusted_allocations": adjusted_allocations,
        "user_overrides_applied": adjustment_count,
        "delta_hours": round(delta_hours, 1),
    }
