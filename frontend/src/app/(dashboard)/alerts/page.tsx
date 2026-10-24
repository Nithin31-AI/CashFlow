"use client";

import React, { useState, useEffect } from "react";
import {
  Bell,
  AlertTriangle,
  ShieldAlert,
  CheckCircle2,
  Clock,
  Filter,
  RefreshCw,
  Plus,
  X,
  Check,
  Eye,
  Sliders,
  Info
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { api, AlertRule, AlertEvent } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

export default function AlertsPage() {
  const { currentBusiness } = useAuth();

  const [rules, setRules] = useState<AlertRule[]>([]);
  const [events, setEvents] = useState<AlertEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Filter state
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [showResolved, setShowResolved] = useState(false);

  // New Rule Modal
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [ruleName, setRuleName] = useState("");
  const [ruleCategory, setRuleCategory] = useState("RESERVE_BREACH");
  const [ruleThreshold, setRuleThreshold] = useState<number>(10000);
  const [ruleSeverity, setRuleSeverity] = useState("WARNING");
  const [ruleSuppressionHours, setRuleSuppressionHours] = useState<number>(24);

  const loadData = async () => {
    if (!currentBusiness) return;
    setIsLoading(true);
    setError(null);
    try {
      const [rulesRes, eventsRes] = await Promise.all([
        api.listAlertRules(currentBusiness.id),
        api.listAlertEvents(currentBusiness.id),
      ]);
      setRules(Array.isArray(rulesRes) ? rulesRes : []);
      setEvents(Array.isArray(eventsRes) ? eventsRes : []);
    } catch (err: any) {
      setError(err.message || "Failed to load financial alerts data.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [currentBusiness]);

  const handleEvaluate = async () => {
    if (!currentBusiness) return;
    setIsEvaluating(true);
    setError(null);
    try {
      const res = await api.evaluateAlerts(currentBusiness.id);
      setSuccessMsg(`Evaluated alert rules: ${res.triggered_count} events triggered or updated.`);
      loadData();
    } catch (err: any) {
      setError(err.message || "Failed to trigger alert evaluation.");
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleAcknowledge = async (eventId: string) => {
    if (!currentBusiness) return;
    try {
      await api.acknowledgeAlert(currentBusiness.id, eventId);
      setEvents((prev) =>
        Array.isArray(prev) ? prev.map((e) => (e.id === eventId ? { ...e, is_acknowledged: true } : e)) : []
      );
    } catch (err: any) {
      setError(err.message || "Failed to acknowledge alert.");
    }
  };

  const handleResolve = async (eventId: string) => {
    if (!currentBusiness) return;
    try {
      await api.resolveAlert(currentBusiness.id, eventId);
      setEvents((prev) =>
        Array.isArray(prev) ? prev.map((e) => (e.id === eventId ? { ...e, is_resolved: true } : e)) : []
      );
    } catch (err: any) {
      setError(err.message || "Failed to resolve alert.");
    }
  };

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentBusiness) return;
    try {
      await api.createAlertRule(currentBusiness.id, {
        name: ruleName,
        category: ruleCategory,
        threshold_value: Number(ruleThreshold),
        severity: ruleSeverity,
        suppression_window_hours: Number(ruleSuppressionHours),
      });
      setShowRuleModal(false);
      setRuleName("");
      setSuccessMsg("Alert rule created successfully.");
      loadData();
    } catch (err: any) {
      setError(err.message || "Failed to create alert rule.");
    }
  };

  // Filter events
  const safeEvents = Array.isArray(events) ? events : [];
  const filteredEvents = safeEvents.filter((ev) => {
    if (!ev) return false;
    if (!showResolved && ev.is_resolved) return false;
    if (severityFilter !== "ALL" && ev.severity !== severityFilter) return false;
    return true;
  });

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[var(--color-sage)]/10 text-[var(--color-sage)] border border-[var(--color-sage)]/20">
              Automated Sentinel
            </span>
            <span className="text-xs text-[var(--foreground)]/50">Liquidity & Breach Monitoring</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Financial Alerts</h1>
          <p className="text-sm text-[var(--foreground)]/70 mt-1">
            Configurable liquidity thresholds, overdue debt alarms, and duplicate suppression.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => setShowRuleModal(true)}
            className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg border border-[var(--border)] hover:bg-[var(--foreground)]/5 transition"
          >
            <Plus className="w-4 h-4 text-[var(--color-sage)]" />
            New Alert Rule
          </button>
          <button
            onClick={handleEvaluate}
            disabled={isEvaluating}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-[var(--color-sage)] text-white hover:opacity-95 transition shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isEvaluating ? "animate-spin" : ""}`} />
            {isEvaluating ? "Evaluating..." : "Evaluate Alerts Now"}
          </button>
        </div>
      </div>

      {/* Messages */}
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

      {/* Active Events Section */}
      <div className="spatial-card rounded-2xl p-6 border border-[var(--border)]">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-[var(--color-sage)]" />
            <h2 className="text-lg font-semibold">Alert Activity Stream</h2>
            <span className="text-xs text-[var(--foreground)]/60">
              ({filteredEvents.length} {filteredEvents.length === 1 ? "event" : "events"})
            </span>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1 text-xs">
              <span className="text-[var(--foreground)]/60">Severity:</span>
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="px-2 py-1 rounded-lg border border-[var(--border)] bg-[var(--card-bg)] text-xs focus:outline-none"
              >
                <option value="ALL">All Severities</option>
                <option value="CRITICAL">Critical Only</option>
                <option value="WARNING">Warning</option>
                <option value="INFO">Info</option>
              </select>
            </div>

            <label className="flex items-center gap-1.5 text-xs text-[var(--foreground)]/70 cursor-pointer ml-2">
              <input
                type="checkbox"
                checked={showResolved}
                onChange={(e) => setShowResolved(e.target.checked)}
                className="rounded border-[var(--border)] text-[var(--color-sage)] focus:ring-[var(--color-sage)]"
              />
              <span>Show Resolved</span>
            </label>
          </div>
        </div>

        {filteredEvents.length === 0 ? (
          <div className="text-center py-10 border border-dashed border-[var(--border)] rounded-xl">
            <CheckCircle2 className="w-10 h-10 mx-auto mb-2 text-[var(--color-sage)] opacity-50" />
            <p className="text-sm font-semibold">No active alert events</p>
            <p className="text-xs text-[var(--foreground)]/50 mt-1">
              Your accounts and cash flows are currently within defined threshold tolerances.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredEvents.map((ev) => (
              <div
                key={ev.id}
                className={`p-5 rounded-xl border transition ${
                  ev.is_resolved
                    ? "border-[var(--border)]/40 bg-[var(--card-bg)]/40 opacity-60"
                    : ev.severity === "CRITICAL"
                    ? "border-red-500/30 bg-red-500/[0.02]"
                    : "border-[var(--border)] bg-[var(--card-bg)]"
                }`}
              >
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                          ev.severity === "CRITICAL"
                            ? "bg-red-500/10 text-red-500 border-red-500/20"
                            : ev.severity === "WARNING"
                            ? "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"
                            : "bg-[var(--color-sage)]/10 text-[var(--color-sage)] border-[var(--color-sage)]/20"
                        }`}
                      >
                        {ev.severity || "INFO"}
                      </span>
                      <span className="text-xs font-semibold uppercase tracking-wider text-[var(--foreground)]/50">
                        {typeof ev.category === "string" ? ev.category.replace(/_/g, " ") : "ALERT"}
                      </span>
                      <span className="text-xs text-[var(--foreground)]/40">•</span>
                      <span className="text-xs text-[var(--foreground)]/50">
                        {ev.created_at ? new Date(ev.created_at).toLocaleString() : "Recently"}
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-[var(--foreground)] mb-1">
                      {ev.title || "Notification"}
                    </h3>
                    <p className="text-sm text-[var(--foreground)]/80 leading-relaxed">
                      {ev.message || "No description provided."}
                    </p>

                    {/* Financial Evidence */}
                    {ev.financial_evidence && typeof ev.financial_evidence === "object" && !Array.isArray(ev.financial_evidence) && Object.keys(ev.financial_evidence).length > 0 && (
                      <div className="mt-3 p-3 rounded-lg bg-[var(--foreground)]/5 text-xs text-[var(--foreground)]/70 flex flex-wrap gap-x-6 gap-y-1">
                        {Object.entries(ev.financial_evidence).map(([key, val]) => (
                          <div key={key}>
                            <span className="text-[var(--foreground)]/50 capitalize">
                              {typeof key === "string" ? key.replace(/_/g, " ") : String(key)}:{" "}
                            </span>
                            <span className="font-semibold text-[var(--foreground)]">
                              {typeof val === "number" ? val.toLocaleString() : String(val ?? "")}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Actions & Status */}
                  <div className="flex md:flex-col items-center md:items-end justify-between gap-2 min-w-[140px]">
                    <div className="flex items-center gap-2">
                      {ev.is_resolved ? (
                        <span className="text-xs text-[var(--color-sage)] font-semibold flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Resolved
                        </span>
                      ) : ev.is_acknowledged ? (
                        <span className="text-xs text-yellow-500 font-semibold flex items-center gap-1">
                          <Eye className="w-3.5 h-3.5" /> Acknowledged
                        </span>
                      ) : (
                        <span className="text-xs text-red-500 font-semibold flex items-center gap-1">
                          <AlertTriangle className="w-3.5 h-3.5" /> Open
                        </span>
                      )}
                    </div>

                    {!ev.is_resolved && (
                      <div className="flex items-center gap-2">
                        {!ev.is_acknowledged && (
                          <button
                            onClick={() => handleAcknowledge(ev.id)}
                            className="px-2.5 py-1 text-xs font-medium rounded-lg border border-[var(--border)] hover:bg-[var(--foreground)]/5 transition text-[var(--foreground)]/70"
                          >
                            Acknowledge
                          </button>
                        )}
                        <button
                          onClick={() => handleResolve(ev.id)}
                          className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-[var(--color-sage)] text-white hover:opacity-90 transition"
                        >
                          Resolve
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

      {/* Alert Rules Management Section */}
      <div className="spatial-card rounded-2xl p-6 border border-[var(--border)]">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-[var(--color-sage)]" />
            <h2 className="text-lg font-semibold">Configured Alert Rules</h2>
          </div>
          <button
            onClick={() => setShowRuleModal(true)}
            className="text-xs font-medium text-[var(--color-sage)] hover:underline flex items-center gap-1"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Rule
          </button>
        </div>

        {rules.length === 0 ? (
          <div className="text-center py-6 text-[var(--foreground)]/60 text-xs">
            No rules configured. Default system triggers apply automatically.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[var(--border)] text-[var(--foreground)]/60 uppercase">
                  <th className="py-2.5 px-3">Rule Name</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Threshold</th>
                  <th className="py-2.5 px-3">Severity</th>
                  <th className="py-2.5 px-3">Suppression</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]/40">
                {rules.map((r) => (
                  <tr key={r.id} className="hover:bg-[var(--foreground)]/[0.02] transition">
                    <td className="py-3 px-3 font-semibold text-[var(--foreground)]">{r.name}</td>
                    <td className="py-3 px-3 uppercase text-[var(--foreground)]/70">
                      {typeof r.category === "string" ? r.category.replace(/_/g, " ") : "GENERAL"}
                    </td>
                    <td className="py-3 px-3 font-mono font-medium">
                      {r.category === "RESERVE_BREACH"
                        ? formatCurrency(r.threshold_value, currentBusiness?.currency)
                        : r.threshold_value}
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                          r.severity === "CRITICAL"
                            ? "bg-red-500/10 text-red-500 border-red-500/20"
                            : r.severity === "WARNING"
                            ? "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"
                            : "bg-[var(--color-sage)]/10 text-[var(--color-sage)] border-[var(--color-sage)]/20"
                        }`}
                      >
                        {r.severity}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-[var(--foreground)]/60">
                      {r.suppression_window_hours} hours
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`inline-block w-2 h-2 rounded-full mr-1.5 ${
                          r.is_active ? "bg-[var(--color-sage)]" : "bg-neutral-400"
                        }`}
                      />
                      <span className="text-[var(--foreground)]/70">
                        {r.is_active ? "Active" : "Disabled"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* MODAL: Create Alert Rule */}
      {showRuleModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="spatial-card bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">Configure Alert Rule</h3>
              <button
                onClick={() => setShowRuleModal(false)}
                className="p-1 rounded-lg hover:bg-[var(--foreground)]/10 text-[var(--foreground)]/60"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateRule} className="space-y-4">
              <div>
                <label className="text-xs font-semibold block mb-1">Rule Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Critical Cash Runway Warning"
                  value={ruleName}
                  onChange={(e) => setRuleName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-transparent text-sm focus:outline-none focus:border-[var(--color-sage)]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold block mb-1">Category</label>
                  <select
                    value={ruleCategory}
                    onChange={(e) => setRuleCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--card-bg)] text-sm focus:outline-none focus:border-[var(--color-sage)]"
                  >
                    <option value="RESERVE_BREACH">Reserve Breach</option>
                    <option value="OVERDUE_INVOICE">Overdue Invoices</option>
                    <option value="UNUSUAL_EXPENSE">Unusual Expense</option>
                    <option value="MAJOR_OBLIGATION">Major Obligation</option>
                    <option value="FORECAST_DROP">Forecast Drop</option>
                    <option value="STALE_DATA">Stale Data</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold block mb-1">Severity</label>
                  <select
                    value={ruleSeverity}
                    onChange={(e) => setRuleSeverity(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--card-bg)] text-sm focus:outline-none focus:border-[var(--color-sage)]"
                  >
                    <option value="WARNING">Warning</option>
                    <option value="CRITICAL">Critical</option>
                    <option value="INFO">Info</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold block mb-1">Threshold Value</label>
                  <input
                    type="number"
                    required
                    value={ruleThreshold}
                    onChange={(e) => setRuleThreshold(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-transparent text-sm focus:outline-none focus:border-[var(--color-sage)]"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold block mb-1">Suppression Window (Hrs)</label>
                  <input
                    type="number"
                    min="1"
                    max="168"
                    value={ruleSuppressionHours}
                    onChange={(e) => setRuleSuppressionHours(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-transparent text-sm focus:outline-none focus:border-[var(--color-sage)]"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowRuleModal(false)}
                  className="px-4 py-2 text-sm rounded-lg border border-[var(--border)] hover:bg-[var(--foreground)]/5 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-semibold rounded-lg bg-[var(--color-sage)] text-white hover:opacity-90 transition"
                >
                  Save Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
