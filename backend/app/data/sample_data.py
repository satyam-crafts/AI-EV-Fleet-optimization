"""Realistic Sample Fleet, Routes, Charging Stations, and TOU Tariffs.

Provides deterministic baseline scenarios including feasible missions,
tight-turnaround missions, and constrained edge cases.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Tuple

from backend.app.domain.battery import (
    BatteryHealthStatus,
    BatterySpecification,
    BatteryState,
)
from backend.app.domain.vehicle import Vehicle, VehicleStatus
from backend.app.domain.route import Route, RouteWaypoint
from backend.app.domain.charging import (
    ChargingStation,
    ChargingPort,
    ConnectorType,
    ChargingStationStatus,
)
from backend.app.domain.energy_price import (
    EnergyPriceSchedule,
    TimeOfUseWindow,
    TariffRateType,
)


def get_default_price_schedule() -> EnergyPriceSchedule:
    """Returns a realistic 3-tier commercial Time-Of-Use tariff schedule."""
    return EnergyPriceSchedule(
        schedule_id="tou-commercial-standard",
        name="Grid Utility Commercial Fleet TOU Tariff",
        currency="USD",
        windows=[
            TimeOfUseWindow(
                start_hour=0,
                end_hour=6,
                rate_per_kwh=0.08,
                rate_type=TariffRateType.OFF_PEAK,
                label="Super Off-Peak Night",
            ),
            TimeOfUseWindow(
                start_hour=6,
                end_hour=16,
                rate_per_kwh=0.16,
                rate_type=TariffRateType.MID_PEAK,
                label="Daytime Regular / Mid-Peak",
            ),
            TimeOfUseWindow(
                start_hour=16,
                end_hour=21,
                rate_per_kwh=0.34,
                rate_type=TariffRateType.ON_PEAK,
                label="Evening Critical Peak",
            ),
            TimeOfUseWindow(
                start_hour=21,
                end_hour=24,
                rate_per_kwh=0.10,
                rate_type=TariffRateType.OFF_PEAK,
                label="Late Evening Off-Peak",
            ),
        ],
    )


def get_default_charging_stations() -> List[ChargingStation]:
    """Returns depot and hub charging infrastructure."""
    return [
        ChargingStation(
            id="CS-DEPOT-DC",
            name="Depot DC Fast Charging Bay",
            location="Depot North Yard",
            total_power_capacity_kw=300.0,
            charging_efficiency=0.92,
            ports=[
                ChargingPort(
                    port_id="P-DC1",
                    connector_type=ConnectorType.CCS2,
                    max_power_kw=150.0,
                    status=ChargingStationStatus.AVAILABLE,
                ),
                ChargingPort(
                    port_id="P-DC2",
                    connector_type=ConnectorType.CCS2,
                    max_power_kw=150.0,
                    status=ChargingStationStatus.AVAILABLE,
                ),
            ],
            base_cost_per_kwh=0.0,
        ),
        ChargingStation(
            id="CS-DEPOT-AC",
            name="Depot Overnight Level 2 Bay",
            location="Depot South Yard",
            total_power_capacity_kw=100.0,
            charging_efficiency=0.90,
            ports=[
                ChargingPort(
                    port_id="P-AC1",
                    connector_type=ConnectorType.TYPE_2,
                    max_power_kw=22.0,
                    status=ChargingStationStatus.AVAILABLE,
                ),
                ChargingPort(
                    port_id="P-AC2",
                    connector_type=ConnectorType.TYPE_2,
                    max_power_kw=22.0,
                    status=ChargingStationStatus.AVAILABLE,
                ),
                ChargingPort(
                    port_id="P-AC3",
                    connector_type=ConnectorType.TYPE_2,
                    max_power_kw=22.0,
                    status=ChargingStationStatus.AVAILABLE,
                ),
                ChargingPort(
                    port_id="P-AC4",
                    connector_type=ConnectorType.TYPE_2,
                    max_power_kw=22.0,
                    status=ChargingStationStatus.AVAILABLE,
                ),
            ],
            base_cost_per_kwh=0.0,
        ),
        ChargingStation(
            id="CS-HUB-FAST",
            name="Metro Logistics Hub High-Power Charger",
            location="Metro Logistics Center",
            total_power_capacity_kw=200.0,
            charging_efficiency=0.93,
            ports=[
                ChargingPort(
                    port_id="P-HUB1",
                    connector_type=ConnectorType.CCS2,
                    max_power_kw=100.0,
                    status=ChargingStationStatus.AVAILABLE,
                ),
                ChargingPort(
                    port_id="P-HUB2",
                    connector_type=ConnectorType.CCS2,
                    max_power_kw=100.0,
                    status=ChargingStationStatus.AVAILABLE,
                ),
            ],
            base_cost_per_kwh=0.02,
        ),
    ]


def get_default_vehicles() -> List[Vehicle]:
    """Returns realistic commercial fleet vehicles."""
    now = datetime.now(timezone.utc)
    return [
        Vehicle(
            id="EV-101",
            name="Rivian EDV-700 Prime",
            make="Rivian",
            model="EDV 700",
            battery_spec=BatterySpecification(
                capacity_kwh=135.0,
                max_charge_power_kw=150.0,
                nominal_voltage_v=400.0,
                degradation_factor=0.98,
                cycle_count=120,
            ),
            battery_state=BatteryState(
                soc=88.0,
                min_soc_limit=15.0,
                max_soc_limit=90.0,
                health_status=BatteryHealthStatus.EXCELLENT,
                temperature_c=22.5,
            ),
            consumption_rate_kwh_per_km=0.28,
            current_status=VehicleStatus.IDLE,
            current_location="Depot North Yard",
            last_updated=now,
        ),
        Vehicle(
            id="EV-102",
            name="Ford E-Transit Cargo",
            make="Ford",
            model="E-Transit 350",
            battery_spec=BatterySpecification(
                capacity_kwh=68.0,
                max_charge_power_kw=115.0,
                nominal_voltage_v=400.0,
                degradation_factor=0.95,
                cycle_count=210,
            ),
            battery_state=BatteryState(
                soc=32.0,  # Low SOC, will require smart charging
                min_soc_limit=15.0,
                max_soc_limit=90.0,
                health_status=BatteryHealthStatus.GOOD,
                temperature_c=24.0,
            ),
            consumption_rate_kwh_per_km=0.31,
            current_status=VehicleStatus.IDLE,
            current_location="Depot South Yard",
            last_updated=now,
        ),
        Vehicle(
            id="EV-103",
            name="BrightDrop Zevo 600 Express",
            make="BrightDrop",
            model="Zevo 600",
            battery_spec=BatterySpecification(
                capacity_kwh=165.0,
                max_charge_power_kw=120.0,
                nominal_voltage_v=400.0,
                degradation_factor=0.96,
                cycle_count=145,
            ),
            battery_state=BatteryState(
                soc=75.0,
                min_soc_limit=15.0,
                max_soc_limit=90.0,
                health_status=BatteryHealthStatus.GOOD,
                temperature_c=21.0,
            ),
            consumption_rate_kwh_per_km=0.34,
            current_status=VehicleStatus.IDLE,
            current_location="Depot North Yard",
            last_updated=now,
        ),
        Vehicle(
            id="EV-104",
            name="Volvo FL Electric Medium Duty",
            make="Volvo",
            model="FL Electric 4x2",
            battery_spec=BatterySpecification(
                capacity_kwh=264.0,
                max_charge_power_kw=150.0,
                nominal_voltage_v=600.0,
                degradation_factor=0.94,
                cycle_count=320,
            ),
            battery_state=BatteryState(
                soc=62.0,
                min_soc_limit=20.0,
                max_soc_limit=90.0,
                health_status=BatteryHealthStatus.GOOD,
                temperature_c=26.0,
            ),
            consumption_rate_kwh_per_km=0.88,
            current_status=VehicleStatus.IDLE,
            current_location="Depot Heavy Bay",
            last_updated=now,
        ),
        Vehicle(
            id="EV-105",
            name="Ford E-Transit Express 2",
            make="Ford",
            model="E-Transit 350",
            battery_spec=BatterySpecification(
                capacity_kwh=68.0,
                max_charge_power_kw=115.0,
                nominal_voltage_v=400.0,
                degradation_factor=0.82,  # Degraded battery
                cycle_count=850,
            ),
            battery_state=BatteryState(
                soc=22.0,
                min_soc_limit=15.0,
                max_soc_limit=85.0,
                health_status=BatteryHealthStatus.ATTENTION,
                temperature_c=28.0,
            ),
            consumption_rate_kwh_per_km=0.32,
            current_status=VehicleStatus.IDLE,
            current_location="Depot South Yard",
            last_updated=now,
        ),
        Vehicle(
            id="EV-106",
            name="Rivian EDV-700 Runner",
            make="Rivian",
            model="EDV 700",
            battery_spec=BatterySpecification(
                capacity_kwh=135.0,
                max_charge_power_kw=150.0,
                nominal_voltage_v=400.0,
                degradation_factor=0.99,
                cycle_count=45,
            ),
            battery_state=BatteryState(
                soc=91.0,
                min_soc_limit=15.0,
                max_soc_limit=90.0,
                health_status=BatteryHealthStatus.EXCELLENT,
                temperature_c=20.0,
            ),
            consumption_rate_kwh_per_km=0.27,
            current_status=VehicleStatus.IDLE,
            current_location="Depot North Yard",
            last_updated=now,
        ),
        Vehicle(
            id="EV-107",
            name="BrightDrop Zevo 400 Urban",
            make="BrightDrop",
            model="Zevo 400",
            battery_spec=BatterySpecification(
                capacity_kwh=120.0,
                max_charge_power_kw=120.0,
                nominal_voltage_v=400.0,
                degradation_factor=0.97,
                cycle_count=80,
            ),
            battery_state=BatteryState(
                soc=54.0,
                min_soc_limit=15.0,
                max_soc_limit=90.0,
                health_status=BatteryHealthStatus.EXCELLENT,
                temperature_c=21.5,
            ),
            consumption_rate_kwh_per_km=0.29,
            current_status=VehicleStatus.IDLE,
            current_location="Depot North Yard",
            last_updated=now,
        ),
        Vehicle(
            id="EV-108",
            name="Mercedes eSprinter Service Van",
            make="Mercedes-Benz",
            model="eSprinter L2H2",
            battery_spec=BatterySpecification(
                capacity_kwh=81.0,
                max_charge_power_kw=115.0,
                nominal_voltage_v=400.0,
                degradation_factor=0.91,
                cycle_count=420,
            ),
            battery_state=BatteryState(
                soc=48.0,
                min_soc_limit=15.0,
                max_soc_limit=90.0,
                health_status=BatteryHealthStatus.GOOD,
                temperature_c=23.0,
            ),
            consumption_rate_kwh_per_km=0.30,
            current_status=VehicleStatus.IDLE,
            current_location="Depot South Yard",
            last_updated=now,
        ),
    ]


def get_default_routes() -> List[Route]:
    """Returns scheduled commercial delivery routes for the operating horizon."""
    base_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return [
        Route(
            id="R-METRO-01",
            name="Downtown Commercial Courier Loop",
            origin="Depot North",
            destination="Financial District",
            distance_km=52.0,
            estimated_duration_minutes=90,
            required_energy_kwh=15.5,
            departure_time=base_time + timedelta(hours=2),
            required_arrival_time=base_time + timedelta(hours=5),
            elevation_gain_m=45.0,
            cargo_weight_kg=600.0,
            priority=2,
        ),
        Route(
            id="R-AIRPORT-02",
            name="International Airport Airfreight Shuttle",
            origin="Depot North",
            destination="Cargo Terminal 4",
            distance_km=98.0,
            estimated_duration_minutes=120,
            required_energy_kwh=31.2,
            departure_time=base_time + timedelta(hours=3),
            required_arrival_time=base_time + timedelta(hours=7),
            elevation_gain_m=120.0,
            cargo_weight_kg=1200.0,
            priority=3,
        ),
        Route(
            id="R-SUBURB-03",
            name="North County Residential Package Drop",
            origin="Depot South",
            destination="North Hills Hub",
            distance_km=76.0,
            estimated_duration_minutes=110,
            required_energy_kwh=24.5,
            departure_time=base_time + timedelta(hours=1),
            required_arrival_time=base_time + timedelta(hours=5),
            elevation_gain_m=180.0,
            cargo_weight_kg=750.0,
            priority=1,
        ),
        Route(
            id="R-REGIONAL-04",
            name="Cross-Valley Distribution Link",
            origin="Depot North",
            destination="East Distribution Center",
            distance_km=185.0,
            estimated_duration_minutes=210,
            required_energy_kwh=62.0,
            departure_time=base_time + timedelta(hours=4),
            required_arrival_time=base_time + timedelta(hours=10),
            elevation_gain_m=310.0,
            cargo_weight_kg=1600.0,
            priority=2,
        ),
        Route(
            id="R-HEAVY-05",
            name="Industrial Pallet Transport",
            origin="Depot Heavy Bay",
            destination="Harbor Logistics Dock",
            distance_km=110.0,
            estimated_duration_minutes=150,
            required_energy_kwh=98.0,  # Requires heavy EV (EV-104)
            departure_time=base_time + timedelta(hours=2),
            required_arrival_time=base_time + timedelta(hours=6),
            elevation_gain_m=60.0,
            cargo_weight_kg=4500.0,
            priority=3,
        ),
        Route(
            id="R-EVENING-06",
            name="Evening Inter-Depot Balancing Transfer",
            origin="Depot South",
            destination="Depot North",
            distance_km=34.0,
            estimated_duration_minutes=45,
            required_energy_kwh=10.2,
            departure_time=base_time + timedelta(hours=8),
            required_arrival_time=base_time + timedelta(hours=11),
            elevation_gain_m=20.0,
            cargo_weight_kg=400.0,
            priority=1,
        ),
    ]
