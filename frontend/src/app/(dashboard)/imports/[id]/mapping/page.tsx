"use client";

import React, { useState, useEffect, use } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Loader2,
  Table,
  Calendar,
  Settings2,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";

export default function MappingPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const jobId = resolvedParams.id;
  const searchParams = useSearchParams();
  const accountIdParam = searchParams.get("account_id") || "";

  const { currentBusiness } = useAuth();
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [headers, setHeaders] = useState<string[]>([]);
  const [sampleRows, setSampleRows] = useState<Record<string, any>[]>([]);
  const [mappings, setMappings] = useState<Record<string, string | null>>({
    date: null,
    description: null,
    reference: null,
    debit: null,
    credit: null,
    amount: null,
    currency: null,
  });
  const [dateFormat, setDateFormat] = useState("%d/%m/%Y");

  useEffect(() => {
    async function loadJobInspection() {
      if (!currentBusiness) return;
      try {
        // Fetch preview/inspection info from backend
        const preview = await api.getImportPreview(currentBusiness.id, jobId);
        if (preview && preview.preview_rows && preview.preview_rows.length > 0) {
          const sample = preview.preview_rows.slice(0, 5).map((r) => r.raw_data);
          setSampleRows(sample);
          const detectedHeaders = Object.keys(sample[0] || {});
          setHeaders(detectedHeaders);

          // Default smart heuristics if not set
          const initialMap: Record<string, string | null> = { ...mappings };
          detectedHeaders.forEach((h) => {
            const low = h.toLowerCase();
            if (low.includes("date") && !initialMap.date) initialMap.date = h;
            if ((low.includes("desc") || low.includes("narrat") || low.includes("particular")) && !initialMap.description) initialMap.description = h;
            if ((low.includes("ref") || low.includes("chq")) && !initialMap.reference) initialMap.reference = h;
            if ((low.includes("debit") || low.includes("dr") || low.includes("withdraw")) && !initialMap.debit) initialMap.debit = h;
            if ((low.includes("credit") || low.includes("cr") || low.includes("deposit")) && !initialMap.credit) initialMap.credit = h;
            if (low.includes("amount") && !initialMap.amount && !initialMap.debit) initialMap.amount = h;
          });
          setMappings(initialMap);
        }
      } catch (err: any) {
        // Fallback inspection via jobs list
        console.error("Preview load error, using default fallback:", err);
      } finally {
        setLoading(false);
      }
    }
    loadJobInspection();
  }, [currentBusiness, jobId]);

  const handleFieldChange = (field: string, headerVal: string) => {
    setMappings((prev) => ({
      ...prev,
      [field]: headerVal === "" ? null : headerVal,
    }));
  };

  const handleApplyAndValidate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentBusiness) return;

    if (!mappings.date) {
      setError("Please map the 'Transaction Date' column.");
      return;
    }
    if (!mappings.description) {
      setError("Please map the 'Description' column.");
      return;
    }
    if (!mappings.amount && (!mappings.debit || !mappings.credit)) {
      setError("Please map either a single 'Amount' column, or both 'Debit' and 'Credit' columns.");
      return;
    }

    setError(null);
    setValidating(true);

    try {
      await api.applyMapping(currentBusiness.id, jobId, {
        account_id: accountIdParam || undefined,
        column_mappings: mappings,
        date_format: dateFormat,
      });

      router.push(`/imports/${jobId}/preview`);
    } catch (err: any) {
      setError(err.message || "Validation failed on the submitted mappings.");
      setValidating(false);
    }
  };

  return (
    <div>
      <Navbar
        title="Column Mapping & Validation"
        subtitle="Match your file columns to standard financial fields (Step 2 of 3)"
      />

      <div className="mt-6 max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 sm:p-10">
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start gap-3">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleApplyAndValidate} className="space-y-8">
            {/* Field Mappings Section */}
            <div>
              <h3 className="text-base font-bold text-slate-900 mb-1 flex items-center gap-2">
                <Settings2 className="w-5 h-5 text-[#10A86B]" />
                Map Columns to Standard Schema
              </h3>
              <p className="text-xs text-slate-500 mb-6">
                Our column detector has pre-selected the closest matches. Review and adjust below:
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {/* Date */}
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                    Transaction Date <span className="text-rose-500">*</span>
                  </label>
                  <select
                    value={mappings.date || ""}
                    onChange={(e) => handleFieldChange("date", e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#10A86B]"
                  >
                    <option value="">-- Select File Column --</option>
                    {headers.map((h) => (
                      <option key={h} value={h}>
                        {h}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Description */}
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                    Description / Narration <span className="text-rose-500">*</span>
                  </label>
                  <select
                    value={mappings.description || ""}
                    onChange={(e) => handleFieldChange("description", e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#10A86B]"
                  >
                    <option value="">-- Select File Column --</option>
                    {headers.map((h) => (
                      <option key={h} value={h}>
                        {h}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Reference Number */}
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                    Reference / Cheque / UTR
                  </label>
                  <select
                    value={mappings.reference || ""}
                    onChange={(e) => handleFieldChange("reference", e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#10A86B]"
                  >
                    <option value="">-- Optional / None --</option>
                    {headers.map((h) => (
                      <option key={h} value={h}>
                        {h}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Date Format */}
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                    Date Format
                  </label>
                  <select
                    value={dateFormat}
                    onChange={(e) => setDateFormat(e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#10A86B]"
                  >
                    <option value="%d/%m/%Y">DD/MM/YYYY (e.g. 25/03/2026 - India Standard)</option>
                    <option value="%Y-%m-%d">YYYY-MM-DD (e.g. 2026-03-25 - ISO)</option>
                    <option value="%d-%m-%Y">DD-MM-YYYY (e.g. 25-03-2026)</option>
                    <option value="%m/%d/%Y">MM/DD/YYYY (e.g. 03/25/2026 - US)</option>
                    <option value="%d.%m.%Y">DD.MM.YYYY (e.g. 25.03.2026)</option>
                  </select>
                </div>

                {/* Debit */}
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                    Debit / Withdrawal Amount
                  </label>
                  <select
                    value={mappings.debit || ""}
                    onChange={(e) => handleFieldChange("debit", e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#10A86B]"
                  >
                    <option value="">-- None (if using single Amount) --</option>
                    {headers.map((h) => (
                      <option key={h} value={h}>
                        {h}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Credit */}
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                    Credit / Deposit Amount
                  </label>
                  <select
                    value={mappings.credit || ""}
                    onChange={(e) => handleFieldChange("credit", e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#10A86B]"
                  >
                    <option value="">-- None (if using single Amount) --</option>
                    {headers.map((h) => (
                      <option key={h} value={h}>
                        {h}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Single Signed Amount */}
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 md:col-span-2">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                    Single Signed Amount Column (Alternative to Debit/Credit)
                  </label>
                  <select
                    value={mappings.amount || ""}
                    onChange={(e) => handleFieldChange("amount", e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#10A86B]"
                  >
                    <option value="">-- None (if using separate Debit/Credit columns) --</option>
                    {headers.map((h) => (
                      <option key={h} value={h}>
                        {h}
                      </option>
                    ))}
                  </select>
                  <p className="mt-1 text-[11px] text-slate-500">
                    Use this if your file contains a single Net Amount column (negative for outflow, positive for inflow).
                  </p>
                </div>
              </div>
            </div>

            {/* Sample Rows Preview */}
            {sampleRows.length > 0 && (
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-3 flex items-center gap-1.5">
                  <Table className="w-4 h-4 text-slate-400" />
                  First 5 Rows Preview from Uploaded File
                </h4>
                <div className="overflow-x-auto border border-slate-200 rounded-xl">
                  <table className="w-full text-left text-xs text-slate-600">
                    <thead className="bg-slate-100 text-[10px] font-bold text-slate-700 uppercase">
                      <tr>
                        {headers.map((h) => (
                          <th key={h} className="py-2.5 px-3 whitespace-nowrap">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {sampleRows.map((r, i) => (
                        <tr key={i} className="hover:bg-slate-50">
                          {headers.map((h) => (
                            <td key={h} className="py-2 px-3 whitespace-nowrap">
                              {r[h] !== undefined && r[h] !== null ? String(r[h]) : ""}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Buttons */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={() => router.back()}
                className="inline-flex items-center gap-1.5 px-4 py-2.5 border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Upload
              </button>

              <button
                type="submit"
                disabled={validating}
                className="inline-flex items-center gap-2 px-6 py-3 bg-[#10A86B] hover:bg-[#0D8554] text-white font-semibold rounded-xl text-sm shadow-md transition-all disabled:opacity-50"
              >
                {validating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Validating Rows...</span>
                  </>
                ) : (
                  <>
                    <span>Validate & Preview Records</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
