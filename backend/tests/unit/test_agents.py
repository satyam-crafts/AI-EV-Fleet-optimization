"""Unit tests for the agent orchestration and tool execution layer."""

from datetime import datetime, timedelta, timezone
import pytest

from backend.app.domain.battery import BatterySpecification, BatteryState
from backend.app.domain.vehicle import Vehicle, VehicleStatus
from backend.app.domain.route import Route
from backend.app.domain.energy_price import EnergyPriceSchedule, TimeOfUseWindow, TariffRateType
from backend.app.domain.optimization.models import OptimizationResult, BaselineComparison
from backend.app.agents.tools import tool_fleet_summary, tool_route_summary, tool_tariff_summary
from backend.app.agents.orchestrator import FleetAgentOrchestrator
from backend.app.agents.llm_enhancer import LLMEnhancer


@pytest.fixture
def agent_fleet():
    v1 = Vehicle(
        id="EV-01",
        name="Delivery Alpha",
        make="Rivian",
        model="EDV",
        battery_spec=BatterySpecification(capacity_kwh=100.0, max_charge_power_kw=100.0),
        battery_state=BatteryState(soc=70.0),
        consumption_rate_kwh_per_km=0.25,
        current_status=VehicleStatus.IDLE,
    )
    v2 = Vehicle(
        id="EV-02",
        name="Delivery Beta",
        make="Ford",
        model="Transit",
        battery_spec=BatterySpecification(capacity_kwh=80.0, max_charge_power_kw=80.0),
        battery_state=BatteryState(soc=18.0),  # Near buffer floor
        consumption_rate_kwh_per_km=0.30,
        current_status=VehicleStatus.CHARGING,
    )
    return [v1, v2]


@pytest.fixture
def agent_routes():
    now = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)
    r1 = Route(
        id="R-01",
        name="Route Alpha",
        origin="Depot",
        destination="Zone 1",
        distance_km=50.0,
        estimated_duration_minutes=60,
        required_energy_kwh=12.5,
        departure_time=now,
        required_arrival_time=now + timedelta(hours=2),
    )
    return [r1]


@pytest.fixture
def agent_schedule():
    return EnergyPriceSchedule(
        schedule_id="tou",
        windows=[
            TimeOfUseWindow(start_hour=0, end_hour=7, rate_per_kwh=0.08, rate_type=TariffRateType.OFF_PEAK),
            TimeOfUseWindow(start_hour=7, end_hour=24, rate_per_kwh=0.25, rate_type=TariffRateType.ON_PEAK),
        ]
    )


def test_agent_tools_extraction(agent_fleet, agent_routes, agent_schedule):
    """Verify tool functions extract accurate factual summaries."""
    f_sum = tool_fleet_summary(agent_fleet)
    assert f_sum["total_vehicles"] == 2
    assert f_sum["charging_vehicles"] == 1
    assert f_sum["available_vehicles"] == 1
    assert f_sum["attention_required_count"] == 1  # EV-02 is at 18% SOC

    r_sum = tool_route_summary(agent_routes)
    assert r_sum["total_routes"] == 1
    assert r_sum["total_distance_km"] == 50.0

    t_sum = tool_tariff_summary(agent_schedule)
    assert t_sum["off_peak_rate"] == 0.08
    assert t_sum["peak_rate"] == 0.25


def test_llm_enhancer_template_fallback():
    """Verify enhancer produces executive summary using verified deterministic numbers."""
    enhancer = LLMEnhancer()
    now = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
    res = OptimizationResult(
        id="opt-test",
        timestamp=now,
        status="OPTIMAL",
        planning_horizon_hours=24,
        assignments=[],
        charging_plans=[],
        recommendations=[],
        total_fleet_energy_kwh=150.0,
        total_charging_cost=18.50,
        baseline_comparison=BaselineComparison(
            baseline_charging_cost=42.00,
            optimized_charging_cost=18.50,
            cost_savings=23.50,
            savings_percentage=56.0,
            peak_energy_avoided_kwh=120.0,
        ),
    )

    summary = enhancer.generate_executive_summary(res)
    assert "OPTIMAL" in summary
    assert "150.0 kWh" in summary
    assert "$18.50" in summary
    assert "$23.50 (56.0%)" in summary


def test_orchestrator_query_answering(agent_fleet, agent_routes, agent_schedule):
    """Verify orchestrator returns grounded answers for cost, battery, and route questions."""
    orchestrator = FleetAgentOrchestrator()

    # Cost query
    cost_res = orchestrator.answer_query("How can we reduce our charging costs?", agent_fleet, agent_routes, agent_schedule)
    assert "TOU Tariff" in cost_res.response_text or "off-peak" in cost_res.response_text.lower()
    assert cost_res.provider_used == "deterministic_template"

    # Battery query
    bat_res = orchestrator.answer_query("Which vehicles need battery attention?", agent_fleet, agent_routes, agent_schedule)
    assert "Average Fleet SOC" in bat_res.response_text
    assert bat_res.fleet_summary["attention_required_count"] == 1
