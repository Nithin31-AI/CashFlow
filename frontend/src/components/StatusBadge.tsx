import React from "react";

interface StatusBadgeProps {
  status: string;
  type?: "role" | "file" | "import";
  className?: string;
}

export function StatusBadge({ status, type = "import", className = "" }: StatusBadgeProps) {
  let style = "bg-slate-100 text-slate-700 border-slate-200";
  let label = status;

  if (type === "role") {
    switch (status) {
      case "OWNER":
        style = "bg-indigo-50 text-indigo-700 border-indigo-200 font-semibold";
        label = "Owner";
        break;
      case "FINANCE_MANAGER":
        style = "bg-blue-50 text-blue-700 border-blue-200 font-medium";
        label = "Finance Manager";
        break;
      case "ACCOUNTANT":
        style = "bg-emerald-50 text-emerald-700 border-emerald-200 font-medium";
        label = "Accountant";
        break;
      case "VIEWER":
        style = "bg-slate-50 text-slate-600 border-slate-200";
        label = "Viewer";
        break;
    }
  } else if (type === "file") {
    switch (status) {
      case "UPLOADED":
        style = "bg-sky-50 text-sky-700 border-sky-200";
        label = "Uploaded";
        break;
      case "PROCESSING":
        style = "bg-amber-50 text-amber-700 border-amber-200 animate-pulse";
        label = "Processing";
        break;
      case "PROCESSED":
        style = "bg-emerald-50 text-emerald-700 border-emerald-200";
        label = "Processed";
        break;
      case "FAILED":
        style = "bg-rose-50 text-rose-700 border-rose-200";
        label = "Failed";
        break;
    }
  } else {
    // import job status
    switch (status) {
      case "PENDING_MAPPING":
        style = "bg-amber-50 text-amber-700 border-amber-200";
        label = "Awaiting Mapping";
        break;
      case "VALIDATING":
        style = "bg-sky-50 text-sky-700 border-sky-200";
        label = "Validating";
        break;
      case "READY_FOR_PREVIEW":
        style = "bg-indigo-50 text-indigo-700 border-indigo-200";
        label = "Ready to Review";
        break;
      case "APPROVED":
        style = "bg-emerald-50 text-emerald-700 border-emerald-200";
        label = "Approved & Imported";
        break;
      case "FAILED":
        style = "bg-rose-50 text-rose-700 border-rose-200";
        label = "Failed";
        break;
    }
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${style} ${className}`}
    >
      {label}
    </span>
  );
}
