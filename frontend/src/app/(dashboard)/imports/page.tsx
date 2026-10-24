"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  UploadCloud,
  FileSpreadsheet,
  FileText,
  Clock,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ArrowRight,
  Hash,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { useAuth } from "@/lib/auth";
import { api, UploadedFileRecord, ImportJobRecord } from "@/lib/api";
import { formatBytes, formatDateTime } from "@/lib/utils";
import { StatusBadge } from "@/components/StatusBadge";

export default function UploadHistoryPage() {
  const { currentBusiness } = useAuth();
  const [uploads, setUploads] = useState<UploadedFileRecord[]>([]);
  const [jobs, setJobs] = useState<ImportJobRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadHistory() {
      if (!currentBusiness) return;
      setLoading(true);
      setError(null);
      try {
        const [uploadData, jobData] = await Promise.all([
          api.listUploads(currentBusiness.id),
          api.listImportJobs(currentBusiness.id),
        ]);
        setUploads(uploadData);
        setJobs(jobData);
      } catch (err: any) {
        setError(err.message || "Failed to load upload history.");
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, [currentBusiness]);

  return (
    <div>
      <Navbar
        title="Upload & Import History"
        subtitle="Audit trail of all uploaded files, validation runs, and approved imports"
      />

      <div className="mt-6 max-w-6xl mx-auto space-y-6">
        {error && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center shadow-sm">
            <Loader2 className="w-8 h-8 text-[#10A86B] animate-spin mx-auto mb-3" />
            <p className="text-sm text-slate-500 font-medium">Loading history records...</p>
          </div>
        ) : uploads.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center shadow-sm max-w-lg mx-auto">
            <div className="w-14 h-14 bg-slate-100 text-slate-400 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <FileSpreadsheet className="w-7 h-7" />
            </div>
            <h3 className="font-bold text-slate-900 text-base mb-1">No uploads yet</h3>
            <p className="text-xs text-slate-500 mb-6">
              Upload your first bank statement or Excel spreadsheet to get started.
            </p>
            <Link
              href="/imports/new"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#10A86B] hover:bg-[#0D8554] text-white text-xs font-semibold rounded-xl shadow-sm transition-colors"
            >
              <UploadCloud className="w-4 h-4" />
              <span>Import File</span>
            </Link>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-200/80 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-900 text-base">File Upload History</h3>
                <p className="text-xs text-slate-500">
                  {uploads.length} document(s) uploaded to this business workspace
                </p>
              </div>
              <Link
                href="/imports/new"
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#10A86B] hover:bg-[#0D8554] text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
              >
                <UploadCloud className="w-3.5 h-3.5" />
                <span>Upload Document</span>
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-600">
                <thead className="bg-slate-50 text-[10px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-5">Original Filename</th>
                    <th className="py-3 px-5">Uploaded At</th>
                    <th className="py-3 px-5">Size</th>
                    <th className="py-3 px-5">File Status</th>
                    <th className="py-3 px-5">Import Status</th>
                    <th className="py-3 px-5">Valid / Total Rows</th>
                    <th className="py-3 px-5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {uploads.map((file) => {
                    const relatedJob = jobs.find((j) => j.uploaded_file_id === file.id);
                    return (
                      <tr key={file.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="py-3.5 px-5 font-medium text-slate-900">
                          <div className="flex items-center gap-2">
                            <FileSpreadsheet className="w-4 h-4 text-[#10A86B] shrink-0" />
                            <span className="truncate max-w-xs">{file.original_filename}</span>
                          </div>
                          <span className="text-[10px] text-slate-400 font-mono flex items-center gap-1 mt-0.5">
                            <Hash className="w-3 h-3" /> {file.file_hash.slice(0, 12)}...
                          </span>
                        </td>
                        <td className="py-3.5 px-5 text-slate-500 whitespace-nowrap">
                          {formatDateTime(file.created_at)}
                        </td>
                        <td className="py-3.5 px-5 text-slate-500 whitespace-nowrap">
                          {formatBytes(file.file_size)}
                        </td>
                        <td className="py-3.5 px-5 whitespace-nowrap">
                          <StatusBadge status={file.status} type="file" />
                        </td>
                        <td className="py-3.5 px-5 whitespace-nowrap">
                          {relatedJob ? (
                            <StatusBadge status={relatedJob.status} type="import" />
                          ) : (
                            <span className="text-slate-400 text-xs">—</span>
                          )}
                        </td>
                        <td className="py-3.5 px-5 whitespace-nowrap font-mono text-xs">
                          {relatedJob ? (
                            <span>
                              <strong className="text-[#10A86B]">{relatedJob.valid_rows}</strong> / {relatedJob.total_rows}
                            </span>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td className="py-3.5 px-5 text-right whitespace-nowrap">
                          {relatedJob && relatedJob.status === "PENDING_MAPPING" && (
                            <Link
                              href={`/imports/${relatedJob.id}/mapping`}
                              className="inline-flex items-center gap-1 text-[#10A86B] hover:text-[#0D8554] font-semibold text-xs"
                            >
                              Configure Mapping <ArrowRight className="w-3.5 h-3.5" />
                            </Link>
                          )}
                          {relatedJob && relatedJob.status === "READY_FOR_PREVIEW" && (
                            <Link
                              href={`/imports/${relatedJob.id}/preview`}
                              className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-700 font-semibold text-xs"
                            >
                              Review & Confirm <ArrowRight className="w-3.5 h-3.5" />
                            </Link>
                          )}
                          {relatedJob && relatedJob.status === "APPROVED" && (
                            <span className="text-emerald-700 font-medium text-xs flex items-center justify-end gap-1">
                              <CheckCircle2 className="w-3.5 h-3.5" /> Approved
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
