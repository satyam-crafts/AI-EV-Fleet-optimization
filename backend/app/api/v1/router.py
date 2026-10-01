"""Version 1 REST API Endpoints.

Provides strongly typed REST interfaces for Fleet KPIs, Vehicles, Routes,
Charging Infrastructure, TOU Tariffs, Deterministic Optimization, Recommendations,
and AI Agent queries.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.domain.vehicle import Vehicle
from backend.app.domain.route import Route
from backend.app.domain.charging import ChargingStation
from backend.app.domain.energy_price import EnergyPriceSchedule
from backend.app.domain.optimization.models import (
    OptimizationRequest,
    OptimizationResult,
)
from backend.app.domain.recommendation import Recommendation
from backend.app.agents.orchestrator import AgentQueryResponse
from backend.app.services.fleet_service import fleet_service

api_v1_router = APIRouter(prefix="/api/v1", tags=["Fleet Optimization API v1"])


class AgentQueryRequest(BaseModel):
    """Payload for operator conversational query."""
    query: str = Field(..., min_length=1, max_length=500, description="Operator question or prompt")


class RouteFeasibilityResponse(BaseModel):
    """Feasibility preview for a specific route."""
    route: Route
    feasible_vehicle_count: int
    candidate_vehicles: List[Dict[str, Any]]


# Health check
@api_v1_router.get("/health", tags=["Health"], summary="API v1 Health Check")
async def api_v1_health():
    """Versioned API health check."""
    return {"status": "healthy", "api_version": "v1"}


# 1. Fleet Overview & KPIs
@api_v1_router.get("/fleet", summary="Get fleet KPIs and summary overview")
async def get_fleet_overview():
    """Returns high-level operational KPIs for the entire fleet."""
    kpis = fleet_service.get_fleet_kpis()
    return {
        "status": "success",
        "kpis": kpis,
        "vehicles_count": len(fleet_service.get_vehicles()),
        "routes_count": len(fleet_service.get_routes()),
        "stations_count": len(fleet_service.get_charging_stations()),
    }


# 2. Vehicles
@api_v1_router.get("/vehicles", response_model=List[Vehicle], summary="List all fleet vehicles")
async def get_all_vehicles():
    """Returns list of all commercial electric vehicles with battery telemetry."""
    return fleet_service.get_vehicles()


@api_v1_router.get("/vehicles/{vehicle_id}", response_model=Vehicle, summary="Get vehicle by ID")
async def get_vehicle_by_id(vehicle_id: str):
    """Returns detailed vehicle state, battery health, and telemetry."""
    vehicle = fleet_service.get_vehicle(vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle '{vehicle_id}' not found.",
        )
    return vehicle


# 3. Routes
@api_v1_router.get("/routes", response_model=List[Route], summary="List scheduled delivery routes")
async def get_all_routes():
    """Returns all scheduled commercial delivery routes."""
    return fleet_service.get_routes()


@api_v1_router.get("/routes/{route_id}", response_model=Route, summary="Get route by ID")
async def get_route_by_id(route_id: str):
    """Returns route specifications, waypoints, and required energy."""
    route = fleet_service.get_route(route_id)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route '{route_id}' not found.",
        )
    return route


# 4. Charging Stations
@api_v1_router.get(
    "/charging-stations",
    response_model=List[ChargingStation],
    summary="List charging stations and ports",
)
async def get_charging_stations():
    """Returns all depot and hub charging stations with power capacity and port status."""
    return fleet_service.get_charging_stations()


# 5. Energy Prices / TOU Tariffs
@api_v1_router.get(
    "/energy-prices",
    response_model=EnergyPriceSchedule,
    summary="Get 24-hour TOU electricity tariff schedule",
)
async def get_energy_prices():
    """Returns Time-of-Use tariff windows and electricity rates."""
    return fleet_service.get_price_schedule()


# 6. Optimization
@api_v1_router.post(
    "/optimize",
    response_model=OptimizationResult,
    summary="Run deterministic fleet energy & route optimization",
)
async def execute_optimization(request: OptimizationRequest):
    """Runs the multi-objective deterministic optimization engine.

    Assigns vehicles to routes, schedules smart charging sessions around TOU tariffs,
    and generates transparent structured reasoning for every decision.
    """
    result = fleet_service.run_optimization(request)
    return result


@api_v1_router.get(
    "/optimization/latest",
    response_model=OptimizationResult,
    summary="Get the most recent optimization result",
)
async def get_latest_optimization():
    """Returns the most recent optimization run."""
    result = fleet_service.get_latest_optimization()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No optimization has been executed yet.",
        )
    return result


@api_v1_router.get(
    "/optimization/{optimization_id}",
    response_model=OptimizationResult,
    summary="Get optimization run by ID",
)
async def get_optimization_by_id(optimization_id: str):
    """Retrieves a historical optimization run by its unique identifier."""
    result = fleet_service.get_optimization(optimization_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Optimization run '{optimization_id}' not found.",
        )
    return result


# 7. Recommendations
@api_v1_router.get(
    "/recommendations",
    response_model=List[Recommendation],
    summary="Get active structured recommendations",
)
async def get_active_recommendations():
    """Returns explainable recommendations with deterministic justifications."""
    return fleet_service.get_recommendations()


# 8. AI Agent Query
@api_v1_router.post(
    "/agent/query",
    response_model=AgentQueryResponse,
    summary="Query conversational AI assistant grounded in deterministic telemetry",
)
async def query_agent_assistant(request: AgentQueryRequest):
    """Answers operator queries in natural language using verified domain facts."""
    return fleet_service.query_agent(request.query)


# 9. Demo Data Reset
@api_v1_router.post("/demo/reset", summary="Reset system to default demo scenario")
async def reset_demo_scenario():
    """Restores baseline vehicle, route, and charging station seed data."""
    fleet_service.reset_to_demo_data()
    return {"status": "success", "message": "Demo data restored successfully."}
