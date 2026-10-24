"use client";

import React, { useEffect, useState } from "react";
import {
  TrendingUp,
  AlertTriangle,
  Calendar,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  Info,
  Loader2,
  ChevronRight,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import {
  api,
  ForecastResponse,
  RiskAssessmentItem,
  ExpenseAnomalyItem,
} from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";

export default function ForecastPage() {
  const { currentBusiness } = useAuth();
  const [horizon, setHorizon] = useState<number>(30);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [risks, setRisks] = useState<RiskAssessmentItem[]>([]);
  const [anomalies, setAnomalies] = useState<ExpenseAnomalyItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [reviewingId, setReviewingId] = useState<string | null>(null);

  const loadData = async () => {
    if (!currentBusiness) return;
    setIsLoading(true);
    try {
      const [fcData, rkData, anData] = await Promise.all([
        api.getForecast(currentBusiness.id, horizon),
        api.getRisks(currentBusiness.id, horizon),
        api.getExpenseAnomalies(currentBusiness.id),
      ]);
      setForecast(fcData);
      setRisks(rkData);
      setAnomalies(anData);
    } catch (err: any) {
      console.error("Failed to load forecast:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [currentBusiness, horizon]);

  const handleReviewAnomaly = async (anomalyId: string) => {
    if (!currentBusiness) return;
    setReviewingId(anomalyId);
    try {
      await api.markAnomalyReviewed(currentBusiness.id, anomalyId);
      setAnomalies((prev) =>
        prev.map((a) => (a.id === anomalyId ? { ...a, reviewed: true } : a))
      );
    } catch (err: any) {
      console.error("Failed to review anomaly:", err);
    } finally {
      setReviewingId(null);
    }
  };

  const currency = currentBusiness?.currency || "INR";

  return (
    <div className="space-y-6 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-theme-sage/20 text-theme-sage border border-theme-sage/30">
              PREDICTIVE CASH FLOW ENGINE
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-theme-text">
            Forecast & Risk Intelligence
          </h1>
          <p className="text-xs sm:text-sm text-theme-textMuted mt-1">
            Multi-horizon runway projections, safety buffer thresholds, and statistical anomaly review.
          </p>
        </div>

        {/* Horizon Selector */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-theme-secondary border border-theme-border self-start sm:self-auto">
          {[7, 30, 90, 180, 365].map((h) => (
            <button
              key={h}
              onClick={() => setHorizon(h)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                horizon === h
                  ? "bg-theme-surface text-theme-text shadow-sm"
                  : "text-theme-textMuted hover:text-theme-text"
              }`}
            >
              {h === 365 ? "12 Months" : h === 180 ? "6 Months" : `${h} Days`}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="py-20 flex justify-center">
          <Loader2 className="w-8 h-8 text-theme-sage animate-spin" />
        </div>
      ) : forecast ? (
        <>
          {/* Metrics Overview */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="spatial-card p-4">
              <span className="text-[10px] font-bold text-theme-textMuted uppercase tracking-wider block">
                Starting Verified Cash
              </span>
              <p className="text-2xl font-black text-theme-text mt-1">{formatCurrency(forecast.starting_cash, currency)}</p>
              <span className="text-[10px] text-theme-textMuted mt-1 block">Day 0 liquid bank balance</span>
            </div>

            <div className="spatial-card p-4">
              <span className="text-[10px] font-bold text-theme-textMuted uppercase tracking-wider block">
                Projected Collections
              </span>
              <p className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1">
                +{formatCurrency(forecast.projected_inflows, currency)}
              </p>
              <span className="text-[10px] text-theme-textMuted mt-1 block">Expected invoice settlements</span>
            </div>

            <div className="spatial-card p-4">
              <span className="text-[10px] font-bold text-theme-textMuted uppercase tracking-wider block">
                Projected Operating Burn
              </span>
              <p className="text-2xl font-black text-red-500 mt-1">
                -{formatCurrency(forecast.projected_outflows, currency)}
              </p>
              <span className="text-[10px] text-theme-textMuted mt-1 block">Based on 90-day moving average</span>
            </div>

            <div className="spatial-card p-4">
              <span className="text-[10px] font-bold text-theme-textMuted uppercase tracking-wider block">
                Ending Projected Runway
              </span>
              <p className="text-2xl font-black text-theme-text mt-1">{formatCurrency(forecast.ending_cash, currency)}</p>
              <span className="text-[10px] text-theme-textMuted mt-1 block">
                Envelope: {formatCurrency(forecast.confidence_lower, currency)} to {formatCurrency(forecast.confidence_upper, currency)}
              </span>
            </div>
          </div>

          {/* Interactive Chart & Envelopes */}
          <div className="spatial-panel p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-sm font-bold text-theme-text">Runway Trajectory ({horizon} Days)</h2>
                <p className="text-xs text-theme-textMuted">Solid line represents baseline trajectory; shaded area shows ±1σ confidence envelope.</p>
              </div>
              <span className="text-[11px] font-mono text-theme-textMuted">Model: {forecast.model_version}</span>
            </div>

            <div className="w-full h-64 relative bg-theme-surface rounded-xl border border-theme-border p-2">
              <svg className="w-full h-full" viewBox="0 0 800 240" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="envelopeGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#788B63" stopOpacity="0.2" />
                    <stop offset="100%" stopColor="#788B63" stopOpacity="0.0" />
                  </linearGradient>
                </defs>

                {(() => {
                  const pts = forecast.daily_projections;
                  if (!pts || pts.length < 2) return null;
                  const allValues = [
                    ...pts.map((p) => p.projected_cash),
                    ...pts.map((p) => p.upper_bound),
                    ...pts.map((p) => p.lower_bound),
                    0,
                  ];
                  const minVal = Math.min(...allValues);
                  const maxVal = Math.max(...allValues, 10000);
                  const range = maxVal - minVal || 1;

                  const getX = (idx: number) => (idx / (pts.length - 1)) * 760 + 20;
                  const getY = (val: number) => 210 - ((val - minVal) / range) * 180;

                  const upperPts = pts.map((p, i) => `${getX(i)},${getY(p.upper_bound)}`);
                  const lowerPts = pts.map((p, i) => `${getX(i)},${getY(p.lower_bound)}`).reverse();
                  const envelopePoly = [...upperPts, ...lowerPts].join(" ");
                  const linePts = pts.map((p, i) => `${getX(i)},${getY(p.projected_cash)}`).join(" ");

                  return (
                    <>
                      {/* Zero baseline */}
                      <line x1="20" y1={getY(0)} x2="780" y2={getY(0)} stroke="#64748B" strokeDasharray="2 2" strokeWidth="1" />
                      {/* Envelope Polygon */}
                      <polygon points={envelopePoly} fill="url(#envelopeGrad)" />
                      {/* Projected cash line */}
                      <polyline points={linePts} fill="none" stroke="#788B63" strokeWidth="2.5" />
                    </>
                  );
                })()}
              </svg>
            </div>
            <div className="flex justify-between items-center text-[10px] text-theme-textMuted px-2 mt-2">
              <span>Day 0 (Verified Today)</span>
              <span>Day {Math.floor(horizon / 2)}</span>
              <span>Day {horizon} (End of Horizon)</span>
            </div>
          </div>

          {/* Forecast Assumptions & Disclaimers */}
          <div className="spatial-panel p-5 bg-theme-secondary/40">
            <div className="flex items-center gap-2 mb-2 text-xs font-bold text-theme-text">
              <Info className="w-4 h-4 text-theme-sage" />
              <span>Model Assumptions & Limitations</span>
            </div>
            <ul className="text-xs text-theme-textMuted space-y-1 list-disc pl-5">
              <li>Operating daily burn rate is modeled at {formatCurrency(forecast.assumptions.daily_burn_rate || 0, currency)}/day.</li>
              <li>Expected inflows reflect customer receivables adjusted by customer historical payment delay windows.</li>
              <li>{forecast.assumptions.limitations || "Projections assume stationary burn rate and normal collection cycles."}</li>
            </ul>
          </div>

          {/* Cash Shortage Risks */}
          {risks.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-sm font-bold text-theme-text uppercase tracking-wider">
                Identified Cash-Shortage Risks
              </h2>
              {risks.map((rk) => (
                <div key={rk.id} className="spatial-panel p-5 border-amber-500/30">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-black uppercase bg-red-500 text-white">
                      {rk.severity}
                    </span>
                    <h3 className="text-sm font-bold text-theme-text">{rk.title}</h3>
                  </div>
                  <p className="text-xs text-theme-textMuted mb-2">{rk.description}</p>
                  <p className="text-xs font-semibold text-theme-sage">
                    Recommended Action: {rk.recommended_action}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Expense Anomalies Section */}
          <div className="spatial-panel p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-theme-text">Statistical Expense Review Indicators</h2>
                <p className="text-xs text-theme-textMuted">Discretionary expenses that deviate by &gt;2.5σ from category norms (indicators for review, not fraud).</p>
              </div>
            </div>

            {anomalies.length > 0 ? (
              <div className="space-y-3">
                {anomalies.map((an) => (
                  <div
                    key={an.id}
                    className="p-4 rounded-xl bg-theme-surface border border-theme-border flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-theme-text text-xs">{an.category}</span>
                        <span className="text-xs font-black text-red-500">+{formatCurrency(an.amount, currency)}</span>
                        {an.reviewed && (
                          <span className="text-[10px] font-bold text-emerald-600 bg-emerald-500/20 px-2 py-0.5 rounded">
                            Reviewed
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-theme-textMuted mt-1">{an.reason}</p>
                    </div>

                    {!an.reviewed && (
                      <button
                        onClick={() => handleReviewAnomaly(an.id)}
                        disabled={reviewingId === an.id}
                        className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-theme-secondary hover:bg-theme-border text-theme-text transition-colors self-start sm:self-auto shrink-0"
                      >
                        {reviewingId === an.id ? "Saving..." : "Mark Reviewed"}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center text-xs text-theme-textMuted">
                <CheckCircle2 className="w-8 h-8 text-theme-sage mx-auto mb-2 opacity-70" />
                <p>No anomalous expense spikes detected in the recent accounting period.</p>
              </div>
            )}
          </div>
        </>
      ) : null}
    </div>
  );
}
