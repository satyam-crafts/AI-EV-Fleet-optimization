"""Fleet Service and In-Memory Data Repository.

Encapsulates data access and coordinates operations between domain models,
the deterministic optimizer, explainability generator, and agent orchestrator.
"""

from typing import Dict, List, Optional
from backend.app.domain.vehicle import Vehicle, VehicleStatus
from backend.app.domain.route import Route
from backend.app.domain.charging import ChargingStation
from backend.app.domain.energy_price import EnergyPriceSchedule
from backend.app.domain.optimization.models import OptimizationRequest, OptimizationResult
from backend.app.domain.recommendation import Recommendation
from backend.app.agents.orchestrator import FleetAgentOrchestrator, AgentQueryResponse
from backend.app.data.sample_data import (
    get_default_vehicles,
    get_default_routes,
    get_default_charging_stations,
    get_default_price_schedule,
)


class FleetService:
    """Singleton service maintaining fleet state, historical runs, and query orchestration."""

    def __init__(self):
        self.vehicles: Dict[str, Vehicle] = {}
        self.routes: Dict[str, Route] = {}
        self.charging_stations: Dict[str, ChargingStation] = {}
        self.price_schedule: EnergyPriceSchedule = get_default_price_schedule()
        self.optimization_history: Dict[str, OptimizationResult] = {}
        self.latest_optimization_id: Optional[str] = None
        self.orchestrator = FleetAgentOrchestrator()

        self.reset_to_demo_data()

    def reset_to_demo_data(self) -> None:
        """Seeds or restores realistic deterministic sample data."""
        self.vehicles = {v.id: v for v in get_default_vehicles()}
        self.routes = {r.id: r for r in get_default_routes()}
        self.charging_stations = {cs.id: cs for cs in get_default_charging_stations()}
        self.price_schedule = get_default_price_schedule()

        # Run an initial default optimization run so dashboard is populated immediately
        default_req = OptimizationRequest(
            planning_horizon_hours=24,
            min_soc_buffer_percent=15.0,
            max_soc_target_percent=90.0,
        )
        self.run_optimization(default_req)

    def get_fleet_kpis(self) -> Dict[str, float]:
        """Calculates executive dashboard KPI metrics."""
        vehicles_list = list(self.vehicles.values())
        routes_list = list(self.routes.values())
        total = len(vehicles_list)
        available = sum(1 for v in vehicles_list if v.current_status == VehicleStatus.IDLE)
        charging = sum(1 for v in vehicles_list if v.current_status == VehicleStatus.CHARGING)
        attention = sum(
            1 for v in vehicles_list
            if v.battery_state.soc <= v.battery_state.min_soc_limit + 5.0
            or v.battery_spec.degradation_factor < 0.85
        )
        avg_soc = sum(v.battery_state.soc for v in vehicles_list) / total if total > 0 else 0.0
        total_energy_demanded = sum(r.required_energy_kwh for r in routes_list)

        latest_opt = self.get_latest_optimization()
        charging_cost = latest_opt.total_charging_cost if latest_opt else 0.0
        cost_savings = latest_opt.baseline_comparison.cost_savings if latest_opt else 0.0
        savings_pct = latest_opt.baseline_comparison.savings_percentage if latest_opt else 0.0

        return {
            "total_vehicles": total,
            "available_vehicles": available,
            "charging_vehicles": charging,
            "attention_required_count": attention,
            "average_soc_percent": round(avg_soc, 1),
            "fleet_energy_demand_kwh": round(total_energy_demanded, 1),
            "estimated_charging_cost": round(charging_cost, 2),
            "cost_savings": round(cost_savings, 2),
            "savings_percentage": round(savings_pct, 1),
        }

    def get_vehicles(self) -> List[Vehicle]:
        return list(self.vehicles.values())

    def get_vehicle(self, vehicle_id: str) -> Optional[Vehicle]:
        return self.vehicles.get(vehicle_id)

    def get_routes(self) -> List[Route]:
        return list(self.routes.values())

    def get_route(self, route_id: str) -> Optional[Route]:
        return self.routes.get(route_id)

    def get_charging_stations(self) -> List[ChargingStation]:
        return list(self.charging_stations.values())

    def get_price_schedule(self) -> EnergyPriceSchedule:
        return self.price_schedule

    def run_optimization(self, request: OptimizationRequest) -> OptimizationResult:
        """Executes the deterministic optimizer via orchestrator."""
        result = self.orchestrator.run_optimization_workflow(
            vehicles=list(self.vehicles.values()),
            routes=list(self.routes.values()),
            charging_stations=list(self.charging_stations.values()),
            price_schedule=self.price_schedule,
            request=request,
        )
        self.optimization_history[result.id] = result
        self.latest_optimization_id = result.id
        return result

    def get_optimization(self, optimization_id: str) -> Optional[OptimizationResult]:
        return self.optimization_history.get(optimization_id)

    def get_latest_optimization(self) -> Optional[OptimizationResult]:
        if self.latest_optimization_id:
            return self.optimization_history.get(self.latest_optimization_id)
        return None

    def get_recommendations(self) -> List[Recommendation]:
        latest = self.get_latest_optimization()
        return latest.recommendations if latest else []

    def query_agent(self, query: str) -> AgentQueryResponse:
        """Invokes conversational assistant with verified domain context."""
        latest = self.get_latest_optimization()
        return self.orchestrator.answer_query(
            query=query,
            vehicles=list(self.vehicles.values()),
            routes=list(self.routes.values()),
            price_schedule=self.price_schedule,
            latest_result=latest,
        )


# Global service singleton
fleet_service = FleetService()
