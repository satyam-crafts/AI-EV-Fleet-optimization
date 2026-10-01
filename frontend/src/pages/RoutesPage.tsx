import React, { useState } from 'react';
import {
  MapPin,
  Clock,
  Zap,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  Truck,
  TrendingUp,
  X,
} from 'lucide-react';
import { Route, VehicleAssignment, OptimizationResult } from '../types';

interface RoutesPageProps {
  routes: Route[];
  latestOptimization: OptimizationResult | null;
  onNavigateToOptimization: () => void;
}

export const RoutesPage: React.FC<RoutesPageProps> = ({
  routes,
  latestOptimization,
  onNavigateToOptimization,
}) => {
  const [selectedRoute, setSelectedRoute] = useState<Route | null>(null);

  // Map assignments from latest optimization
  const assignmentMap = new Map<string, VehicleAssignment>();
  if (latestOptimization) {
    for (const a of latestOptimization.assignments) {
      assignmentMap.set(a.route_id, a);
    }
  }

  // Find violations for route
  const getViolationForRoute = (routeId: string) => {
    return latestOptimization?.constraint_violations.find(
      (v) => v.route_id === routeId
    );
  };

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-sm flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-white tracking-tight">Scheduled Commercial Delivery Routes</h3>
          <p className="text-xs text-slate-400">
            Validated against vehicle battery capacity, min SOC buffer, and departure windows
          </p>
        </div>
        <button
          onClick={onNavigateToOptimization}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-colors"
        >
          <span>Run Route Dispatch</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Routes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {routes.map((route) => {
          const assignment = assignmentMap.get(route.id);
          const violation = getViolationForRoute(route.id);
          const isAssigned = !!assignment;
          const isFeasible = assignment ? assignment.feasible : !violation;

          return (
            <div
              key={route.id}
              onClick={() => setSelectedRoute(route)}
              className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 hover:border-slate-700 cursor-pointer transition-all shadow-sm flex flex-col justify-between"
            >
              <div>
                {/* Header Row */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                      {route.id}
                    </span>
                    <span
                      className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full border ${
                        route.priority === 3
                          ? 'border-rose-500/30 bg-rose-500/10 text-rose-300'
                          : route.priority === 2
                          ? 'border-amber-500/30 bg-amber-500/10 text-amber-300'
                          : 'border-slate-700 bg-slate-800 text-slate-300'
                      }`}
                    >
                      P{route.priority} Priority
                    </span>
                  </div>

                  {/* Feasibility Indicator */}
                  {isAssigned && isFeasible ? (
                    <span className="inline-flex items-center space-x-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>Feasible</span>
                    </span>
                  ) : violation ? (
                    <span className="inline-flex items-center space-x-1 text-[11px] font-semibold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded-full">
                      <AlertTriangle className="w-3 h-3" />
                      <span>Infeasible</span>
                    </span>
                  ) : (
                    <span className="text-[11px] font-semibold text-slate-400 bg-slate-800 px-2 py-0.5 rounded-full">
                      Pending Dispatch
                    </span>
                  )}
                </div>

                {/* Route Name & Path */}
                <h4 className="text-sm font-bold text-white tracking-tight mb-2">
                  {route.name}
                </h4>

                <div className="rounded-xl bg-slate-950/60 border border-slate-800/80 p-3 space-y-1.5 text-xs text-slate-300">
                  <div className="flex items-center space-x-2">
                    <MapPin className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span className="text-slate-400">From:</span>
                    <span className="font-medium text-white">{route.origin}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <MapPin className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                    <span className="text-slate-400">To:</span>
                    <span className="font-medium text-white">{route.destination}</span>
                  </div>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-slate-800/60 text-xs">
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase">Distance</span>
                    <div className="font-bold text-white font-mono">{route.distance_km} km</div>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase">Duration</span>
                    <div className="font-bold text-white font-mono">{route.estimated_duration_minutes} min</div>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase">Req Energy</span>
                    <div className="font-bold text-amber-400 font-mono">{route.required_energy_kwh} kWh</div>
                  </div>
                </div>
              </div>

              {/* Assignment Footer */}
              <div className="mt-4 pt-3 border-t border-slate-800/60">
                {assignment ? (
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-2">
                      <Truck className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="font-bold text-white">{assignment.vehicle_id}</span>
                      <span className="text-slate-400 text-[11px]">({assignment.vehicle_name})</span>
                    </div>
                    <span className="text-xs font-mono text-emerald-400">
                      End SOC: {assignment.estimated_final_soc}%
                    </span>
                  </div>
                ) : violation ? (
                  <div className="text-[11px] text-rose-300 leading-tight">
                    {violation.description}
                  </div>
                ) : (
                  <div className="text-xs text-slate-400 italic">
                    Not assigned to any vehicle
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Route Detail & Feasibility Diagnostic Modal */}
      {selectedRoute && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-xl overflow-hidden shadow-2xl">
            <div className="p-6 border-b border-slate-800 flex items-start justify-between">
              <div>
                <span className="text-xs font-mono font-bold text-emerald-400">{selectedRoute.id}</span>
                <h3 className="text-lg font-bold text-white tracking-tight">{selectedRoute.name}</h3>
                <p className="text-xs text-slate-400">{selectedRoute.origin} → {selectedRoute.destination}</p>
              </div>
              <button
                onClick={() => setSelectedRoute(null)}
                className="rounded-xl p-2 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto text-xs">
              <div className="grid grid-cols-2 gap-3 bg-slate-950/60 p-4 rounded-2xl border border-slate-800">
                <div>
                  <span className="text-slate-400">Scheduled Departure:</span>
                  <div className="font-bold text-white font-mono text-sm mt-0.5">
                    {new Date(selectedRoute.departure_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
                <div>
                  <span className="text-slate-400">Required Arrival Deadline:</span>
                  <div className="font-bold text-white font-mono text-sm mt-0.5">
                    {new Date(selectedRoute.required_arrival_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>

              {/* Physical specifications */}
              <div className="space-y-2">
                <h5 className="font-semibold text-slate-300 uppercase tracking-wider text-[10px]">Physical Parameters</h5>
                <div className="grid grid-cols-3 gap-2 bg-slate-950/40 p-3 rounded-xl border border-slate-800/60 font-mono">
                  <div>
                    <span className="text-slate-400">Distance:</span> {selectedRoute.distance_km} km
                  </div>
                  <div>
                    <span className="text-slate-400">Elevation:</span> +{selectedRoute.elevation_gain_m || 0} m
                  </div>
                  <div>
                    <span className="text-slate-400">Cargo:</span> {selectedRoute.cargo_weight_kg || 0} kg
                  </div>
                </div>
              </div>

              {/* Assignment Diagnosis */}
              {assignmentMap.get(selectedRoute.id) ? (
                <div className="rounded-2xl border border-emerald-500/20 bg-emerald-950/20 p-4 space-y-2">
                  <div className="flex items-center gap-1.5 font-bold text-emerald-400 text-sm">
                    <CheckCircle2 className="w-4 h-4" />
                    Feasible Vehicle Assignment
                  </div>
                  <p className="text-slate-300">
                    Vehicle <strong>{assignmentMap.get(selectedRoute.id)?.vehicle_id}</strong> is assigned and verified to complete this route.
                  </p>
                  <div className="grid grid-cols-2 gap-2 text-slate-300 pt-1 font-mono">
                    <div>Departure SOC: {assignmentMap.get(selectedRoute.id)?.initial_soc}%</div>
                    <div>Projected Arrival SOC: {assignmentMap.get(selectedRoute.id)?.estimated_final_soc}%</div>
                  </div>
                </div>
              ) : getViolationForRoute(selectedRoute.id) ? (
                <div className="rounded-2xl border border-rose-500/30 bg-rose-950/20 p-4 space-y-2">
                  <div className="flex items-center gap-1.5 font-bold text-rose-400 text-sm">
                    <AlertTriangle className="w-4 h-4" />
                    Feasibility Constraint Breach
                  </div>
                  <p className="text-rose-200">
                    {getViolationForRoute(selectedRoute.id)?.description}
                  </p>
                </div>
              ) : (
                <p className="text-slate-400 italic">No vehicle currently dispatched to this route.</p>
              )}
            </div>

            <div className="p-4 border-t border-slate-800 bg-slate-950/50 flex justify-end">
              <button
                onClick={() => setSelectedRoute(null)}
                className="rounded-xl bg-slate-800 hover:bg-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
