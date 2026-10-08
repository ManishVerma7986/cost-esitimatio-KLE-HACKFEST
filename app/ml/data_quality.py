"""Data Quality Engine for inspecting and scoring dataset cleanliness."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.schemas.dataset import DataQualityReport


def assess_data_quality(df: pd.DataFrame) -> DataQualityReport:
    """Analyze dataset quality metrics without silently mutating user data."""
    total_rows = int(len(df))
    total_cols = int(len(df.columns))

    if total_rows == 0 or total_cols == 0:
        return DataQualityReport(
            total_rows=0,
            total_columns=0,
            missing_cells=0,
            missing_percentage=0.0,
            duplicate_rows=0,
            constant_columns=[],
            outlier_counts={},
            column_types={},
            quality_score=0.0,
        )

    # 1. Missing cells
    missing_cells = int(df.isna().sum().sum())
    total_cells = total_rows * total_cols
    missing_pct = round((missing_cells / total_cells) * 100.0, 2)

    # 2. Duplicate rows
    duplicate_rows = int(df.duplicated().sum())

    # 3. Constant columns
    constant_cols = [str(col) for col in df.columns if df[col].nunique(dropna=False) <= 1]

    # 4. Outlier detection using 1.5 * IQR for numeric columns
    outlier_counts: dict[str, int] = {}
    for col in df.select_dtypes(include=[np.number]).columns:
        series = df[col].dropna()
        if len(series) >= 4:
            q25, q75 = np.percentile(series, 25), np.percentile(series, 75)
            iqr = q75 - q25
            if iqr > 0:
                lower = q25 - 1.5 * iqr
                upper = q75 + 1.5 * iqr
                outliers = int(((series < lower) | (series > upper)).sum())
                outlier_counts[str(col)] = outliers

    # 5. Column types
    col_types = {str(col): str(dtype) for col, dtype in df.dtypes.items()}

    # 6. Overall Quality Score computation (0 - 100)
    score = 100.0
    # Penalty for missing cells: up to -30
    score -= min(30.0, missing_pct * 3.0)
    # Penalty for duplicate rows: up to -20
    score -= min(20.0, (duplicate_rows / total_rows) * 100.0 * 2.0)
    # Penalty for constant columns: up to -20
    score -= min(20.0, len(constant_cols) * 10.0)
    # Penalty for extreme outliers: up to -15
    total_outliers = sum(outlier_counts.values())
    score -= min(15.0, (total_outliers / total_rows) * 10.0)

    quality_score = max(0.0, min(100.0, round(score, 1)))

    return DataQualityReport(
        total_rows=total_rows,
        total_columns=total_cols,
        missing_cells=missing_cells,
        missing_percentage=missing_pct,
        duplicate_rows=duplicate_rows,
        constant_columns=constant_cols,
        outlier_counts=outlier_counts,
        column_types=col_types,
        quality_score=quality_score,
    )
