"""NASA93 dataset adapter."""

from __future__ import annotations

from typing import Any, Dict
import numpy as np
import pandas as pd

from app.datasets.adapter import DatasetAdapter


class NASA93Adapter(DatasetAdapter):
    """Adapter for the NASA93 COCOMO software cost estimation benchmark dataset."""

    def load(self, source_path_or_buffer: Any) -> pd.DataFrame:
        if isinstance(source_path_or_buffer, pd.DataFrame):
            return source_path_or_buffer
        return pd.read_csv(source_path_or_buffer)

    def get_column_mapping(self) -> Dict[str, str]:
        return {
            "sloc": "ksloc",
            "act_effort": "effort_person_months",
            "duration": "duration_months",
            "team_size": "team_size",
            "cplx": "complexity",
        }

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        cleaned = df.copy()
        col_map = self.get_column_mapping()

        result = pd.DataFrame()
        # ksloc
        if "sloc" in cleaned.columns:
            result["ksloc"] = pd.to_numeric(cleaned["sloc"], errors="coerce")
        elif "ksloc" in cleaned.columns:
            result["ksloc"] = pd.to_numeric(cleaned["ksloc"], errors="coerce")
        else:
            result["ksloc"] = 10.0

        # effort
        if "act_effort" in cleaned.columns:
            result["effort_person_months"] = pd.to_numeric(cleaned["act_effort"], errors="coerce")
        elif "effort" in cleaned.columns:
            result["effort_person_months"] = pd.to_numeric(cleaned["effort"], errors="coerce")
        else:
            result["effort_person_months"] = result["ksloc"] * 2.5

        # duration
        if "duration" in cleaned.columns:
            result["duration_months"] = pd.to_numeric(cleaned["duration"], errors="coerce")
        else:
            result["duration_months"] = 3.67 * np.power(result["effort_person_months"].clip(lower=0.5), 0.317)

        # team size
        result["team_size"] = (
            pd.to_numeric(cleaned.get("team_size", result["effort_person_months"] / result["duration_months"].clip(lower=1.0)), errors="coerce")
            .clip(lower=1.0)
            .round(1)
        )

        # complexity
        result["complexity"] = cleaned.get("cplx", 2.0).astype(float)

        return result.dropna()
