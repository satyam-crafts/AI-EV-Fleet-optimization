import React, { useState, useEffect } from 'react';
import { Sidebar, NavTab } from './components/Sidebar';
import { Header } from './components/Header';
import { DashboardPage } from './pages/DashboardPage';
import { FleetPage } from './pages/FleetPage';
import { RoutesPage } from './pages/RoutesPage';
import { ChargingPage } from './pages/ChargingPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { OptimizationPage } from './pages/OptimizationPage';
import { VehicleDetailModal } from './components/VehicleDetailModal';
import { AIAssistantDrawer } from './components/AIAssistantDrawer';
import { LoadingSpinner } from './components/LoadingSpinner';
import { ErrorMessage } from './components/ErrorMessage';
import { api } from './services/api';
import {
  Vehicle,
  Route,
  ChargingStation,
  EnergyPriceSchedule,
  OptimizationResult,
  OptimizationRequest,
  Recommendation,
  FleetKPIs,
} from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('dashboard');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(true);
  const [isResetting, setIsResetting] = useState<boolean>(false);
  const [isOptimizing, setIsOptimizing] = useState<boolean>(false);
  const [isAssistantOpen, setIsAssistantOpen] = useState<boolean>(false);

  // Core Data State
  const [kpis, setKpis] = useState<FleetKPIs>({
    total_vehicles: 8,
    available_vehicles: 7,
    charging_vehicles: 1,
    attention_required_count: 2,
    average_soc_percent: 61.3,
    fleet_energy_demand_kwh: 241.4,
    estimated_charging_cost: 14.80,
    cost_savings: 32.40,
    savings_percentage: 68.6,
  });
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [stations, setStations] = useState<ChargingStation[]>([]);
  const [priceSchedule, setPriceSchedule] = useState<EnergyPriceSchedule | null>(null);
  const [latestOptimization, setLatestOptimization] = useState<OptimizationResult | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null);

  // Fetch initial data
  const loadFleetData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [overviewRes, vehiclesRes, routesRes, stationsRes, pricesRes, optRes, recsRes] =
        await Promise.all([
          api.getFleetOverview(),
          api.getVehicles(),
          api.getRoutes(),
          api.getChargingStations(),
          api.getEnergyPrices(),
          api.getLatestOptimization().catch(() => null),
          api.getRecommendations().catch(() => []),
        ]);

      setKpis(overviewRes.kpis);
      setVehicles(vehiclesRes);
      setRoutes(routesRes);
      setStations(stationsRes);
      setPriceSchedule(pricesRes);
      if (optRes) setLatestOptimization(optRes);
      if (recsRes) setRecommendations(recsRes);
      setIsConnected(true);
    } catch (err: any) {
      console.warn('API connection issue:', err.message);
      setIsConnected(false);
      setVehicles([]);
      setRoutes([]);
      setStations([]);
      setPriceSchedule(null);
      setLatestOptimization(null);
      setRecommendations([]);
      setKpis({
        total_vehicles: 0,
        available_vehicles: 0,
        charging_vehicles: 0,
        attention_required_count: 0,
        average_soc_percent: 0,
        fleet_energy_demand_kwh: 0,
        estimated_charging_cost: 0,
        cost_savings: 0,
        savings_percentage: 0,
      });
      setError(
        `Cannot reach the backend API (${err.message}). Start the FastAPI server on port 8000, then retry.`,
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFleetData();
  }, []);

  // Run Optimization Trigger
  const handleExecuteOptimization = async (req: OptimizationRequest) => {
    setIsOptimizing(true);
    setError(null);
    try {
      const result = await api.runOptimization(req);
      setLatestOptimization(result);
      setRecommendations(result.recommendations);
      const overview = await api.getFleetOverview();
      setKpis(overview.kpis);
      setIsConnected(true);
    } catch (err: any) {
      setError(`Optimization failed: ${err.message}`);
    } finally {
      setIsOptimizing(false);
    }
  };

  // Reset Demo Trigger
  const handleResetDemo = async () => {
    setIsResetting(true);
    setError(null);
    try {
      await api.resetDemo();
      await loadFleetData();
    } catch (err: any) {
      setError(`Demo reset failed: ${err.message}`);
    } finally {
      setIsResetting(false);
    }
  };

  // Helper to find assignment and charging plan for selected vehicle
  const selectedVehicleAssignment = selectedVehicle && latestOptimization
    ? latestOptimization.assignments.find((a) => a.vehicle_id === selectedVehicle.id)
    : undefined;

  const selectedVehicleChargingPlan = selectedVehicle && latestOptimization
    ? latestOptimization.charging_plans.find((p) => p.vehicle_id === selectedVehicle.id)
    : undefined;

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar Navigation */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        onToggleAssistant={() => setIsAssistantOpen(!isAssistantOpen)}
        isAssistantOpen={isAssistantOpen}
        attentionCount={kpis.attention_required_count}
      />

      {/* Main App Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <Header
          title={
            currentTab === 'dashboard'
              ? 'Fleet Operations Dashboard'
              : currentTab === 'fleet'
              ? 'Electric Vehicle Fleet View'
              : currentTab === 'routes'
              ? 'Route Scheduling & Feasibility'
              : currentTab === 'charging'
              ? 'Smart Charging Infrastructure'
              : currentTab === 'analytics'
              ? 'Energy & Cost Analytics'
              : 'Deterministic Optimization Workspace'
          }
          subtitle={
            currentTab === 'dashboard'
              ? 'Real-time telemetry, battery state-of-charge, and energy cost optimization'
              : currentTab === 'fleet'
              ? 'Battery specifications, degradation health, and operational status'
              : currentTab === 'routes'
              ? 'Delivery missions evaluated against physical battery and time constraints'
              : currentTab === 'charging'
              ? '24-hour TOU-integrated charging timeline and load shifting'
              : currentTab === 'analytics'
              ? 'Baseline comparisons, peak energy avoidance, and tariff schedules'
              : 'Multi-objective heuristic engine matching vehicles to routes and schedules'
          }
          kpis={kpis}
          isConnected={isConnected}
          onResetDemo={handleResetDemo}
          onRunOptimizationClick={() => setCurrentTab('optimization')}
          isResetting={isResetting}
        />

        {/* Page Content Scroll Area */}
        <main className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="mb-6">
              <ErrorMessage
                title="Backend Connectivity Notice"
                message={error}
                onRetry={loadFleetData}
              />
            </div>
          )}

          {loading ? (
            <div className="h-96 flex items-center justify-center">
              <LoadingSpinner message="Loading fleet and optimization models..." size="lg" />
            </div>
          ) : (
            <>
              {currentTab === 'dashboard' && (
                <DashboardPage
                  kpis={kpis}
                  vehicles={vehicles}
                  routes={routes}
                  priceSchedule={priceSchedule}
                  latestOptimization={latestOptimization}
                  recommendations={recommendations}
                  onSelectVehicle={setSelectedVehicle}
                  onNavigateToOptimization={() => setCurrentTab('optimization')}
                />
              )}

              {currentTab === 'fleet' && (
                <FleetPage
                  vehicles={vehicles}
                  onSelectVehicle={setSelectedVehicle}
                />
              )}

              {currentTab === 'routes' && (
                <RoutesPage
                  routes={routes}
                  latestOptimization={latestOptimization}
                  onNavigateToOptimization={() => setCurrentTab('optimization')}
                />
              )}

              {currentTab === 'charging' && (
                <ChargingPage
                  stations={stations}
                  priceSchedule={priceSchedule}
                  latestOptimization={latestOptimization}
                  onNavigateToOptimization={() => setCurrentTab('optimization')}
                />
              )}

              {currentTab === 'analytics' && (
                <AnalyticsPage
                  latestOptimization={latestOptimization}
                  priceSchedule={priceSchedule}
                  routes={routes}
                />
              )}

              {currentTab === 'optimization' && (
                <OptimizationPage
                  latestResult={latestOptimization}
                  isOptimizing={isOptimizing}
                  onExecuteOptimization={handleExecuteOptimization}
                  recommendations={recommendations}
                />
              )}
            </>
          )}
        </main>
      </div>

      {/* Vehicle Detail Telemetry Drawer */}
      <VehicleDetailModal
        vehicle={selectedVehicle}
        assignment={selectedVehicleAssignment}
        chargingPlan={selectedVehicleChargingPlan}
        onClose={() => setSelectedVehicle(null)}
      />

      {/* AI Assistant Conversational Drawer */}
      <AIAssistantDrawer
        isOpen={isAssistantOpen}
        onClose={() => setIsAssistantOpen(false)}
        latestOptimization={latestOptimization}
      />
    </div>
  );
};

export default App;
