import React from "react";
import Link from "next/link";
import { Upload, FileSpreadsheet, ArrowRight, ShieldCheck, CheckCircle2 } from "lucide-react";

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionText?: string;
  actionHref?: string;
}

export function EmptyState({
  title = "No financial records imported yet",
  description = "Connect your bank statements or accounting exports to start tracking cash flow and financial health.",
  actionText = "Import Financial Records",
  actionHref = "/imports/new",
}: EmptyStateProps) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-8 sm:p-12 text-center max-w-3xl mx-auto shadow-sm">
      <div className="w-16 h-16 bg-[#E8F8F1] text-[#10A86B] rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-inner">
        <FileSpreadsheet className="w-8 h-8" />
      </div>

      <h3 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight mb-3">
        {title}
      </h3>
      <p className="text-slate-600 max-w-lg mx-auto text-sm sm:text-base mb-8 leading-relaxed">
        {description}
      </p>

      {/* 3 Step Workflow Explanation */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8 text-left">
        <div className="bg-slate-50 border border-slate-100 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-6 h-6 rounded-full bg-[#10A86B] text-white text-xs font-bold flex items-center justify-center">1</span>
            <span className="font-semibold text-slate-900 text-sm">Upload File</span>
          </div>
          <p className="text-xs text-slate-500 leading-normal">
            Upload statement in CSV, Excel (.xlsx/.xls), PDF, or receipt images.
          </p>
        </div>

        <div className="bg-slate-50 border border-slate-100 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-6 h-6 rounded-full bg-[#10A86B] text-white text-xs font-bold flex items-center justify-center">2</span>
            <span className="font-semibold text-slate-900 text-sm">Map & Validate</span>
          </div>
          <p className="text-xs text-slate-500 leading-normal">
            System detects columns, checks dates, decimal amounts, and highlights errors.
          </p>
        </div>

        <div className="bg-slate-50 border border-slate-100 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-6 h-6 rounded-full bg-[#10A86B] text-white text-xs font-bold flex items-center justify-center">3</span>
            <span className="font-semibold text-slate-900 text-sm">Review & Confirm</span>
          </div>
          <p className="text-xs text-slate-500 leading-normal">
            Preview verified records and explicitly approve them into your cashFlow ledger.
          </p>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
        <Link
          href={actionHref}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 bg-[#10A86B] hover:bg-[#0D8554] text-white font-medium rounded-xl shadow-sm transition-colors text-sm"
        >
          <Upload className="w-4 h-4" />
          {actionText}
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <div className="mt-8 pt-6 border-t border-slate-100 flex items-center justify-center gap-6 text-xs text-slate-400">
        <span className="flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-[#10A86B]" /> Bank-grade Tenant Isolation
        </span>
        <span className="flex items-center gap-1.5">
          <CheckCircle2 className="w-4 h-4 text-[#10A86B]" /> Zero Synthetic Figures
        </span>
      </div>
    </div>
  );
}
