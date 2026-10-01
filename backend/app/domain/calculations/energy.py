"""Deterministic Route Energy Consumption Calculations.

Calculates energy requirements factoring vehicle consumption characteristics,
environmental temperature impacts, payload weight, and elevation profiles.
"""

from backend.app.domain.vehicle import Vehicle
from backend.app.domain.route import Route


def calculate_temperature_impact_factor(ambient_temp_c: float) -> float:
    """Calculates HVAC and thermal management multiplier on battery consumption.

    Optimal temperature is ~20°C (factor = 1.0).
    Extreme cold (< 0°C) increases consumption by up to 25-35%.
    Extreme heat (> 35°C) increases consumption by 15-20% due to cabin/battery cooling.
    """
    if 18.0 <= ambient_temp_c <= 24.0:
        return 1.0
    elif ambient_temp_c < 18.0:
        # Increase ~1.2% per degree below 18C, capped at +35%
        temp_deficit = 18.0 - ambient_temp_c
        return round(min(1.35, 1.0 + (temp_deficit * 0.012)), 3)
    else:
        # Increase ~1.0% per degree above 24C, capped at +20%
        temp_excess = ambient_temp_c - 24.0
        return round(min(1.20, 1.0 + (temp_excess * 0.010)), 3)


def calculate_route_energy_requirement(
    vehicle: Vehicle,
    route: Route,
    ambient_temp_c: float = 20.0,
) -> float:
    """Calculates the deterministic total energy requirement (kWh) for a vehicle on a route.

    Factors:
    - Base distance * vehicle nominal consumption rate
    - Payload contribution (approx. +1.5% consumption per 500kg over nominal)
    - Elevation climb (potential energy minus 65% regenerative braking recapture on descent)
    - Ambient temperature HVAC impact
    """
    base_energy_kwh = route.distance_km * vehicle.consumption_rate_kwh_per_km

    # Payload factor: nominal baseline assumed 500kg
    cargo_diff_kg = max(0.0, route.cargo_weight_kg - 500.0)
    payload_multiplier = 1.0 + ((cargo_diff_kg / 500.0) * 0.015)

    # Elevation factor: Delta E_potential = m * g * h (factoring 65% regen recovery)
    # 1000m climb for ~3000kg gross weight ~= 8.17 kWh, net with regen ~= 5.3 kWh
    elevation_energy_kwh = 0.0
    if route.elevation_gain_m > 0:
        # Simplified physical conversion: ~0.005 kWh per meter climb for commercial EV
        elevation_energy_kwh = route.elevation_gain_m * 0.005

    temp_factor = calculate_temperature_impact_factor(ambient_temp_c)

    total_energy_kwh = (base_energy_kwh * payload_multiplier * temp_factor) + elevation_energy_kwh
    return round(total_energy_kwh, 2)


def calculate_soc_after_route(
    initial_soc: float,
    effective_battery_capacity_kwh: float,
    energy_consumed_kwh: float,
) -> float:
    """Calculates final SOC percentage remaining after completing a route.

    Returns the resulting SOC, bounded between 0.0% and 100.0%.
    """
    if effective_battery_capacity_kwh <= 0.0:
        return 0.0
    delta_soc = (energy_consumed_kwh / effective_battery_capacity_kwh) * 100.0
    final_soc = initial_soc - delta_soc
    return round(max(0.0, min(100.0, final_soc)), 1)
