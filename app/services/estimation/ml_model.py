"""Machine Learning Estimation Model inference."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib
import numpy as np

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger("services.estimation.ml")


def extract_tabular_features(tasks: List[Dict[str, Any]]) -> Dict[str, float]:
    """Extract quantitative features from task list for ML inference."""
    total_tasks = len(tasks)
    if total_tasks == 0:
        return {}

    low_count = sum(1 for t in tasks if str(t.get("complexity", "")).lower() == "low")
    med_count = sum(1 for t in tasks if str(t.get("complexity", "")).lower() == "medium")
    high_count = sum(1 for t in tasks if str(t.get("complexity", "")).lower() == "high")
    vhigh_count = sum(1 for t in tasks if str(t.get("complexity", "")).lower() == "very_high")

    phases = len(set(str(t.get("phase", "")) for t in tasks if t.get("phase")))
    roles = len(set(str(t.get("role", "")) for t in tasks if t.get("role")))

    avg_complexity = (low_count * 1 + med_count * 2 + high_count * 3 + vhigh_count * 4) / total_tasks

    return {
        "task_count": float(total_tasks),
        "low_count": float(low_count),
        "med_count": float(med_count),
        "high_count": float(high_count),
        "vhigh_count": float(vhigh_count),
        "unique_phases": float(phases),
        "unique_roles": float(roles),
        "avg_complexity": float(avg_complexity),
    }


def predict_ml_effort(tasks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Predict software effort using trained LightGBM / Gradient Boosting model if available."""
    settings = get_settings()
    model_path = Path(settings.model_dir) / "latest_model.joblib"

    if not model_path.exists():
        logger.info("No trained ML model found at path, skipping ML prediction", path=str(model_path))
        return None

    try:
        model_payload = joblib.load(model_path)
        model = model_payload.get("model")
        feature_names = model_payload.get("feature_names", [])

        feats = extract_tabular_features(tasks)
        x_vec = np.array([[feats.get(fn, 0.0) for fn in feature_names]])

        pred_pm = float(model.predict(x_vec)[0])
        pred_pm = max(0.5, pred_pm)

        return {
            "ml_effort_person_months": round(pred_pm, 2),
            "ml_effort_hours": round(pred_pm * 152.0, 1),
            "model_version": model_payload.get("version", "v1.0.0"),
            "model_algorithm": model_payload.get("algorithm", "LightGBM"),
        }
    except Exception as exc:
        logger.warning("ML inference failed", error=str(exc))
        return None
