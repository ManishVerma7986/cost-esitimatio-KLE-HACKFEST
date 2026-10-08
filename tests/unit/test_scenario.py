"""Unit tests for What-If scenario modeling and Brooks' Law schedule compression."""

from __future__ import annotations

import uuid
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.models.estimate import Estimate
from app.db.models.project import Project
from app.db.models.user import User
from app.db.models.work_item import WorkItem
from app.schemas.scenario import ScenarioCreate, ScenarioModification
from app.services.scenario import create_scenario, get_scenario_comparison


def test_what_if_scenario_modeling_and_compression(db_session: Session, test_user: User):
    # 1. Setup project, work items, and base estimate
    proj = Project(
        id=uuid.uuid4(),
        owner_id=test_user.id,
        name="Scenario Test Project",
        description="Testing scenario deltas.",
    )
    db_session.add(proj)

    # Add work items
    item1 = WorkItem(
        id=uuid.uuid4(),
        project_id=proj.id,
        name="Backend Microservice",
        phase="Backend",
        complexity="high",
        role="Backend Developer",
        estimated_hours=100.0,
    )
    item2 = WorkItem(
        id=uuid.uuid4(),
        project_id=proj.id,
        name="Frontend Dashboard",
        phase="Frontend",
        complexity="medium",
        role="Frontend Developer",
        estimated_hours=60.0,
    )
    db_session.add_all([item1, item2])

    base_estimate = Estimate(
        id=uuid.uuid4(),
        project_id=proj.id,
        version=1,
        status="completed",
        total_effort_hours=160.0,
        estimated_duration_weeks=10.0,
        personnel_cost=Decimal("15000.00"),
        total_cost=Decimal("20000.00"),
    )
    db_session.add(base_estimate)
    db_session.commit()

    # 2. Create Scenario with Brooks' law compression (cutting deadline to 5 weeks) and rate increase
    scenario_in = ScenarioCreate(
        estimate_id=base_estimate.id,
        name="Aggressive Rush Delivery",
        description="Compress timeline and increase senior consultant rates",
        modifications=ScenarioModification(
            deadline_weeks=5.0,
            rate_multiplier=1.2,
            contingency_percentage=20.0,
        ),
    )

    scenario = create_scenario(db_session, scenario_in, user_id=test_user.id)

    assert scenario.name == "Aggressive Rush Delivery"
    assert scenario.estimated_duration_weeks == 5.0
    # Schedule compression overhead + rate multiplier should increase total cost
    assert scenario.total_cost > base_estimate.total_cost
    assert scenario.cost_delta > 0

    # 3. Verify comparison
    comparison = get_scenario_comparison(db_session, base_estimate.id)
    assert comparison.baseline_estimate_id == base_estimate.id
    assert len(comparison.scenarios) == 1
    assert comparison.scenarios[0].name == "Aggressive Rush Delivery"
