/**
 * API Service Client for EV Fleet Optimization Platform.
 */

import type {
  AgentQueryResponse,
  ChargingStation,
  EnergyPriceSchedule,
  FleetOverviewResponse,
  OptimizationRequest,
  OptimizationResult,
  Recommendation,
  Route,
  Vehicle,
} from '../types';

const BASE_URL = '/api/v1';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMsg = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      } else if (errorData.message) {
        errorMsg = errorData.message;
      }
    } catch {
      // JSON parse failed; use default errorMsg
    }
    throw new Error(errorMsg);
  }
  return response.json();
}

export const api = {
  // 1. Fleet KPIs and Overview
  async getFleetOverview(): Promise<FleetOverviewResponse> {
    const res = await fetch(`${BASE_URL}/fleet`);
    return handleResponse<FleetOverviewResponse>(res);
  },

  // 2. Vehicles
  async getVehicles(): Promise<Vehicle[]> {
    const res = await fetch(`${BASE_URL}/vehicles`);
    return handleResponse<Vehicle[]>(res);
  },

  async getVehicleById(id: string): Promise<Vehicle> {
    const res = await fetch(`${BASE_URL}/vehicles/${id}`);
    return handleResponse<Vehicle>(res);
  },

  // 3. Routes
  async getRoutes(): Promise<Route[]> {
    const res = await fetch(`${BASE_URL}/routes`);
    return handleResponse<Route[]>(res);
  },

  async getRouteById(id: string): Promise<Route> {
    const res = await fetch(`${BASE_URL}/routes/${id}`);
    return handleResponse<Route>(res);
  },

  // 4. Charging Stations
  async getChargingStations(): Promise<ChargingStation[]> {
    const res = await fetch(`${BASE_URL}/charging-stations`);
    return handleResponse<ChargingStation[]>(res);
  },

  // 5. Energy Prices
  async getEnergyPrices(): Promise<EnergyPriceSchedule> {
    const res = await fetch(`${BASE_URL}/energy-prices`);
    return handleResponse<EnergyPriceSchedule>(res);
  },

  // 6. Optimization
  async runOptimization(request: OptimizationRequest): Promise<OptimizationResult> {
    const res = await fetch(`${BASE_URL}/optimize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<OptimizationResult>(res);
  },

  async getLatestOptimization(): Promise<OptimizationResult> {
    const res = await fetch(`${BASE_URL}/optimization/latest`);
    return handleResponse<OptimizationResult>(res);
  },

  async getOptimizationById(id: string): Promise<OptimizationResult> {
    const res = await fetch(`${BASE_URL}/optimization/${id}`);
    return handleResponse<OptimizationResult>(res);
  },

  // 7. Recommendations
  async getRecommendations(): Promise<Recommendation[]> {
    const res = await fetch(`${BASE_URL}/recommendations`);
    return handleResponse<Recommendation[]>(res);
  },

  // 8. AI Agent Query
  async queryAgent(query: string): Promise<AgentQueryResponse> {
    const res = await fetch(`${BASE_URL}/agent/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });
    return handleResponse<AgentQueryResponse>(res);
  },

  // 9. Demo Reset
  async resetDemo(): Promise<{ status: string; message: string }> {
    const res = await fetch(`${BASE_URL}/demo/reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    return handleResponse<{ status: string; message: string }>(res);
  },
};
