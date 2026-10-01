import React, { useState } from 'react';
import { Recommendation, StructuredReasoning } from '../types';
import {
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Info,
  Zap,
  DollarSign,
  AlertCircle,
  Clock,
  ArrowRight,
} from 'lucide-react';

interface ReasoningCardProps {
  recommendation: Recommendation;
}

export const ReasoningCard: React.FC<ReasoningCardProps> = ({ recommendation }) => {
  const [expanded, setExpanded] = useState(false);
  const reasoning: StructuredReasoning = recommendation.reasoning;

  const priorityStyles = {
    LOW: 'border-slate-700 bg-slate-800/40 text-slate-300',
    MEDIUM: 'border-blue-500/30 bg-blue-500/10 text-blue-300',
    HIGH: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
    CRITICAL: 'border-rose-500/30 bg-rose-500/10 text-rose-300',
  }[recommendation.priority];

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-sm hover:border-slate-700 transition-all">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider border ${priorityStyles}`}>
              {recommendation.priority}
            </span>
            <span className="rounded-full bg-slate-800 border border-slate-700 px-2.5 py-0.5 text-xs font-mono text-slate-300">
              {recommendation.recommendation_type}
            </span>
            {recommendation.vehicle_id && (
              <span className="text-xs font-semibold text-emerald-400">
                {recommendation.vehicle_id}
              </span>
            )}
            {recommendation.route_id && (
              <span className="text-xs font-semibold text-cyan-400">
                → {recommendation.route_id}
              </span>
            )}
          </div>
          <h4 className="text-base font-bold text-white tracking-tight">
            {recommendation.title}
          </h4>
          <p className="mt-1 text-sm text-slate-300">{recommendation.summary}</p>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="rounded-lg p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors shrink-0"
          title={expanded ? 'Collapse Reasoning' : 'Expand Mathematical Reasoning'}
        >
          {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
      </div>

      {/* Decision Summary Pill */}
      <div className="mt-4 rounded-xl bg-slate-950/70 border border-slate-800/80 p-3 flex items-start gap-3">
        <ArrowRight className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
        <div className="text-xs">
          <span className="font-semibold text-slate-300">Decision: </span>
          <span className="text-slate-200 font-mono">{reasoning.decision}</span>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-800/60">
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span>{reasoning.estimated_energy_kwh.toFixed(1)} kWh</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
          <span>${reasoning.estimated_cost.toFixed(2)}</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
          <span>{reasoning.constraints_satisfied.length} Constraints OK</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <Clock className="w-3.5 h-3.5 text-indigo-400" />
          <span>Confidence: {Math.round(recommendation.confidence_score * 100)}%</span>
        </div>
      </div>

      {/* Expanded Reasoning Deep Dive */}
      {expanded && (
        <div className="mt-4 space-y-3 pt-3 border-t border-slate-800/80 text-xs">
          {/* Mathematical Justification */}
          <div>
            <h5 className="font-semibold text-slate-200 flex items-center gap-1.5 mb-1">
              <Info className="w-3.5 h-3.5 text-cyan-400" />
              Mathematical Justification
            </h5>
            <p className="text-slate-300 leading-relaxed bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/50">
              {reasoning.reason}
            </p>
          </div>

          {/* Constraints Verified */}
          <div>
            <h5 className="font-semibold text-slate-200 flex items-center gap-1.5 mb-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              Satisfied Physical & Safety Constraints
            </h5>
            <ul className="space-y-1">
              {reasoning.constraints_satisfied.map((c, i) => (
                <li key={i} className="flex items-center gap-2 text-slate-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  {c}
                </li>
              ))}
            </ul>
          </div>

          {/* Evaluated Numerical Inputs */}
          <div>
            <h5 className="font-semibold text-slate-200 mb-1">Evaluated Numerical Parameters</h5>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60 font-mono text-[11px]">
              {Object.entries(reasoning.inputs_considered).map(([key, val]) => (
                <div key={key}>
                  <span className="text-slate-400">{key}: </span>
                  <span className="text-emerald-300 font-semibold">{String(val)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Warnings if any */}
          {reasoning.warnings.length > 0 && (
            <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-2.5 text-amber-200">
              <div className="flex items-center gap-1.5 font-semibold mb-1">
                <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                Operational Flags
              </div>
              <ul className="space-y-0.5 list-disc list-inside">
                {reasoning.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
