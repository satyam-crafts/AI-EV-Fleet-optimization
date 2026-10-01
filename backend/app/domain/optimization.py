"""Optimization Domain Models.

Defines optimization requests, vehicle-to-route assignments, charging schedules,
constraint violations, warnings, baseline comparisons, and optimization results.
"""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.domain.energy_price import TariffRateType
from backend.app.domain.recommendation import Recommendation


class OptimizationObjectiveWeights(BaseModel):
    """Configurable weights for multi-objective optimization."""
    cost_weight: float = Field(default=0.5, ge=0.0, le=1.0, description="Priority on electricity cost minimization")
    battery_health_weight: float = Field(default=0.3, ge=0.0, le=1.0, description="Priority on avoiding deep discharge/stress")
    schedule_slack_weight: float = Field(default=0.2, ge=0.0, le=1.0, description="Priority on buffer time before departure")


class OptimizationRequest(BaseModel):
    """Input payload to trigger fleet optimization."""
    planning_horizon_hours: int = Field(default=24, ge=1, le=72, description="Lookahead horizon in hours")
    vehicle_ids: Optional[List[str]] = Field(default=None, description="Subset of vehicle IDs (None = all available)")
    route_ids: Optional[List[str]] = Field(default=None, description="Subset of route IDs (None = all unassigned)")
    charging_station_ids: Optional[List[str]] = Field(default=None, description="Subset of stations to utilize")
    weights: OptimizationObjectiveWeights = Field(default_factory=OptimizationObjectiveWeights)
    min_soc_buffer_percent: float = Field(default=15.0, ge=5.0, le=40.0, description="Safety SOC reserve percentage")
    max_soc_target_percent: float = Field(default=90.0, ge=60.0, le=100.0, description="Daily charging target ceiling")
    max_depot_power_kw: Optional[float] = Field(default=None, gt=0.0, description="Total depot instantaneous power cap")


class VehicleAssignment(BaseModel):
    """Assignment of a specific vehicle to a scheduled route."""
    vehicle_id: str
    vehicle_name: str
    route_id: str
    route_name: str
    departure_time: datetime
    arrival_time: datetime
    initial_soc: float = Field(..., ge=0.0, le=100.0)
    estimated_final_soc: float = Field(..., ge=0.0, le=100.0)
    energy_required_kwh: float = Field(..., gt=0.0)
    feasible: bool
    infeasibility_reasons: List[str] = Field(default_factory=list)


class ChargingPlan(BaseModel):
    """Optimized charging session schedule for an EV."""
    plan_id: str
    vehicle_id: str
    vehicle_name: str
    station_id: str
    station_name: str
    port_id: str
    start_time: datetime
    end_time: datetime
    start_soc: float = Field(..., ge=0.0, le=100.0)
    target_soc: float = Field(..., ge=0.0, le=100.0)
    energy_to_charge_kwh: float = Field(..., ge=0.0)
    charging_power_kw: float = Field(..., gt=0.0)
    estimated_cost: float = Field(..., ge=0.0)
    tariff_type: TariffRateType = Field(default=TariffRateType.OFF_PEAK)
    average_rate_per_kwh: float = Field(default=0.0, ge=0.0)
    shifted_from_peak: bool = Field(default=False, description="True if charging was shifted away from peak hours")


class ConstraintViolation(BaseModel):
    """Explicitly flagged operational or physical constraint violation."""
    constraint_type: str = Field(..., description="e.g. INSUFFICIENT_SOC, TIME_OVERLAP, POWER_CAP_EXCEEDED")
    vehicle_id: Optional[str] = None
    route_id: Optional[str] = None
    station_id: Optional[str] = None
    description: str
    severity: str = Field(default="ERROR", description="ERROR or WARNING")


class OptimizationWarning(BaseModel):
    """Operational advisory warning from the solver."""
    code: str
    message: str
    entity_id: Optional[str] = None


class BaselineComparison(BaseModel):
    """Calculated cost and energy metrics comparing optimization against unmanaged charging."""
    baseline_charging_cost: float = Field(..., description="Cost if vehicle charged immediately upon arrival at peak rates")
    optimized_charging_cost: float = Field(..., description="Cost under optimized off-peak/smart schedule")
    cost_savings: float = Field(..., description="Direct dollar savings achieved")
    savings_percentage: float = Field(..., description="Percentage cost reduction")
    peak_energy_avoided_kwh: float = Field(default=0.0, description="Energy shifted away from peak hours")
    methodology: str = Field(
        default="Immediate unmanaged charging upon arrival vs TOU-optimized load-shifted charging",
    )


class OptimizationResult(BaseModel):
    """Complete output produced by the deterministic optimization engine."""
    id: str = Field(..., description="Unique optimization result identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = Field(..., description="OPTIMAL, FEASIBLE, PARTIALLY_FEASIBLE, or INFEASIBLE")
    planning_horizon_hours: int
    assignments: List[VehicleAssignment] = Field(default_factory=list)
    charging_plans: List[ChargingPlan] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)
    total_fleet_energy_kwh: float = Field(default=0.0)
    total_charging_cost: float = Field(default=0.0)
    baseline_comparison: BaselineComparison
    constraint_violations: List[ConstraintViolation] = Field(default_factory=list)
    warnings: List[OptimizationWarning] = Field(default_factory=list)
    unassigned_routes: List[str] = Field(default_factory=list)
    execution_time_ms: float = Field(default=0.0)
