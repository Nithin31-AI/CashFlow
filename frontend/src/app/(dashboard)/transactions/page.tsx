"use client";

import React, { useEffect, useState } from "react";
import {
  ArrowLeftRight,
  Plus,
  Search,
  Filter,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  Loader2,
  Calendar,
  Building2,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { api, TransactionRecord, FinancialAccount } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";

const CATEGORIES = [
  "ALL",
  "REVENUE",
  "PAYROLL",
  "RENT",
  "SOFTWARE",
  "CONSULTING",
  "UTILITIES",
  "MARKETING",
  "TAX",
  "INTERNAL_TRANSFER",
  "OTHER",
];

export default function TransactionsPage() {
  const { currentBusiness } = useAuth();
  const [transactions, setTransactions] = useState<TransactionRecord[]>([]);
  const [accounts, setAccounts] = useState<FinancialAccount[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("ALL");
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  // New Transaction Form State
  const [accountId, setAccountId] = useState("");
  const [txDate, setTxDate] = useState(new Date().toISOString().split("T")[0]);
  const [amount, setAmount] = useState("");
  const [txType, setTxType] = useState<"INFLOW" | "OUTFLOW" | "INTERNAL_TRANSFER">("OUTFLOW");
  const [category, setCategory] = useState("SOFTWARE");
  const [destAccountId, setDestAccountId] = useState("");
  const [description, setDescription] = useState("");
  const [refNum, setRefNum] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const loadData = async () => {
    if (!currentBusiness) return;
    setIsLoading(true);
    try {
      const [txs, accs] = await Promise.all([
        api.listTransactions(currentBusiness.id, {
          category: selectedCategory === "ALL" ? undefined : selectedCategory,
          search: search || undefined,
        }),
        api.listAccounts(currentBusiness.id),
      ]);
      setTransactions(txs);
      setAccounts(accs);
      if (accs.length > 0 && !accountId) {
        setAccountId(accs[0].id);
        if (accs.length > 1) setDestAccountId(accs[1].id);
      }
    } catch (err: any) {
      console.error("Failed to load transactions:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [currentBusiness, selectedCategory]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadData();
  };

  const handleCreateTransaction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentBusiness) return;
    setIsSubmitting(true);
    setFormError(null);
    try {
      const parsedAmount = parseFloat(amount);
      if (isNaN(parsedAmount) || parsedAmount <= 0) {
        throw new Error("Please enter a valid positive number for amount.");
      }

      const isTransfer = txType === "INTERNAL_TRANSFER";
      const finalAmount = txType === "OUTFLOW" ? -parsedAmount : parsedAmount;

      await api.createTransaction(currentBusiness.id, {
        account_id: accountId,
        transaction_date: txDate,
        amount: finalAmount,
        currency: currentBusiness.currency || "INR",
        description,
        category: isTransfer ? "INTERNAL_TRANSFER" : category,
        transaction_type: txType,
        is_internal_transfer: isTransfer,
        transfer_counterpart_account_id: isTransfer ? destAccountId : undefined,
        reference_number: refNum || undefined,
      });

      setShowModal(false);
      setDescription("");
      setAmount("");
      setRefNum("");
      loadData();
    } catch (err: any) {
      setFormError(err.message || "Failed to create transaction.");
    } finally {
      setIsSubmitting(false);
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
              FINANCIAL LEDGER
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-theme-text">
            Transactions & Ledger
          </h1>
          <p className="text-xs sm:text-sm text-theme-textMuted mt-1">
            Traceable financial transactions with automatic internal transfer isolation.
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 rounded-xl text-xs font-bold bg-theme-sage hover:bg-theme-sageDark text-white shadow-sm flex items-center gap-2 transition-all self-start sm:self-auto"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Record Transaction</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-3.5 rounded-2xl bg-theme-surface border border-theme-border shadow-sm">
        <form onSubmit={handleSearch} className="flex-1 flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-theme-textMuted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by description or reference number..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-theme-secondary border border-theme-border text-xs text-theme-text focus:outline-none focus:border-theme-sage"
            />
          </div>
          <button
            type="submit"
            className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-theme-secondary text-theme-text hover:bg-theme-border transition-colors"
          >
            Search
          </button>
        </form>

        <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 rounded-xl bg-theme-secondary border border-theme-border text-xs text-theme-text font-medium focus:outline-none focus:border-theme-sage shrink-0"
          >
            {CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                Category: {cat.replace("_", " ")}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Ledger Table */}
      <div className="spatial-panel p-5">
        {isLoading ? (
          <div className="py-12 flex justify-center">
            <Loader2 className="w-6 h-6 text-theme-sage animate-spin" />
          </div>
        ) : transactions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-theme-border text-theme-textMuted uppercase text-[10px]">
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3">Description</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-theme-border">
                {transactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-theme-secondary/40 transition-colors">
                    <td className="py-3 px-3 font-medium text-theme-textMuted">{formatDate(tx.transaction_date)}</td>
                    <td className="py-3 px-3">
                      <span className="font-bold text-theme-text block">{tx.description}</span>
                      {tx.reference_number && (
                        <span className="text-[10px] text-theme-textMuted font-mono block mt-0.5">
                          Ref: {tx.reference_number}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          tx.is_internal_transfer
                            ? "bg-purple-500/20 text-purple-600 dark:text-purple-400 border border-purple-500/30"
                            : "bg-theme-secondary text-theme-text border border-theme-border"
                        }`}
                      >
                        {tx.category.replace("_", " ")}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="text-[10px] font-semibold text-theme-textMuted uppercase">
                        {tx.transaction_type.replace("_", " ")}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`text-[9px] font-bold uppercase px-2 py-0.5 rounded ${
                          tx.status === "RECONCILED"
                            ? "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400"
                            : "bg-theme-secondary text-theme-textMuted"
                        }`}
                      >
                        {tx.status}
                      </span>
                    </td>
                    <td
                      className={`py-3 px-3 text-right font-extrabold ${
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
          <div className="py-12 text-center text-xs text-theme-textMuted">
            <ArrowLeftRight className="w-8 h-8 text-theme-textMuted mx-auto mb-2 opacity-50" />
            <p>No transactions match the current filters.</p>
          </div>
        )}
      </div>

      {/* RECORD TRANSACTION MODAL */}
      {showModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="spatial-panel p-6 max-w-md w-full shadow-2xl">
            <h2 className="text-base font-bold text-theme-text mb-4">Record Financial Movement</h2>
            {formError && (
              <div className="p-3 mb-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-500 text-xs">
                {formError}
              </div>
            )}
            <form onSubmit={handleCreateTransaction} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-theme-textMuted font-bold uppercase text-[10px] mb-1">Movement Type</label>
                <div className="grid grid-cols-3 gap-2">
                  {(["OUTFLOW", "INFLOW", "INTERNAL_TRANSFER"] as const).map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setTxType(t)}
                      className={`py-2 rounded-xl text-xs font-bold border transition-all ${
                        txType === t
                          ? "bg-theme-sage text-white border-theme-sage shadow-sm"
                          : "bg-theme-surface text-theme-textMuted border-theme-border"
                      }`}
                    >
                      {t === "OUTFLOW" ? "Expense" : t === "INFLOW" ? "Income" : "Transfer"}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-theme-textMuted font-bold uppercase text-[10px] mb-1">
                  Source Account
                </label>
                <select
                  value={accountId}
                  onChange={(e) => setAccountId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-theme-surface border border-theme-border text-theme-text focus:border-theme-sage outline-none"
                >
                  {accounts.map((acc) => (
                    <option key={acc.id} value={acc.id}>
                      {acc.name} ({acc.currency})
                    </option>
                  ))}
                </select>
              </div>

              {txType === "INTERNAL_TRANSFER" && (
                <div>
                  <label className="block text-theme-textMuted font-bold uppercase text-[10px] mb-1">
                    Destination Account
                  </label>
                  <select
                    value={destAccountId}
                    onChange={(e) => setDestAccountId(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-theme-surface border border-theme-border text-theme-text focus:border-theme-sage outline-none"
                  >
                    {accounts.map((acc) => (
                      <option key={acc.id} value={acc.id}>
                        {acc.name} ({acc.currency})
                      </option>
                    ))}
                  </select>
                  <p className="text-[10px] text-theme-textMuted mt-1">
                    Internal transfers create balanced reciprocal ledger entries excluded from revenue/expenses.
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-theme-textMuted font-bold uppercase text-[10px] mb-1">Amount (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="e.g. 15000"
                    className="w-full px-3 py-2 rounded-xl bg-theme-surface border border-theme-border text-theme-text focus:border-theme-sage outline-none"
                  />
                </div>
                <div>
                  <label className="block text-theme-textMuted font-bold uppercase text-[10px] mb-1">Date</label>
                  <input
                    type="date"
                    required
                    value={txDate}
                    onChange={(e) => setTxDate(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-theme-surface border border-theme-border text-theme-text focus:border-theme-sage outline-none"
                  />
                </div>
              </div>

              {txType !== "INTERNAL_TRANSFER" && (
                <div>
                  <label className="block text-theme-textMuted font-bold uppercase text-[10px] mb-1">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-theme-surface border border-theme-border text-theme-text focus:border-theme-sage outline-none"
                  >
                    {CATEGORIES.filter((c) => c !== "ALL" && c !== "INTERNAL_TRANSFER").map((c) => (
                      <option key={c} value={c}>
                        {c.replace("_", " ")}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-theme-textMuted font-bold uppercase text-[10px] mb-1">Description</label>
                <input
                  type="text"
                  required
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="e.g. Google Cloud compute instance"
                  className="w-full px-3 py-2 rounded-xl bg-theme-surface border border-theme-border text-theme-text focus:border-theme-sage outline-none"
                />
              </div>

              <div>
                <label className="block text-theme-textMuted font-bold uppercase text-[10px] mb-1">
                  Reference # (Optional)
                </label>
                <input
                  type="text"
                  value={refNum}
                  onChange={(e) => setRefNum(e.target.value)}
                  placeholder="e.g. TX-2026-99"
                  className="w-full px-3 py-2 rounded-xl bg-theme-surface border border-theme-border text-theme-text focus:border-theme-sage outline-none"
                />
              </div>

              <div className="flex justify-end gap-2.5 pt-3 border-t border-theme-border">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl text-theme-textMuted hover:bg-theme-secondary font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-theme-sage hover:bg-theme-sageDark text-white font-bold transition-all disabled:opacity-50"
                >
                  {isSubmitting ? "Recording..." : "Record Entry"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
