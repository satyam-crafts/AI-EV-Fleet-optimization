"""Integration tests for all FastAPI REST endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_get_fleet_overview():
    """Verify GET /api/v1/fleet returns KPIs and counts."""
    response = client.get("/api/v1/fleet")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "kpis" in data
    assert data["vehicles_count"] >= 5
    assert data["routes_count"] >= 4


def test_get_vehicles_and_by_id():
    """Verify GET /api/v1/vehicles and single vehicle lookup."""
    res = client.get("/api/v1/vehicles")
    assert res.status_code == 200
    vehicles = res.json()
    assert len(vehicles) > 0

    first_id = vehicles[0]["id"]
    res_single = client.get(f"/api/v1/vehicles/{first_id}")
    assert res_single.status_code == 200
    assert res_single.json()["id"] == first_id

    # 404 test
    res_not_found = client.get("/api/v1/vehicles/NON_EXISTENT_VEHICLE")
    assert res_not_found.status_code == 404


def test_get_routes_and_by_id():
    """Verify GET /api/v1/routes and single route lookup."""
    res = client.get("/api/v1/routes")
    assert res.status_code == 200
    routes = res.json()
    assert len(routes) > 0

    first_id = routes[0]["id"]
    res_single = client.get(f"/api/v1/routes/{first_id}")
    assert res_single.status_code == 200
    assert res_single.json()["id"] == first_id

    # 404 test
    res_not_found = client.get("/api/v1/routes/NON_EXISTENT_ROUTE")
    assert res_not_found.status_code == 404


def test_get_charging_stations():
    """Verify GET /api/v1/charging-stations returns depot and hub bays."""
    res = client.get("/api/v1/charging-stations")
    assert res.status_code == 200
    stations = res.json()
    assert len(stations) >= 2
    for s in stations:
        assert len(s["ports"]) >= 1


def test_get_energy_prices():
    """Verify GET /api/v1/energy-prices returns TOU schedule."""
    res = client.get("/api/v1/energy-prices")
    assert res.status_code == 200
    schedule = res.json()
    assert "windows" in schedule
    assert len(schedule["windows"]) >= 3


def test_post_optimize():
    """Verify POST /api/v1/optimize triggers optimization and returns result."""
    payload = {
        "planning_horizon_hours": 24,
        "weights": {
            "cost_weight": 0.6,
            "battery_health_weight": 0.2,
            "schedule_slack_weight": 0.2,
        },
        "min_soc_buffer_percent": 15.0,
        "max_soc_target_percent": 90.0,
    }
    res = client.post("/api/v1/optimize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "assignments" in data
    assert "charging_plans" in data
    assert "baseline_comparison" in data
    assert len(data["recommendations"]) > 0


def test_get_latest_optimization():
    """Verify GET /api/v1/optimization/latest returns result."""
    res = client.get("/api/v1/optimization/latest")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "assignments" in data


def test_get_recommendations():
    """Verify GET /api/v1/recommendations returns active explainability recommendations."""
    res = client.get("/api/v1/recommendations")
    assert res.status_code == 200
    recs = res.json()
    assert isinstance(recs, list)
    if len(recs) > 0:
        first = recs[0]
        assert "reasoning" in first
        assert "decision" in first["reasoning"]


def test_agent_conversational_query():
    """Verify POST /api/v1/agent/query processes questions and returns grounded response."""
    payload = {"query": "How can we shift our fleet charging to off-peak periods?"}
    res = client.post("/api/v1/agent/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "response_text" in data
    assert "fleet_summary" in data
    assert len(data["response_text"]) > 20


def test_demo_reset():
    """Verify POST /api/v1/demo/reset restores clean seed data."""
    res = client.post("/api/v1/demo/reset")
    assert res.status_code == 200
    assert res.json()["status"] == "success"
