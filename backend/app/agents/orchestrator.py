"""Agent Orchestration Layer.

Coordinates deterministic tools, domain telemetry, optimization runs, and natural language
synthesis without allowing LLM hallucinations into safety-critical math.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.domain.vehicle import Vehicle
from backend.app.domain.route import Route
from backend.app.domain.charging import ChargingStation
from backend.app.domain.energy_price import EnergyPriceSchedule
from backend.app.domain.optimization.models import OptimizationRequest, OptimizationResult
from backend.app.agents.tools import (
    tool_fleet_summary,
    tool_route_summary,
    tool_tariff_summary,
    tool_run_optimization,
)
from backend.app.agents.llm_enhancer import LLMEnhancer


class AgentQueryResponse(BaseModel):
    """Structured response from the AI Agent Orchestrator."""
    query: str
    response_text: str
    fleet_summary: Dict[str, Any]
    routes_summary: Dict[str, Any]
    tariff_summary: Dict[str, Any]
    provider_used: str = "deterministic_template"


class FleetAgentOrchestrator:
    """Master orchestrator for fleet energy management and operator interaction."""

    def __init__(self, enhancer: Optional[LLMEnhancer] = None):
        self.enhancer = enhancer or LLMEnhancer()

    def run_optimization_workflow(
        self,
        vehicles: List[Vehicle],
        routes: List[Route],
        charging_stations: List[ChargingStation],
        price_schedule: EnergyPriceSchedule,
        request: OptimizationRequest,
    ) -> OptimizationResult:
        """Coordinates deterministic optimization and generates executive summary."""
        result = tool_run_optimization(
            vehicles=vehicles,
            routes=routes,
            charging_stations=charging_stations,
            price_schedule=price_schedule,
            request=request,
        )
        return result

    def generate_result_summary(self, result: OptimizationResult) -> str:
        """Produces natural language executive briefing for an optimization result."""
        return self.enhancer.generate_executive_summary(result)

    def answer_query(
        self,
        query: str,
        vehicles: List[Vehicle],
        routes: List[Route],
        price_schedule: EnergyPriceSchedule,
        latest_result: Optional[OptimizationResult] = None,
    ) -> AgentQueryResponse:
        """Processes conversational operator query grounded strictly in domain facts."""
        fleet_sum = tool_fleet_summary(vehicles)
        routes_sum = tool_route_summary(routes)
        tariff_sum = tool_tariff_summary(price_schedule)

        context: Dict[str, Any] = {
            "fleet_summary": fleet_sum,
            "routes_summary": routes_sum,
            "tariff_summary": tariff_sum,
        }

        if latest_result:
            context["latest_optimization"] = {
                "status": latest_result.status,
                "assignments": len(latest_result.assignments),
                "savings": f"${latest_result.baseline_comparison.cost_savings:.2f}",
                "savings_pct": f"{latest_result.baseline_comparison.savings_percentage:.1f}%",
                "energy_kwh": latest_result.total_fleet_energy_kwh,
            }

        response_text = self.enhancer.answer_operator_query(query, context)
        provider = (
            f"llm_{self.enhancer.provider}"
            if (self.enhancer.provider == "openai" and self.enhancer.openai_key)
            else "deterministic_template"
        )

        return AgentQueryResponse(
            query=query,
            response_text=response_text,
            fleet_summary=fleet_sum,
            routes_summary=routes_sum,
            tariff_summary=tariff_sum,
            provider_used=provider,
        )
