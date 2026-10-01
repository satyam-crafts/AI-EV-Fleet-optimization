import React from 'react';
import {
  Truck,
  BatteryCharging,
  Zap,
  DollarSign,
  TrendingDown,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  AreaChart,
  Area,
  ReferenceLine,
} from 'recharts';
import { StatCard } from '../components/StatCard';
import { ReasoningCard } from '../components/ReasoningCard';
import {
  FleetKPIs,
  Vehicle,
  Route,
  EnergyPriceSchedule,
  OptimizationResult,
  Recommendation,
} from '../types';

interface DashboardPageProps {
  kpis: FleetKPIs;
  vehicles: Vehicle[];
  routes: Route[];
  priceSchedule: EnergyPriceSchedule | null;
  latestOptimization: OptimizationResult | null;
  recommendations: Recommendation[];
  onSelectVehicle: (v: Vehicle) => void;
  onNavigateToOptimization: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  kpis,
  vehicles,
  routes,
  priceSchedule,
  latestOptimization,
  recommendations,
  onSelectVehicle,
  onNavigateToOptimization,
}) => {
  // 1. Data for Fleet SOC Chart
  const socChartData = vehicles.map((v) => ({
    name: v.id,
    model: v.name,
    soc: v.battery_state.soc,
    minLimit: v.battery_state.min_soc_limit,
    usableKwh: ((v.battery_spec.capacity_kwh * v.battery_spec.degradation_factor) * Math.max(0, v.battery_state.soc - v.battery_state.min_soc_limit) / 100),
  }));

  // 2. Data for 24-Hour TOU Price & Charging Demand Curve
  const hourlyData = Array.from({ length: 24 }).map((_, hour) => {
    const rate = priceSchedule?.windows.find(
      (w) => w.start_hour <= hour && hour < w.end_hour
    )?.rate_per_kwh || 0.16;

    // Check if any charging plan is active in this hour
    let scheduledKw = 0;
    if (latestOptimization) {
      for (const plan of latestOptimization.charging_plans) {
        const startH = new Date(plan.start_time).getUTCHours();
        const endH = new Date(plan.end_time).getUTCHours();
        if (startH <= hour && hour <= endH) {
          scheduledKw += plan.charging_power_kw;
        }
      }
    }

    return {
      hour: `${hour.toString().padStart(2, '0')}:00`,
      rate: rate,
      rateDisplay: `$${rate.toFixed(2)}`,
      scheduledKw: scheduledKw,
    };
  });

  // 3. Vehicles requiring attention
  const attentionVehicles = vehicles.filter(
    (v) =>
      v.battery_state.soc <= v.battery_state.min_soc_limit + 5.0 ||
      v.battery_spec.degradation_factor < 0.85
  );

  return (
    <div className="space-y-6">
      {/* Attention / Advisory Banner if any */}
      {attentionVehicles.length > 0 && (
        <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-amber-200 flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-bold text-amber-300">
                Fleet Attention Required ({attentionVehicles.length} vehicles)
              </h4>
              <p className="mt-0.5 text-xs text-amber-200/80">
                {attentionVehicles.map((v) => `${v.id} (${v.battery_state.soc}% SOC)`).join(', ')} are near the safety reserve floor or have battery degradation advisories.
              </p>
            </div>
          </div>
          <button
            onClick={onNavigateToOptimization}
            className="shrink-0 flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/30 text-amber-100 transition-colors"
          >
            <span>Resolve in Optimizer</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Main KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Fleet Size / Available"
          value={`${kpis.available_vehicles} / ${kpis.total_vehicles}`}
          subtitle={`${kpis.charging_vehicles} currently charging`}
          icon={<Truck className="w-5 h-5" />}
        />
        <StatCard
          title="Average Fleet SOC"
          value={`${kpis.average_soc_percent}%`}
          subtitle={`${kpis.attention_required_count} vehicles near min buffer`}
          icon={<BatteryCharging className="w-5 h-5 text-emerald-400" />}
          trend={{ value: '15% Min Floor Active', isPositive: true }}
        />
        <StatCard
          title="Fleet Energy Demand"
          value={`${kpis.fleet_energy_demand_kwh} kWh`}
          subtitle={`${routes.length} scheduled delivery routes`}
          icon={<Zap className="w-5 h-5 text-amber-400" />}
        />
        <StatCard
          title="Cost Savings"
          value={`$${kpis.cost_savings.toFixed(2)}`}
          subtitle={`Reduced from $${(kpis.estimated_charging_cost + kpis.cost_savings).toFixed(2)}`}
          icon={<TrendingDown className="w-5 h-5 text-emerald-400" />}
          trend={{ value: `-${kpis.savings_percentage}% Off-Peak`, isPositive: true }}
          highlight={true}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Fleet SOC Distribution */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-white tracking-tight">Fleet Battery SOC Levels</h3>
              <p className="text-xs text-slate-400">Current State of Charge vs 15% Minimum Reserve Floor</p>
            </div>
            <span className="text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
              Live Telemetry
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={socChartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94a3b8" domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                  formatter={(val: any) => [`${val}%`, 'SOC']}
                />
                <ReferenceLine y={15} stroke="#f43f5e" strokeDasharray="4 4" label={{ value: 'Min 15%', fill: '#f43f5e', fontSize: 10, position: 'right' }} />
                <Bar
                  dataKey="soc"
                  fill="#10b981"
                  radius={[6, 6, 0, 0]}
                  onClick={(entry) => {
                    const match = vehicles.find((v) => v.id === entry.name);
                    if (match) onSelectVehicle(match);
                  }}
                  cursor="pointer"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: 24-Hour TOU Electricity Price vs Scheduled Charging */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-white tracking-tight">24h TOU Tariff vs Charging Load</h3>
              <p className="text-xs text-slate-400">Demonstrates automated load shifting into off-peak valley rates</p>
            </div>
            <span className="text-[11px] font-semibold text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 rounded-full">
              TOU Optimized
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hourlyData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <defs>
                  <linearGradient id="rateGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="chargeGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.1} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="hour" stroke="#94a3b8" tick={{ fontSize: 10 }} />
                <YAxis yAxisId="left" stroke="#38bdf8" tick={{ fontSize: 11 }} unit="$" domain={[0, 0.40]} />
                <YAxis yAxisId="right" orientation="right" stroke="#10b981" tick={{ fontSize: 11 }} unit="kW" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                />
                <Area yAxisId="left" type="stepAfter" dataKey="rate" stroke="#38bdf8" strokeWidth={2} fillOpacity={1} fill="url(#rateGradient)" name="TOU Tariff ($/kWh)" />
                <Area yAxisId="right" type="monotone" dataKey="scheduledKw" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#chargeGradient)" name="Scheduled Charge (kW)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Optimization & Recommendations Quick Highlights */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              Active Optimization Recommendations
            </h3>
            <p className="text-xs text-slate-400">
              Deterministic, auditable decisions generated by the optimization engine
            </p>
          </div>
          <button
            onClick={onNavigateToOptimization}
            className="flex items-center space-x-1.5 text-xs font-semibold text-emerald-400 hover:text-emerald-300 transition-colors"
          >
            <span>Open Optimization Workspace</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {recommendations.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendations.slice(0, 4).map((rec) => (
              <ReasoningCard key={rec.id} recommendation={rec} />
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-xs text-slate-400 border border-dashed border-slate-800 rounded-xl">
            No active recommendations. Click "Optimize" to run fleet scheduling.
          </div>
        )}
      </div>
    </div>
  );
};
