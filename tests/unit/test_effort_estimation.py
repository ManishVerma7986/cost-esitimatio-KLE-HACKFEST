"""Unit tests for Parametric COCOMO-II and Hybrid Estimation Engine."""

from app.services.estimation.engine import HybridEstimationEngine
from app.services.estimation.parametric import calculate_cocomo_baseline, estimate_sloc_from_tasks


def test_sloc_conversion():
    """Verify task complexity weights translate accurately to SLOC."""
    tasks = [
        {"complexity": "low"},      # 150
        {"complexity": "medium"},   # 450
        {"complexity": "high"},     # 1200
        {"complexity": "very_high"} # 2800
    ]
    total_sloc = estimate_sloc_from_tasks(tasks)
    assert total_sloc == 4600.0


def test_cocomo_baseline_properties():
    """Verify COCOMO baseline produces non-negative, non-zero results for non-empty tasks."""
    tasks = [
        {"id": "t1", "name": "Task 1", "complexity": "medium"},
        {"id": "t2", "name": "Task 2", "complexity": "high"},
    ]
    res = calculate_cocomo_baseline(tasks)

    assert res["total_effort_hours"] > 0
    assert res["effort_person_months"] > 0
    assert res["duration_weeks"] > 0
    assert len(res["task_allocations"]) == 2
    # High complexity task should receive more hours than medium
    assert res["task_allocations"]["t2"]["likely_hours"] > res["task_allocations"]["t1"]["likely_hours"]


def test_hybrid_engine_orchestration():
    """Verify hybrid engine ensembles models and returns complete structure."""
    engine = HybridEstimationEngine()
    tasks = [
        {"id": "t1", "name": "Auth", "complexity": "medium", "role": "Backend Developer"},
        {"id": "t2", "name": "UI", "complexity": "medium", "role": "Frontend Developer"},
    ]
    res = engine.estimate(tasks)

    assert res["total_effort_hours"] > 0
    assert res["duration_weeks"] > 0
    assert "method" in res
    assert "similar_projects" in res
    assert len(res["similar_projects"]) > 0
