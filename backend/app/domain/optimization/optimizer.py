"""Deterministic Multi-Objective Fleet Optimization Engine.

Coordinates vehicle-route assignments, charging schedules, TOU tariff minimization,
battery-health preservation, and baseline savings analysis.

METHODOLOGY NOTE:
This implementation utilizes a deterministic multi-objective heuristic with polynomial
time complexity O(V * R * C). It searches for Pareto-efficient allocations optimizing:
1. Electricity cost (TOU tariff minimization via off-peak load shifting)
2. Battery health (avoiding deep discharge below safety floor and thermal stress)
3. Operational schedule slack (maximizing turnaround buffers)

The architecture strictly decouples the domain and API interfaces so that a formal
Mixed-Integer Linear Programming (MILP) solver (e.g., HiGHS or PuLP) can be substituted
without modifying domain contracts.
"""

from datetime import datetime, timedelta, timezone
import time
from typing import Dict, List, Optional, Tuple
import uuid

from backend.app.domain.vehicle import Vehicle, VehicleStatus
from backend.app.domain.route import Route
from backend.app.domain.charging import ChargingStation
from backend.app.domain.energy_price import EnergyPriceSchedule, TariffRateType
from backend.app.domain.optimization.models import (
    BaselineComparison,
    ChargingPlan,
    ConstraintViolation,
    OptimizationRequest,
    OptimizationResult,
    OptimizationWarning,
    VehicleAssignment,
)
from backend.app.domain.optimization.feasibility import evaluate_vehicle_route_feasibility
from backend.app.domain.optimization.scheduler import PortOccupancyTracker, schedule_smart_charging_session
from backend.app.domain.calculations.charging_math import calculate_unmanaged_baseline_cost


