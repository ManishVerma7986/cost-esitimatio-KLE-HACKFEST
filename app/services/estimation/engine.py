"""Hybrid Estimation Engine Orchestrator.

Ensembles COCOMO-II parametric baseline, ML prediction, historical analogy,
and expert overrides with complete mathematical transparency and source attribution.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.services.estimation.analogy import find_similar_projects
from app.services.estimation.expert import apply_expert_adjustments
from app.services.estimation.ml_model import predict_ml_effort
from app.services.estimation.parametric import calculate_cocomo_baseline
from app.utils.logging import get_logger

logger = get_logger("services.estimation.engine")


class HybridEstimationEngine:
    """Orchestrates multi-model hybrid software effort and schedule estimation."""

    def estimate(
        self,
        tasks: List[Dict[str, Any]],
        effort_multipliers: Dict[str, float] | None = None,
    ) -> Dict[str, Any]:
        """Compute multi-model hybrid estimate."""
        if not tasks:
            return {
                "total_effort_hours": 0.0,
                "person_months": 0.0,
                "duration_weeks": 0.0,
                "task_allocations": {},
                "method": "None",
                "breakdown_by_model": {},
                "similar_projects": [],
            }

        # 1. Parametric Baseline (COCOMO-II)
        cocomo_res = calculate_cocomo_baseline(tasks, effort_multipliers)
        base_pm = cocomo_res["effort_person_months"]
        base_hours = cocomo_res["total_effort_hours"]
        ksloc = cocomo_res["ksloc"]

        # 2. Historical Analogy (Cosine Similarity)
        # Average complexity score: low=1, med=2, high=3, vhigh=4
        comp_map = {"low": 1.0, "medium": 2.0, "high": 3.0, "very_high": 4.0}
        total_comp = sum(comp_map.get(str(t.get("complexity", "medium")).lower(), 2.0) for t in tasks)
        avg_comp = total_comp / len(tasks) if tasks else 2.0

        analogy_res = find_similar_projects(
            ksloc=ksloc, tasks_count=len(tasks), complexity_score=avg_comp
        )
        analogy_pm = analogy_res.get("analogy_effort_person_months")

        # 3. ML Model (LightGBM)
        ml_res = predict_ml_effort(tasks)
        ml_pm = ml_res.get("ml_effort_person_months") if ml_res else None

        # 4. Ensemble Blending
        if ml_pm is not None and analogy_pm is not None:
            # 3-way ensemble
            w_cocomo, w_ml, w_analogy = 0.45, 0.35, 0.20
            ensemble_pm = (w_cocomo * base_pm) + (w_ml * ml_pm) + (w_analogy * analogy_pm)
            method_desc = "Hybrid Ensemble (COCOMO-II 45% + LightGBM 35% + Historical Analogy 20%)"
        elif analogy_pm is not None:
            # 2-way ensemble
            w_cocomo, w_analogy = 0.70, 0.30
            ensemble_pm = (w_cocomo * base_pm) + (w_analogy * analogy_pm)
            method_desc = "Hybrid Ensemble (COCOMO-II 70% + Historical Analogy 30%)"
        else:
            ensemble_pm = base_pm
            method_desc = "COCOMO-II Post-Architecture Baseline"

        ensemble_hours = ensemble_pm * 152.0

        # Scale task allocations by ensemble factor
        ratio = ensemble_hours / base_hours if base_hours > 0 else 1.0
        scaled_allocations = {}
        for key, alloc in cocomo_res["task_allocations"].items():
            scaled_allocations[key] = {
                "likely_hours": round(alloc["likely_hours"] * ratio, 1),
                "optimistic_hours": round(alloc["optimistic_hours"] * ratio, 1),
                "pessimistic_hours": round(alloc["pessimistic_hours"] * ratio, 1),
            }

        # 5. Expert Adjustments / User Overrides
        adjustment_res = apply_expert_adjustments(
            ensemble_hours, scaled_allocations, tasks
        )

        final_hours = adjustment_res["final_effort_hours"]
        final_pm = adjustment_res["final_person_months"]
        final_allocations = adjustment_res["adjusted_allocations"]

        # Recalculate duration from final person months: Duration = 3.67 * (Effort)^0.317
        import math
        duration_months = 3.67 * math.pow(max(0.5, final_pm), 0.317)
        duration_weeks = round(duration_months * 4.33, 1)

        return {
            "total_effort_hours": round(final_hours, 1),
            "person_months": round(final_pm, 2),
            "duration_weeks": duration_weeks,
            "duration_months": round(duration_months, 2),
            "ksloc": ksloc,
            "method": method_desc,
            "task_allocations": final_allocations,
            "breakdown_by_model": {
                "cocomo_hours": round(base_hours, 1),
                "analogy_hours": analogy_res.get("analogy_effort_hours"),
                "ml_hours": ml_res.get("ml_effort_hours") if ml_res else None,
            },
            "similar_projects": analogy_res.get("similar_projects", []),
            "user_overrides_applied": adjustment_res.get("user_overrides_applied", 0),
        }


_engine = HybridEstimationEngine()


def get_estimation_engine() -> HybridEstimationEngine:
    return _engine
