"""Deterministic Agent Tool Callables.

Provides verifiable factual data extraction tools for the agent orchestrator.
"""

from typing import Any, Dict, List, Optional
from backend.app.domain.vehicle import Vehicle, VehicleStatus
from backend.app.domain.route import Route
from backend.app.domain.charging import ChargingStation
from backend.app.domain.energy_price import EnergyPriceSchedule
from backend.app.domain.optimization.models import OptimizationRequest, OptimizationResult
from backend.app.domain.optimization.optimizer import FleetOptimizationEngine


def tool_fleet_summary(vehicles: List[Vehicle]) -> Dict[str, Any]:
    """Generates deterministic summary metrics across the fleet."""
    total = len(vehicles)
    available = sum(1 for v in vehicles if v.current_status == VehicleStatus.IDLE)
    charging = sum(1 for v in vehicles if v.current_status == VehicleStatus.CHARGING)
    en_route = sum(1 for v in vehicles if v.current_status == VehicleStatus.EN_ROUTE)
    maintenance = sum(1 for v in vehicles if v.current_status == VehicleStatus.MAINTENANCE)

    avg_soc = sum(v.battery_state.soc for v in vehicles) / total if total > 0 else 0.0
    attention_required = sum(
        1 for v in vehicles
        if v.battery_state.soc <= v.battery_state.min_soc_limit + 5.0
        or v.battery_spec.degradation_factor < 0.85
    )

    return {
        "total_vehicles": total,
        "available_vehicles": available,
        "charging_vehicles": charging,
        "en_route_vehicles": en_route,
        "maintenance_vehicles": maintenance,
        "average_soc_percent": round(avg_soc, 1),
        "attention_required_count": attention_required,
    }


def tool_route_summary(routes: List[Route]) -> Dict[str, Any]:
    """Generates deterministic summary metrics across scheduled routes."""
    total_distance = sum(r.distance_km for r in routes)
    total_energy = sum(r.required_energy_kwh for r in routes)
    assigned_count = sum(1 for r in routes if r.assigned_vehicle_id is not None)

    return {
        "total_routes": len(routes),
        "assigned_routes": assigned_count,
        "unassigned_routes": len(routes) - assigned_count,
        "total_distance_km": round(total_distance, 1),
        "total_energy_demanded_kwh": round(total_energy, 1),
    }


def tool_tariff_summary(price_schedule: EnergyPriceSchedule) -> Dict[str, Any]:
    """Generates tariff summary and lowest off-peak charging window information."""
    return {
        "schedule_name": price_schedule.name,
        "currency": price_schedule.currency,
        "off_peak_rate": price_schedule.off_peak_rate,
        "peak_rate": price_schedule.peak_rate,
        "rate_ratio_peak_to_offpeak": round(price_schedule.peak_rate / price_schedule.off_peak_rate, 2),
        "windows_count": len(price_schedule.windows),
    }


def tool_run_optimization(
    vehicles: List[Vehicle],
    routes: List[Route],
    charging_stations: List[ChargingStation],
    price_schedule: EnergyPriceSchedule,
    request: OptimizationRequest,
) -> OptimizationResult:
    """Executes the deterministic fleet optimization engine."""
    engine = FleetOptimizationEngine(
        vehicles=vehicles,
        routes=routes,
        charging_stations=charging_stations,
        price_schedule=price_schedule,
    )
    return engine.optimize(request)
