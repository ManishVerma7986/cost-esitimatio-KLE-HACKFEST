"""Base interface for dataset adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict
import pandas as pd


class DatasetAdapter(ABC):
    """Abstract base class for software engineering historical dataset adapters."""

    @abstractmethod
    def load(self, source_path_or_buffer: Any) -> pd.DataFrame:
        """Load raw dataset into pandas DataFrame."""
        pass

    @abstractmethod
    def get_column_mapping(self) -> Dict[str, str]:
        """Return mapping from dataset raw columns to canonical feature names."""
        pass

    @abstractmethod
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform raw DataFrame into canonical schema:
        ['ksloc', 'effort_person_months', 'duration_months', 'team_size', 'complexity']
        """
        pass
