"use client";

import React, { useEffect, useState } from "react";
import {
  GitCompare,
  CheckCircle2,
  XCircle,
  AlertCircle,
  HelpCircle,
  ArrowRight,
  Loader2,
  Receipt,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { api, ReconciliationCandidate } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";

export default function ReconciliationPage() {
  const { currentBusiness } = useAuth();
  const [candidates, setCandidates] = useState<ReconciliationCandidate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadCandidates = async () => {
    if (!currentBusiness) return;
    setIsLoading(true);
    try {
      const data = await api.listReconciliationCandidates(currentBusiness.id);
      setCandidates(data);
    } catch (err: any) {
      console.error("Failed to load candidates:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCandidates();
  }, [currentBusiness]);

  const handleApprove = async (cand: ReconciliationCandidate) => {
    if (!currentBusiness) return;
    setProcessingId(cand.reconciliation_id);
    setMessage(null);
    try {
      await api.approveReconciliation(currentBusiness.id, cand.reconciliation_id);
      setMessage({
        type: "success",
        text: `Successfully reconciled ₹${cand.matched_amount} for ${cand.invoice_number} against transaction.`,
      });
      loadCandidates();
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Approval failed." });
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (cand: ReconciliationCandidate) => {
    if (!currentBusiness) return;
    setProcessingId(cand.reconciliation_id);
    setMessage(null);
    try {
      await api.rejectReconciliation(currentBusiness.id, cand.reconciliation_id);
      setMessage({ type: "success", text: `Match candidate rejected.` });
      loadCandidates();
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Rejection failed." });
    } finally {
      setProcessingId(null);
    }
  };

  const pendingCandidates = candidates.filter((c) => c.status === "PENDING_REVIEW");

  return (
    <div className="space-y-6 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-theme-sage/20 text-theme-sage border border-theme-sage/30 flex items-center gap-1.5">
            <Sparkles className="w-3 h-3" />
            INTELLIGENT RECONCILIATION ENGINE
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-theme-text">
          Bank Statement & Invoice Reconciliation
        </h1>
        <p className="text-xs sm:text-sm text-theme-textMuted mt-1">
          Automated matching between unallocated bank inflow transactions and customer invoices with mandatory human review.
        </p>
      </div>

      {message && (
        <div
          className={`p-4 rounded-xl text-xs flex items-center gap-2.5 ${
            message.type === "success"
              ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400"
              : "bg-red-500/10 border border-red-500/30 text-red-500"
          }`}
        >
          {message.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 shrink-0" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {/* Candidate List */}
      <div className="spatial-panel p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-theme-text">Candidate Matches For Review</h2>
            <p className="text-xs text-theme-textMuted">
              {pendingCandidates.length} pending candidate match{pendingCandidates.length === 1 ? "" : "es"}
            </p>
          </div>
        </div>

        {isLoading ? (
          <div className="py-12 flex justify-center">
            <Loader2 className="w-6 h-6 text-theme-sage animate-spin" />
          </div>
        ) : pendingCandidates.length > 0 ? (
          <div className="space-y-4">
            {pendingCandidates.map((cand) => (
              <div
                key={cand.reconciliation_id}
                className="p-5 rounded-2xl bg-theme-surface border border-theme-border shadow-sm flex flex-col lg:flex-row lg:items-center justify-between gap-5 transition-all"
              >
                {/* Match Cards Comparison */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-1">
                  {/* Left: Bank Transaction */}
                  <div className="p-3.5 rounded-xl bg-theme-secondary/50 border border-theme-border text-xs">
                    <span className="text-[10px] font-bold text-theme-textMuted uppercase block mb-1">
                      Bank Transaction
                    </span>
                    <p className="font-bold text-theme-text">{cand.transaction_description}</p>
                    <div className="flex items-center justify-between mt-2 pt-2 border-t border-theme-border text-theme-textMuted text-[11px]">
                      <span>{formatDate(cand.transaction_date)}</span>
                      <strong className="text-emerald-600 dark:text-emerald-400 font-extrabold text-sm">
                        +{formatCurrency(cand.transaction_amount, "INR")}
                      </strong>
                    </div>
                  </div>

                  {/* Right: Invoice */}
                  <div className="p-3.5 rounded-xl bg-theme-secondary/50 border border-theme-border text-xs">
                    <span className="text-[10px] font-bold text-theme-textMuted uppercase block mb-1">
                      Customer Invoice
                    </span>
                    <p className="font-bold text-theme-text">
                      {cand.invoice_number} • {cand.customer_name}
                    </p>
                    <div className="flex items-center justify-between mt-2 pt-2 border-t border-theme-border text-theme-textMuted text-[11px]">
                      <span>Unpaid: {formatCurrency(cand.unpaid_amount, "INR")}</span>
                      <strong className="text-theme-text font-extrabold text-sm">
                        Total {formatCurrency(cand.invoice_total, "INR")}
                      </strong>
                    </div>
                  </div>
                </div>

                {/* Score & Explanation */}
                <div className="lg:w-64 shrink-0 flex flex-col justify-between">
                  <div className="flex items-center justify-between lg:justify-start gap-2 mb-2">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase ${
                        cand.match_type === "EXACT"
                          ? "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30"
                          : "bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30"
                      }`}
                    >
                      {cand.match_type} ({cand.confidence_score}%)
                    </span>
                  </div>
                  <p className="text-[11px] text-theme-textMuted mb-3 leading-relaxed">{cand.explanation}</p>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleReject(cand)}
                      disabled={processingId === cand.reconciliation_id}
                      className="flex-1 py-1.5 rounded-xl text-xs font-semibold text-theme-textMuted hover:bg-theme-secondary border border-theme-border transition-colors disabled:opacity-50"
                    >
                      Reject
                    </button>
                    <button
                      onClick={() => handleApprove(cand)}
                      disabled={processingId === cand.reconciliation_id}
                      className="flex-1 py-1.5 rounded-xl text-xs font-bold bg-theme-sage hover:bg-theme-sageDark text-white shadow-sm transition-all disabled:opacity-50 flex items-center justify-center gap-1.5"
                    >
                      {processingId === cand.reconciliation_id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Approve</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-12 text-center text-xs text-theme-textMuted flex flex-col items-center gap-2">
            <CheckCircle2 className="w-8 h-8 text-theme-sage opacity-70" />
            <p className="font-semibold text-theme-text">All transactions and invoices are reconciled!</p>
            <p className="text-[11px] text-theme-textMuted max-w-sm">
              New candidate matches will automatically be detected when you import bank statements or issue customer invoices.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
