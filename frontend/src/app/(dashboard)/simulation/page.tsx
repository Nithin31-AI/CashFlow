"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  Calendar,
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
  RefreshCw,
  Info,
  Sliders,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { api, SimulationRun } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

export default function SimulationPage() {
  const { currentBusiness } = useAuth();
  const [simulation, setSimulation] = useState<SimulationRun | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSimulating, setIsSimulating] = useState(false);
  const [horizonDays, setHorizonDays] = useState(30);
  const [numPaths, setNumPaths] = useState(1000);
  const [customDelayDays, setCustomDelayDays] = useState(0);
  const [collectionProbability, setCollectionProbability] = useState(90);
  const [expenseMultiplier, setExpenseMultiplier] = useState(1.0);
  const [showAssumptions, setShowAssumptions] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadLatest = async () => {
    if (!currentBusiness) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getLatestSimulation(currentBusiness.id);
      setSimulation(data);
    } catch (err: any) {
      setError(err.message || "Failed to load simulation.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadLatest();
  }, [currentBusiness]);

  const handleRunSimulation = async () => {
    if (!currentBusiness) return;
    setIsSimulating(true);
    setError(null);
    try {
      const res = await api.runSimulation(currentBusiness.id, {
        horizon_days: horizonDays,
        num_paths: numPaths,
        custom_delay_days: customDelayDays > 0 ? customDelayDays : undefined,
        collection_probability: collectionProbability / 100.0,
        expense_volatility_multiplier: expenseMultiplier,
      });
      setSimulation(res);
    } catch (err: any) {
      setError(err.message || "Simulation failed.");
    } finally {
      setIsSimulating(false);
    }
  };

  const currency = currentBusiness?.currency || "INR";
  const breachProbPct = simulation ? Number((simulation.reserve_breach_probability * 100).toFixed(1)) : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-theme-text">Monte Carlo Simulation</h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#8A9A78]/20 text-[#8A9A78] border border-[#8A9A78]/30">
              1,000 Stochastic Paths
            </span>
          </div>
          <p className="text-sm text-theme-textMuted mt-1">
            Simulate thousands of possible cash paths under customer payment delays and expense volatility.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAssumptions(!showAssumptions)}
            className="px-3.5 py-2 rounded-xl border border-theme-border text-xs font-semibold hover:bg-theme-secondary transition-colors flex items-center gap-2"
          >
            <Info className="w-4 h-4 text-theme-textMuted" />
            <span>Assumptions & Limitations</span>
          </button>
          <button
            onClick={handleRunSimulation}
            disabled={isSimulating}
            className="px-4 py-2 rounded-xl bg-[#8A9A78] hover:opacity-90 text-white text-xs font-semibold shadow-md transition-all flex items-center gap-2 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isSimulating ? "animate-spin" : ""}`} />
            <span>{isSimulating ? "Simulating..." : "Run New Simulation"}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Simulation Controls Panel */}
      <div className="spatial-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <Sliders className="w-4 h-4 text-[#8A9A78]" />
          <h2 className="text-sm font-bold text-theme-text">Simulation Parameters</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Horizon Selector */}
          <div>
            <label className="block text-xs font-medium text-theme-textMuted mb-1.5">Horizon (Days)</label>
            <div className="grid grid-cols-4 gap-1 p-1 bg-theme-secondary rounded-lg border border-theme-border">
              {[14, 30, 60, 90].map((d) => (
                <button
                  key={d}
                  onClick={() => setHorizonDays(d)}
                  className={`py-1 rounded text-xs font-semibold transition-colors ${
                    horizonDays === d ? "bg-theme-surface text-theme-text shadow-sm" : "text-theme-textMuted"
                  }`}
                >
                  {d}d
                </button>
              ))}
            </div>
          </div>

          {/* Payment Delay */}
          <div>
            <div className="flex justify-between text-xs font-medium mb-1.5">
              <span className="text-theme-textMuted">Avg Delay Offset</span>
              <span className="text-theme-text font-bold">+{customDelayDays} days</span>
            </div>
            <input
              type="range"
              min="0"
              max="45"
              step="5"
              value={customDelayDays}
              onChange={(e) => setCustomDelayDays(Number(e.target.value))}
              className="w-full accent-[#8A9A78]"
            />
          </div>

          {/* Collection Rate */}
          <div>
            <div className="flex justify-between text-xs font-medium mb-1.5">
              <span className="text-theme-textMuted">Collection Probability</span>
              <span className="text-theme-text font-bold">{collectionProbability}%</span>
            </div>
            <input
              type="range"
              min="50"
              max="100"
              step="5"
              value={collectionProbability}
              onChange={(e) => setCollectionProbability(Number(e.target.value))}
              className="w-full accent-[#8A9A78]"
            />
          </div>

          {/* Expense Multiplier */}
          <div>
            <div className="flex justify-between text-xs font-medium mb-1.5">
              <span className="text-theme-textMuted">Expense Volatility</span>
              <span className="text-theme-text font-bold">{expenseMultiplier.toFixed(1)}x</span>
            </div>
            <input
              type="range"
              min="0.8"
              max="2.0"
              step="0.1"
              value={expenseMultiplier}
              onChange={(e) => setExpenseMultiplier(Number(e.target.value))}
              className="w-full accent-[#8A9A78]"
            />
          </div>
        </div>
      </div>

      {/* Assumptions Overlay Card */}
      {showAssumptions && simulation && (
        <div className="spatial-card p-5 border-[#8A9A78]/40 bg-[#8A9A78]/5">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2 mb-2">
              <Info className="w-4 h-4 text-[#8A9A78]" />
              <h3 className="text-sm font-bold text-theme-text">Model Assumptions & Governance</h3>
            </div>
            <button onClick={() => setShowAssumptions(false)} className="text-xs text-theme-textMuted hover:text-theme-text">
              Close
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs mt-3">
            <div className="p-3 bg-theme-surface rounded-lg border border-theme-border">
              <span className="text-theme-textMuted block">Starting Liquid Cash</span>
              <span className="font-bold text-theme-text">{formatCurrency(simulation.starting_cash, currency)}</span>
            </div>
            <div className="p-3 bg-theme-surface rounded-lg border border-theme-border">
              <span className="text-theme-textMuted block">Scheduled Pending Receivables</span>
              <span className="font-bold text-theme-text">
                {formatCurrency(simulation.assumptions?.total_pending_receivables || 0, currency)}
              </span>
            </div>
            <div className="p-3 bg-theme-surface rounded-lg border border-theme-border">
              <span className="text-theme-textMuted block">Minimum Reserve Target</span>
              <span className="font-bold text-theme-text">
                {formatCurrency(simulation.assumptions?.minimum_cash_reserve || 0, currency)}
              </span>
            </div>
          </div>
          <p className="text-[11px] text-theme-textMuted mt-3">
            <strong>Limitation Notice:</strong> Simulations evaluate Gaussian daily stochastic deviations and Bernoulli collection trials.
            Tail-risk macroeconomic events or sudden vendor renegotiations are not modelled automatically.
          </p>
        </div>
      )}

      {/* Metrics Grid */}
      {simulation && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Reserve Breach Risk */}
          <div className="spatial-card p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-theme-textMuted uppercase tracking-wider">Reserve Breach Risk</span>
              {breachProbPct > 25 ? (
                <ShieldAlert className="w-5 h-5 text-rose-500" />
              ) : (
                <ShieldCheck className="w-5 h-5 text-[#8A9A78]" />
              )}
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-theme-text">{breachProbPct}%</span>
              <span className="text-xs text-theme-textMuted">probability</span>
            </div>
            <p className="text-xs text-theme-textMuted mt-2">
              {breachProbPct === 0
                ? "Zero paths dipped below your minimum reserve target."
                : `Shortage duration estimated around day ${simulation.potential_shortage_day || 1}.`}
            </p>
          </div>

          {/* Conservative Downside (P10) */}
          <div className="spatial-card p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-theme-textMuted uppercase tracking-wider">10th Percentile (P10)</span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
                Downside
              </span>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-extrabold text-theme-text">
                {formatCurrency(simulation.p10_ending_cash, currency)}
              </span>
            </div>
            <p className="text-xs text-theme-textMuted mt-2">90% of simulated outcomes end above this balance.</p>
          </div>

          {/* Expected Median (P50) */}
          <div className="spatial-card p-5 border-[#8A9A78]/30">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-theme-textMuted uppercase tracking-wider">Median Outcome (P50)</span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#8A9A78]/20 text-[#8A9A78] border border-[#8A9A78]/30">
                Most Likely
              </span>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-extrabold text-theme-text">
                {formatCurrency(simulation.p50_ending_cash, currency)}
              </span>
            </div>
            <p className="text-xs text-theme-textMuted mt-2">Central expected path with standard collection timing.</p>
          </div>

          {/* Optimistic Upside (P90) */}
          <div className="spatial-card p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-theme-textMuted uppercase tracking-wider">90th Percentile (P90)</span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#8A9A78]/20 text-[#8A9A78] border border-[#8A9A78]/30">
                Upside
              </span>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-extrabold text-theme-text">
                {formatCurrency(simulation.p90_ending_cash, currency)}
              </span>
            </div>
            <p className="text-xs text-theme-textMuted mt-2">Accelerated collections and lower operational variance.</p>
          </div>
        </div>
      )}

      {/* Daily Percentile Path Table */}
      {simulation && simulation.percentile_paths && (
        <div className="spatial-card p-5 overflow-hidden">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-theme-text">Simulated Cash Distribution Over Time</h2>
              <p className="text-xs text-theme-textMuted mt-0.5">
                Daily projected envelopes across {simulation.horizon_days} days.
              </p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-400"></span>
                <span className="text-theme-textMuted">P10 (Downside)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#8A9A78]"></span>
                <span className="text-theme-text font-bold">P50 (Median)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#8A9A78]/40"></span>
                <span className="text-theme-textMuted">P90 (Upside)</span>
              </div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-theme-border text-theme-textMuted uppercase tracking-wider font-semibold">
                  <th className="py-2.5 px-3">Timeline</th>
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3 text-rose-400">P10 (Downside)</th>
                  <th className="py-2.5 px-3 text-theme-text font-bold">P50 (Expected)</th>
                  <th className="py-2.5 px-3 text-[#8A9A78]">P90 (Upside)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-theme-border/50">
                {simulation.percentile_paths
                  .filter((_, idx) => idx % Math.max(1, Math.floor(simulation.horizon_days / 10)) === 0)
                  .map((point) => (
                    <tr key={point.day} className="hover:bg-theme-secondary/40 transition-colors">
                      <td className="py-2.5 px-3 font-semibold text-theme-text">Day {point.day}</td>
                      <td className="py-2.5 px-3 text-theme-textMuted">{point.date}</td>
                      <td className="py-2.5 px-3 text-rose-400 font-medium">
                        {formatCurrency(point.p10, currency)}
                      </td>
                      <td className="py-2.5 px-3 font-bold text-theme-text">
                        {formatCurrency(point.p50, currency)}
                      </td>
                      <td className="py-2.5 px-3 text-[#8A9A78] font-medium">
                        {formatCurrency(point.p90, currency)}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
