import React from 'react';
import {
  BatteryCharging,
  Zap,
  Clock,
  DollarSign,
  ShieldCheck,
  TrendingDown,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { ChargingStation, OptimizationResult, EnergyPriceSchedule } from '../types';

interface ChargingPageProps {
  stations: ChargingStation[];
  priceSchedule: EnergyPriceSchedule | null;
  latestOptimization: OptimizationResult | null;
  onNavigateToOptimization: () => void;
}

export const ChargingPage: React.FC<ChargingPageProps> = ({
  stations,
  priceSchedule,
  latestOptimization,
  onNavigateToOptimization,
}) => {
  const plans = latestOptimization?.charging_plans || [];
  const shiftedPlans = plans.filter((p) => p.shifted_from_peak);

  return (
    <div className="space-y-6">
      {/* Infrastructure KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {stations.map((st) => (
          <div
            key={st.id}
            className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-sm space-y-3"
          >
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                  {st.id}
                </span>
                <h4 className="text-sm font-bold text-white tracking-tight mt-1">{st.name}</h4>
                <p className="text-xs text-slate-400">{st.location}</p>
              </div>
              <div className="w-9 h-9 rounded-xl bg-slate-800 flex items-center justify-center text-emerald-400">
                <BatteryCharging className="w-5 h-5" />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800/60 text-xs">
              <div>
                <span className="text-slate-400 text-[10px] uppercase">Power Cap</span>
                <div className="font-bold text-white font-mono">{st.total_power_capacity_kw} kW</div>
              </div>
              <div>
                <span className="text-slate-400 text-[10px] uppercase">Efficiency</span>
                <div className="font-bold text-emerald-400 font-mono">{(st.charging_efficiency * 100).toFixed(0)}%</div>
              </div>
              <div>
                <span className="text-slate-400 text-[10px] uppercase">Ports</span>
                <div className="font-bold text-cyan-400 font-mono">{st.ports.length} Plugs</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Load Shifting Callout Banner */}
      {shiftedPlans.length > 0 && (
        <div className="rounded-2xl border border-emerald-500/30 bg-emerald-950/20 p-5 flex items-start justify-between">
          <div className="flex items-start space-x-3.5">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
              <TrendingDown className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-emerald-300">
                Automated Off-Peak Load Shifting Active ({shiftedPlans.length} Sessions Shifted)
              </h4>
              <p className="text-xs text-emerald-200/80 mt-0.5 leading-relaxed">
                The smart scheduler avoided immediate afternoon plug-in (16:00 - 21:00 on-peak window at $0.34/kWh), shifting charging into overnight valley hours ($0.08 - $0.10/kWh) while guaranteeing full readiness before route departure.
              </p>
            </div>
          </div>
          <div className="hidden md:flex flex-col items-end text-xs shrink-0">
            <span className="text-slate-400">Total Shifted Energy</span>
            <span className="text-base font-bold text-emerald-400 font-mono">
              {latestOptimization?.baseline_comparison.peak_energy_avoided_kwh.toFixed(1)} kWh
            </span>
          </div>
        </div>
      )}

      {/* Charging Schedule / Timeline Table */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/90 overflow-hidden shadow-sm">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              <Clock className="w-4 h-4 text-emerald-400" />
              Smart Charging Schedule Timeline
            </h3>
            <p className="text-xs text-slate-400">
              Vehicle → Station Port → Charging Window → Energy Added → Total Cost
            </p>
          </div>
          <button
            onClick={onNavigateToOptimization}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-colors"
          >
            <span>Re-optimize Schedule</span>
            <Sparkles className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 uppercase font-semibold text-[10px] tracking-wider">
                <th className="py-3 px-4">Vehicle</th>
                <th className="py-3 px-4">Station & Port</th>
                <th className="py-3 px-4">Scheduled Window</th>
                <th className="py-3 px-4">SOC Transition</th>
                <th className="py-3 px-4">Energy Added</th>
                <th className="py-3 px-4">Power Rate</th>
                <th className="py-3 px-4">Tariff Tier</th>
                <th className="py-3 px-4 text-right">Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {plans.map((p) => {
                const startTime = new Date(p.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const endTime = new Date(p.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                return (
                  <tr key={p.plan_id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="font-bold text-white font-mono">{p.vehicle_id}</div>
                      <div className="text-[11px] text-slate-400">{p.vehicle_name}</div>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="font-medium text-slate-200">{p.station_name}</div>
                      <div className="text-[10px] text-slate-400 font-mono">Port {p.port_id}</div>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="font-mono text-white font-semibold">
                        {startTime} – {endTime}
                      </div>
                      {p.shifted_from_peak && (
                        <span className="inline-block mt-0.5 text-[9px] font-bold text-emerald-400 uppercase bg-emerald-500/10 px-1.5 py-0.2 rounded border border-emerald-500/20">
                          Load Shifted
                        </span>
                      )}
                    </td>

                    <td className="py-3.5 px-4 font-mono">
                      <span className="text-amber-400 font-bold">{p.start_soc}%</span>
                      <span className="text-slate-400 mx-1.5">→</span>
                      <span className="text-emerald-400 font-bold">{p.target_soc}%</span>
                    </td>

                    <td className="py-3.5 px-4 font-mono font-bold text-white">
                      +{p.energy_to_charge_kwh} kWh
                    </td>

                    <td className="py-3.5 px-4 font-mono text-slate-300">
                      {p.charging_power_kw} kW
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          p.tariff_type === 'OFF_PEAK'
                            ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/20'
                            : 'bg-amber-500/15 text-amber-300 border border-amber-500/20'
                        }`}
                      >
                        {p.tariff_type}
                      </span>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                        ${p.average_rate_per_kwh.toFixed(3)}/kWh
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-right font-mono font-bold text-emerald-400 text-sm">
                      ${p.estimated_cost.toFixed(2)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {plans.length === 0 && (
          <div className="p-8 text-center text-xs text-slate-400">
            No charging sessions currently scheduled. Run an optimization to generate a smart charging plan.
          </div>
        )}
      </div>
    </div>
  );
};
