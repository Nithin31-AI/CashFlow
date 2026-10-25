"use client";

import React, { useState, useEffect } from "react";
import {
  Compass,
  Target,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Plus,
  RefreshCw,
  Info,
  Layers,
  ArrowRight,
  TrendingUp,
  DollarSign,
  Calendar,
  Check,
  X,
  Shield,
  HelpCircle
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import {
  api,
  FinancialGoal,
  SavedScenario,
  OptimisationPlan,
  FinancialRecommendation
} from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

export default function DecisionsPage() {
  const { currentBusiness } = useAuth();

  // State
  const [goals, setGoals] = useState<FinancialGoal[]>([]);
  const [scenarios, setScenarios] = useState<SavedScenario[]>([]);
  const [optimisation, setOptimisation] = useState<OptimisationPlan | null>(null);
  const [recommendations, setRecommendations] = useState<FinancialRecommendation[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isOptimising, setIsOptimising] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Modals
  const [showGoalModal, setShowGoalModal] = useState(false);
  const [showScenarioModal, setShowScenarioModal] = useState(false);

  // New Goal Form
  const [goalName, setGoalName] = useState("");
  const [goalType, setGoalType] = useState("MIN_CASH_BUFFER");
  const [goalAmount, setGoalAmount] = useState<number>(10000);
  const [goalDate, setGoalDate] = useState("");
  const [isHardConstraint, setIsHardConstraint] = useState(true);
  const [goalPriority, setGoalPriority] = useState(1);
  const [goalNotes, setGoalNotes] = useState("");

  // New Scenario Form
  const [scenarioName, setScenarioName] = useState("");
  const [scenarioDesc, setScenarioDesc] = useState("");
  const [receivableDelayDays, setReceivableDelayDays] = useState(14);
  const [collectionRatePercent, setCollectionRatePercent] = useState(85);
  const [expenseMultiplier, setExpenseMultiplier] = useState(1.0);
  const [oneOffCapex, setOneOffCapex] = useState(0);

  // User confirmation checkboxes for optimisation plan
  const [confirmedActions, setConfirmedActions] = useState<Record<number, boolean>>({});

  const loadData = async () => {
    if (!currentBusiness) return;
    setIsLoading(true);
    setError(null);
    try {
      const [goalsRes, scenariosRes, recsRes] = await Promise.all([
        api.listGoals(currentBusiness.id),
        api.listScenarios(currentBusiness.id),
        api.listRecommendations(currentBusiness.id),
      ]);
      setGoals(goalsRes);
      setScenarios(scenariosRes);
      setRecommendations(recsRes);
    } catch (err: any) {
      setError(err.message || "Failed to load decision intelligence data.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [currentBusiness]);

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentBusiness) return;
    try {
      await api.createGoal(currentBusiness.id, {
        name: goalName,
        goal_type: goalType,
        target_amount: Number(goalAmount),
        target_date: goalDate ? new Date(goalDate).toISOString() : undefined,
        is_hard_constraint: isHardConstraint,
        priority: Number(goalPriority),
        notes: goalNotes || undefined,
      });
      setShowGoalModal(false);
      setGoalName("");
      setGoalNotes("");
      setSuccessMsg("Financial goal successfully saved.");
      loadData();
    } catch (err: any) {
      setError(err.message || "Failed to create financial goal.");
    }
  };

  const handleCreateScenario = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentBusiness) return;
    try {
      await api.createScenario(currentBusiness.id, {
        name: scenarioName,
        description: scenarioDesc || undefined,
        receivable_delay_days: Number(receivableDelayDays),
        collection_rate_pct: Number(collectionRatePercent),
        expense_multiplier: Number(expenseMultiplier),
        one_off_capex: Number(oneOffCapex),
      });
      setShowScenarioModal(false);
      setScenarioName("");
      setScenarioDesc("");
      setSuccessMsg("Scenario evaluated and saved successfully.");
      loadData();
    } catch (err: any) {
      setError(err.message || "Failed to create scenario.");
    }
  };

  const handleRunOptimisation = async () => {
    if (!currentBusiness) return;
    setIsOptimising(true);
    setError(null);
    try {
      const plan = await api.runOptimisation(currentBusiness.id);
      setOptimisation(plan);
      setConfirmedActions({});
      setSuccessMsg("Decision optimisation completed. Review recommended actions below.");
    } catch (err: any) {
      setError(err.message || "Failed to solve constrained optimisation.");
    } finally {
      setIsOptimising(false);
    }
  };

  const handleRecommendationStatus = async (
    recId: string,
    status: "ACCEPTED" | "DISMISSED"
  ) => {
    if (!currentBusiness) return;
    try {
      await api.updateRecommendationStatus(currentBusiness.id, recId, status);
      setRecommendations((prev) =>
        prev.map((r) => (r.id === recId ? { ...r, status } : r))
      );
    } catch (err: any) {
      setError(err.message || "Failed to update recommendation status.");
    }
  };

  const toggleActionConfirmation = (index: number) => {
    setConfirmedActions((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[var(--color-sage)]/10 text-[var(--color-sage)] border border-[var(--color-sage)]/20">
              AI Decision Intelligence
            </span>
            <span className="text-xs text-[var(--foreground)]/50">Autonomous Solver</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
            Financial Decisions & Scenarios
          </h1>
          <p className="text-sm text-[var(--foreground)]/70 mt-1">
            Constrained decision optimisation, interactive scenario modeling, and grounded advisory plans.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => setShowGoalModal(true)}
            className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg border border-[var(--border)] hover:bg-[var(--foreground)]/5 transition"
          >
            <Plus className="w-4 h-4 text-[var(--color-sage)]" />
            Add Goal
          </button>
          <button
            onClick={() => setShowScenarioModal(true)}
            className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg border border-[var(--border)] hover:bg-[var(--foreground)]/5 transition"
          >
            <Sliders className="w-4 h-4 text-[var(--color-sage)]" />
            New Scenario
          </button>
          <button
            onClick={handleRunOptimisation}
            disabled={isOptimising}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-[var(--color-sage)] text-white hover:opacity-95 transition shadow-sm disabled:opacity-50"
          >
            <Compass className={`w-4 h-4 ${isOptimising ? "animate-spin" : ""}`} />
            {isOptimising ? "Optimising..." : "Run Optimiser"}
          </button>
        </div>
      </div>

      {/* Alerts / Feedback */}
      {error && (
        <div className="p-4 rounded-xl border border-red-500/20 bg-red-500/10 text-red-500 text-sm flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {successMsg && (
        <div className="p-4 rounded-xl border border-[var(--color-sage)]/30 bg-[var(--color-sage)]/10 text-[var(--color-sage)] text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="opacity-70 hover:opacity-100">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* SECTION 1: Goals and Constraints */}
      <div className="spatial-card rounded-2xl p-6 border border-[var(--border)]">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-[var(--color-sage)]" />
            <h2 className="text-lg font-semibold">Business Financial Goals & Constraints</h2>
          </div>
          <span className="text-xs text-[var(--foreground)]/60">
            {goals.length} defined {goals.length === 1 ? "goal" : "goals"}
          </span>
        </div>

        {goals.length === 0 ? (
          <div className="text-center py-8 text-[var(--foreground)]/60 border border-dashed border-[var(--border)] rounded-xl">
            <Target className="w-8 h-8 mx-auto mb-2 opacity-40 text-[var(--color-sage)]" />
            <p className="text-sm font-medium">No business goals or constraints defined yet.</p>
            <p className="text-xs text-[var(--foreground)]/50 mt-1 max-w-md mx-auto">
              Define a minimum cash buffer, target savings amount, or maximum overdue days to guide the optimisation solver.
            </p>
            <button
              onClick={() => setShowGoalModal(true)}
              className="mt-3 px-3 py-1.5 text-xs font-medium rounded-lg bg-[var(--color-sage)] text-white hover:opacity-90 transition"
            >
              Add First Goal
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {goals.map((goal) => (
              <div
                key={goal.id}
                className="p-4 rounded-xl border border-[var(--border)] bg-[var(--card-bg)] flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-[var(--foreground)]/60">
                      {goal.goal_type.replace(/_/g, " ")}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                        goal.is_hard_constraint
                          ? "bg-red-500/10 text-red-500 border-red-500/20"
                          : "bg-[var(--color-sage)]/10 text-[var(--color-sage)] border-[var(--color-sage)]/20"
                      }`}
                    >
                      {goal.is_hard_constraint ? "Hard Constraint" : "Soft Target"}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-[var(--foreground)]">{goal.name}</h3>
                  <div className="text-2xl font-black mt-2 text-[var(--color-sage)]">
                    {formatCurrency(goal.target_amount, currentBusiness?.currency)}
                  </div>
                  {goal.notes && (
                    <p className="text-xs text-[var(--foreground)]/60 mt-2 line-clamp-2">
                      {goal.notes}
                    </p>
                  )}
                </div>
                <div className="mt-4 pt-3 border-t border-[var(--border)]/50 flex items-center justify-between text-xs text-[var(--foreground)]/50">
                  <span>Priority #{goal.priority}</span>
                  <span className="capitalize">{goal.status.toLowerCase()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* SECTION 2: Scenarios Comparison */}
      <div className="spatial-card rounded-2xl p-6 border border-[var(--border)]">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-[var(--color-sage)]" />
            <h2 className="text-lg font-semibold">Scenario Comparison & Impact Analysis</h2>
          </div>
          <button
            onClick={() => setShowScenarioModal(true)}
            className="text-xs font-medium text-[var(--color-sage)] hover:underline flex items-center gap-1"
          >
            <Plus className="w-3.5 h-3.5" />
            Create Custom Scenario
          </button>
        </div>

        {scenarios.length === 0 ? (
          <div className="text-center py-8 text-[var(--foreground)]/60 border border-dashed border-[var(--border)] rounded-xl">
            <Layers className="w-8 h-8 mx-auto mb-2 opacity-40 text-[var(--color-sage)]" />
            <p className="text-sm font-medium">No saved scenarios.</p>
            <p className="text-xs text-[var(--foreground)]/50 mt-1">
              Create a scenario to simulate delayed collections, increased costs, or one-off investments.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {scenarios.map((sc) => (
              <div
                key={sc.id}
                className={`p-5 rounded-xl border flex flex-col justify-between ${
                  sc.is_baseline
                    ? "border-[var(--color-sage)] bg-[var(--color-sage)]/5"
                    : "border-[var(--border)] bg-[var(--card-bg)]"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-base flex items-center gap-2">
                      {sc.name}
                      {sc.is_baseline && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-[var(--color-sage)] text-white">
                          Baseline
                        </span>
                      )}
                    </span>
                  </div>
                  {sc.description && (
                    <p className="text-xs text-[var(--foreground)]/60 mb-4">{sc.description}</p>
                  )}

                  {/* Metrics Table */}
                  <div className="space-y-2 mt-4 text-xs">
                    <div className="flex justify-between py-1.5 border-b border-[var(--border)]/40">
                      <span className="text-[var(--foreground)]/60">Projected Ending Cash</span>
                      <span className="font-semibold text-[var(--foreground)]">
                        {formatCurrency(sc.projected_ending_cash, currentBusiness?.currency)}
                      </span>
                    </div>
                    <div className="flex justify-between py-1.5 border-b border-[var(--border)]/40">
                      <span className="text-[var(--foreground)]/60">Minimum Projected Cash</span>
                      <span className="font-semibold text-[var(--foreground)]">
                        {formatCurrency(sc.min_cash, currentBusiness?.currency)}
                      </span>
                    </div>
                    <div className="flex justify-between py-1.5 border-b border-[var(--border)]/40">
                      <span className="text-[var(--foreground)]/60">Shortage Risk</span>
                      <span
                        className={`font-semibold ${
                          Number.isFinite(Number(sc.shortage_risk_percent)) && Number(sc.shortage_risk_percent) > 30
                            ? "text-red-500"
                            : "text-[var(--color-sage)]"
                        }`}
                      >
                        {Number.isFinite(Number(sc.shortage_risk_percent))
                          ? `${Number(sc.shortage_risk_percent).toFixed(1)}%`
                          : "0.0%"}
                      </span>
                    </div>
                    <div className="flex justify-between py-1.5 border-b border-[var(--border)]/40">
                      <span className="text-[var(--foreground)]/60">Estimated Runway</span>
                      <span className="font-semibold text-[var(--foreground)]">
                        {Number.isFinite(Number(sc.runway_days))
                          ? Number(sc.runway_days) >= 365
                            ? "365+ days"
                            : `${sc.runway_days} days`
                          : "N/A"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Parameter Tags */}
                {sc.parameters && Object.keys(sc.parameters).length > 0 && (
                  <div className="mt-4 pt-3 border-t border-[var(--border)]/50 flex flex-wrap gap-1.5">
                    {sc.parameters.receivable_delay_days !== undefined && (
                      <span className="px-2 py-0.5 rounded bg-[var(--foreground)]/5 text-[10px] text-[var(--foreground)]/70">
                        Delay: +{sc.parameters.receivable_delay_days}d
                      </span>
                    )}
                    {(sc.parameters.collection_rate_percent !== undefined || sc.parameters.collection_rate_pct !== undefined) && (
                      <span className="px-2 py-0.5 rounded bg-[var(--foreground)]/5 text-[10px] text-[var(--foreground)]/70">
                        Collect: {sc.parameters.collection_rate_percent ?? sc.parameters.collection_rate_pct}%
                      </span>
                    )}
                    {(sc.parameters.expense_growth_multiplier !== undefined || sc.parameters.expense_multiplier !== undefined) && (
                      <span className="px-2 py-0.5 rounded bg-[var(--foreground)]/5 text-[10px] text-[var(--foreground)]/70">
                        Expense: {sc.parameters.expense_growth_multiplier ?? sc.parameters.expense_multiplier}x
                      </span>
                    )}
                    {Number(sc.parameters.one_off_capex) > 0 && (
                      <span className="px-2 py-0.5 rounded bg-[var(--foreground)]/5 text-[10px] text-[var(--foreground)]/70">
                        CapEx: {formatCurrency(sc.parameters.one_off_capex, currentBusiness?.currency)}
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* SECTION 3: Constrained Decision Optimisation Plan */}
      <div className="spatial-card rounded-2xl p-6 border border-[var(--border)]">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-6">
          <div>
            <div className="flex items-center gap-2">
              <Compass className="w-5 h-5 text-[var(--color-sage)]" />
              <h2 className="text-lg font-semibold">Decision Optimisation Plan</h2>
              {optimisation && (
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${
                    optimisation.status === "FEASIBLE"
                      ? "bg-[var(--color-sage)]/10 text-[var(--color-sage)] border-[var(--color-sage)]/20"
                      : optimisation.status === "PARTIALLY_FEASIBLE"
                      ? "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"
                      : "bg-red-500/10 text-red-500 border-red-500/20"
                  }`}
                >
                  {optimisation.status}
                </span>
              )}
            </div>
            <p className="text-xs text-[var(--foreground)]/60 mt-1">
              Linear constrained solver balancing cash preservation against operating goals.
            </p>
          </div>

          <button
            onClick={handleRunOptimisation}
            disabled={isOptimising}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--color-sage)] text-white hover:opacity-95 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isOptimising ? "animate-spin" : ""}`} />
            Re-solve Constraints
          </button>
        </div>

        {!optimisation ? (
          <div className="text-center py-10 border border-dashed border-[var(--border)] rounded-xl">
            <Compass className="w-10 h-10 mx-auto mb-2 opacity-30 text-[var(--color-sage)]" />
            <p className="text-sm font-medium">No optimisation plan generated yet.</p>
            <p className="text-xs text-[var(--foreground)]/50 mt-1 max-w-sm mx-auto">
              Click &quot;Run Optimiser&quot; to compute the mathematically optimal financial trajectory honoring your hard constraints.
            </p>
            <button
              onClick={handleRunOptimisation}
              disabled={isOptimising}
              className="mt-4 px-4 py-2 text-xs font-medium rounded-lg bg-[var(--color-sage)] text-white hover:opacity-90 transition"
            >
              Run Constrained Optimiser
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Status & Trade-offs Bar */}
            <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--foreground)]/[0.02] flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <span className="text-xs text-[var(--foreground)]/60 block mb-0.5">Objective Value</span>
                <span className="text-xl font-black text-[var(--foreground)]">
                  {formatCurrency(optimisation.objective_value, currentBusiness?.currency)}
                </span>
              </div>
              <div>
                <span className="text-xs text-[var(--foreground)]/60 block mb-0.5">Hard Constraints</span>
                <span
                  className={`text-sm font-bold flex items-center gap-1 ${
                    optimisation.hard_constraints_satisfied ? "text-[var(--color-sage)]" : "text-red-500"
                  }`}
                >
                  {optimisation.hard_constraints_satisfied ? (
                    <>
                      <CheckCircle2 className="w-4 h-4" /> All Hard Constraints Satisfied
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="w-4 h-4" /> Hard Constraints Breached
                    </>
                  )}
                </span>
              </div>
              {optimisation.trade_offs && (
                <div className="max-w-md text-xs text-[var(--foreground)]/70">
                  <span className="font-semibold text-[var(--foreground)] block">Key Trade-off:</span>
                  {optimisation.trade_offs}
                </div>
              )}
            </div>

            {/* Recommended Actions Table */}
            <div>
              <h3 className="text-sm font-bold mb-3 flex items-center gap-2">
                <span>Recommended Action Sequence</span>
                <span className="text-xs font-normal text-[var(--foreground)]/50">
                  (Requires explicit owner confirmation)
                </span>
              </h3>

              <div className="space-y-3">
                {optimisation.recommended_actions.map((act: any, idx: number) => {
                  const isChecked = !!confirmedActions[idx];
                  return (
                    <div
                      key={idx}
                      onClick={() => toggleActionConfirmation(idx)}
                      className={`p-4 rounded-xl border cursor-pointer transition flex items-start gap-4 ${
                        isChecked
                          ? "border-[var(--color-sage)] bg-[var(--color-sage)]/5"
                          : "border-[var(--border)] bg-[var(--card-bg)] hover:border-[var(--color-sage)]/40"
                      }`}
                    >
                      <div className="mt-0.5">
                        <div
                          className={`w-5 h-5 rounded flex items-center justify-center border transition ${
                            isChecked
                              ? "bg-[var(--color-sage)] border-[var(--color-sage)] text-white"
                              : "border-[var(--border)] bg-[var(--card-bg)]"
                          }`}
                        >
                          {isChecked && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                        </div>
                      </div>

                      <div className="flex-1">
                        <div className="flex items-center justify-between gap-2">
                          <h4 className="font-semibold text-sm text-[var(--foreground)]">
                            {act.action || act.title || `Action #${idx + 1}`}
                          </h4>
                          {act.impact !== undefined && (
                            <span className="font-bold text-xs text-[var(--color-sage)]">
                              +{formatCurrency(act.impact, currentBusiness?.currency)}
                            </span>
                          )}
                        </div>
                        {act.timing && (
                          <div className="text-xs text-[var(--foreground)]/50 mt-1 flex items-center gap-1">
                            <Calendar className="w-3.5 h-3.5" />
                            <span>Timing: {act.timing}</span>
                          </div>
                        )}
                        {act.trade_off && (
                          <p className="text-xs text-[var(--foreground)]/70 mt-2 bg-[var(--foreground)]/5 p-2 rounded">
                            <span className="font-semibold">Trade-off: </span>
                            {act.trade_off}
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Advisory Disclaimer Notice */}
            <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--foreground)]/[0.02] flex items-start gap-3">
              <Shield className="w-5 h-5 text-[var(--color-sage)] flex-shrink-0 mt-0.5" />
              <div className="text-xs text-[var(--foreground)]/70">
                <span className="font-bold text-[var(--foreground)] block mb-0.5">
                  Advisory-Only Financial Intelligence
                </span>
                Optimisation plans provide algorithmic decision support based on recorded financial history and stated constraints. Cash transfers, payment schedules, and credit lines require deliberate manual execution by authorized business administrators.
              </div>
            </div>
          </div>
        )}
      </div>

      {/* SECTION 4: Explainable Recommendations */}
      <div className="spatial-card rounded-2xl p-6 border border-[var(--border)]">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-[var(--color-sage)]" />
            <h2 className="text-lg font-semibold">Explainable Recommendations</h2>
          </div>
          <span className="text-xs text-[var(--foreground)]/60">
            {recommendations.filter((r) => r.status === "ACTIVE").length} active
          </span>
        </div>

        {recommendations.length === 0 ? (
          <div className="text-center py-8 text-[var(--foreground)]/60 border border-dashed border-[var(--border)] rounded-xl">
            <TrendingUp className="w-8 h-8 mx-auto mb-2 opacity-40 text-[var(--color-sage)]" />
            <p className="text-sm font-medium">No recommendations available.</p>
            <p className="text-xs text-[var(--foreground)]/50 mt-1">
              As invoices and transactions are processed, the AI recommendation engine will detect liquidity opportunities.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {recommendations.map((rec) => (
              <div
                key={rec.id}
                className={`p-5 rounded-xl border transition ${
                  rec.status === "ACTIVE"
                    ? "border-[var(--border)] bg-[var(--card-bg)]"
                    : "border-[var(--border)]/40 bg-[var(--card-bg)]/40 opacity-60"
                }`}
              >
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                          rec.severity === "CRITICAL"
                            ? "bg-red-500/10 text-red-500 border-red-500/20"
                            : rec.severity === "HIGH"
                            ? "bg-orange-500/10 text-orange-500 border-orange-500/20"
                            : "bg-[var(--color-sage)]/10 text-[var(--color-sage)] border-[var(--color-sage)]/20"
                        }`}
                      >
                        {rec.severity}
                      </span>
                      <span className="text-xs font-semibold uppercase tracking-wider text-[var(--foreground)]/50">
                        {rec.action_type.replace(/_/g, " ")}
                      </span>
                      <span className="text-xs text-[var(--foreground)]/40">•</span>
                      <span className="text-xs text-[var(--foreground)]/50">
                        Status: <strong className="capitalize">{rec.status.toLowerCase()}</strong>
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-[var(--foreground)] mb-1">
                      {rec.title}
                    </h3>
                    <p className="text-sm text-[var(--foreground)]/80 leading-relaxed">
                      {rec.reasoning}
                    </p>

                    {/* Financial Evidence & Disadvantages */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3 pt-3 border-t border-[var(--border)]/50 text-xs">
                      {rec.disadvantages && (
                        <div className="p-2.5 rounded bg-[var(--foreground)]/5 text-[var(--foreground)]/70">
                          <span className="font-semibold text-red-500 block mb-0.5">
                            Trade-offs & Disadvantages:
                          </span>
                          {rec.disadvantages}
                        </div>
                      )}
                      {rec.assumptions && (
                        <div className="p-2.5 rounded bg-[var(--foreground)]/5 text-[var(--foreground)]/70">
                          <span className="font-semibold text-[var(--color-sage)] block mb-0.5">
                            Underlying Assumptions:
                          </span>
                          {rec.assumptions}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Impact & Actions */}
                  <div className="flex flex-col md:items-end justify-between gap-3 min-w-[160px]">
                    <div>
                      <span className="text-xs text-[var(--foreground)]/50 block md:text-right">Estimated Impact</span>
                      <span className="text-lg font-black text-[var(--color-sage)] md:text-right block">
                        +{formatCurrency(rec.estimated_impact, currentBusiness?.currency)}
                      </span>
                    </div>

                    {rec.status === "ACTIVE" && (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleRecommendationStatus(rec.id, "DISMISSED")}
                          className="px-3 py-1.5 text-xs font-medium rounded-lg border border-[var(--border)] hover:bg-[var(--foreground)]/5 transition text-[var(--foreground)]/70"
                        >
                          Dismiss
                        </button>
                        <button
                          onClick={() => handleRecommendationStatus(rec.id, "ACCEPTED")}
                          className="px-3 py-1.5 text-xs font-medium rounded-lg bg-[var(--color-sage)] text-white hover:opacity-90 transition"
                        >
                          Accept
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* MODAL: Add Financial Goal */}
      {showGoalModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="spatial-card bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">Add Business Financial Goal</h3>
              <button
                onClick={() => setShowGoalModal(false)}
                className="p-1 rounded-lg hover:bg-[var(--foreground)]/10 text-[var(--foreground)]/60"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateGoal} className="space-y-4">
              <div>
                <label className="text-xs font-semibold block mb-1">Goal Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 60-Day Reserve Buffer"
                  value={goalName}
                  onChange={(e) => setGoalName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-transparent text-sm focus:outline-none focus:border-[var(--color-sage)]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold block mb-1">Goal Type</label>
                  <select
                    value={goalType}
                    onChange={(e) => setGoalType(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--card-bg)] text-sm focus:outline-none focus:border-[var(--color-sage)]"
                  >
                    <option value="MIN_CASH_BUFFER">Min Cash Buffer</option>
                    <option value="TARGET_SAVINGS">Target Savings</option>
                    <option value="DEBT_REDUCTION">Debt Reduction</option>
                    <option value="MAX_OVERDUE_DAYS">Max Overdue Days</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold block mb-1">Target Amount ({currentBusiness?.currency || "$" })</label>
                  <input
                    type="number"
                    required
                    min="0"
                    step="100"
                    value={goalAmount}
                    onChange={(e) => setGoalAmount(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-transparent text-sm focus:outline-none focus:border-[var(--color-sage)]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold block mb-1">Target Date (Optional)</label>
                  <input
                    type="date"
                    value={goalDate}
                    onChange={(e) => setGoalDate(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-transparent text-sm focus:outline-none focus:border-[var(--color-sage)]"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold block mb-1">Priority (1-5)</label>
                  <input
                    type="number"
                    min="1"
                    max="5"
                    value={goalPriority}
                    onChange={(e) => setGoalPriority(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-transparent text-sm focus:outline-none focus:border-[var(--color-sage)]"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="hardConstraint"
                  checked={isHardConstraint}
                  onChange={(e) => setIsHardConstraint(e.target.checked)}
                  className="rounded border-[var(--border)] text-[var(--color-sage)] focus:ring-[var(--color-sage)]"
                />
                <label htmlFor="hardConstraint" className="text-xs text-[var(--foreground)]/80 cursor-pointer">
                  Treat as <strong>Hard Constraint</strong> (must never be breached by optimiser)
                </label>
              </div>

              <div>
                <label className="text-xs font-semibold block mb-1">Notes & Context</label>
                <textarea
                  rows={2}
                  placeholder="e.g. Critical working capital requirement for payroll."
                  value={goalNotes}
                  onChange={(e) => setGoalNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-transparent text-sm focus:outline-none focus:border-[var(--color-sage)]"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowGoalModal(false)}
                  className="px-4 py-2 text-sm rounded-lg border border-[var(--border)] hover:bg-[var(--foreground)]/5 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-semibold rounded-lg bg-[var(--color-sage)] text-white hover:opacity-90 transition"
                >
                  Save Goal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Create Scenario */}
      {showScenarioModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="spatial-card bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl max-w-lg w-full p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">Create Custom Financial Scenario</h3>
              <button
                onClick={() => setShowScenarioModal(false)}
                className="p-1 rounded-lg hover:bg-[var(--foreground)]/10 text-[var(--foreground)]/60"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateScenario} className="space-y-4">
              <div>
                <label className="text-xs font-semibold block mb-1">Scenario Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 30-Day Delay + 15% CapEx Shock"
                  value={scenarioName}
                  onChange={(e) => setScenarioName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-transparent text-sm focus:outline-none focus:border-[var(--color-sage)]"
                />
              </div>

              <div>
                <label className="text-xs font-semibold block mb-1">Description (Optional)</label>
                <input
                  type="text"
                  placeholder="Simulates delayed client invoice settlements and equipment purchase."
                  value={scenarioDesc}
                  onChange={(e) => setScenarioDesc(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-transparent text-sm focus:outline-none focus:border-[var(--color-sage)]"
                />
              </div>

              {/* Sliders */}
              <div className="space-y-3 pt-2">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-semibold">Receivable Delay: +{receivableDelayDays} days</span>
                    <span className="text-[var(--foreground)]/50">0 to 60 days</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="60"
                    value={receivableDelayDays}
                    onChange={(e) => setReceivableDelayDays(Number(e.target.value))}
                    className="w-full accent-[var(--color-sage)] cursor-pointer"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-semibold">Collection Rate: {collectionRatePercent}%</span>
                    <span className="text-[var(--foreground)]/50">50% to 100%</span>
                  </div>
                  <input
                    type="range"
                    min="50"
                    max="100"
                    value={collectionRatePercent}
                    onChange={(e) => setCollectionRatePercent(Number(e.target.value))}
                    className="w-full accent-[var(--color-sage)] cursor-pointer"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-semibold">Expense Multiplier: {expenseMultiplier}x</span>
                    <span className="text-[var(--foreground)]/50">0.8x to 1.5x</span>
                  </div>
                  <input
                    type="range"
                    min="0.8"
                    max="1.5"
                    step="0.05"
                    value={expenseMultiplier}
                    onChange={(e) => setExpenseMultiplier(Number(e.target.value))}
                    className="w-full accent-[var(--color-sage)] cursor-pointer"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold block mb-1">
                    One-Off CapEx / Investment ({currentBusiness?.currency || "$"})
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="500"
                    value={oneOffCapex}
                    onChange={(e) => setOneOffCapex(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-transparent text-sm focus:outline-none focus:border-[var(--color-sage)]"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowScenarioModal(false)}
                  className="px-4 py-2 text-sm rounded-lg border border-[var(--border)] hover:bg-[var(--foreground)]/5 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-semibold rounded-lg bg-[var(--color-sage)] text-white hover:opacity-90 transition"
                >
                  Simulate & Save Scenario
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
