import React from 'react';
import {
  LayoutDashboard,
  Truck,
  MapPin,
  BatteryCharging,
  BarChart3,
  Cpu,
  Bot,
  Zap,
  ShieldCheck,
  ChevronRight,
} from 'lucide-react';

export type NavTab = 'dashboard' | 'fleet' | 'routes' | 'charging' | 'analytics' | 'optimization';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  onToggleAssistant: () => void;
  isAssistantOpen: boolean;
  attentionCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  onToggleAssistant,
  isAssistantOpen,
  attentionCount = 0,
}) => {
  const navItems = [
    { id: 'dashboard' as NavTab, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'fleet' as NavTab, label: 'Fleet View', icon: Truck, badge: attentionCount > 0 ? `${attentionCount} alert` : undefined },
    { id: 'routes' as NavTab, label: 'Routes & Trips', icon: MapPin },
    { id: 'charging' as NavTab, label: 'Smart Charging', icon: BatteryCharging },
    { id: 'analytics' as NavTab, label: 'Energy Analytics', icon: BarChart3 },
    { id: 'optimization' as NavTab, label: 'Optimization Hub', icon: Cpu, highlight: true },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between shrink-0 select-none">
      {/* Brand Header */}
      <div>
        <div className="p-5 border-b border-slate-800 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-950/40">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight text-white leading-tight">
              AI & EV FLEET
            </h1>
            <p className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">
              OPTIMIZER
            </p>
          </div>
        </div>

        {/* Tagline */}
        <div className="px-5 py-3 bg-slate-950/40 border-b border-slate-800/60">
          <p className="text-[11px] text-slate-400 italic">
            "From Fleet Data to Intelligent Energy Decisions"
          </p>
        </div>

        {/* Nav Links */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-bold shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon
                    className={`w-4 h-4 ${
                      isActive ? 'text-emerald-400' : 'text-slate-400'
                    }`}
                  />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="rounded-full bg-amber-500/20 text-amber-300 text-[10px] px-2 py-0.5 border border-amber-500/30">
                    {item.badge}
                  </span>
                )}
                {item.highlight && !item.badge && (
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Controls & AI Assistant Trigger */}
      <div className="p-3 border-t border-slate-800 space-y-2">
        <button
          onClick={onToggleAssistant}
          className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
            isAssistantOpen
              ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-md'
              : 'bg-slate-800/80 hover:bg-slate-800 text-slate-200 border border-slate-700/60'
          }`}
        >
          <div className="flex items-center space-x-2.5">
            <Bot className="w-4 h-4 text-emerald-300" />
            <span>AI Fleet Copilot</span>
          </div>
          <ChevronRight className={`w-3.5 h-3.5 transition-transform ${isAssistantOpen ? 'rotate-90' : ''}`} />
        </button>

        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-400">
          <div className="flex items-center space-x-1.5 text-emerald-400 font-semibold mb-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Deterministic Core</span>
          </div>
          <p className="text-[10px] text-slate-400 leading-normal">
            Physical safety & battery limits guaranteed by mathematical engine.
          </p>
        </div>
      </div>
    </aside>
  );
};
