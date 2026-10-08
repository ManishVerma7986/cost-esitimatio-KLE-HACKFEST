"""Total Cost Engine Orchestrator."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Tuple

from app.schemas.estimate import CostBreakdown
from app.services.cost.cloud import calculate_cloud_cost
from app.services.cost.contingency import calculate_contingency
from app.services.cost.personnel import calculate_personnel_cost
from app.services.cost.tooling import calculate_tooling_cost


class CostEngine:
    """Orchestrates comprehensive software project cost estimation."""

    def calculate_project_cost(
        self,
        tasks: List[Dict[str, Any]],
        task_allocations: Dict[str, Dict[str, float]],
        duration_weeks: float,
        team_size: int = 4,
        scale_tier: str = "medium",
        custom_rates: Dict[str, Decimal] | None = None,
        custom_tooling: List[Dict[str, Any]] | None = None,
        custom_cloud_budget: Decimal | None = None,
        contingency_percentage: float = 15.0,
    ) -> Tuple[CostBreakdown, List[Dict[str, Any]]]:
        """Compute total cost across all categories with full itemized line items."""
        all_components: List[Dict[str, Any]] = []

        # 1. Personnel Labor Cost
        personnel_cost, personnel_items = calculate_personnel_cost(
            tasks=tasks,
            task_allocations=task_allocations,
            custom_rates=custom_rates,
        )
        all_components.extend(personnel_items)

        # 2. Tooling & Software Licenses
        tooling_cost, tooling_items = calculate_tooling_cost(
            duration_weeks=duration_weeks,
            team_size=team_size,
            custom_tooling=custom_tooling,
        )
        all_components.extend(tooling_items)

        # 3. Cloud Infrastructure
        cloud_cost, cloud_items = calculate_cloud_cost(
            duration_weeks=duration_weeks,
            scale_tier=scale_tier,
            custom_monthly_budget=custom_cloud_budget,
        )
        all_components.extend(cloud_items)

        # 4. Other / Direct Costs
        other_cost = Decimal("0.00")

        # 5. Contingency Buffer
        subtotal = personnel_cost + tooling_cost + cloud_cost + other_cost
        contingency_cost, contingency_item = calculate_contingency(
            subtotal=subtotal,
            contingency_percentage=contingency_percentage,
        )
        all_components.append(contingency_item)

        total_cost = subtotal + contingency_cost

        breakdown = CostBreakdown(
            personnel=personnel_cost,
            tooling=tooling_cost,
            cloud=cloud_cost,
            other=other_cost,
            contingency=contingency_cost,
            total=total_cost,
        )

        return breakdown, all_components


_cost_engine = CostEngine()


def get_cost_engine() -> CostEngine:
    return _cost_engine