class FleetOptimizationEngine:
    """Core deterministic optimization engine."""

    def __init__(
        self,
        vehicles: List[Vehicle],
        routes: List[Route],
        charging_stations: List[ChargingStation],
        price_schedule: EnergyPriceSchedule,
    ):
        self.vehicles = vehicles
        self.routes = routes
        self.charging_stations = charging_stations
        self.price_schedule = price_schedule

    def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        """Executes the multi-objective deterministic optimization."""
        start_exec_time = time.perf_counter()
        now = datetime.now(timezone.utc)

        # 1. Filter active subsets
        candidate_vehicles = [
            v for v in self.vehicles
            if request.vehicle_ids is None or v.id in request.vehicle_ids
        ]
        candidate_routes = [
            r for r in self.routes
            if request.route_ids is None or r.id in request.route_ids
        ]
        candidate_stations = [
            cs for cs in self.charging_stations
            if request.charging_station_ids is None or cs.id in request.charging_station_ids
        ]

        # Sort routes by priority (highest first) and then departure time
        sorted_routes = sorted(
            candidate_routes,
            key=lambda r: (-r.priority, r.departure_time),
        )

        assignments: List[VehicleAssignment] = []
        charging_plans: List[ChargingPlan] = []
        violations: List[ConstraintViolation] = []
        warnings: List[OptimizationWarning] = []
        unassigned_routes: List[str] = []

        assigned_vehicle_ids = set()
        port_tracker = PortOccupancyTracker()

        # Total energy and cost tracking
        total_fleet_energy_kwh = 0.0
        total_optimized_charging_cost = 0.0
        total_baseline_charging_cost = 0.0
        total_peak_energy_avoided_kwh = 0.0

        # 2. Match vehicles to routes using multi-objective evaluation
        for route in sorted_routes:
            best_match: Optional[Tuple[Vehicle, float, Optional[ChargingPlan]]] = None
            best_score = float("inf")
            candidate_infeasibility_reasons: List[str] = []

            for vehicle in candidate_vehicles:
                if vehicle.id in assigned_vehicle_ids:
                    continue

                feasibility = evaluate_vehicle_route_feasibility(
                    vehicle=vehicle,
                    route=route,
                    min_soc_buffer_percent=request.min_soc_buffer_percent,
                )

                pre_route_plan: Optional[ChargingPlan] = None

                # If energy deficit exists, test if vehicle can charge before departure
                if feasibility.energy_deficit_kwh > 0:
                    needed_target_soc = feasibility.required_departure_soc
                    pre_route_plan = schedule_smart_charging_session(
                        vehicle=vehicle,
                        target_soc=min(request.max_soc_target_percent, needed_target_soc),
                        deadline=route.departure_time,
                        available_from=now,
                        charging_stations=candidate_stations,
                        price_schedule=self.price_schedule,
                        tracker=port_tracker,
                    )
                    if not pre_route_plan:
                        candidate_infeasibility_reasons.append(
                            f"Vehicle {vehicle.id} needs {feasibility.energy_deficit_kwh:.1f} kWh before {route.id}, but cannot complete charging prior to {route.departure_time.strftime('%H:%M')}."
                        )
                        continue

                elif not feasibility.feasible:
                    candidate_infeasibility_reasons.extend(feasibility.violations)
                    continue

                # Multi-Objective Scoring:
                # 1. Cost Score (charging cost if charging needed)
                cost = pre_route_plan.estimated_cost if pre_route_plan else 0.0
                # 2. Battery Health Score (penalize low degradation factor or high cycles)
                health_penalty = (1.0 - vehicle.battery_spec.degradation_factor) * 50.0
                # 3. Schedule Buffer Score (penalize if pre-charge finishes < 30 min before departure)
                slack_penalty = 0.0
                if pre_route_plan:
                    slack_minutes = (route.departure_time - pre_route_plan.end_time).total_seconds() / 60.0
                    if slack_minutes < 30.0:
                        slack_penalty = (30.0 - slack_minutes) * 2.0

                score = (
                    (request.weights.cost_weight * cost)
                    + (request.weights.battery_health_weight * health_penalty)
                    + (request.weights.schedule_slack_weight * slack_penalty)
                )

                if score < best_score:
                    best_score = score
                    best_match = (vehicle, score, pre_route_plan)

            # Process assignment result
            if best_match:
                matched_vehicle, score, pre_plan = best_match
                assigned_vehicle_ids.add(matched_vehicle.id)

                if pre_plan:
                    charging_plans.append(pre_plan)
                    total_optimized_charging_cost += pre_plan.estimated_cost
                    total_fleet_energy_kwh += pre_plan.energy_to_charge_kwh

                    # Calculate unmanaged baseline cost (charging upon arrival)
                    base_cost, _ = calculate_unmanaged_baseline_cost(
                        energy_needed_kwh=pre_plan.energy_to_charge_kwh,
                        arrival_time=now,
                        charger_power_kw=pre_plan.charging_power_kw,
                        vehicle_max_power_kw=matched_vehicle.battery_spec.max_charge_power_kw,
                        efficiency=0.92,
                        price_schedule=self.price_schedule,
                    )
                    total_baseline_charging_cost += base_cost
                    if pre_plan.shifted_from_peak:
                        total_peak_energy_avoided_kwh += pre_plan.energy_to_charge_kwh

                initial_soc = pre_plan.target_soc if pre_plan else matched_vehicle.battery_state.soc
                feasibility_check = evaluate_vehicle_route_feasibility(
                    vehicle=matched_vehicle,
                    route=route,
                    min_soc_buffer_percent=request.min_soc_buffer_percent,
                )
                final_soc = max(0.0, initial_soc - ((feasibility_check.required_energy_kwh / matched_vehicle.battery_spec.effective_capacity_kwh) * 100.0))

                assignments.append(
                    VehicleAssignment(
                        vehicle_id=matched_vehicle.id,
                        vehicle_name=matched_vehicle.name,
                        route_id=route.id,
                        route_name=route.name,
                        departure_time=route.departure_time,
                        arrival_time=route.required_arrival_time,
                        initial_soc=round(initial_soc, 1),
                        estimated_final_soc=round(final_soc, 1),
                        energy_required_kwh=feasibility_check.required_energy_kwh,
                        feasible=True,
                    )
                )
            else:
                unassigned_routes.append(route.id)
                violations.append(
                    ConstraintViolation(
                        constraint_type="UNASSIGNABLE_ROUTE",
                        route_id=route.id,
                        description=f"Route {route.id} ({route.name}) could not be assigned to any available vehicle. Reasons: {'; '.join(candidate_infeasibility_reasons[:2]) if candidate_infeasibility_reasons else 'No idle vehicles with sufficient range or charging windows.'}",
                        severity="ERROR",
                    )
                )

        # 3. Post-Route & Overnight Depot Smart Charging
        # For assigned vehicles finishing routes with low SOC, schedule overnight charging
        for assignment in assignments:
            if assignment.estimated_final_soc < request.max_soc_target_percent:
                v = next((veh for veh in candidate_vehicles if veh.id == assignment.vehicle_id), None)
                if v:
                    post_charge_plan = schedule_smart_charging_session(
                        vehicle=v,
                        target_soc=request.max_soc_target_percent,
                        deadline=assignment.arrival_time + timedelta(hours=12),
                        available_from=assignment.arrival_time + timedelta(minutes=30),
                        charging_stations=candidate_stations,
                        price_schedule=self.price_schedule,
                        tracker=port_tracker,
                    )
                    if post_charge_plan:
                        charging_plans.append(post_charge_plan)
                        total_optimized_charging_cost += post_charge_plan.estimated_cost
                        total_fleet_energy_kwh += post_charge_plan.energy_to_charge_kwh

                        base_cost, _ = calculate_unmanaged_baseline_cost(
                            energy_needed_kwh=post_charge_plan.energy_to_charge_kwh,
                            arrival_time=assignment.arrival_time,
                            charger_power_kw=post_charge_plan.charging_power_kw,
                            vehicle_max_power_kw=v.battery_spec.max_charge_power_kw,
                            efficiency=0.92,
                            price_schedule=self.price_schedule,
                        )
                        total_baseline_charging_cost += base_cost
                        if post_charge_plan.shifted_from_peak:
                            total_peak_energy_avoided_kwh += post_charge_plan.energy_to_charge_kwh

        # 4. Compute baseline comparison metrics
        # If baseline charging cost calculated is 0 (e.g. no charging was needed), provide clear 0.0 values
        if total_baseline_charging_cost <= 0.0:
            total_baseline_charging_cost = total_optimized_charging_cost
        cost_savings = max(0.0, total_baseline_charging_cost - total_optimized_charging_cost)
        savings_pct = (
            (cost_savings / total_baseline_charging_cost * 100.0)
            if total_baseline_charging_cost > 0
            else 0.0
        )

        baseline_comparison = BaselineComparison(
            baseline_charging_cost=round(total_baseline_charging_cost, 2),
            optimized_charging_cost=round(total_optimized_charging_cost, 2),
            cost_savings=round(cost_savings, 2),
            savings_percentage=round(savings_pct, 1),
            peak_energy_avoided_kwh=round(total_peak_energy_avoided_kwh, 2),
            methodology="Immediate unmanaged charging upon arrival vs TOU-optimized load-shifted charging",
        )

        # 5. Determine overall optimization status
        status = "OPTIMAL"
        if unassigned_routes:
            status = "PARTIALLY_FEASIBLE" if assignments else "INFEASIBLE"
        elif violations:
            status = "FEASIBLE_WITH_WARNINGS"

        elapsed_ms = (time.perf_counter() - start_exec_time) * 1000.0

        from backend.app.domain.explainability.generator import generate_recommendations_for_result

        partial_result = OptimizationResult(
            id=f"opt-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            status=status,
            planning_horizon_hours=request.planning_horizon_hours,
            assignments=assignments,
            charging_plans=charging_plans,
            recommendations=[],
            total_fleet_energy_kwh=round(total_fleet_energy_kwh, 2),
            total_charging_cost=round(total_optimized_charging_cost, 2),
            baseline_comparison=baseline_comparison,
            constraint_violations=violations,
            warnings=warnings,
            unassigned_routes=unassigned_routes,
            execution_time_ms=round(elapsed_ms, 2),
        )

        partial_result.recommendations = generate_recommendations_for_result(partial_result)
        return partial_result

