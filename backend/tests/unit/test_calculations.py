"""Unit tests for deterministic calculations (energy, battery, charging, TOU costs)."""

from datetime import datetime, timezone
import pytest

from backend.app.domain.battery import BatterySpecification, BatteryState
from backend.app.domain.vehicle import Vehicle
from backend.app.domain.route import Route
from backend.app.domain.energy_price import EnergyPriceSchedule, TimeOfUseWindow, TariffRateType
from backend.app.domain.calculations.energy import (
    calculate_route_energy_requirement,
    calculate_soc_after_route,
    calculate_temperature_impact_factor,
)
from backend.app.domain.calculations.battery_math import (
    calculate_usable_battery_energy,
    calculate_energy_deficit,
    calculate_required_departure_soc,
)
from backend.app.domain.calculations.charging_math import (
    calculate_charging_duration_minutes,
    calculate_soc_after_charging,
    calculate_charging_cost,
    calculate_unmanaged_baseline_cost,
)


@pytest.fixture
def sample_vehicle() -> Vehicle:
    spec = BatterySpecification(capacity_kwh=100.0, max_charge_power_kw=100.0, degradation_factor=1.0)
    state = BatteryState(soc=50.0, min_soc_limit=15.0, max_soc_limit=90.0)
    return Vehicle(
        id="EV-TEST",
        name="Test EV",
        make="Ford",
        model="E-Transit",
        battery_spec=spec,
        battery_state=state,
        consumption_rate_kwh_per_km=0.30,
    )


