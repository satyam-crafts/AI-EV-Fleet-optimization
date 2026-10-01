"""Unit tests for domain models and validation logic."""

from datetime import datetime, timedelta, timezone
import pytest
from pydantic import ValidationError

from backend.app.domain.battery import BatteryHealthStatus, BatterySpecification, BatteryState
from backend.app.domain.vehicle import Vehicle, VehicleStatus
from backend.app.domain.route import Route
from backend.app.domain.charging import ChargingStation, ChargingPort, ConnectorType, ChargingStationStatus
from backend.app.domain.energy_price import EnergyPriceSchedule, TimeOfUseWindow, TariffRateType


def test_battery_specification_valid():
    """Verify standard battery specification and effective capacity calculation."""
    spec = BatterySpecification(
        capacity_kwh=100.0,
        max_charge_power_kw=150.0,
        degradation_factor=0.9,
    )
    assert spec.effective_capacity_kwh == 90.0


def test_battery_specification_invalid():
    """Verify validation rejects zero or negative capacity."""
    with pytest.raises(ValidationError):
        BatterySpecification(capacity_kwh=-10.0, max_charge_power_kw=50.0)


def test_battery_state_bounds():
    """Verify min_soc must be strictly less than max_soc."""
    # Valid
    state = BatteryState(soc=50.0, min_soc_limit=15.0, max_soc_limit=90.0)
    assert state.soc == 50.0

    # Invalid: min >= max
    with pytest.raises(ValidationError):
        BatteryState(soc=50.0, min_soc_limit=90.0, max_soc_limit=80.0)

    # Invalid: SOC > 100
    with pytest.raises(ValidationError):
        BatteryState(soc=105.0)


def test_vehicle_usable_energy_and_range():
    """Verify vehicle computed properties for energy and estimated range."""
    spec = BatterySpecification(capacity_kwh=100.0, max_charge_power_kw=150.0, degradation_factor=1.0)
    state = BatteryState(soc=65.0, min_soc_limit=15.0, max_soc_limit=90.0)
    vehicle = Vehicle(
        id="EV-01",
        name="Delivery Van 1",
        make="Rivian",
        model="EDV 700",
        battery_spec=spec,
        battery_state=state,
        consumption_rate_kwh_per_km=0.25,
    )
    # usable SOC = 65% - 15% = 50%
    # usable energy = 100 kWh * 50% = 50 kWh
    assert vehicle.usable_energy_kwh == 50.0
    # estimated range = 50 kWh / 0.25 kWh/km = 200.0 km
    assert vehicle.estimated_range_km == 200.0


def test_route_schedule_validation():
    """Verify departure must precede arrival and distance must be positive."""
    now = datetime.now(timezone.utc)
    
    # Valid route
    route = Route(
        id="R-01",
        name="Metro Delivery",
        origin="Depot",
        destination="District B",
        distance_km=45.0,
        estimated_duration_minutes=60,
        required_energy_kwh=11.25,
        departure_time=now + timedelta(hours=1),
        required_arrival_time=now + timedelta(hours=3),
    )
    assert route.total_scheduled_duration_minutes == 120

    # Invalid: departure after arrival
    with pytest.raises(ValidationError):
        Route(
            id="R-02",
            name="Invalid Schedule",
            origin="Depot",
            destination="District B",
            distance_km=45.0,
            estimated_duration_minutes=60,
            required_energy_kwh=11.25,
            departure_time=now + timedelta(hours=3),
            required_arrival_time=now + timedelta(hours=1),
        )


def test_tou_schedule_lookup():
    """Verify TOU rate lookups at various hours."""
    schedule = EnergyPriceSchedule(
        schedule_id="test_tou",
        windows=[
            TimeOfUseWindow(start_hour=0, end_hour=7, rate_per_kwh=0.08, rate_type=TariffRateType.OFF_PEAK),
            TimeOfUseWindow(start_hour=7, end_hour=16, rate_per_kwh=0.16, rate_type=TariffRateType.MID_PEAK),
            TimeOfUseWindow(start_hour=16, end_hour=21, rate_per_kwh=0.34, rate_type=TariffRateType.ON_PEAK),
            TimeOfUseWindow(start_hour=21, end_hour=24, rate_per_kwh=0.08, rate_type=TariffRateType.OFF_PEAK),
        ]
    )
    assert schedule.get_rate_at_hour(3) == 0.08
    assert schedule.get_rate_at_hour(10) == 0.16
    assert schedule.get_rate_at_hour(18) == 0.34
    assert schedule.get_rate_type_at_hour(18) == TariffRateType.ON_PEAK
    assert schedule.off_peak_rate == 0.08
    assert schedule.peak_rate == 0.34
