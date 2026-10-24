"use client";

import React, { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ShieldCheck,
  Loader2,
  ArrowRight,
  AlertCircle,
  FileSpreadsheet,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { useAuth } from "@/lib/auth";
import { api, ImportValidationSummary } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";

export default function PreviewPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const jobId = resolvedParams.id;

  const { currentBusiness } = useAuth();
  const router = useRouter();

  const [summary, setSummary] = useState<ImportValidationSummary | null>(null);
  const [filter, setFilter] = useState<"all" | "valid" | "invalid">("all");
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    async function loadPreview() {
      if (!currentBusiness) return;
      try {
        const data = await api.getImportPreview(currentBusiness.id, jobId);
        setSummary(data);
      } catch (err: any) {
        setError(err.message || "Failed to load validation preview.");
      } finally {
        setLoading(false);
      }
    }
    loadPreview();
  }, [currentBusiness, jobId]);

  const canConfirm =
    currentBusiness?.role === "OWNER" || currentBusiness?.role === "FINANCE_MANAGER";

  const handleConfirm = async () => {
    if (!currentBusiness || !canConfirm) return;
    setError(null);
    setConfirming(true);

    try {
      const res = await api.confirmImport(currentBusiness.id, jobId);
      setSuccessMsg(res.message);
      setTimeout(() => {
        router.push("/dashboard");
      }, 1500);
    } catch (err: any) {
      setError(err.message || "Failed to confirm and approve import.");
      setConfirming(false);
    }
  };

  const filteredRows =
    summary?.preview_rows.filter((r) => {
      if (filter === "valid") return r.is_valid;
      if (filter === "invalid") return !r.is_valid;
      return true;
    }) || [];

  return (
    <div>
      <Navbar
        title="Import Preview & Confirmation"
        subtitle="Review row-level validation results before approving (Step 3 of 3)"
      />

      <div className="mt-6 max-w-6xl mx-auto space-y-6">
        {error && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-[#10A86B] shrink-0 mt-0.5" />
            <div>
              <p className="font-bold">{successMsg}</p>
              <p className="text-xs text-emerald-600 mt-0.5">
                Approved transactions have been recorded into your cashFlow ledger. Redirecting to dashboard...
              </p>
            </div>
          </div>
        )}

        {loading ? (
          <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center shadow-sm">
            <Loader2 className="w-8 h-8 text-[#10A86B] animate-spin mx-auto mb-3" />
            <p className="text-sm text-slate-500 font-medium">Generating import preview...</p>
          </div>
        ) : !summary ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center">
            <p className="text-slate-600 text-sm">No preview data found for this import job.</p>
          </div>
        ) : (
          <>
            {/* Stats Overview Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Total Rows
                  </p>
                  <p className="text-2xl font-bold text-slate-900 mt-1">{summary.total_rows}</p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-600 flex items-center justify-center">
                  <FileSpreadsheet className="w-5 h-5" />
                </div>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Valid Records
                  </p>
                  <p className="text-2xl font-bold text-[#10A86B] mt-1">{summary.valid_rows}</p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-[#E8F8F1] text-[#10A86B] flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Invalid Rows
                  </p>
                  <p className={`text-2xl font-bold mt-1 ${summary.invalid_rows > 0 ? "text-rose-600" : "text-slate-400"}`}>
                    {summary.invalid_rows}
                  </p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center">
                  <XCircle className="w-5 h-5" />
                </div>
              </div>
            </div>

            {/* Validation Info Alert */}
            {summary.invalid_rows > 0 && (
              <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold">Invalid rows detected ({summary.invalid_rows})</p>
                  <p className="mt-0.5 leading-relaxed text-amber-700">
                    cashFlow does not silently discard invalid rows. Each error is highlighted below. Only the {summary.valid_rows} valid records will be imported upon confirmation.
                  </p>
                </div>
              </div>
            )}

            {/* Preview Table with Filter Tabs */}
            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
              <div className="p-4 sm:p-5 border-b border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setFilter("all")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      filter === "all"
                        ? "bg-slate-900 text-white"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    All Rows ({summary.preview_rows.length})
                  </button>
                  <button
                    onClick={() => setFilter("valid")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      filter === "valid"
                        ? "bg-[#10A86B] text-white"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    Valid Only ({summary.valid_rows})
                  </button>
                  {summary.invalid_rows > 0 && (
                    <button
                      onClick={() => setFilter("invalid")}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                        filter === "invalid"
                          ? "bg-rose-600 text-white"
                          : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                      }`}
                    >
                      Invalid Only ({summary.invalid_rows})
                    </button>
                  )}
                </div>

                <div className="text-xs text-slate-400 font-mono">
                  Showing {filteredRows.length} rows
                </div>
              </div>

              <div className="overflow-x-auto max-h-[500px]">
                <table className="w-full text-left text-xs text-slate-600">
                  <thead className="bg-slate-50 text-[10px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200 sticky top-0 z-10">
                    <tr>
                      <th className="py-2.5 px-4">Row #</th>
                      <th className="py-2.5 px-4">Status</th>
                      <th className="py-2.5 px-4">Parsed Date</th>
                      <th className="py-2.5 px-4">Description</th>
                      <th className="py-2.5 px-4">Reference</th>
                      <th className="py-2.5 px-4 text-right">Debit</th>
                      <th className="py-2.5 px-4 text-right">Credit</th>
                      <th className="py-2.5 px-4 text-right">Amount</th>
                      <th className="py-2.5 px-4">Validation Notes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredRows.map((r) => {
                      const p = r.parsed_data;
                      return (
                        <tr
                          key={r.row_index}
                          className={`hover:bg-slate-50/80 transition-colors ${
                            !r.is_valid ? "bg-rose-50/30" : ""
                          }`}
                        >
                          <td className="py-3 px-4 font-mono text-slate-400">
                            {r.row_index}
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap">
                            {r.is_valid ? (
                              <span className="inline-flex items-center gap-1 text-[#10A86B] font-semibold">
                                <CheckCircle2 className="w-3.5 h-3.5" /> Valid
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-rose-600 font-semibold">
                                <XCircle className="w-3.5 h-3.5" /> Error
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap">
                            {p?.transaction_date ? formatDate(p.transaction_date) : "—"}
                          </td>
                          <td className="py-3 px-4 font-medium text-slate-900 max-w-xs truncate">
                            {p?.description || JSON.stringify(r.raw_data)}
                          </td>
                          <td className="py-3 px-4 font-mono text-slate-500">
                            {p?.reference_number || "—"}
                          </td>
                          <td className="py-3 px-4 text-right text-rose-600 font-mono">
                            {p?.debit ? formatCurrency(p.debit, p.currency) : "—"}
                          </td>
                          <td className="py-3 px-4 text-right text-[#10A86B] font-mono">
                            {p?.credit ? formatCurrency(p.credit, p.currency) : "—"}
                          </td>
                          <td className="py-3 px-4 text-right font-bold font-mono">
                            {p?.amount !== undefined ? (
                              <span className={p.amount >= 0 ? "text-[#10A86B]" : "text-rose-600"}>
                                {formatCurrency(p.amount, p.currency)}
                              </span>
                            ) : (
                              "—"
                            )}
                          </td>
                          <td className="py-3 px-4">
                            {r.errors && r.errors.length > 0 ? (
                              <div className="text-rose-600 space-y-0.5">
                                {r.errors.map((err: any, i: number) => (
                                  <div key={i} className="flex items-center gap-1">
                                    <span>• {err}</span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <span className="text-slate-400">Passed all checks</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Approval / Confirmation Bar */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <p className="text-sm font-bold text-slate-900">
                  Ready to confirm import of {summary.valid_rows} valid records?
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  Only OWNER and FINANCE_MANAGER roles can approve imports into the ledger.
                </p>
              </div>

              <div className="flex items-center gap-3 w-full sm:w-auto">
                <Link
                  href={`/imports/${jobId}/mapping`}
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 px-4 py-2.5 border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  <ArrowLeft className="w-3.5 h-3.5" /> Adjust Mapping
                </Link>

                <button
                  onClick={handleConfirm}
                  disabled={confirming || summary.valid_rows === 0 || !canConfirm}
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-[#10A86B] hover:bg-[#0D8554] text-white font-semibold rounded-xl text-sm shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {confirming ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Saving Records...</span>
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="w-4 h-4" />
                      <span>Confirm & Approve Import</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
