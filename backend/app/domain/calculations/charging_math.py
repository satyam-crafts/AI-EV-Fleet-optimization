"""Charging Duration, Energy, and TOU Cost Calculations.

Deterministic integration of charging physics, power constraints, efficiency losses,
and Time-of-Use electricity tariffs.
"""

import math
from datetime import datetime, timedelta
from typing import Tuple
from backend.app.domain.energy_price import EnergyPriceSchedule, TariffRateType


def calculate_effective_charging_power(
    charger_max_power_kw: float,
    vehicle_max_power_kw: float,
) -> float:
    """Calculates the physical bottleneck power (kW) between charger and vehicle BMS."""
    return min(charger_max_power_kw, vehicle_max_power_kw)


def calculate_charging_duration_minutes(
    energy_needed_kwh: float,
    charger_power_kw: float,
    vehicle_max_power_kw: float,
    efficiency: float = 0.92,
) -> int:
    """Calculates charging duration in minutes required to deliver energy_needed_kwh to battery.

    P_battery = min(P_charger, P_vehicle) * efficiency
    t_hours = energy_needed_kwh / P_battery
    t_minutes = ceil(t_hours * 60)
    """
    if energy_needed_kwh <= 0.0:
        return 0

    effective_power_kw = calculate_effective_charging_power(charger_power_kw, vehicle_max_power_kw)
    battery_input_power_kw = effective_power_kw * efficiency

    if battery_input_power_kw <= 0.0:
        raise ValueError("Effective charging power must be greater than zero")

    duration_hours = energy_needed_kwh / battery_input_power_kw
    return math.ceil(duration_hours * 60.0)


def calculate_soc_after_charging(
    initial_soc: float,
    energy_added_kwh: float,
    battery_capacity_kwh: float,
) -> float:
    """Calculates the battery SOC (%) after receiving energy_added_kwh.

    Guarantees ceiling of 100.0%.
    """
    if battery_capacity_kwh <= 0.0:
        return initial_soc
    delta_soc = (energy_added_kwh / battery_capacity_kwh) * 100.0
    return round(min(100.0, initial_soc + delta_soc), 1)


def calculate_charging_cost(
    start_time: datetime,
    duration_minutes: int,
    charging_power_kw: float,
    efficiency: float,
    price_schedule: EnergyPriceSchedule,
) -> Tuple[float, float, TariffRateType, float]:
    """Calculates total electricity cost and energy by integrating TOU rates over the session.

    Grid energy drawn = (Power_effective * duration_hours)
    Rate integrated minute-by-minute or hourly across window boundaries.

    Returns:
    - total_cost_usd: float
    - total_grid_energy_kwh: float
    - predominant_rate_type: TariffRateType
    - average_cost_per_kwh: float
    """
    if duration_minutes <= 0 or charging_power_kw <= 0:
        return 0.0, 0.0, TariffRateType.OFF_PEAK, 0.0

    total_cost = 0.0
    total_grid_energy = 0.0
    rate_type_counts = {t: 0 for t in TariffRateType}

    # Step in 15-minute segments for fast, accurate TOU integration
    step_minutes = 15
    power_draw_kw = charging_power_kw  # Power drawn from grid
    step_energy_kwh = power_draw_kw * (step_minutes / 60.0)

    current_time = start_time
    remaining_minutes = duration_minutes

    while remaining_minutes > 0:
        chunk = min(remaining_minutes, step_minutes)
        chunk_fraction = chunk / step_minutes
        chunk_energy = step_energy_kwh * chunk_fraction

        rate = price_schedule.get_rate_at_hour(current_time.hour)
        rate_type = price_schedule.get_rate_type_at_hour(current_time.hour)
        rate_type_counts[rate_type] += chunk

        total_cost += chunk_energy * rate
        total_grid_energy += chunk_energy

        current_time += timedelta(minutes=chunk)
        remaining_minutes -= chunk

    predominant_rate_type = max(rate_type_counts, key=rate_type_counts.get)
    avg_rate = total_cost / total_grid_energy if total_grid_energy > 0 else 0.0

    return round(total_cost, 2), round(total_grid_energy, 2), predominant_rate_type, round(avg_rate, 4)


def calculate_unmanaged_baseline_cost(
    energy_needed_kwh: float,
    arrival_time: datetime,
    charger_power_kw: float,
    vehicle_max_power_kw: float,
    efficiency: float,
    price_schedule: EnergyPriceSchedule,
) -> Tuple[float, float]:
    """Calculates unmanaged immediate charging cost upon arrival at depot.

    Simulates the common operational baseline where drivers plug in immediately upon shift
    end (often 16:00 - 18:00 on-peak window) rather than shifting to off-peak night hours.

    Returns:
    - baseline_cost_usd: float
    - baseline_duration_minutes: int
    """
    duration_min = calculate_charging_duration_minutes(
        energy_needed_kwh=energy_needed_kwh,
        charger_power_kw=charger_power_kw,
        vehicle_max_power_kw=vehicle_max_power_kw,
        efficiency=efficiency,
    )
    effective_power = calculate_effective_charging_power(charger_power_kw, vehicle_max_power_kw)
    cost, _, _, _ = calculate_charging_cost(
        start_time=arrival_time,
        duration_minutes=duration_min,
        charging_power_kw=effective_power,
        efficiency=efficiency,
        price_schedule=price_schedule,
    )
    return cost, duration_min
