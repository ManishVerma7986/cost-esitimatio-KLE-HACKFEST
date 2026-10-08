"""End-to-end Machine Learning training and evaluation pipeline."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.model_selection import train_test_split
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models.model_registry import ModelVersion
from app.ml.evaluation import evaluate_estimation_metrics
from app.schemas.dataset import ModelBenchmarkMetrics
from app.utils.logging import get_logger

logger = get_logger("ml.pipeline")


def train_estimation_model(
    df: pd.DataFrame,
    dataset_name: str = "NASA93 / Empirical Benchmark",
    db: Optional[Session] = None,
    dataset_id: Optional[uuid.UUID] = None,
    version_str: str = "v1.0.0",
) -> Tuple[ModelBenchmarkMetrics, Path]:
    """Train LightGBM regressor on software effort data and register model version."""
    settings = get_settings()

    # Features: ksloc, duration_months, team_size, complexity
    feature_cols = [c for c in ["ksloc", "duration_months", "team_size", "complexity"] if c in df.columns]
    target_col = "effort_person_months"

    if target_col not in df.columns or len(feature_cols) == 0:
        raise ValueError(f"Dataset must contain '{target_col}' and feature columns.")

    clean_df = df[feature_cols + [target_col]].dropna()
    if len(clean_df) < 10:
        raise ValueError("Insufficient data rows for training (minimum 10 required).")

    X = clean_df[feature_cols].values
    y = clean_df[target_col].values

    # 80/20 Train-Test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    # Train LightGBM Regressor
    model = LGBMRegressor(
        n_estimators=100,
        learning_rate=0.05,
        max_depth=4,
        num_leaves=15,
        random_state=42,
        verbosity=-1,
    )
    model.fit(X_train, y_train)

    # Test evaluation
    y_pred = model.predict(X_test)
    y_pred = np.clip(y_pred, 0.5, None)

    # 80% empirical prediction interval
    residual_std = np.std(y_train - model.predict(X_train))
    intervals_low = y_pred - 1.28 * residual_std
    intervals_high = y_pred + 1.28 * residual_std

    metrics = evaluate_estimation_metrics(
        y_true=y_test,
        y_pred=y_pred,
        intervals_lower=intervals_low,
        intervals_upper=intervals_high,
    )

    now = datetime.now(timezone.utc)
    model_record = ModelBenchmarkMetrics(
        model_name="LightGBM Software Cost Regressor",
        model_version=version_str,
        dataset_name=dataset_name,
        sample_count=len(clean_df),
        mmre=metrics["mmre"],
        mdmre=metrics["mdmre"],
        pred25=metrics["pred25"],
        mae=metrics["mae"],
        rmse=metrics["rmse"],
        bias=metrics["bias"],
        prediction_interval_coverage_80=metrics["coverage_80"],
        trained_at=now,
    )

    # Persist model artifact
    save_dir = Path(settings.model_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = save_dir / "latest_model.joblib"

    payload = {
        "model": model,
        "feature_names": feature_cols,
        "version": version_str,
        "algorithm": "LightGBM",
        "metrics": metrics,
        "trained_at": now.isoformat(),
    }
    joblib.dump(payload, artifact_path)

    # Save to database registry if db session provided
    if db:
        from sqlalchemy import select, func
        max_v = db.scalar(select(func.max(ModelVersion.version)))
        version_int = (max_v + 1) if max_v is not None else 1

        mv = ModelVersion(
            id=uuid.uuid4(),
            name="LightGBM Software Cost Regressor",
            version=version_int,
            status="production",
            model_type="lightgbm",
            training_dataset_id=dataset_id,
            features_json=json.dumps(feature_cols),
            hyperparameters_json=json.dumps({
                "n_estimators": 100,
                "learning_rate": 0.05,
                "max_depth": 4,
            }),
            metrics_json=json.dumps(metrics),
            test_sample_count=len(X_test),
            training_completed_at=now,
            artifact_path=str(artifact_path),
        )
        db.add(mv)
        db.commit()

    logger.info(
        "Trained and registered ML estimation model",
        version=version_str,
        mmre=metrics["mmre"],
        pred25=metrics["pred25"],
    )

    return model_record, artifact_path


if __name__ == "__main__":
    from app.datasets.nasa93 import NASA93Adapter
    from app.datasets.seed_data import generate_canonical_datasets
    from app.db.session import SessionLocal

    print("Ensuring canonical empirical datasets are ready...")
    generate_canonical_datasets()

    settings = get_settings()
    dataset_file = Path(settings.dataset_dir) / "nasa93.csv"
    adapter = NASA93Adapter()
    raw = adapter.load(dataset_file)
    clean = adapter.normalize(raw)

    print(f"Loaded authentic NASA93 dataset ({len(clean)} rows). Training LightGBM model...")
    db = SessionLocal()
    try:
        record, path = train_estimation_model(
            df=clean,
            dataset_name="NASA93",
            db=db,
            version_str="v1.0.0",
        )
        print(f"Model trained and registered successfully!")
        print(f"Artifact: {path}")
        print(f"MMRE: {record.mmre:.3f} | MdMRE: {record.mdmre:.3f} | PRED(25): {record.pred25:.1f}%")
    finally:
        db.close()
