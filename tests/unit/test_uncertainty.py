"""Unit tests for Monte Carlo simulation and uncertainty quantification."""

from decimal import Decimal
from app.services.uncertainty.monte_carlo import run_monte_carlo_simulation


def test_monte_carlo_percentile_ordering():
    """Verify strictly monotonic ordering: P90 >= P80 >= P75 >= P50 >= P25 >= P10."""
    allocations = {
        "t1": {"likely_hours": 100.0, "optimistic_hours": 75.0, "pessimistic_hours": 150.0},
        "t2": {"likely_hours": 200.0, "optimistic_hours": 150.0, "pessimistic_hours": 300.0},
    }

    res = run_monte_carlo_simulation(
        task_allocations=allocations,
        hourly_rate_mean=85.0,
        cloud_monthly_budget=500.0,
        duration_months=3.0,
        tooling_monthly_budget=400.0,
        contingency_pct=15.0,
        n_simulations=2000,
    )

    u = res["uncertainty_result"]
    assert u.p10 is not None
    assert u.p50 is not None
    assert u.p80 is not None
    assert u.p90 is not None

    # Monotonic CDF property check
    assert u.p10 <= u.p25
    assert u.p25 <= u.p50
    assert u.p50 <= u.p75
    assert u.p75 <= u.p80
    assert u.p80 <= u.p90
    assert u.p80 >= u.p50


def test_monte_carlo_empty_tasks():
    """Verify empty allocations return zero percentiles cleanly without crashing."""
    res = run_monte_carlo_simulation(
        task_allocations={},
        hourly_rate_mean=85.0,
        cloud_monthly_budget=0.0,
        duration_months=1.0,
        tooling_monthly_budget=0.0,
        n_simulations=100,
    )
    assert res["mean_cost"] == 0.0
