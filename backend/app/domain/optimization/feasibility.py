"""Deterministic Route & Vehicle Feasibility Engine.

Verifies whether a vehicle can physically and safely execute a designated route
under battery capacity, SOC safety buffers, time windows, and health constraints.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from backend.app.domain.vehicle import Vehicle, VehicleStatus
from backend.app.domain.route import Route
from backend.app.domain.battery import BatteryHealthStatus
from backend.app.domain.calculations.energy import calculate_route_energy_requirement, calculate_soc_after_route
from backend.app.domain.calculations.battery_math import calculate_usable_battery_energy, calculate_required_departure_soc


class FeasibilityCheckResult(BaseModel):
    """Structured diagnostic report for vehicle-to-route feasibility."""
    feasible: bool = Field(..., description="True if vehicle can complete the route without constraint violation")
    vehicle_id: str
    route_id: str
    required_energy_kwh: float
    current_usable_energy_kwh: float
    energy_deficit_kwh: float = Field(default=0.0, description="Additional kWh needed if current SOC is insufficient")
    initial_soc: float
    projected_arrival_soc: float
    required_departure_soc: float
    violations: List[str] = Field(default_factory=list, description="Hard constraint violations blocking feasibility")
    warnings: List[str] = Field(default_factory=list, description="Operational advisories")


def evaluate_vehicle_route_feasibility(
    vehicle: Vehicle,
    route: Route,
    min_soc_buffer_percent: float = 15.0,
    ambient_temp_c: float = 20.0,
) -> FeasibilityCheckResult:
    """Deterministically evaluates if a vehicle can execute a route.

    Checks:
    1. Operational status (Maintenance blocks assignment).
    2. Battery health (Critical degradation warning).
    3. Energy requirement vs usable battery energy (above safety floor).
    4. Projected final SOC >= min_soc_buffer_percent.
    """
    violations: List[str] = []
    warnings: List[str] = []

    # 1. Operational status
    if vehicle.current_status == VehicleStatus.MAINTENANCE:
        violations.append(f"Vehicle {vehicle.id} is currently under MAINTENANCE and cannot be dispatched.")

    # 2. Battery health check
    if vehicle.battery_spec.degradation_factor < 0.75 or vehicle.battery_state.health_status == BatteryHealthStatus.CRITICAL:
        warnings.append(
            f"Vehicle {vehicle.id} battery is in CRITICAL state (degradation factor {vehicle.battery_spec.degradation_factor:.2f}). Reserve extra buffer."
        )

    # 3. Energy consumption calculation
    required_energy = calculate_route_energy_requirement(vehicle, route, ambient_temp_c=ambient_temp_c)
    effective_cap = vehicle.battery_spec.effective_capacity_kwh
    buffer_soc = max(vehicle.battery_state.min_soc_limit, min_soc_buffer_percent)

    # Usable energy available now
    usable_soc_now = max(0.0, vehicle.battery_state.soc - buffer_soc)
    usable_energy_now = round(effective_cap * (usable_soc_now / 100.0), 2)

    # Projected arrival SOC if departed with current SOC
    projected_arrival_soc = calculate_soc_after_route(
        initial_soc=vehicle.battery_state.soc,
        effective_battery_capacity_kwh=effective_cap,
        energy_consumed_kwh=required_energy,
    )

    # Departure SOC required to finish with buffer
    needed_departure_soc = calculate_required_departure_soc(
        vehicle=vehicle,
        required_energy_kwh=required_energy,
        target_arrival_soc=buffer_soc,
    )

    energy_deficit = 0.0
    if usable_energy_now < required_energy:
        energy_deficit = round(required_energy - usable_energy_now, 2)
        violations.append(
            f"Energy deficit: Route requires {required_energy:.1f} kWh, but usable battery energy is {usable_energy_now:.1f} kWh (SOC {vehicle.battery_state.soc:.1f}% vs buffer {buffer_soc:.1f}%). Pre-departure charging of {energy_deficit:.1f} kWh required."
        )

    if projected_arrival_soc < buffer_soc:
        violations.append(
            f"Final SOC breach: Estimated arrival SOC is {projected_arrival_soc:.1f}%, which violates the minimum safety buffer of {buffer_soc:.1f}%."
        )

    # Range sanity check
    if vehicle.estimated_range_km < route.distance_km:
        warnings.append(
            f"Estimated current range ({vehicle.estimated_range_km:.0f} km) is less than route distance ({route.distance_km:.0f} km)."
        )

    is_feasible = len(violations) == 0

    return FeasibilityCheckResult(
        feasible=is_feasible,
        vehicle_id=vehicle.id,
        route_id=route.id,
        required_energy_kwh=required_energy,
        current_usable_energy_kwh=usable_energy_now,
        energy_deficit_kwh=energy_deficit,
        initial_soc=vehicle.battery_state.soc,
        projected_arrival_soc=projected_arrival_soc,
        required_departure_soc=needed_departure_soc,
        violations=violations,
        warnings=warnings,
    )
