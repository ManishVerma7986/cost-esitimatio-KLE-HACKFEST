"""COCOMO-II Parametric Estimation Baseline.

Implements the standard published Constructive Cost Model (COCOMO-II)
post-architecture model for deterministic software effort and duration calculation.
Reference: Boehm et al., 'Software Cost Estimation with COCOMO II'
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

# Standard COCOMO-II published constants for nominal software development
A_NOMINAL = 2.94  # Base calibration coefficient
B_NOMINAL = 1.10  # Scale factor exponent (slight diseconomy of scale)
C_SCHEDULE = 3.67  # Duration coefficient
D_SCHEDULE = 0.317  # Duration exponent

# Standard working hours conversion
HOURS_PER_PERSON_MONTH = 152.0  # (19 working days/month * 8 hours/day)

# Complexity to nominal Source Lines of Code (SLOC) per task
SLOC_PER_COMPLEXITY = {
    "low": 150.0,
    "medium": 450.0,
    "high": 1200.0,
    "very_high": 2800.0,
}

# Standard Effort Multipliers (Nominal = 1.0)
EFFORT_MULTIPLIERS = {
    "RELY": 1.0,  # Required software reliability
    "DATA": 1.0,  # Database size
    "CPLX": 1.0,  # Product complexity
    "TIME": 1.0,  # Execution time constraint
    "STOR": 1.0,  # Main storage constraint
    "ACAP": 1.0,  # Analyst capability
    "PCAP": 1.0,  # Programmer capability
    "APEX": 1.0,  # Applications experience
    "PLEX": 1.0,  # Platform experience
    "LTEX": 1.0,  # Language and tool experience
    "TOOL": 1.0,  # Use of software tools
    "SCED": 1.0,  # Required development schedule
}


def estimate_sloc_from_tasks(tasks: List[Dict[str, Any]]) -> float:
    """Calculate equivalent SLOC based on task complexities and scope."""
    total_sloc = 0.0
    for task in tasks:
        complexity = str(task.get("complexity", "medium")).lower()
        sloc = SLOC_PER_COMPLEXITY.get(complexity, 450.0)
        total_sloc += sloc
    return total_sloc


def calculate_cocomo_baseline(
    tasks: List[Dict[str, Any]],
    effort_multipliers: Dict[str, float] | None = None,
    a_coefficient: float = A_NOMINAL,
    b_exponent: float = B_NOMINAL,
) -> Dict[str, Any]:
    """Calculate COCOMO-II effort, duration, and task-level hour allocations.

    Returns:
        dict containing:
            - total_sloc: Estimated source lines of code
            - ksloc: Thousands of SLOC
            - effort_person_months: Nominal person-months
            - total_effort_hours: Total effort in hours (152 hrs/PM)
            - duration_months: Estimated calendar duration in months
            - duration_weeks: Estimated calendar duration in weeks
            - task_allocations: Map of task_id/name -> allocated hours
    """
    if not tasks:
        return {
            "total_sloc": 0.0,
            "ksloc": 0.0,
            "effort_person_months": 0.0,
            "total_effort_hours": 0.0,
            "duration_months": 0.0,
            "duration_weeks": 0.0,
            "task_allocations": {},
        }

    total_sloc = estimate_sloc_from_tasks(tasks)
    ksloc = max(0.1, total_sloc / 1000.0)

    # Effort Multiplier product EAF (Effort Adjustment Factor)
    multipliers = effort_multipliers or EFFORT_MULTIPLIERS
    eaf = 1.0
    for factor, value in multipliers.items():
        eaf *= value

    # Effort = A * (Size)^B * EAF (in Person-Months)
    effort_pm = a_coefficient * math.pow(ksloc, b_exponent) * eaf
    effort_pm = max(0.5, effort_pm)  # Minimum half a person-month for non-empty project
    total_hours = effort_pm * HOURS_PER_PERSON_MONTH

    # Duration = C * (Effort)^D (in Calendar Months)
    duration_months = C_SCHEDULE * math.pow(effort_pm, D_SCHEDULE)
    duration_weeks = duration_months * 4.33  # 52 weeks / 12 months

    # Proportionally distribute hours across tasks based on their complexity weights
    task_weights = []
    for task in tasks:
        comp = str(task.get("complexity", "medium")).lower()
        weight = SLOC_PER_COMPLEXITY.get(comp, 450.0)
        task_weights.append(weight)

    total_w = sum(task_weights)
    sum_weights = total_w if total_w > 0 else 1.0

    task_allocations = {}
    for task, weight in zip(tasks, task_weights):
        task_hours = (weight / sum_weights) * total_hours
        key = str(task.get("id") or task.get("name"))
        task_allocations[key] = {
            "likely_hours": round(task_hours, 1),
            "optimistic_hours": round(task_hours * 0.75, 1),
            "pessimistic_hours": round(task_hours * 1.45, 1),
        }

    return {
        "total_sloc": round(total_sloc, 0),
        "ksloc": round(ksloc, 2),
        "effort_person_months": round(effort_pm, 2),
        "total_effort_hours": round(total_hours, 1),
        "duration_months": round(duration_months, 2),
        "duration_weeks": round(duration_weeks, 1),
        "task_allocations": task_allocations,
        "method": "COCOMO-II Post-Architecture Baseline",
    }
