"""Generic CSV dataset adapter with dynamic column mapping."""

from __future__ import annotations

from typing import Any, Dict, Optional
import numpy as np
import pandas as pd

from app.datasets.adapter import DatasetAdapter


class GenericCSVAdapter(DatasetAdapter):
    """Adapter for arbitrary user-uploaded CSV software project data."""

    def __init__(self, custom_mapping: Optional[Dict[str, str]] = None):
        self.custom_mapping = custom_mapping or {}

    def load(self, source_path_or_buffer: Any) -> pd.DataFrame:
        if isinstance(source_path_or_buffer, pd.DataFrame):
            return source_path_or_buffer
        return pd.read_csv(source_path_or_buffer)

    def get_column_mapping(self) -> Dict[str, str]:
        return self.custom_mapping

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        cleaned = df.copy()
        result = pd.DataFrame()

        # Target fields: ksloc, effort_person_months, duration_months, team_size, complexity
        col_ksloc = self.custom_mapping.get("ksloc")
        if col_ksloc and col_ksloc in cleaned.columns:
            result["ksloc"] = pd.to_numeric(cleaned[col_ksloc], errors="coerce")
        else:
            # Auto-detect column
            for candidate in ["ksloc", "sloc", "loc", "size", "lines_of_code"]:
                if candidate in cleaned.columns:
                    scale = 0.001 if candidate in ["sloc", "loc", "lines_of_code"] else 1.0
                    result["ksloc"] = pd.to_numeric(cleaned[candidate], errors="coerce") * scale
                    break

        if "ksloc" not in result.columns:
            result["ksloc"] = 15.0

        col_effort = self.custom_mapping.get("effort_person_months")
        if col_effort and col_effort in cleaned.columns:
            result["effort_person_months"] = pd.to_numeric(cleaned[col_effort], errors="coerce")
        else:
            for candidate in ["effort", "person_months", "actual_effort", "pm", "effort_pm"]:
                if candidate in cleaned.columns:
                    result["effort_person_months"] = pd.to_numeric(cleaned[candidate], errors="coerce")
                    break

        if "effort_person_months" not in result.columns:
            result["effort_person_months"] = result["ksloc"] * 2.8

        col_duration = self.custom_mapping.get("duration_months")
        if col_duration and col_duration in cleaned.columns:
            result["duration_months"] = pd.to_numeric(cleaned[col_duration], errors="coerce")
        else:
            result["duration_months"] = 3.67 * np.power(result["effort_person_months"].clip(lower=0.5), 0.317)

        result["team_size"] = (
            (result["effort_person_months"] / result["duration_months"].clip(lower=1.0))
            .clip(lower=1.0)
            .round(1)
        )
        result["complexity"] = 2.5

        return result.dropna()
