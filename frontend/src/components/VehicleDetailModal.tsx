import React from 'react';
import { Vehicle, ChargingPlan, VehicleAssignment } from '../types';
import {
  X,
  Battery,
  Zap,
  Activity,
  Gauge,
  Thermometer,
  ShieldAlert,
  Calendar,
  CheckCircle2,
  Clock,
  ArrowRight,
} from 'lucide-react';

interface VehicleDetailModalProps {
  vehicle: Vehicle | null;
  assignment?: VehicleAssignment;
  chargingPlan?: ChargingPlan;
  onClose: () => void;
}

export const VehicleDetailModal: React.FC<VehicleDetailModalProps> = ({
  vehicle,
  assignment,
  chargingPlan,
  onClose,
}) => {
  if (!vehicle) return null;

  const spec = vehicle.battery_spec;
  const state = vehicle.battery_state;
  const usableKwh = ((spec.capacity_kwh * spec.degradation_factor) * Math.max(0, state.soc - state.min_soc_limit) / 100).toFixed(1);
  const totalRangeKm = (spec.capacity_kwh * spec.degradation_factor / vehicle.consumption_rate_kwh_per_km).toFixed(0);
  const usableRangeKm = (Number(usableKwh) / vehicle.consumption_rate_kwh_per_km).toFixed(0);

  const healthColors = {
    EXCELLENT: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
    GOOD: 'text-teal-400 bg-teal-500/10 border-teal-500/30',
    ATTENTION: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
    CRITICAL: 'text-rose-400 bg-rose-500/10 border-rose-500/30',
  }[state.health_status];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-2xl overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Battery className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono font-bold text-emerald-400">{vehicle.id}</span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${healthColors}`}>
                  {state.health_status} HEALTH
                </span>
                <span className="text-xs text-slate-400">· {vehicle.current_status}</span>
              </div>
              <h3 className="text-lg font-bold text-white tracking-tight">{vehicle.name}</h3>
              <p className="text-xs text-slate-400">{vehicle.make} {vehicle.model} · {vehicle.current_location}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-xl p-2 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
          {/* SOC Gauge and Limits */}
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-2xl p-5 space-y-3">
            <div className="flex justify-between items-baseline">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                State of Charge (SOC)
              </span>
              <span className="text-2xl font-bold text-white font-mono">{state.soc.toFixed(1)}%</span>
            </div>

            {/* Custom Multi-marker Progress Bar */}
            <div className="relative w-full h-4 bg-slate-800 rounded-full overflow-hidden">
              {/* Actual SOC Bar */}
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  state.soc < state.min_soc_limit + 5.0
                    ? 'bg-rose-500'
                    : state.soc < 40
                    ? 'bg-amber-500'
                    : 'bg-emerald-500'
                }`}
                style={{ width: `${state.soc}%` }}
              />
              {/* Min Buffer marker */}
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-rose-400"
                style={{ left: `${state.min_soc_limit}%` }}
                title={`Min Buffer: ${state.min_soc_limit}%`}
              />
              {/* Max Ceiling marker */}
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-cyan-400"
                style={{ left: `${state.max_soc_limit}%` }}
                title={`Max Target: ${state.max_soc_limit}%`}
              />
            </div>

            <div className="flex justify-between text-[11px] text-slate-400 pt-1">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-rose-400" /> Min Buffer: {state.min_soc_limit}%
              </span>
              <span className="text-slate-300 font-semibold">Usable: {usableKwh} kWh</span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-cyan-400" /> Max Ceiling: {state.max_soc_limit}%
              </span>
            </div>
          </div>

          {/* Battery Telemetry Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="bg-slate-950/40 border border-slate-800/80 p-3.5 rounded-xl">
              <span className="text-slate-400 flex items-center gap-1.5 mb-1">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                Capacity
              </span>
              <span className="text-sm font-bold text-white font-mono">{spec.capacity_kwh} kWh</span>
              <p className="text-[10px] text-slate-400 mt-0.5">Eff: {(spec.capacity_kwh * spec.degradation_factor).toFixed(1)} kWh</p>
            </div>

            <div className="bg-slate-950/40 border border-slate-800/80 p-3.5 rounded-xl">
              <span className="text-slate-400 flex items-center gap-1.5 mb-1">
                <Activity className="w-3.5 h-3.5 text-emerald-400" />
                Degradation
              </span>
              <span className="text-sm font-bold text-white font-mono">{(spec.degradation_factor * 100).toFixed(0)}%</span>
              <p className="text-[10px] text-slate-400 mt-0.5">{spec.cycle_count} cycles</p>
            </div>

            <div className="bg-slate-950/40 border border-slate-800/80 p-3.5 rounded-xl">
              <span className="text-slate-400 flex items-center gap-1.5 mb-1">
                <Gauge className="w-3.5 h-3.5 text-cyan-400" />
                Usable Range
              </span>
              <span className="text-sm font-bold text-white font-mono">{usableRangeKm} km</span>
              <p className="text-[10px] text-slate-400 mt-0.5">Max: {totalRangeKm} km</p>
            </div>

            <div className="bg-slate-950/40 border border-slate-800/80 p-3.5 rounded-xl">
              <span className="text-slate-400 flex items-center gap-1.5 mb-1">
                <Thermometer className="w-3.5 h-3.5 text-orange-400" />
                Pack Temp
              </span>
              <span className="text-sm font-bold text-white font-mono">{state.temperature_c.toFixed(1)} °C</span>
              <p className="text-[10px] text-slate-400 mt-0.5">Max Charge: {spec.max_charge_power_kw} kW</p>
            </div>
          </div>

          {/* Active Route Assignment Card */}
          {assignment && (
            <div className="bg-slate-950/60 border border-cyan-500/20 rounded-2xl p-4 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-cyan-400 flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5" />
                  Assigned Route
                </span>
                <span className="font-mono text-slate-300 font-bold">{assignment.route_id}</span>
              </div>
              <h4 className="text-sm font-bold text-white">{assignment.route_name}</h4>
              <div className="flex justify-between items-center text-xs text-slate-400 pt-1">
                <span>Dep: {new Date(assignment.departure_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
                <span>Arr: {new Date(assignment.arrival_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                <span className="text-slate-300 font-semibold">{assignment.energy_required_kwh} kWh needed</span>
              </div>
            </div>
          )}

          {/* Scheduled Smart Charging Session */}
          {chargingPlan && (
            <div className="bg-slate-950/60 border border-emerald-500/20 rounded-2xl p-4 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Scheduled Charging Session
                </span>
                <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                  {chargingPlan.tariff_type}
                </span>
              </div>
              <h4 className="text-sm font-bold text-white">
                {chargingPlan.station_name} (Port {chargingPlan.port_id})
              </h4>
              <div className="flex justify-between items-center text-xs text-slate-400 pt-1">
                <span>{new Date(chargingPlan.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} – {new Date(chargingPlan.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                <span>+{chargingPlan.energy_to_charge_kwh} kWh</span>
                <span className="text-emerald-400 font-bold">${chargingPlan.estimated_cost.toFixed(2)}</span>
              </div>
            </div>
          )}

          {/* Degradation / Health Constraints Notice */}
          {spec.degradation_factor < 0.85 && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 flex items-start gap-2.5 text-xs text-amber-200">
              <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold">Battery Degradation Advisory: </span>
                This vehicle has degraded to {(spec.degradation_factor * 100).toFixed(0)}% nominal capacity.
                The optimizer automatically preserves an elevated safety buffer and restricts assignment to high-altitude routes.
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/50 flex justify-end">
          <button
            onClick={onClose}
            className="rounded-xl bg-slate-800 hover:bg-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 transition-colors"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
};
