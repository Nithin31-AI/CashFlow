"use client";

import React, { useState, useEffect } from "react";
import {
  Building2,
  Wallet,
  Plus,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Loader2,
  History,
  Lock,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { useAuth } from "@/lib/auth";
import { api, FinancialAccount, AuditLogItem } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";

export default function SettingsPage() {
  const { currentBusiness, refreshBusinesses } = useAuth();

  // Business Details Form State
  const [bizName, setBizName] = useState("");
  const [currency, setCurrency] = useState("INR");
  const [country, setCountry] = useState("IN");
  const [timezone, setTimezone] = useState("Asia/Kolkata");
  const [isUpdatingBiz, setIsUpdatingBiz] = useState(false);
  const [bizSuccess, setBizSuccess] = useState(false);
  const [bizError, setBizError] = useState<string | null>(null);

  // Accounts State
  const [accounts, setAccounts] = useState<FinancialAccount[]>([]);
  const [newAccName, setNewAccName] = useState("");
  const [newAccType, setNewAccType] = useState<"BANK" | "CREDIT_CARD" | "WALLET" | "OTHER">("BANK");
  const [newAccNumber, setNewAccNumber] = useState("");
  const [isAddingAcc, setIsAddingAcc] = useState(false);
  const [accError, setAccError] = useState<string | null>(null);

  // Audit Logs State
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [loadingAudit, setLoadingAudit] = useState(false);

  const isOwner = currentBusiness?.role === "OWNER";
  const canManageAccounts = currentBusiness?.role === "OWNER" || currentBusiness?.role === "FINANCE_MANAGER";

  useEffect(() => {
    if (currentBusiness) {
      setBizName(currentBusiness.name);
      setCurrency(currentBusiness.currency);
      setCountry(currentBusiness.country);
      setTimezone(currentBusiness.timezone);
      loadAccounts();
      if (canManageAccounts) {
        loadAuditLogs();
      }
    }
  }, [currentBusiness]);

  async function loadAccounts() {
    if (!currentBusiness) return;
    try {
      const data = await api.listAccounts(currentBusiness.id);
      setAccounts(data);
    } catch (err: any) {
      console.error("Failed to load accounts:", err);
    }
  }

  async function loadAuditLogs() {
    if (!currentBusiness) return;
    setLoadingAudit(true);
    try {
      const logs = await api.getAuditLogs(currentBusiness.id);
      setAuditLogs(logs);
    } catch (err: any) {
      console.error("Failed to load audit logs:", err);
    } finally {
      setLoadingAudit(false);
    }
  }

  const handleUpdateBusiness = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentBusiness || !isOwner) return;
    setBizError(null);
    setBizSuccess(false);
    setIsUpdatingBiz(true);

    try {
      await api.updateBusiness(currentBusiness.id, {
        name: bizName,
        currency,
        country,
        timezone,
      });
      await refreshBusinesses();
      setBizSuccess(true);
      setTimeout(() => setBizSuccess(false), 3000);
    } catch (err: any) {
      setBizError(err.message || "Failed to update business settings.");
    } finally {
      setIsUpdatingBiz(false);
    }
  };

  const handleAddAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentBusiness || !canManageAccounts || !newAccName.trim()) return;
    setAccError(null);
    setIsAddingAcc(true);

    try {
      await api.createAccount(currentBusiness.id, {
        name: newAccName,
        account_type: newAccType,
        account_number_mask: newAccNumber ? `•••• ${newAccNumber.slice(-4)}` : undefined,
        currency: currentBusiness.currency,
      });
      setNewAccName("");
      setNewAccNumber("");
      await loadAccounts();
    } catch (err: any) {
      setAccError(err.message || "Failed to create account.");
    } finally {
      setIsAddingAcc(false);
    }
  };

  return (
    <div>
      <Navbar
        title="Business Settings & Financial Accounts"
        subtitle="Manage business profile, ledger accounts, and view security audit logs"
      />

      <div className="mt-6 max-w-5xl mx-auto space-y-8">
        {/* Business Profile Settings */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 sm:p-8">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#E8F8F1] text-[#10A86B] flex items-center justify-center">
                <Building2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 text-base">Business Profile</h3>
                <p className="text-xs text-slate-500">Legal entity name and regional settings</p>
              </div>
            </div>
            {!isOwner && (
              <span className="text-xs text-amber-700 bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200 flex items-center gap-1">
                <Lock className="w-3.5 h-3.5" /> Read-only (Owner permissions required)
              </span>
            )}
          </div>

          {bizError && (
            <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start gap-3">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <span>{bizError}</span>
            </div>
          )}

          {bizSuccess && (
            <div className="mb-6 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#10A86B]" />
              <span>Business settings updated successfully.</span>
            </div>
          )}

          <form onSubmit={handleUpdateBusiness} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                Business Legal Name
              </label>
              <input
                type="text"
                disabled={!isOwner}
                value={bizName}
                onChange={(e) => setBizName(e.target.value)}
                className="block w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-[#10A86B] disabled:opacity-60 disabled:cursor-not-allowed"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                  Operating Currency
                </label>
                <select
                  disabled={!isOwner}
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                  className="block w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-[#10A86B] disabled:opacity-60"
                >
                  <option value="INR">INR (₹ - Indian Rupee)</option>
                  <option value="USD">USD ($ - US Dollar)</option>
                  <option value="EUR">EUR (€ - Euro)</option>
                  <option value="GBP">GBP (£ - British Pound)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                  Country
                </label>
                <select
                  disabled={!isOwner}
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className="block w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-[#10A86B] disabled:opacity-60"
                >
                  <option value="IN">India (IN)</option>
                  <option value="US">United States (US)</option>
                  <option value="UK">United Kingdom (UK)</option>
                  <option value="AE">United Arab Emirates (AE)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
                  Timezone
                </label>
                <input
                  type="text"
                  disabled={!isOwner}
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="block w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-[#10A86B] disabled:opacity-60"
                />
              </div>
            </div>

            {isOwner && (
              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={isUpdatingBiz}
                  className="px-5 py-2.5 bg-[#10A86B] hover:bg-[#0D8554] text-white font-semibold rounded-xl text-xs shadow-sm transition-colors disabled:opacity-50"
                >
                  {isUpdatingBiz ? "Saving..." : "Save Business Profile"}
                </button>
              </div>
            )}
          </form>
        </div>

        {/* Financial Accounts Section */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 sm:p-8">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                <Wallet className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 text-base">Financial Accounts</h3>
                <p className="text-xs text-slate-500">Bank accounts, corporate cards, and payment wallets</p>
              </div>
            </div>
          </div>

          {accError && (
            <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
              {accError}
            </div>
          )}

          {/* Existing Accounts List */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
            {accounts.map((acc) => (
              <div
                key={acc.id}
                className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 flex items-start justify-between"
              >
                <div>
                  <p className="text-sm font-bold text-slate-900">{acc.name}</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {acc.account_type} {acc.account_number_mask ? `• ${acc.account_number_mask}` : ""}
                  </p>
                  <span className="inline-block mt-2 px-2 py-0.5 rounded bg-emerald-50 text-[#10A86B] font-mono text-[10px] font-semibold border border-emerald-200">
                    {acc.currency}
                  </span>
                </div>
                <span className="w-2 h-2 rounded-full bg-[#10A86B] mt-1" title="Active Account" />
              </div>
            ))}
          </div>

          {/* Add Account Form */}
          {canManageAccounts && (
            <form onSubmit={handleAddAccount} className="pt-4 border-t border-slate-100">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-3">
                Add New Financial Account
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <input
                  type="text"
                  required
                  placeholder="Account Name (e.g. Current Account)"
                  value={newAccName}
                  onChange={(e) => setNewAccName(e.target.value)}
                  className="px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#10A86B]"
                />
                <select
                  value={newAccType}
                  onChange={(e) => setNewAccType(e.target.value as any)}
                  className="px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#10A86B]"
                >
                  <option value="BANK">Bank Account</option>
                  <option value="CREDIT_CARD">Credit Card</option>
                  <option value="WALLET">Digital Wallet</option>
                  <option value="OTHER">Other Account</option>
                </select>
                <div className="flex gap-2">
                  <input
                    type="text"
                    maxLength={10}
                    placeholder="Last 4 Digits (Optional)"
                    value={newAccNumber}
                    onChange={(e) => setNewAccNumber(e.target.value)}
                    className="flex-1 px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#10A86B]"
                  />
                  <button
                    type="submit"
                    disabled={isAddingAcc || !newAccName.trim()}
                    className="inline-flex items-center gap-1 px-4 py-2 bg-[#10A86B] hover:bg-[#0D8554] text-white text-xs font-semibold rounded-xl transition-colors disabled:opacity-50 shrink-0 shadow-sm"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add</span>
                  </button>
                </div>
              </div>
            </form>
          )}
        </div>

        {/* Security & Audit Logs Section */}
        {canManageAccounts && (
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 sm:p-8">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
                  <History className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-base">Security Audit Trail</h3>
                  <p className="text-xs text-slate-500">Immutable chronological log of critical business actions</p>
                </div>
              </div>
              <span className="text-xs text-slate-400 font-mono">
                {auditLogs.length} logged events
              </span>
            </div>

            <div className="overflow-x-auto max-h-60 border border-slate-100 rounded-xl">
              <table className="w-full text-left text-xs text-slate-600">
                <thead className="bg-slate-50 text-[10px] font-bold text-slate-500 uppercase tracking-wider sticky top-0">
                  <tr>
                    <th className="py-2.5 px-4">Timestamp</th>
                    <th className="py-2.5 px-4">Action</th>
                    <th className="py-2.5 px-4">Resource</th>
                    <th className="py-2.5 px-4">IP Address</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50/70">
                      <td className="py-2.5 px-4 font-mono text-[11px] text-slate-500 whitespace-nowrap">
                        {formatDateTime(log.created_at)}
                      </td>
                      <td className="py-2.5 px-4 font-semibold text-slate-800">
                        {log.action}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-[11px] text-slate-500">
                        {log.resource_type || "—"}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-[11px] text-slate-400">
                        {log.ip_address || "internal"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
