"""Unit tests for the explainability and structured reasoning layer."""

from datetime import datetime, timezone
import pytest

from backend.app.domain.optimization.models import (
    VehicleAssignment,
    ChargingPlan,
    OptimizationResult,
    BaselineComparison,
    ConstraintViolation,
)
from backend.app.domain.energy_price import TariffRateType
from backend.app.domain.recommendation import RecommendationType
from backend.app.domain.explainability.generator import (
    generate_assignment_reasoning,
    generate_charging_reasoning,
    generate_recommendations_for_result,
)


def test_assignment_reasoning_generation():
    """Verify structured reasoning card has decision, reason, inputs, and constraints."""
    now = datetime(2026, 10, 1, 8, 0, tzinfo=timezone.utc)
    assignment = VehicleAssignment(
        vehicle_id="EV-01",
        vehicle_name="Van Alpha",
        route_id="R-01",
        route_name="Downtown Loop",
        departure_time=now,
        arrival_time=now,
        initial_soc=85.0,
        estimated_final_soc=55.0,
        energy_required_kwh=30.0,
        feasible=True,
    )
    reasoning = generate_assignment_reasoning(assignment)

    assert "EV-01" in reasoning.decision
    assert "Downtown Loop" in reasoning.decision
    assert "85.0" in str(reasoning.inputs_considered["initial_soc_percent"])
    assert len(reasoning.constraints_satisfied) >= 3
    assert reasoning.estimated_energy_kwh == 30.0


def test_charging_reasoning_and_load_shift():
    """Verify charging reasoning reflects TOU rates and load shifting flag."""
    now = datetime(2026, 10, 1, 2, 0, tzinfo=timezone.utc)
    plan = ChargingPlan(
        plan_id="p-1",
        vehicle_id="EV-02",
        vehicle_name="Van Beta",
        station_id="CS-01",
        station_name="Depot Fast Bay",
        port_id="P-1",
        start_time=now,
        end_time=now,
        start_soc=30.0,
        target_soc=90.0,
        energy_to_charge_kwh=45.0,
        charging_power_kw=50.0,
        estimated_cost=3.60,
        tariff_type=TariffRateType.OFF_PEAK,
        average_rate_per_kwh=0.08,
        shifted_from_peak=True,
    )
    reasoning = generate_charging_reasoning(plan)

    assert "Load Shifted" in reasoning.decision
    assert "CS-01" in reasoning.decision
    assert reasoning.inputs_considered["shifted_from_peak"] is True
    assert reasoning.estimated_cost == 3.60


def test_full_result_recommendations_generation():
    """Verify all assignments, charging sessions, and violations produce recommendations."""
    now = datetime(2026, 10, 1, 8, 0, tzinfo=timezone.utc)
    assignment = VehicleAssignment(
        vehicle_id="EV-01",
        vehicle_name="Van Alpha",
        route_id="R-01",
        route_name="Loop",
        departure_time=now,
        arrival_time=now,
        initial_soc=80.0,
        estimated_final_soc=50.0,
        energy_required_kwh=25.0,
        feasible=True,
    )
    violation = ConstraintViolation(
        constraint_type="UNASSIGNABLE_ROUTE",
        route_id="R-99",
        description="Distance exceeds range of all vehicles",
    )
    res = OptimizationResult(
        id="opt-test",
        timestamp=now,
        status="PARTIALLY_FEASIBLE",
        planning_horizon_hours=24,
        assignments=[assignment],
        charging_plans=[],
        recommendations=[],
        total_fleet_energy_kwh=25.0,
        total_charging_cost=0.0,
        baseline_comparison=BaselineComparison(
            baseline_charging_cost=0.0,
            optimized_charging_cost=0.0,
            cost_savings=0.0,
            savings_percentage=0.0,
        ),
        constraint_violations=[violation],
        unassigned_routes=["R-99"],
    )

    recs = generate_recommendations_for_result(res)
    assert len(recs) == 2
    types = [r.recommendation_type for r in recs]
    assert RecommendationType.ROUTE_ASSIGNMENT in types
    assert RecommendationType.INFEASIBILITY_ALERT in types
