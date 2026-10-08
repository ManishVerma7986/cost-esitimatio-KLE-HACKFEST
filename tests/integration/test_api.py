"""End-to-end integration tests for FastAPI backend."""

import uuid
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Verify health endpoint responds with system status."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("healthy", "degraded")
    assert "checks" in data


def test_full_estimation_workflow(client: TestClient):
    """Verify complete lifecycle: Create project -> Decompose -> Estimate -> Scenario -> Export."""
    # 1. Create Project
    proj_payload = {
        "name": "Cloud FinTech Payment Switch",
        "description": "High-throughput cloud payment switch processing card transactions with PCI-DSS compliance, OAuth2, and webhooks.",
        "product_type": "SaaS Platform",
        "industry": "FinTech",
        "target_platform": "AWS Cloud Native",
        "expected_users": "100,000 MAU",
        "required_integrations": "Stripe, Plaid, Datadog",
    }
    create_res = client.post("/api/projects", json=proj_payload)
    assert create_res.status_code == 201
    project = create_res.json()
    project_id = project["id"]
    assert project["name"] == proj_payload["name"]

    # 2. Scope Decomposition
    decomp_res = client.post(f"/api/projects/{project_id}/decompose")
    assert decomp_res.status_code == 200
    decomp_data = decomp_res.json()
    assert decomp_data["tasks_generated"] > 0

    # 3. Verify WBS
    wbs_res = client.get(f"/api/projects/{project_id}/wbs")
    assert wbs_res.status_code == 200
    wbs_items = wbs_res.json()
    assert len(wbs_items) > 0

    # 4. Calculate Estimate
    est_res = client.post(f"/api/projects/{project_id}/estimate")
    assert est_res.status_code == 201
    estimate = est_res.json()
    estimate_id = estimate["id"]

    cb = estimate["cost_breakdown"]
    assert float(cb["total"]) > 0
    assert float(cb["personnel"]) > 0
    assert float(cb["contingency"]) > 0
    assert estimate["total_effort_hours"] > 0
    assert estimate["estimated_duration_weeks"] > 0

    # Verify Uncertainty
    unc = estimate["uncertainty"]
    assert unc is not None
    assert float(unc["p50"]) > 0
    assert float(unc["p80"]) >= float(unc["p50"])

    # 5. Create Scenario
    scenario_payload = {
        "estimate_id": estimate_id,
        "name": "Fast Track Launch",
        "description": "Compress deadline by 20% and add 1 senior engineer",
        "modifications": {
            "team_size_multiplier": 1.25,
            "contingency_percentage": 20.0,
            "deadline_weeks": estimate["estimated_duration_weeks"] * 0.8,
        },
    }
    scen_res = client.post(f"/api/estimates/{estimate_id}/scenarios", json=scenario_payload)
    assert scen_res.status_code == 201
    scenario = scen_res.json()
    assert scenario["name"] == "Fast Track Launch"
    assert scenario["total_cost"] is not None

    # 6. Scenario Comparison
    comp_res = client.get(f"/api/estimates/{estimate_id}/scenarios/compare")
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert len(comp_data["scenarios"]) == 1

    # 7. Exports
    json_export = client.get(f"/api/estimates/{estimate_id}/export/json")
    assert json_export.status_code == 200
    assert "project_name" in json_export.json()

    csv_export = client.get(f"/api/estimates/{estimate_id}/export/csv")
    assert csv_export.status_code == 200
    assert "Total Amount ($)" in csv_export.text

    excel_export = client.get(f"/api/estimates/{estimate_id}/export/excel")
    assert excel_export.status_code == 200
    assert len(excel_export.content) > 1000

    pdf_export = client.get(f"/api/estimates/{estimate_id}/export/pdf")
    assert pdf_export.status_code == 200
    assert pdf_export.content.startswith(b"%PDF")
