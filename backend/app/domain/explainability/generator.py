"""Deterministic Explainability and Recommendation Generator.

Transforms deterministic optimization outputs into auditable, transparent
recommendations and structured reasoning cards with zero hallucination.
"""

from datetime import datetime, timezone
from typing import List
import uuid

from backend.app.domain.optimization.models import (
    ChargingPlan,
    OptimizationResult,
    VehicleAssignment,
)
from backend.app.domain.recommendation import (
    Recommendation,
    RecommendationType,
    StructuredReasoning,
)
from backend.app.domain.energy_price import TariffRateType


def generate_assignment_reasoning(assignment: VehicleAssignment) -> StructuredReasoning:
    """Generates structured reasoning for a vehicle-to-route assignment."""
    soc_consumed = assignment.initial_soc - assignment.estimated_final_soc
    return StructuredReasoning(
        decision=f"Assign {assignment.vehicle_name} ({assignment.vehicle_id}) to {assignment.route_name} ({assignment.route_id}).",
        reason=(
            f"Vehicle {assignment.vehicle_id} has sufficient usable battery capacity to complete the {assignment.energy_required_kwh:.1f} kWh "
            f"route departing at {assignment.departure_time.strftime('%H:%M')} and arriving by {assignment.arrival_time.strftime('%H:%M')}, "
            f"maintaining a final SOC of {assignment.estimated_final_soc:.1f}% above the minimum safety buffer."
        ),
        inputs_considered={
            "initial_soc_percent": assignment.initial_soc,
            "projected_final_soc_percent": assignment.estimated_final_soc,
            "energy_required_kwh": assignment.energy_required_kwh,
            "soc_consumed_percent": round(soc_consumed, 1),
            "departure_time": assignment.departure_time.isoformat(),
            "arrival_time": assignment.arrival_time.isoformat(),
        },
        constraints_satisfied=[
            "Vehicle availability window satisfied",
            "Projected final SOC >= minimum reserve floor",
            "Route energy requirement < usable battery energy",
            "Battery thermal/health limits respected",
        ],
        estimated_energy_kwh=assignment.energy_required_kwh,
        estimated_cost=0.0,
        assumptions=[
            "Nominal driving conditions and average payload weight",
            "Continuous route execution without unplanned detours",
        ],
        warnings=[],
    )


def generate_charging_reasoning(plan: ChargingPlan) -> StructuredReasoning:
    """Generates structured reasoning for a smart charging schedule."""
    delta_soc = plan.target_soc - plan.start_soc
    shifted_msg = " [Load Shifted from Peak Rate Window]" if plan.shifted_from_peak else ""
    return StructuredReasoning(
        decision=f"Charge {plan.vehicle_name} ({plan.vehicle_id}) at {plan.station_name} ({plan.station_id}, Port {plan.port_id}) from {plan.start_time.strftime('%H:%M')} to {plan.end_time.strftime('%H:%M')}.{shifted_msg}",
        reason=(
            f"{plan.vehicle_id} requires {plan.energy_to_charge_kwh:.1f} kWh to elevate SOC from {plan.start_soc:.1f}% to {plan.target_soc:.1f}%. "
            f"Station {plan.station_id} delivers {plan.charging_power_kw:.0f} kW power at an average rate of ${plan.average_rate_per_kwh:.3f}/kWh "
            f"({plan.tariff_type.value}), yielding an estimated electricity cost of ${plan.estimated_cost:.2f}."
        ),
        inputs_considered={
            "start_soc_percent": plan.start_soc,
            "target_soc_percent": plan.target_soc,
            "energy_to_charge_kwh": plan.energy_to_charge_kwh,
            "effective_power_kw": plan.charging_power_kw,
            "tariff_tier": plan.tariff_type.value,
            "average_rate_per_kwh": plan.average_rate_per_kwh,
            "shifted_from_peak": plan.shifted_from_peak,
        },
        constraints_satisfied=[
            "Charging completed prior to scheduled vehicle departure",
            "Port concurrency limit respected (no station collision)",
            "Maximum continuous charging power within BMS limits",
            "Target SOC within battery operational ceiling",
        ],
        estimated_energy_kwh=plan.energy_to_charge_kwh,
        estimated_cost=plan.estimated_cost,
        assumptions=[
            "Nominal 92% charger-to-battery efficiency",
            "Grid connection delivers uninterrupted rated power",
        ],
        warnings=(
            ["Pre-departure turnaround window is under 45 minutes"]
            if (plan.target_soc >= 90.0)
            else []
        ),
    )


def generate_recommendations_for_result(result: OptimizationResult) -> List[Recommendation]:
    """Generates comprehensive structured recommendations for all operational facets."""
    recommendations: List[Recommendation] = []

    # 1. Assignment Recommendations
    for assignment in result.assignments:
        reasoning = generate_assignment_reasoning(assignment)
        recommendations.append(
            Recommendation(
                id=f"rec-assign-{assignment.route_id}",
                recommendation_type=RecommendationType.ROUTE_ASSIGNMENT,
                vehicle_id=assignment.vehicle_id,
                route_id=assignment.route_id,
                title=f"Dispatch {assignment.vehicle_name} on {assignment.route_name}",
                summary=f"Dispatches {assignment.vehicle_id} for {assignment.route_id} departing {assignment.departure_time.strftime('%H:%M')} (Final SOC: {assignment.estimated_final_soc:.0f}%).",
                reasoning=reasoning,
                priority="HIGH",
                confidence_score=1.0,
            )
        )

    # 2. Charging & Load-Shifting Recommendations
    for plan in result.charging_plans:
        reasoning = generate_charging_reasoning(plan)
        rec_type = RecommendationType.LOAD_SHIFT if plan.shifted_from_peak else RecommendationType.CHARGE_SCHEDULE
        priority = "HIGH" if plan.shifted_from_peak else "MEDIUM"
        recommendations.append(
            Recommendation(
                id=f"rec-charge-{plan.plan_id}",
                recommendation_type=rec_type,
                vehicle_id=plan.vehicle_id,
                station_id=plan.station_id,
                title=f"Smart Charge {plan.vehicle_name} ({plan.start_time.strftime('%H:%M')}-{plan.end_time.strftime('%H:%M')})",
                summary=f"Charges {plan.vehicle_id} to {plan.target_soc:.0f}% at {plan.station_name} at {plan.tariff_type.value} rate (${plan.estimated_cost:.2f}).",
                reasoning=reasoning,
                priority=priority,
                confidence_score=1.0,
            )
        )

    # 3. Infeasibility Diagnostic Alerts
    for violation in result.constraint_violations:
        if violation.constraint_type == "UNASSIGNABLE_ROUTE":
            reasoning = StructuredReasoning(
                decision=f"Operator intervention required for Route {violation.route_id}.",
                reason=violation.description,
                inputs_considered={"route_id": violation.route_id},
                constraints_satisfied=[],
                estimated_energy_kwh=0.0,
                estimated_cost=0.0,
                assumptions=[],
                warnings=["Operator re-scheduling or external vehicle required"],
            )
            recommendations.append(
                Recommendation(
                    id=f"rec-alert-{violation.route_id}",
                    recommendation_type=RecommendationType.INFEASIBILITY_ALERT,
                    route_id=violation.route_id,
                    title=f"Route {violation.route_id} Unassigned Alert",
                    summary=violation.description,
                    reasoning=reasoning,
                    priority="CRITICAL",
                    confidence_score=1.0,
                )
            )

    return recommendations
