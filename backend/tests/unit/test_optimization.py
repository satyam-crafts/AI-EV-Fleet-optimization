"""Unit tests for deterministic optimization engine, feasibility, and scheduling."""

from datetime import datetime, timedelta, timezone
import pytest

from backend.app.domain.battery import BatterySpecification, BatteryState, BatteryHealthStatus
from backend.app.domain.vehicle import Vehicle, VehicleStatus
from backend.app.domain.route import Route
from backend.app.domain.charging import ChargingStation, ChargingPort, ConnectorType, ChargingStationStatus
from backend.app.domain.energy_price import EnergyPriceSchedule, TimeOfUseWindow, TariffRateType
from backend.app.domain.optimization import OptimizationRequest, OptimizationObjectiveWeights
from backend.app.domain.optimization.feasibility import evaluate_vehicle_route_feasibility
from backend.app.domain.optimization.scheduler import PortOccupancyTracker, schedule_smart_charging_session
from backend.app.domain.optimization.optimizer import FleetOptimizationEngine


@pytest.fixture
def test_fleet():
    spec1 = BatterySpecification(capacity_kwh=100.0, max_charge_power_kw=100.0, degradation_factor=1.0)
    state1 = BatteryState(soc=85.0, min_soc_limit=15.0, max_soc_limit=90.0)
    v1 = Vehicle(
        id="EV-01",
        name="Van Alpha",
        make="Rivian",
        model="EDV 700",
        battery_spec=spec1,
        battery_state=state1,
        consumption_rate_kwh_per_km=0.25,
    )

    spec2 = BatterySpecification(capacity_kwh=75.0, max_charge_power_kw=50.0, degradation_factor=0.95)
    state2 = BatteryState(soc=20.0, min_soc_limit=15.0, max_soc_limit=90.0)  # Low SOC
    v2 = Vehicle(
        id="EV-02",
        name="Van Beta",
        make="Ford",
        model="E-Transit",
        battery_spec=spec2,
        battery_state=state2,
        consumption_rate_kwh_per_km=0.30,
    )
    return [v1, v2]


@pytest.fixture
def test_routes():
    now = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)
    r1 = Route(
        id="R-01",
        name="Downtown Loop",
        origin="Depot",
        destination="Metro Center",
        distance_km=60.0,
        estimated_duration_minutes=90,
        required_energy_kwh=15.0,
        departure_time=now,
        required_arrival_time=now + timedelta(hours=2),
    )
    # Long route requiring ~60 kWh
    r2 = Route(
        id="R-02",
        name="Regional Cargo",
        origin="Depot",
        destination="Airport Hub",
        distance_km=200.0,
        estimated_duration_minutes=180,
        required_energy_kwh=60.0,
        departure_time=now + timedelta(hours=3),
        required_arrival_time=now + timedelta(hours=7),
    )
    return [r1, r2]


@pytest.fixture
def test_stations():
    port1 = ChargingPort(port_id="P-1", connector_type=ConnectorType.CCS2, max_power_kw=100.0)
    port2 = ChargingPort(port_id="P-2", connector_type=ConnectorType.CCS2, max_power_kw=50.0)
    return [
        ChargingStation(
            id="CS-01",
            name="Depot Fast Bay",
            location="Depot",
            total_power_capacity_kw=150.0,
            charging_efficiency=0.92,
            ports=[port1, port2],
        )
    ]


@pytest.fixture
def test_price_schedule():
    return EnergyPriceSchedule(
        schedule_id="test_tou",
        windows=[
            TimeOfUseWindow(start_hour=0, end_hour=7, rate_per_kwh=0.08, rate_type=TariffRateType.OFF_PEAK),
            TimeOfUseWindow(start_hour=7, end_hour=16, rate_per_kwh=0.16, rate_type=TariffRateType.MID_PEAK),
            TimeOfUseWindow(start_hour=16, end_hour=21, rate_per_kwh=0.34, rate_type=TariffRateType.ON_PEAK),
            TimeOfUseWindow(start_hour=21, end_hour=24, rate_per_kwh=0.08, rate_type=TariffRateType.OFF_PEAK),
        ]
    )


def test_feasibility_evaluation_feasible(test_fleet, test_routes):
    """Verify EV-01 with 85% SOC can complete 15 kWh route without deficit."""
    result = evaluate_vehicle_route_feasibility(test_fleet[0], test_routes[0])
    assert result.feasible is True
    assert result.energy_deficit_kwh == 0.0
    assert result.projected_arrival_soc > 15.0


def test_feasibility_evaluation_energy_deficit(test_fleet, test_routes):
    """Verify EV-02 with 20% SOC flags energy deficit for 60 kWh route."""
    result = evaluate_vehicle_route_feasibility(test_fleet[1], test_routes[1])
    assert result.feasible is False
    assert result.energy_deficit_kwh > 0.0
    assert len(result.violations) > 0


def test_port_occupancy_tracker():
    """Verify occupancy tracker prevents overlapping port reservations."""
    tracker = PortOccupancyTracker()
    now = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
    t1_end = now + timedelta(hours=2)

    assert tracker.is_port_available("CS-01", "P-1", now, t1_end) is True
    tracker.book_port("CS-01", "P-1", now, t1_end)

    # Overlapping interval should be unavailable
    overlap_start = now + timedelta(minutes=30)
    overlap_end = now + timedelta(hours=1)
    assert tracker.is_port_available("CS-01", "P-1", overlap_start, overlap_end) is False

    # Disjoint interval after t1_end should be available
    after_start = now + timedelta(hours=2, minutes=5)
    after_end = now + timedelta(hours=3)
    assert tracker.is_port_available("CS-01", "P-1", after_start, after_end) is True


def test_fleet_optimizer_execution(test_fleet, test_routes, test_stations, test_price_schedule):
    """Verify optimizer executes and produces assignments, baseline comparison, and valid result."""
    engine = FleetOptimizationEngine(
        vehicles=test_fleet,
        routes=test_routes,
        charging_stations=test_stations,
        price_schedule=test_price_schedule,
    )
    request = OptimizationRequest(
        planning_horizon_hours=24,
        min_soc_buffer_percent=15.0,
        max_soc_target_percent=90.0,
    )
    result = engine.optimize(request)

    assert result.id.startswith("opt-")
    assert result.status in ["OPTIMAL", "FEASIBLE", "PARTIALLY_FEASIBLE"]
    assert len(result.assignments) > 0
    assert result.baseline_comparison.baseline_charging_cost >= result.baseline_comparison.optimized_charging_cost
    assert result.execution_time_ms >= 0.0
