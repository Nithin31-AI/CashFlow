"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  UploadCloud,
  FileSpreadsheet,
  FileText,
  Image as ImageIcon,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Trash2,
  Plus,
  RefreshCw,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { api, FinancialAccount, BatchFileResult } from "@/lib/api";
import { formatBytes } from "@/lib/utils";

interface QueuedFile {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
  status: "QUEUED" | "UPLOADING" | "SUCCESS" | "FAILED";
  errorMessage?: string;
  uploadId?: string;
  importJobId?: string;
}

export default function NewImportPage() {
  const { currentBusiness } = useAuth();
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [queue, setQueue] = useState<QueuedFile[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [accounts, setAccounts] = useState<FinancialAccount[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<string>("");
  const [isUploading, setIsUploading] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAccounts() {
      if (!currentBusiness) return;
      try {
        const accs = await api.listAccounts(currentBusiness.id);
        setAccounts(accs);
        if (accs.length > 0) {
          setSelectedAccountId(accs[0].id);
        }
      } catch (err: any) {
        console.error("Failed to load accounts:", err);
      }
    }
    loadAccounts();
  }, [currentBusiness]);

  const detectFileType = (filename: string): string => {
    const ext = filename.substring(filename.lastIndexOf(".")).toLowerCase();
    if (ext === ".csv") return "CSV";
    if (ext === ".xlsx" || ext === ".xls") return "EXCEL";
    if (ext === ".pdf") return "PDF";
    if ([".png", ".jpg", ".jpeg"].includes(ext)) return "IMAGE";
    return "UNKNOWN";
  };

  const addFilesToQueue = (fileList: FileList | File[]) => {
    setGlobalError(null);
    const validExtensions = [".csv", ".xls", ".xlsx", ".pdf", ".png", ".jpg", ".jpeg"];
    const newItems: QueuedFile[] = [];

    Array.from(fileList).forEach((f) => {
      const ext = f.name.substring(f.name.lastIndexOf(".")).toLowerCase();
      if (!validExtensions.includes(ext)) {
        setGlobalError(`File '${f.name}' has an unsupported extension. Allowed: CSV, XLS, XLSX, PDF, PNG, JPG.`);
        return;
      }
      if (f.size > 15 * 1024 * 1024) {
        setGlobalError(`File '${f.name}' exceeds the 15 MB maximum size limit.`);
        return;
      }

      // Check not already in queue
      if (!queue.some((q) => q.name === f.name && q.size === f.size)) {
        newItems.push({
          id: `${f.name}-${f.size}-${Date.now()}-${Math.random()}`,
          file: f,
          name: f.name,
          size: f.size,
          type: detectFileType(f.name),
          status: "QUEUED",
        });
      }
    });

    setQueue((prev) => [...prev, ...newItems]);
  };

  const removeFileFromQueue = (id: string) => {
    setQueue((prev) => prev.filter((item) => item.id !== id));
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFilesToQueue(e.dataTransfer.files);
    }
  };

  const handleUploadAll = async () => {
    if (!currentBusiness) return;
    const pendingFiles = queue.filter((q) => q.status === "QUEUED" || q.status === "FAILED");
    if (pendingFiles.length === 0) return;

    setIsUploading(true);
    setGlobalError(null);

    // Mark pending files as UPLOADING
    setQueue((prev) =>
      prev.map((item) =>
        item.status === "QUEUED" || item.status === "FAILED" ? { ...item, status: "UPLOADING" } : item
      )
    );

    try {
      const filesToUpload = pendingFiles.map((p) => p.file);
      const res = await api.uploadBatchFiles(currentBusiness.id, filesToUpload);

      // Match results back to queue items
      setQueue((prev) =>
        prev.map((item) => {
          const match = res.results.find((r) => r.filename === item.name);
          if (match) {
            if (match.status === "SUCCESS") {
              return {
                ...item,
                status: "SUCCESS",
                uploadId: match.upload_id,
                importJobId: match.import_job_id,
                errorMessage: undefined,
              };
            } else {
              return {
                ...item,
                status: "FAILED",
                errorMessage: match.error_message || "Upload failed.",
              };
            }
          }
          return item;
        })
      );
    } catch (err: any) {
      setGlobalError(err.message || "Batch upload failed.");
      setQueue((prev) =>
        prev.map((item) => (item.status === "UPLOADING" ? { ...item, status: "FAILED" } : item))
      );
    } finally {
      setIsUploading(false);
    }
  };

  const successfulUploads = queue.filter((q) => q.status === "SUCCESS");
  const failedUploads = queue.filter((q) => q.status === "FAILED");
  const queuedUploads = queue.filter((q) => q.status === "QUEUED");

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-theme-sage/20 text-theme-sage border border-theme-sage/30">
            MULTI-FILE INGESTION QUEUE
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-theme-text">
          Import Financial Statements
        </h1>
        <p className="text-xs sm:text-sm text-theme-textMuted mt-1">
          Upload multiple bank statements, credit card statements, and receipts simultaneously.
        </p>
      </div>

      {globalError && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{globalError}</span>
        </div>
      )}

      {/* Target Account Selector */}
      <div className="spatial-panel p-5">
        <label className="block text-xs font-bold text-theme-text uppercase tracking-wider mb-2">
          Target Financial Account
        </label>
        <select
          value={selectedAccountId}
          onChange={(e) => setSelectedAccountId(e.target.value)}
          className="w-full sm:w-80 px-3.5 py-2.5 rounded-xl bg-theme-surface border border-theme-border text-theme-text text-xs font-medium focus:outline-none focus:border-theme-sage"
        >
          {accounts.map((acc) => (
            <option key={acc.id} value={acc.id}>
              {acc.name} ({acc.currency})
            </option>
          ))}
        </select>
        <p className="text-[11px] text-theme-textMuted mt-1.5">
          Transactions confirmed from these files will post to this account ledger.
        </p>
      </div>

      {/* Drag & Drop Multi-File Zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`spatial-panel p-8 sm:p-12 text-center border-2 border-dashed transition-all cursor-pointer ${
          dragActive
            ? "border-theme-sage bg-theme-sage/10 scale-[1.01]"
            : "border-theme-border hover:border-theme-sage/60 hover:bg-theme-secondary/40"
        }`}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".csv,.xls,.xlsx,.pdf,.png,.jpg,.jpeg"
          className="hidden"
          onChange={(e) => {
            if (e.target.files) addFilesToQueue(e.target.files);
          }}
        />

        <div className="w-14 h-14 rounded-2xl bg-theme-sage/20 border border-theme-sage/40 flex items-center justify-center mx-auto mb-4 text-theme-sage">
          <UploadCloud className="w-7 h-7" />
        </div>

        <h3 className="text-base font-bold text-theme-text">
          Drag & drop multiple statements here, or <span className="text-theme-sage underline">browse files</span>
        </h3>
        <p className="text-xs text-theme-textMuted mt-1">
          Supports CSV, Excel (.xlsx, .xls), digital PDF statements, and image receipts up to 15 MB each.
        </p>
        <p className="text-[11px] text-theme-textMuted mt-3 flex items-center justify-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-theme-sage" />
          <span>Files are deduplicated via SHA-256 and stored in tenant-isolated encrypted storage.</span>
        </p>
      </div>

      {/* Selected Files Queue */}
      {queue.length > 0 && (
        <div className="spatial-panel p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-theme-text">
                File Queue ({queue.length} {queue.length === 1 ? "file" : "files"})
              </h2>
              <p className="text-xs text-theme-textMuted">
                {successfulUploads.length} uploaded • {queuedUploads.length} queued • {failedUploads.length} failed
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-theme-secondary text-theme-text hover:bg-theme-border flex items-center gap-1.5 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add More</span>
              </button>

              {(queuedUploads.length > 0 || failedUploads.length > 0) && (
                <button
                  onClick={handleUploadAll}
                  disabled={isUploading}
                  className="px-4 py-1.5 rounded-lg text-xs font-bold bg-theme-sage hover:bg-theme-sageDark text-white shadow-sm flex items-center gap-1.5 transition-all disabled:opacity-50"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Uploading Queue...</span>
                    </>
                  ) : (
                    <>
                      <UploadCloud className="w-3.5 h-3.5" />
                      <span>Upload {queuedUploads.length + failedUploads.length} Files</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          <div className="divide-y divide-theme-border">
            {queue.map((item) => (
              <div key={item.id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-theme-secondary flex items-center justify-center text-theme-sage shrink-0">
                    {item.type === "CSV" || item.type === "EXCEL" ? (
                      <FileSpreadsheet className="w-4 h-4" />
                    ) : item.type === "PDF" ? (
                      <FileText className="w-4 h-4" />
                    ) : (
                      <ImageIcon className="w-4 h-4" />
                    )}
                  </div>
                  <div>
                    <p className="text-xs font-bold text-theme-text truncate max-w-xs sm:max-w-md">{item.name}</p>
                    <p className="text-[10px] text-theme-textMuted">
                      {formatBytes(item.size)} • {item.type}
                    </p>
                    {item.errorMessage && (
                      <p className="text-[11px] text-red-500 font-medium mt-0.5">{item.errorMessage}</p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-3 self-end sm:self-auto">
                  {item.status === "QUEUED" && (
                    <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-theme-secondary text-theme-textMuted">
                      Queued
                    </span>
                  )}
                  {item.status === "UPLOADING" && (
                    <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-theme-sage/20 text-theme-sage flex items-center gap-1">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      Uploading
                    </span>
                  )}
                  {item.status === "SUCCESS" && (
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        Uploaded
                      </span>
                      {item.importJobId && (
                        <Link
                          href={`/imports/${item.importJobId}/mapping`}
                          className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-theme-sage text-white hover:bg-theme-sageDark flex items-center gap-1 transition-colors"
                        >
                          <span>Review Mapping</span>
                          <ArrowRight className="w-3 h-3" />
                        </Link>
                      )}
                    </div>
                  )}
                  {item.status === "FAILED" && (
                    <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-red-500/20 text-red-500">
                      Failed
                    </span>
                  )}

                  {item.status !== "UPLOADING" && (
                    <button
                      onClick={() => removeFileFromQueue(item.id)}
                      className="p-1 text-theme-textMuted hover:text-red-500 transition-colors"
                      title="Remove from queue"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
