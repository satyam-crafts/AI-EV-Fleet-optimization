"""Battery Health and Energy Calculations.

Provides deterministic calculations for usable battery energy, SOC bounds,
and energy deficits required to safely complete assignments.
"""

from backend.app.domain.battery import BatterySpecification, BatteryState
from backend.app.domain.vehicle import Vehicle
from backend.app.domain.route import Route


def calculate_usable_battery_energy(
    battery_spec: BatterySpecification,
    battery_state: BatteryState,
) -> float:
    """Calculates usable energy (kWh) strictly above the vehicle's min_soc_limit.

    E_usable = Capacity_eff * max(0, SOC - min_soc_limit) / 100
    """
    usable_soc = max(0.0, battery_state.soc - battery_state.min_soc_limit)
    return round(battery_spec.effective_capacity_kwh * (usable_soc / 100.0), 2)


def calculate_energy_deficit(
    vehicle: Vehicle,
    required_energy_kwh: float,
    min_soc_buffer_percent: float = 15.0,
) -> float:
    """Calculates additional energy (kWh) required if current battery is insufficient.

    If current usable energy >= required_energy_kwh, deficit is 0.0.
    Otherwise, returns the exact energy shortage in kWh.
    """
    effective_cap = vehicle.battery_spec.effective_capacity_kwh
    buffer_soc = max(vehicle.battery_state.min_soc_limit, min_soc_buffer_percent)
    usable_soc = max(0.0, vehicle.battery_state.soc - buffer_soc)
    usable_energy_kwh = effective_cap * (usable_soc / 100.0)

    if usable_energy_kwh >= required_energy_kwh:
        return 0.0
    return round(required_energy_kwh - usable_energy_kwh, 2)


def calculate_required_departure_soc(
    vehicle: Vehicle,
    required_energy_kwh: float,
    target_arrival_soc: float = 15.0,
) -> float:
    """Calculates target SOC (%) the vehicle must have at departure.

    Ensures the vehicle finishes the route with at least target_arrival_soc %.
    """
    effective_cap = vehicle.battery_spec.effective_capacity_kwh
    needed_delta_soc = (required_energy_kwh / effective_cap) * 100.0
    required_departure_soc = target_arrival_soc + needed_delta_soc
    return round(min(100.0, required_departure_soc), 1)
