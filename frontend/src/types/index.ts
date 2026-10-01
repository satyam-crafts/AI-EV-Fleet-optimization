/**
 * TypeScript Domain Interfaces for EV Fleet Optimization Platform.
 */

export type VehicleStatus = 'IDLE' | 'EN_ROUTE' | 'CHARGING' | 'MAINTENANCE';

export type BatteryHealthStatus = 'EXCELLENT' | 'GOOD' | 'ATTENTION' | 'CRITICAL';

export type ConnectorType = 'CCS2' | 'TYPE_2' | 'CHADEMO' | 'TESLA_NACS';

export type ChargingStationStatus = 'AVAILABLE' | 'OCCUPIED' | 'MAINTENANCE' | 'OFFLINE';

export type TariffRateType = 'OFF_PEAK' | 'MID_PEAK' | 'ON_PEAK' | 'CRITICAL_PEAK';

export type RecommendationType =
  | 'CHARGE_SCHEDULE'
  | 'ROUTE_ASSIGNMENT'
  | 'LOAD_SHIFT'
  | 'BATTERY_HEALTH_ACTION'
  | 'INFEASIBILITY_ALERT';

export interface BatterySpecification {
  capacity_kwh: number;
  max_charge_power_kw: number;
  max_discharge_power_kw?: number;
  nominal_voltage_v?: number;
  chemistry?: string;
  degradation_factor: number;
  cycle_count: number;
}

export interface BatteryState {
  soc: number;
  min_soc_limit: number;
  max_soc_limit: number;
  health_status: BatteryHealthStatus;
  temperature_c: number;
}

export interface Vehicle {
  id: string;
  name: string;
  make: string;
  model: string;
  battery_spec: BatterySpecification;
  battery_state: BatteryState;
  consumption_rate_kwh_per_km: number;
  current_status: VehicleStatus;
  current_location: string;
  assigned_route_id?: string | null;
  charging_station_id?: string | null;
  last_updated?: string;
}

export interface RouteWaypoint {
  name: string;
  lat?: number | null;
  lng?: number | null;
  stop_duration_minutes: number;
}

export interface Route {
  id: string;
  name: string;
  origin: string;
  destination: string;
  distance_km: number;
  estimated_duration_minutes: number;
  required_energy_kwh: number;
  departure_time: string;
  required_arrival_time: string;
  elevation_gain_m?: number;
  cargo_weight_kg?: number;
  assigned_vehicle_id?: string | null;
  priority: number;
  waypoints?: RouteWaypoint[];
}

export interface ChargingPort {
  port_id: string;
  connector_type: ConnectorType;
  max_power_kw: number;
  status: ChargingStationStatus;
  current_vehicle_id?: string | null;
}

export interface ChargingStation {
  id: string;
  name: string;
  location: string;
  total_power_capacity_kw: number;
  charging_efficiency: number;
  ports: ChargingPort[];
  base_cost_per_kwh: number;
}

export interface TimeOfUseWindow {
  start_hour: number;
  end_hour: number;
  rate_per_kwh: number;
  rate_type: TariffRateType;
  label: string;
}

export interface EnergyPriceSchedule {
  schedule_id: string;
  name: string;
  currency: string;
  windows: TimeOfUseWindow[];
}

export interface VehicleAssignment {
  vehicle_id: string;
  vehicle_name: string;
  route_id: string;
  route_name: string;
  departure_time: string;
  arrival_time: string;
  initial_soc: number;
  estimated_final_soc: number;
  energy_required_kwh: number;
  feasible: boolean;
  infeasibility_reasons?: string[];
}

export interface ChargingPlan {
  plan_id: string;
  vehicle_id: string;
  vehicle_name: string;
  station_id: string;
  station_name: string;
  port_id: string;
  start_time: string;
  end_time: string;
  start_soc: number;
  target_soc: number;
  energy_to_charge_kwh: number;
  charging_power_kw: number;
  estimated_cost: number;
  tariff_type: TariffRateType;
  average_rate_per_kwh: number;
  shifted_from_peak: boolean;
}

export interface StructuredReasoning {
  decision: string;
  reason: string;
  inputs_considered: Record<string, any>;
  constraints_satisfied: string[];
  estimated_energy_kwh: number;
  estimated_cost: number;
  assumptions: string[];
  warnings: string[];
}

export interface Recommendation {
  id: string;
  recommendation_type: RecommendationType;
  vehicle_id?: string | null;
  route_id?: string | null;
  station_id?: string | null;
  title: string;
  summary: string;
  reasoning: StructuredReasoning;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence_score: number;
  created_at?: string;
}

export interface ConstraintViolation {
  constraint_type: string;
  vehicle_id?: string | null;
  route_id?: string | null;
  station_id?: string | null;
  description: string;
  severity: 'ERROR' | 'WARNING';
}

export interface OptimizationWarning {
  code: string;
  message: string;
  entity_id?: string | null;
}

export interface BaselineComparison {
  baseline_charging_cost: number;
  optimized_charging_cost: number;
  cost_savings: number;
  savings_percentage: number;
  peak_energy_avoided_kwh: number;
  methodology: string;
}

export interface OptimizationResult {
  id: string;
  timestamp: string;
  status: string;
  planning_horizon_hours: number;
  assignments: VehicleAssignment[];
  charging_plans: ChargingPlan[];
  recommendations: Recommendation[];
  total_fleet_energy_kwh: number;
  total_charging_cost: number;
  baseline_comparison: BaselineComparison;
  constraint_violations: ConstraintViolation[];
  warnings: OptimizationWarning[];
  unassigned_routes: string[];
  execution_time_ms: number;
}

export interface OptimizationRequest {
  planning_horizon_hours?: number;
  vehicle_ids?: string[] | null;
  route_ids?: string[] | null;
  charging_station_ids?: string[] | null;
  weights?: {
    cost_weight: number;
    battery_health_weight: number;
    schedule_slack_weight: number;
  };
  min_soc_buffer_percent?: number;
  max_soc_target_percent?: number;
  max_depot_power_kw?: number | null;
}

export interface FleetKPIs {
  total_vehicles: number;
  available_vehicles: number;
  charging_vehicles: number;
  attention_required_count: number;
  average_soc_percent: number;
  fleet_energy_demand_kwh: number;
  estimated_charging_cost: number;
  cost_savings: number;
  savings_percentage: number;
}

export interface FleetOverviewResponse {
  status: string;
  kpis: FleetKPIs;
  vehicles_count: number;
  routes_count: number;
  stations_count: number;
}

export interface AgentQueryResponse {
  query: string;
  response_text: string;
  fleet_summary: Record<string, any>;
  routes_summary: Record<string, any>;
  tariff_summary: Record<string, any>;
  provider_used: string;
}
