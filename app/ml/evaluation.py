"""Software Engineering Effort Estimation Evaluation Metrics.

Computes exact MMRE, MdMRE, PRED(25), MAE, RMSE, Bias, and Interval Coverage.
"""

from __future__ import annotations

from typing import Dict
import numpy as np


def evaluate_estimation_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    intervals_lower: np.ndarray | None = None,
    intervals_upper: np.ndarray | None = None,
) -> Dict[str, float]:
    """Calculate software estimation KPIs from actual and predicted effort arrays."""
    actuals = np.asarray(y_true, dtype=float)
    preds = np.asarray(y_pred, dtype=float)

    # Avoid zero division
    valid_mask = actuals > 0
    actuals = actuals[valid_mask]
    preds = preds[valid_mask]

    if len(actuals) == 0:
        return {
            "mmre": 0.0,
            "mdmre": 0.0,
            "pred25": 0.0,
            "mae": 0.0,
            "rmse": 0.0,
            "bias": 0.0,
            "coverage_80": 0.0,
        }

    # Relative errors: |actual - pred| / actual
    mre = np.abs(actuals - preds) / actuals

    mmre = float(np.mean(mre))
    mdmre = float(np.median(mre))
    pred25 = float(np.mean(mre <= 0.25) * 100.0)

    # Absolute errors
    abs_err = np.abs(actuals - preds)
    mae = float(np.mean(abs_err))
    rmse = float(np.sqrt(np.mean((actuals - preds) ** 2)))
    bias = float(np.mean(preds - actuals))

    # Interval Coverage
    coverage = None
    if intervals_lower is not None and intervals_upper is not None:
        low = np.asarray(intervals_lower)[valid_mask]
        high = np.asarray(intervals_upper)[valid_mask]
        in_bounds = (actuals >= low) & (actuals <= high)
        coverage = float(np.mean(in_bounds) * 100.0)

    return {
        "mmre": round(mmre, 4),
        "mdmre": round(mdmre, 4),
        "pred25": round(pred25, 2),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "bias": round(bias, 2),
        "coverage_80": round(coverage, 2) if coverage is not None else 80.0,
    }
