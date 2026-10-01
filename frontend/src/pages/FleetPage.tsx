import React, { useState } from 'react';
import {
  Search,
  Filter,
  Truck,
  Battery,
  Zap,
  Gauge,
  Activity,
  ShieldAlert,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import { Vehicle, VehicleStatus, BatteryHealthStatus } from '../types';

interface FleetPageProps {
  vehicles: Vehicle[];
  onSelectVehicle: (v: Vehicle) => void;
}

export const FleetPage: React.FC<FleetPageProps> = ({ vehicles, onSelectVehicle }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [healthFilter, setHealthFilter] = useState<string>('ALL');

  // Filter vehicles
  const filteredVehicles = vehicles.filter((v) => {
    const matchesSearch =
      v.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.model.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.current_location.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (v.assigned_route_id && v.assigned_route_id.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesStatus = statusFilter === 'ALL' || v.current_status === statusFilter;
    const matchesHealth = healthFilter === 'ALL' || v.battery_state.health_status === healthFilter;

    return matchesSearch && matchesStatus && matchesHealth;
  });

  const getStatusBadge = (status: VehicleStatus) => {
    switch (status) {
      case 'IDLE':
        return 'bg-slate-800 text-slate-300 border-slate-700';
      case 'CHARGING':
        return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30 animate-pulse';
      case 'EN_ROUTE':
        return 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30';
      case 'MAINTENANCE':
        return 'bg-rose-500/15 text-rose-400 border-rose-500/30';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  const getHealthBadge = (health: BatteryHealthStatus) => {
    switch (health) {
      case 'EXCELLENT':
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      case 'GOOD':
        return 'text-teal-400 bg-teal-500/10 border-teal-500/20';
      case 'ATTENTION':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
      case 'CRITICAL':
        return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
    }
  };

  return (
    <div className="space-y-6">
      {/* Search and Filters Bar */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-4 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search vehicle ID, model, location..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          {/* Status Filter */}
          <div className="flex items-center space-x-1.5 text-xs">
            <span className="text-slate-400">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="IDLE">Idle</option>
              <option value="CHARGING">Charging</option>
              <option value="EN_ROUTE">En Route</option>
              <option value="MAINTENANCE">Maintenance</option>
            </select>
          </div>

          {/* Health Filter */}
          <div className="flex items-center space-x-1.5 text-xs">
            <span className="text-slate-400">Health:</span>
            <select
              value={healthFilter}
              onChange={(e) => setHealthFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="ALL">All Health</option>
              <option value="EXCELLENT">Excellent</option>
              <option value="GOOD">Good</option>
              <option value="ATTENTION">Attention</option>
              <option value="CRITICAL">Critical</option>
            </select>
          </div>
        </div>
      </div>

      {/* Fleet Vehicles Table / Cards */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/90 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 uppercase font-semibold text-[10px] tracking-wider">
                <th className="py-3 px-4">Vehicle ID & Model</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">State of Charge (SOC)</th>
                <th className="py-3 px-4">Usable Range</th>
                <th className="py-3 px-4">Battery Spec</th>
                <th className="py-3 px-4">Assigned Route</th>
                <th className="py-3 px-4">Battery Health</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredVehicles.map((v) => {
                const spec = v.battery_spec;
                const state = v.battery_state;
                const usableKwh = (spec.capacity_kwh * spec.degradation_factor * Math.max(0, state.soc - state.min_soc_limit) / 100);
                const usableRangeKm = (usableKwh / v.consumption_rate_kwh_per_km).toFixed(0);

                return (
                  <tr
                    key={v.id}
                    onClick={() => onSelectVehicle(v)}
                    className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                  >
                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-300">
                          <Truck className="w-4 h-4 text-emerald-400" />
                        </div>
                        <div>
                          <div className="font-bold text-white font-mono">{v.id}</div>
                          <div className="text-[11px] text-slate-400">{v.name}</div>
                          <div className="text-[10px] text-slate-400">{v.current_location}</div>
                        </div>
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider border ${getStatusBadge(v.current_status)}`}>
                        {v.current_status}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 min-w-[140px]">
                      <div className="space-y-1">
                        <div className="flex justify-between text-[11px] font-mono">
                          <span className="font-bold text-white">{state.soc.toFixed(1)}%</span>
                          <span className="text-[10px] text-slate-400">Min {state.min_soc_limit}%</span>
                        </div>
                        <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              state.soc <= state.min_soc_limit + 5.0
                                ? 'bg-rose-500'
                                : state.soc < 40
                                ? 'bg-amber-500'
                                : 'bg-emerald-500'
                            }`}
                            style={{ width: `${state.soc}%` }}
                          />
                        </div>
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="font-mono font-bold text-white text-xs">{usableRangeKm} km</div>
                      <div className="text-[10px] text-slate-400">{usableKwh.toFixed(1)} kWh usable</div>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="font-mono text-slate-200">{spec.capacity_kwh} kWh</div>
                      <div className="text-[10px] text-slate-400">{v.consumption_rate_kwh_per_km} kWh/km</div>
                    </td>

                    <td className="py-3.5 px-4">
                      {v.assigned_route_id ? (
                        <span className="font-mono text-cyan-400 font-semibold bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 rounded">
                          {v.assigned_route_id}
                        </span>
                      ) : (
                        <span className="text-slate-400 italic">Unassigned</span>
                      )}
                    </td>

                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold border ${getHealthBadge(state.health_status)}`}>
                        {state.health_status}
                      </span>
                      <div className="text-[10px] text-slate-400 mt-0.5 font-mono">
                        {(spec.degradation_factor * 100).toFixed(0)}% SoH
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectVehicle(v);
                        }}
                        className="inline-flex items-center space-x-1 text-slate-400 hover:text-emerald-400 text-xs font-semibold"
                      >
                        <span>Details</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {filteredVehicles.length === 0 && (
          <div className="p-8 text-center text-xs text-slate-400">
            No vehicles matched your search filter criteria.
          </div>
        )}
      </div>
    </div>
  );
};