@pytest.fixture
def sample_route() -> Route:
    now = datetime(2026, 10, 1, 8, 0, tzinfo=timezone.utc)
    return Route(
        id="R-TEST",
        name="Test Route",
        origin="Depot",
        destination="Suburbs",
        distance_km=100.0,
        estimated_duration_minutes=120,
        required_energy_kwh=30.0,
        departure_time=now,
        required_arrival_time=datetime(2026, 10, 1, 10, 30, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_price_schedule() -> EnergyPriceSchedule:
    return EnergyPriceSchedule(
        schedule_id="test_tou",
        windows=[
            TimeOfUseWindow(start_hour=0, end_hour=7, rate_per_kwh=0.08, rate_type=TariffRateType.OFF_PEAK),
            TimeOfUseWindow(start_hour=7, end_hour=16, rate_per_kwh=0.16, rate_type=TariffRateType.MID_PEAK),
            TimeOfUseWindow(start_hour=16, end_hour=21, rate_per_kwh=0.34, rate_type=TariffRateType.ON_PEAK),
            TimeOfUseWindow(start_hour=21, end_hour=24, rate_per_kwh=0.08, rate_type=TariffRateType.OFF_PEAK),
        ]
    )


def test_temperature_impact_factor():
    """Verify temperature degradation factor is 1.0 at 20C and increases in cold/hot."""
    assert calculate_temperature_impact_factor(20.0) == 1.0
    assert calculate_temperature_impact_factor(0.0) > 1.0
    assert calculate_temperature_impact_factor(40.0) > 1.0


def test_route_energy_calculation(sample_vehicle, sample_route):
    """Verify route energy calculation produces expected kWh."""
    energy = calculate_route_energy_requirement(sample_vehicle, sample_route, ambient_temp_c=20.0)
    # 100 km * 0.3 kWh/km = 30.0 kWh
    assert energy == 30.0


def test_soc_after_route():
    """Verify post-route SOC calculation."""
    # 50% initial SOC - (30 kWh / 100 kWh * 100%) = 20%
    final_soc = calculate_soc_after_route(initial_soc=50.0, effective_battery_capacity_kwh=100.0, energy_consumed_kwh=30.0)
    assert final_soc == 20.0


def test_usable_battery_energy_and_deficit(sample_vehicle):
    """Verify usable energy strictly respects min_soc buffer and computes deficit."""
    # SOC = 50%, min_soc = 15% -> usable = 35% of 100 kWh = 35.0 kWh
    usable = calculate_usable_battery_energy(sample_vehicle.battery_spec, sample_vehicle.battery_state)
    assert usable == 35.0

    # Needed 30 kWh <= 35 kWh usable -> deficit is 0
    assert calculate_energy_deficit(sample_vehicle, required_energy_kwh=30.0) == 0.0

    # Needed 45 kWh > 35 kWh usable -> deficit is 10.0 kWh
    assert calculate_energy_deficit(sample_vehicle, required_energy_kwh=45.0) == 10.0


def test_required_departure_soc(sample_vehicle):
    """Verify target departure SOC ensures arrival buffer."""
    # 30 kWh required on 100 kWh pack = 30% SOC consumption.
    # Target arrival SOC = 15% -> Required departure SOC = 45%
    dep_soc = calculate_required_departure_soc(sample_vehicle, required_energy_kwh=30.0, target_arrival_soc=15.0)
    assert dep_soc == 45.0


def test_charging_duration_calculation():
    """Verify charging duration math with efficiency."""
    # 46 kWh needed, 50 kW charger, 100 kW vehicle max, 0.92 efficiency
    # Effective power to battery = 50 * 0.92 = 46.0 kW
    # 46 kWh / 46 kW = 1.0 hour = 60 minutes
    duration = calculate_charging_duration_minutes(
        energy_needed_kwh=46.0,
        charger_power_kw=50.0,
        vehicle_max_power_kw=100.0,
        efficiency=0.92,
    )
    assert duration == 60


def test_soc_after_charging():
    """Verify SOC rises after charging and caps at 100%."""
    new_soc = calculate_soc_after_charging(initial_soc=30.0, energy_added_kwh=40.0, battery_capacity_kwh=100.0)
    assert new_soc == 70.0

    capped_soc = calculate_soc_after_charging(initial_soc=80.0, energy_added_kwh=50.0, battery_capacity_kwh=100.0)
    assert capped_soc == 100.0


def test_charging_cost_tou_integration(sample_price_schedule):
    """Verify charging cost calculation integrates across TOU rate windows."""
    # Charging from 02:00 for 2 hours (120 min) at 50 kW power draw
    start_time = datetime(2026, 10, 1, 2, 0, tzinfo=timezone.utc)
    cost, energy, rate_type, avg_rate = calculate_charging_cost(
        start_time=start_time,
        duration_minutes=120,
        charging_power_kw=50.0,
        efficiency=0.92,
        price_schedule=sample_price_schedule,
    )
    # 50 kW * 2 hrs = 100 kWh drawn from grid
    # Rate at 2am is off-peak ($0.08/kWh)
    # Cost = 100 * 0.08 = $8.00
    assert energy == 100.0
    assert cost == 8.00
    assert rate_type == TariffRateType.OFF_PEAK


def test_unmanaged_baseline_cost_comparison(sample_price_schedule):
    """Verify baseline cost at peak rate is substantially higher than off-peak."""
    # Immediate charging upon arrival at 17:00 (5 PM, peak rate $0.34)
    arrival_time = datetime(2026, 10, 1, 17, 0, tzinfo=timezone.utc)
    baseline_cost, _ = calculate_unmanaged_baseline_cost(
        energy_needed_kwh=46.0,  # ~1 hour at 50 kW
        arrival_time=arrival_time,
        charger_power_kw=50.0,
        vehicle_max_power_kw=100.0,
        efficiency=0.92,
        price_schedule=sample_price_schedule,
    )
    # Off-peak charging at 02:00
    offpeak_time = datetime(2026, 10, 1, 2, 0, tzinfo=timezone.utc)
    offpeak_cost, _, _, _ = calculate_charging_cost(
        start_time=offpeak_time,
        duration_minutes=60,
        charging_power_kw=50.0,
        efficiency=0.92,
        price_schedule=sample_price_schedule,
    )
    # Peak rate ($0.34) vs off-peak ($0.08) -> baseline is ~4.25x higher
    assert baseline_cost > offpeak_cost
    assert baseline_cost == round(50.0 * 0.34, 2)
