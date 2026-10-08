"""Unit tests for the Data Quality Engine."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.ml.data_quality import assess_data_quality


def test_empty_dataframe_quality():
    df = pd.DataFrame()
    report = assess_data_quality(df)
    assert report.total_rows == 0
    assert report.total_columns == 0
    assert report.quality_score == 0.0


def test_clean_dataframe_high_score():
    df = pd.DataFrame({
        "loc": [1000, 2500, 5000, 10000, 15000, 20000],
        "effort_pm": [5.2, 12.0, 24.5, 48.0, 70.0, 92.0],
        "team_size": [2, 3, 4, 5, 6, 7],
    })
    report = assess_data_quality(df)
    assert report.total_rows == 6
    assert report.total_columns == 3
    assert report.missing_cells == 0
    assert report.duplicate_rows == 0
    assert report.quality_score >= 95.0


def test_dirty_dataframe_penalties_and_outliers():
    # Construct dataframe with missing values, duplicate row, and extreme outlier
    df = pd.DataFrame({
        "loc": [1000, 1000, np.nan, 2000, 1000000],
        "effort_pm": [5.0, 5.0, 10.0, 12.0, 5000.0],
        "constant_col": ["fixed", "fixed", "fixed", "fixed", "fixed"],
    })
    report = assess_data_quality(df)
    assert report.duplicate_rows == 1
    assert report.missing_cells >= 1
    assert "constant_col" in report.constant_columns
    assert report.quality_score < 80.0
