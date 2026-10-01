import React, { useState } from 'react';
import {
  Cpu,
  Sparkles,
  Sliders,
  Play,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Zap,
  DollarSign,
  TrendingDown,
  ShieldCheck,
  RotateCcw,
  ArrowRight,
  Info,
} from 'lucide-react';
import { ReasoningCard } from '../components/ReasoningCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import {
  OptimizationRequest,
  OptimizationResult,
  Recommendation,
} from '../types';

interface OptimizationPageProps {
  latestResult: OptimizationResult | null;
  isOptimizing: boolean;
  onExecuteOptimization: (req: OptimizationRequest) => Promise<void>;
  recommendations: Recommendation[];
}

export const OptimizationPage: React.FC<OptimizationPageProps> = ({
  latestResult,
  isOptimizing,
  onExecuteOptimization,
  recommendations,
}) => {
  // Optimization form parameters
  const [horizon, setHorizon] = useState<number>(24);
  const [minSocBuffer, setMinSocBuffer] = useState<number>(15.0);
  const [maxSocTarget, setMaxSocTarget] = useState<number>(90.0);
  const [presetMode, setPresetMode] = useState<'balanced' | 'cost' | 'health'>('balanced');
  const [costWeight, setCostWeight] = useState<number>(0.5);
  const [healthWeight, setHealthWeight] = useState<number>(0.3);
  const [slackWeight, setSlackWeight] = useState<number>(0.2);

  const applyPreset = (mode: 'balanced' | 'cost' | 'health') => {
    setPresetMode(mode);
    if (mode === 'balanced') {
      setCostWeight(0.5);
      setHealthWeight(0.3);
      setSlackWeight(0.2);
    } else if (mode === 'cost') {
      setCostWeight(0.8);
      setHealthWeight(0.1);
      setSlackWeight(0.1);
    } else if (mode === 'health') {
      setCostWeight(0.2);
      setHealthWeight(0.6);
      setSlackWeight(0.2);
    }
  };

  const handleRunOptimization = () => {
    const request: OptimizationRequest = {
      planning_horizon_hours: horizon,
      min_soc_buffer_percent: minSocBuffer,
      max_soc_target_percent: maxSocTarget,
      weights: {
        cost_weight: costWeight,
        battery_health_weight: healthWeight,
        schedule_slack_weight: slackWeight,
      },
    };
    onExecuteOptimization(request);
  };

  return (
    <div className="space-y-6">
      {/* Control Workspace: Parameters & Solver Trigger */}
      <div className="rounded-3xl border border-slate-800 bg-slate-900/90 p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
                Deterministic Solver Workspace
              </span>
            </div>
            <h3 className="text-lg font-bold text-white tracking-tight mt-1">
              Configure Optimization Objectives & Constraints
            </h3>
            <p className="text-xs text-slate-400">
              Tune multi-objective weights, SOC reserve buffers, and planning horizon
            </p>
          </div>

          <button
            onClick={handleRunOptimization}
            disabled={isOptimizing}
            className="flex items-center justify-center space-x-2 px-6 py-3 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white text-sm font-bold shadow-lg shadow-emerald-950/40 transition-all disabled:opacity-50"
          >
            {isOptimizing ? (
              <>
                <LoadingSpinner size="sm" message="" />
                <span>Running Optimizer...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Run Optimization</span>
              </>
            )}
          </button>
        </div>

        {/* Parameters Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6 text-xs">
          {/* Column 1: Horizon & Mode */}
          <div className="space-y-4">
            <div>
              <label className="font-semibold text-slate-300 block mb-1">Planning Horizon</label>
              <div className="grid grid-cols-3 gap-2">
                {[12, 24, 48].map((h) => (
                  <button
                    key={h}
                    onClick={() => setHorizon(h)}
                    className={`py-2 rounded-xl font-bold border transition-colors ${
                      horizon === h
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:bg-slate-800'
                    }`}
                  >
                    {h} Hours
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">Optimization Strategy Preset</label>
              <div className="space-y-1.5">
                {[
                  { id: 'balanced', label: 'Balanced (Cost & Health)', desc: '50% Cost, 30% Battery, 20% Slack' },
                  { id: 'cost', label: 'Maximum Cost Reduction', desc: '80% Cost, 10% Battery, 10% Slack' },
                  { id: 'health', label: 'Battery Preservation', desc: '20% Cost, 60% Battery, 20% Slack' },
                ].map((p) => (
                  <button
                    key={p.id}
                    onClick={() => applyPreset(p.id as any)}
                    className={`w-full text-left p-2.5 rounded-xl border transition-colors ${
                      presetMode === p.id
                        ? 'bg-emerald-500/15 border-emerald-500/30 text-white'
                        : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:bg-slate-800/40'
                    }`}
                  >
                    <div className="font-bold text-slate-200">{p.label}</div>
                    <div className="text-[10px] text-slate-400">{p.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Column 2: Safety Buffers */}
          <div className="space-y-4">
            <div className="bg-slate-950/60 border border-slate-800/80 p-4 rounded-2xl space-y-2">
              <div className="flex justify-between">
                <span className="font-semibold text-slate-300">Min SOC Reserve Buffer</span>
                <span className="font-mono font-bold text-rose-400">{minSocBuffer}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="30"
                step="1"
                value={minSocBuffer}
                onChange={(e) => setMinSocBuffer(Number(e.target.value))}
                className="w-full accent-rose-500 cursor-pointer"
              />
              <p className="text-[10px] text-slate-400">
                Guaranteed emergency reserve below which no vehicle is permitted to discharge.
              </p>
            </div>

            <div className="bg-slate-950/60 border border-slate-800/80 p-4 rounded-2xl space-y-2">
              <div className="flex justify-between">
                <span className="font-semibold text-slate-300">Max Operational SOC Target</span>
                <span className="font-mono font-bold text-cyan-400">{maxSocTarget}%</span>
              </div>
              <input
                type="range"
                min="75"
                max="100"
                step="5"
                value={maxSocTarget}
                onChange={(e) => setMaxSocTarget(Number(e.target.value))}
                className="w-full accent-cyan-500 cursor-pointer"
              />
              <p className="text-[10px] text-slate-400">
                Daily charging ceiling to protect cell chemistry from prolonged high voltage degradation.
              </p>
            </div>
          </div>

          {/* Column 3: Multi-Objective Weight Values */}
          <div className="bg-slate-950/60 border border-slate-800/80 p-4 rounded-2xl space-y-3">
            <h5 className="font-semibold text-slate-200 uppercase tracking-wider text-[10px]">
              Multi-Objective Weights
            </h5>

            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Electricity Cost Priority:</span>
                <span className="font-mono font-bold text-emerald-400">{(costWeight * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={costWeight}
                onChange={(e) => {
                  setCostWeight(Number(e.target.value));
                  setPresetMode('balanced' as any);
                }}
                className="w-full accent-emerald-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Battery Health Priority:</span>
                <span className="font-mono font-bold text-teal-400">{(healthWeight * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={healthWeight}
                onChange={(e) => {
                  setHealthWeight(Number(e.target.value));
                  setPresetMode('balanced' as any);
                }}
                className="w-full accent-teal-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Schedule Slack Priority:</span>
                <span className="font-mono font-bold text-indigo-400">{(slackWeight * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={slackWeight}
                onChange={(e) => {
                  setSlackWeight(Number(e.target.value));
                  setPresetMode('balanced' as any);
                }}
                className="w-full accent-indigo-500"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Optimization Results View */}
      {latestResult && (
        <div className="space-y-6 animate-in fade-in duration-300">
          {/* Results Summary Header */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-bold text-slate-400">{latestResult.id}</span>
                  <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                    {latestResult.status}
                  </span>
                </div>
                <h4 className="text-base font-bold text-white tracking-tight">
                  Optimization Results Overview
                </h4>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
              <div className="bg-slate-950/60 border border-slate-800 px-3 py-1.5 rounded-xl">
                <span className="text-slate-400">Execution Time: </span>
                <span className="text-white font-bold">{latestResult.execution_time_ms} ms</span>
              </div>
              <div className="bg-slate-950/60 border border-slate-800 px-3 py-1.5 rounded-xl">
                <span className="text-slate-400">Total Charging Cost: </span>
                <span className="text-emerald-400 font-bold">${latestResult.total_charging_cost.toFixed(2)}</span>
              </div>
              <div className="bg-emerald-950/30 border border-emerald-500/30 px-3 py-1.5 rounded-xl text-emerald-300">
                <span>Net Savings: </span>
                <span className="font-bold">${latestResult.baseline_comparison.cost_savings.toFixed(2)} ({latestResult.baseline_comparison.savings_percentage}%)</span>
              </div>
            </div>
          </div>

          {/* Vehicle Assignments Table */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/90 overflow-hidden shadow-sm">
            <div className="p-4 border-b border-slate-800">
              <h4 className="text-sm font-bold text-white tracking-tight">
                Optimized Vehicle-to-Route Assignments ({latestResult.assignments.length})
              </h4>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 uppercase font-semibold text-[10px] tracking-wider">
                    <th className="py-3 px-4">Vehicle</th>
                    <th className="py-3 px-4">Assigned Route</th>
                    <th className="py-3 px-4">Departure & Arrival</th>
                    <th className="py-3 px-4">Initial SOC</th>
                    <th className="py-3 px-4">Projected Arrival SOC</th>
                    <th className="py-3 px-4">Route Energy</th>
                    <th className="py-3 px-4 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {latestResult.assignments.map((a, i) => (
                    <tr key={i} className="hover:bg-slate-800/30">
                      <td className="py-3 px-4">
                        <span className="font-bold text-white font-mono">{a.vehicle_id}</span>
                        <div className="text-[10px] text-slate-400">{a.vehicle_name}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-semibold text-cyan-300">{a.route_id}</span>
                        <div className="text-[10px] text-slate-400">{a.route_name}</div>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">
                        {new Date(a.departure_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} → {new Date(a.arrival_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-amber-400">
                        {a.initial_soc}%
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-emerald-400">
                        {a.estimated_final_soc}%
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-200">
                        {a.energy_required_kwh} kWh
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className="inline-flex items-center space-x-1 text-[10px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Feasible</span>
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Structured Explainability Cards */}
          <div className="space-y-4">
            <div>
              <h4 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-400" />
                Structured Operational Reasoning & Explainability
              </h4>
              <p className="text-xs text-slate-400">
                Auditable mathematical justification for every dispatch, charging session, and constraint verification
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {recommendations.map((rec) => (
                <ReasoningCard key={rec.id} recommendation={rec} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
