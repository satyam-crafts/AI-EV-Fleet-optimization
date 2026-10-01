import React from 'react';
import { RefreshCw, CheckCircle, AlertCircle, Sparkles, BatteryMedium } from 'lucide-react';
import { FleetKPIs } from '../types';

interface HeaderProps {
  title: string;
  subtitle?: string;
  kpis?: FleetKPIs;
  isConnected: boolean;
  onResetDemo: () => void;
  onRunOptimizationClick: () => void;
  isResetting?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  kpis,
  isConnected,
  onResetDemo,
  onRunOptimizationClick,
  isResetting = false,
}) => {
  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-6 flex items-center justify-between shrink-0 sticky top-0 z-20">
      {/* Title & Subtitle */}
      <div>
        <h2 className="text-lg font-bold text-white tracking-tight">{title}</h2>
        {subtitle && <p className="text-xs text-slate-400 hidden sm:block">{subtitle}</p>}
      </div>

      {/* Quick KPI pills & Actions */}
      <div className="flex items-center space-x-3">
        {kpis && (
          <div className="hidden lg:flex items-center space-x-3 text-xs bg-slate-950/60 border border-slate-800/80 px-3 py-1.5 rounded-xl">
            <div className="flex items-center space-x-1.5 text-slate-300">
              <BatteryMedium className="w-3.5 h-3.5 text-emerald-400" />
              <span>Avg SOC: </span>
              <span className="font-semibold text-white">{kpis.average_soc_percent}%</span>
            </div>
            <span className="text-slate-700">|</span>
            <div className="flex items-center space-x-1.5 text-slate-300">
              <span>Savings: </span>
              <span className="font-semibold text-emerald-400">${kpis.cost_savings.toFixed(2)} ({kpis.savings_percentage}%)</span>
            </div>
          </div>
        )}

        {/* Connection status */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 border border-slate-700">
          {isConnected ? (
            <>
              <CheckCircle className="w-3 h-3 text-emerald-400" />
              <span className="text-slate-300 hidden md:inline">API Online</span>
            </>
          ) : (
            <>
              <AlertCircle className="w-3 h-3 text-amber-400" />
              <span className="text-amber-300">Local Cache</span>
            </>
          )}
        </div>

        {/* Reset Demo button */}
        <button
          onClick={onResetDemo}
          disabled={isResetting}
          title="Reset to default scenario"
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isResetting ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">Reset Demo</span>
        </button>

        {/* Quick Optimize Button */}
        <button
          onClick={onRunOptimizationClick}
          className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white text-xs font-bold shadow-md shadow-emerald-950/40 transition-all"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Optimize</span>
        </button>
      </div>
    </header>
  );
};
