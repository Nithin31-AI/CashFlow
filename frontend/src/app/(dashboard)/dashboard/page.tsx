"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  UploadCloud,
  FileSpreadsheet,
  ArrowUpRight,
  ArrowDownRight,
  TrendingUp,
  Clock,
  ShieldCheck,
  Building2,
  AlertTriangle,
  Receipt,
  ArrowLeftRight,
  GitCompare,
  Loader2,
  Calendar,
  CheckCircle2,
  ChevronRight,
  Info,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import {
  api,
  FinancialOverview,
  ForecastResponse,
  RiskAssessmentItem,
  ExpenseAnomalyItem,
  InvoiceRecord,
  TransactionRecord,
} from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";

export default function DashboardPage() {
  const { currentBusiness } = useAuth();
  const [overview, setOverview] = useState<FinancialOverview | null>(null);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [risks, setRisks] = useState<RiskAssessmentItem[]>([]);
  const [anomalies, setAnomalies] = useState<ExpenseAnomalyItem[]>([]);
  const [invoices, setInvoices] = useState<InvoiceRecord[]>([]);
  const [transactions, setTransactions] = useState<TransactionRecord[]>([]);
  const [horizon, setHorizon] = useState<number>(30);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboardData() {
      if (!currentBusiness) return;
      setIsLoading(true);
      setError(null);
      try {
        const [ovData, fcData, rkData, anData, invData, txData] = await Promise.all([
          api.getFinancialOverview(currentBusiness.id).catch(() => null),
          api.getForecast(currentBusiness.id, horizon).catch(() => null),
          api.getRisks(currentBusiness.id, horizon).catch(() => []),
          api.getExpenseAnomalies(currentBusiness.id).catch(() => []),
          api.listInvoices(currentBusiness.id).catch(() => []),
          api.listTransactions(currentBusiness.id, { limit: 10 } as any).catch(() => []),
        ]);
        setOverview(ovData);
        setForecast(fcData);
        setRisks(rkData);
        setAnomalies(anData);
        setInvoices(invData);
        setTransactions(txData);
      } catch (err: any) {
        setError(err.message || "Failed to load financial records.");
      } finally {
        setIsLoading(false);
      }
    }
    loadDashboardData();
  }, [currentBusiness, horizon]);

  const currency = currentBusiness?.currency || "INR";

  if (isLoading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center">
        <Loader2 className="w-8 h-8 text-theme-sage animate-spin mb-4" />
        <p className="text-sm text-theme-textMuted">Consolidating financial intelligence...</p>
      </div>
    );
  }

  const actualCash = overview?.actual_cash_balance ?? 0;
  const reserveBuffer = overview?.minimum_cash_reserve ?? 100000;
  const headroom = overview?.reserve_headroom ?? actualCash - reserveBuffer;
  const receivables = overview?.outstanding_receivables ?? 0;
  const overdueReceivables = overview?.overdue_receivables ?? 0;
  const netIncome = overview?.net_income ?? 0;

  return (
    <div className="space-y-8 pb-16">
      {/* Top Welcome & Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-theme-sage/20 text-theme-sage border border-theme-sage/30">
              STAGE 2 FINANCIAL INTELLIGENCE
            </span>
            <span className="text-xs text-theme-textMuted font-medium">
              Currency: <strong className="text-theme-text">{currency} (₹)</strong>
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-theme-text">
            Financial Command Center
          </h1>
          <p className="text-xs sm:text-sm text-theme-textMuted mt-1">
            Authoritative cash balance, predictive runway, and explainable risk analysis.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            href="/invoices"
            className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-theme-surface hover:bg-theme-secondary text-theme-text border border-theme-border shadow-sm flex items-center gap-2 transition-all"
          >
            <Receipt className="w-3.5 h-3.5 text-theme-sage" />
            <span>Invoices</span>
          </Link>
          <Link
            href="/imports/new"
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-theme-sage hover:bg-theme-sageDark text-white shadow-sm flex items-center gap-2 transition-all"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Upload Statements</span>
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400 text-xs flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* SECTION 1: SPATIAL FINANCIAL POSITION CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Actual Cash */}
        <div className="spatial-card p-5">
          <div className="flex items-center justify-between text-xs font-semibold text-theme-textMuted mb-2">
            <span>Verified Liquid Cash</span>
            <ShieldCheck className="w-4 h-4 text-theme-sage" />
          </div>
          <p className="text-2xl sm:text-3xl font-black text-theme-text tracking-tight">
            {formatCurrency(actualCash, currency)}
          </p>
          <p className="text-[11px] text-theme-textMuted mt-2 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>
            Bank & on-hand liquid balances
          </p>
        </div>

        {/* Safety Buffer Headroom */}
        <div className="spatial-card p-5">
          <div className="flex items-center justify-between text-xs font-semibold text-theme-textMuted mb-2">
            <span>Reserve Headroom</span>
            <Building2 className="w-4 h-4 text-theme-textMuted" />
          </div>
          <p className={`text-2xl sm:text-3xl font-black tracking-tight ${headroom >= 0 ? "text-theme-text" : "text-red-500"}`}>
            {formatCurrency(headroom, currency)}
          </p>
          <p className="text-[11px] text-theme-textMuted mt-2">
            Min safety buffer: {formatCurrency(reserveBuffer, currency)}
          </p>
        </div>

        {/* Outstanding Receivables */}
        <div className="spatial-card p-5">
          <div className="flex items-center justify-between text-xs font-semibold text-theme-textMuted mb-2">
            <span>Outstanding Receivables</span>
            <Receipt className="w-4 h-4 text-amber-500" />
          </div>
          <p className="text-2xl sm:text-3xl font-black text-theme-text tracking-tight">
            {formatCurrency(receivables, currency)}
          </p>
          <p className="text-[11px] text-theme-textMuted mt-2">
            {overdueReceivables > 0 ? (
              <span className="text-red-500 font-semibold">
                {formatCurrency(overdueReceivables, currency)} overdue
              </span>
            ) : (
              "All customer invoices within due date"
            )}
          </p>
        </div>

        {/* Net Cash Flow */}
        <div className="spatial-card p-5">
          <div className="flex items-center justify-between text-xs font-semibold text-theme-textMuted mb-2">
            <span>Net Operating Cash Flow</span>
            {netIncome >= 0 ? (
              <ArrowUpRight className="w-4 h-4 text-emerald-500" />
            ) : (
              <ArrowDownRight className="w-4 h-4 text-red-500" />
            )}
          </div>
          <p className={`text-2xl sm:text-3xl font-black tracking-tight ${netIncome >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-red-500"}`}>
            {formatCurrency(netIncome, currency)}
          </p>
          <p className="text-[11px] text-theme-textMuted mt-2">
            Internal transfers excluded from totals
          </p>
        </div>
      </div>

      {/* SECTION 2: CASH-SHORTAGE RISK ALERTS */}
      {risks.length > 0 && (
        <div className="spatial-panel p-5 border-amber-500/30 bg-amber-500/5">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0" />
            <h2 className="text-sm font-bold text-theme-text tracking-wide uppercase">
              Predictive Cash Shortage Alerts
            </h2>
          </div>
          <div className="space-y-3">
            {risks.map((risk) => (
              <div
                key={risk.id}
                className="p-4 rounded-xl bg-theme-surface border border-theme-border flex flex-col md:flex-row md:items-center justify-between gap-3"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
                        risk.severity === "CRITICAL"
                          ? "bg-red-500 text-white"
                          : risk.severity === "HIGH"
                          ? "bg-orange-500/20 text-orange-600 dark:text-orange-400 border border-orange-500/30"
                          : "bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30"
                      }`}
                    >
                      {risk.severity} RISK
                    </span>
                    <h3 className="text-sm font-bold text-theme-text">{risk.title}</h3>
                  </div>
                  <p className="text-xs text-theme-textMuted mt-1">{risk.description}</p>
                  <p className="text-xs font-semibold text-theme-sage mt-2">
                    Recommendation: {risk.recommended_action}
                  </p>
                </div>
                {risk.estimated_shortfall && (
                  <div className="text-right shrink-0">
                    <span className="text-[10px] uppercase text-theme-textMuted block font-bold">Estimated Shortfall</span>
                    <span className="text-lg font-black text-red-500">
                      -{formatCurrency(risk.estimated_shortfall, currency)}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SECTION 3: CASH-FLOW FORECAST WIDGET */}
      <div className="spatial-panel p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-theme-sage" />
              <h2 className="text-base font-bold text-theme-text">Cash-Flow Projections</h2>
            </div>
            <p className="text-xs text-theme-textMuted mt-0.5">
              Based on verified historical burn rate and expected customer invoice collections.
            </p>
          </div>

          {/* Horizon Selector */}
          <div className="flex items-center gap-1.5 p-1 rounded-xl bg-theme-secondary border border-theme-border self-start sm:self-auto">
            {[7, 30, 90, 180, 365].map((h) => (
              <button
                key={h}
                onClick={() => setHorizon(h)}
                className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                  horizon === h
                    ? "bg-theme-surface text-theme-text shadow-sm"
                    : "text-theme-textMuted hover:text-theme-text"
                }`}
              >
                {h === 365 ? "12M" : h === 180 ? "6M" : `${h}D`}
              </button>
            ))}
          </div>
        </div>

        {forecast && forecast.daily_projections?.length > 0 ? (
          <div>
            {/* Forecast Summary Numbers */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3.5 rounded-xl bg-theme-secondary border border-theme-border mb-6">
              <div>
                <span className="text-[10px] font-semibold text-theme-textMuted block uppercase">Starting Cash</span>
                <span className="text-sm font-bold text-theme-text">{formatCurrency(forecast.starting_cash, currency)}</span>
              </div>
              <div>
                <span className="text-[10px] font-semibold text-theme-textMuted block uppercase">Expected Inflows</span>
                <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400">+{formatCurrency(forecast.projected_inflows, currency)}</span>
              </div>
              <div>
                <span className="text-[10px] font-semibold text-theme-textMuted block uppercase">Projected Burn</span>
                <span className="text-sm font-bold text-red-500">-{formatCurrency(forecast.projected_outflows, currency)}</span>
              </div>
              <div>
                <span className="text-[10px] font-semibold text-theme-textMuted block uppercase">Ending Runway Cash</span>
                <span className="text-sm font-bold text-theme-text">{formatCurrency(forecast.ending_cash, currency)}</span>
              </div>
            </div>

            {/* Projection Chart (Responsive SVG) */}
            <div className="w-full h-56 sm:h-64 relative bg-theme-surface rounded-xl border border-theme-border p-2">
              <svg className="w-full h-full" viewBox="0 0 800 240" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="forecastFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#788B63" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#788B63" stopOpacity="0.0" />
                  </linearGradient>
                </defs>

                {(() => {
                  const pts = forecast.daily_projections;
                  if (!pts || pts.length < 2) return null;
                  const vals = pts.map((p) => p.projected_cash);
                  const minVal = Math.min(...vals, 0);
                  const maxVal = Math.max(...vals, 10000);
                  const range = maxVal - minVal || 1;

                  const getX = (idx: number) => (idx / (pts.length - 1)) * 760 + 20;
                  const getY = (val: number) => 210 - ((val - minVal) / range) * 180;

                  const linePoints = pts.map((p, i) => `${getX(i)},${getY(p.projected_cash)}`).join(" ");
                  const areaPoints = `${getX(0)},210 ` + linePoints + ` ${getX(pts.length - 1)},210`;

                  return (
                    <>
                      {/* Reserve threshold line */}
                      {reserveBuffer > minVal && reserveBuffer < maxVal && (
                        <line
                          x1="20"
                          y1={getY(reserveBuffer)}
                          x2="780"
                          y2={getY(reserveBuffer)}
                          stroke="#E07A5F"
                          strokeDasharray="4 4"
                          strokeWidth="1.5"
                        />
                      )}
                      {/* Area Fill */}
                      <polygon points={areaPoints} fill="url(#forecastFill)" />
                      {/* Line */}
                      <polyline points={linePoints} fill="none" stroke="#788B63" strokeWidth="2.5" />
                    </>
                  );
                })()}
              </svg>
              <div className="flex justify-between items-center text-[10px] text-theme-textMuted px-2 mt-1">
                <span>Today</span>
                <span>Day {Math.floor(horizon / 2)}</span>
                <span>Day {horizon} (End of Horizon)</span>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-xs text-theme-textMuted">No projections available.</p>
        )}
      </div>

      {/* SECTION 4: INVOICES & EXPENSE ANOMALIES (2 Columns) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Outstanding Invoices */}
        <div className="spatial-panel p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Receipt className="w-4 h-4 text-theme-sage" />
              <h3 className="text-sm font-bold text-theme-text">Outstanding Invoices</h3>
            </div>
            <Link href="/invoices" className="text-xs font-semibold text-theme-sage hover:underline flex items-center gap-1">
              <span>View All</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {invoices.length > 0 ? (
            <div className="space-y-2.5">
              {invoices.slice(0, 4).map((inv) => (
                <div
                  key={inv.id}
                  className="p-3 rounded-xl bg-theme-surface border border-theme-border flex items-center justify-between text-xs"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-theme-text">{inv.invoice_number}</span>
                      <span className="text-theme-textMuted">• {inv.customer_name}</span>
                    </div>
                    <span className="text-[10px] text-theme-textMuted block mt-0.5">
                      Due: {formatDate(inv.due_date)} {inv.predicted_delay_days > 0 && `(Est. +${inv.predicted_delay_days}d delay)`}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="font-extrabold text-theme-text block">{formatCurrency(inv.total_amount, inv.currency)}</span>
                    <span
                      className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${
                        inv.status === "PAID"
                          ? "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400"
                          : inv.status === "OVERDUE"
                          ? "bg-red-500/20 text-red-500"
                          : "bg-amber-500/20 text-amber-600"
                      }`}
                    >
                      {inv.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-theme-textMuted py-4 text-center">No outstanding customer invoices.</p>
          )}
        </div>

        {/* Expense Anomaly Indicators */}
        <div className="spatial-panel p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              <h3 className="text-sm font-bold text-theme-text">Expense Review Indicators</h3>
            </div>
            <span className="text-[10px] text-theme-textMuted font-medium">Statistical 2.5σ Deviations</span>
          </div>

          {anomalies.length > 0 ? (
            <div className="space-y-2.5">
              {anomalies.slice(0, 4).map((an) => (
                <div
                  key={an.id}
                  className="p-3 rounded-xl bg-theme-surface border border-theme-border text-xs flex flex-col gap-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-theme-text">{an.category}</span>
                    <span className="font-extrabold text-red-500">+{formatCurrency(an.amount, currency)}</span>
                  </div>
                  <p className="text-[11px] text-theme-textMuted">{an.reason}</p>
                  <span className="text-[10px] text-theme-textMuted">Typical range: {an.expected_range}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-6 text-center text-xs text-theme-textMuted flex flex-col items-center gap-2">
              <CheckCircle2 className="w-6 h-6 text-theme-sage opacity-70" />
              <span>No statistical expense anomalies detected. Spending is aligned with historical averages.</span>
            </div>
          )}
        </div>
      </div>

      {/* SECTION 5: RECENT TRANSACTIONS & RECONCILIATION */}
      <div className="spatial-panel p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-theme-text">Recent Transactions Ledger</h3>
            <p className="text-xs text-theme-textMuted">Verified movements across financial accounts.</p>
          </div>
          <Link
            href="/transactions"
            className="text-xs font-semibold text-theme-sage hover:underline flex items-center gap-1"
          >
            <span>Full Ledger</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {transactions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-theme-border text-theme-textMuted uppercase text-[10px]">
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3">Description</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-theme-border">
                {transactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-theme-secondary/40 transition-colors">
                    <td className="py-2.5 px-3 font-medium text-theme-textMuted">{formatDate(tx.transaction_date)}</td>
                    <td className="py-2.5 px-3 font-semibold text-theme-text">{tx.description}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-theme-secondary text-theme-text border border-theme-border">
                        {tx.category}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          tx.status === "RECONCILED"
                            ? "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400"
                            : "bg-theme-secondary text-theme-textMuted"
                        }`}
                      >
                        {tx.status}
                      </span>
                    </td>
                    <td
                      className={`py-2.5 px-3 text-right font-bold ${
                        tx.amount > 0 ? "text-emerald-600 dark:text-emerald-400" : "text-theme-text"
                      }`}
                    >
                      {tx.amount > 0 ? `+${formatCurrency(tx.amount, tx.currency)}` : formatCurrency(tx.amount, tx.currency)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-theme-textMuted">
            <p>No recent transactions in this workspace.</p>
            <Link href="/imports/new" className="text-theme-sage font-semibold underline mt-1 inline-block">
              Upload bank statements to populate ledger
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
