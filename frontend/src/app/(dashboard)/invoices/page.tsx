"use client";

import React, { useEffect, useState } from "react";
import {
  Receipt,
  Plus,
  Clock,
  CheckCircle2,
  AlertCircle,
  Calendar,
  CreditCard,
  Loader2,
  DollarSign,
  Search,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { api, InvoiceRecord } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";

export default function InvoicesPage() {
  const { currentBusiness } = useAuth();
  const [invoices, setInvoices] = useState<InvoiceRecord[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState<InvoiceRecord | null>(null);

  // Form states
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [customerEmail, setCustomerEmail] = useState("");
  const [issueDate, setIssueDate] = useState(new Date().toISOString().split("T")[0]);
  const [dueDate, setDueDate] = useState(
    new Date(Date.now() + 15 * 86400000).toISOString().split("T")[0]
  );
  const [amount, setAmount] = useState("");
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Payment form state
  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("BANK_TRANSFER");
  const [paymentRef, setPaymentRef] = useState("");

  const loadInvoices = async () => {
    if (!currentBusiness) return;
    setIsLoading(true);
    try {
      const data = await api.listInvoices(currentBusiness.id);
      setInvoices(data);
    } catch (err: any) {
      console.error("Failed to load invoices:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadInvoices();
  }, [currentBusiness]);

  const handleCreateInvoice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentBusiness) return;
    setIsSubmitting(true);
    setFormError(null);
    try {
      const total = parseFloat(amount);
      if (isNaN(total) || total <= 0) {
        throw new Error("Please enter a valid invoice amount.");
      }

      await api.createInvoice(currentBusiness.id, {
        invoice_number: invoiceNumber,
        customer_name: customerName,
        customer_email: customerEmail || undefined,
        issue_date: issueDate,
        due_date: dueDate,
        currency: currentBusiness.currency || "INR",
        subtotal: total,
        tax_amount: 0,
        total_amount: total,
        notes: notes || undefined,
      });

      setShowCreateModal(false);
      // Reset form
      setInvoiceNumber("");
      setCustomerName("");
      setCustomerEmail("");
      setAmount("");
      setNotes("");
      loadInvoices();
    } catch (err: any) {
      setFormError(err.message || "Failed to create invoice.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRecordPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentBusiness || !showPaymentModal) return;
    setIsSubmitting(true);
    setFormError(null);
    try {
      const pAmt = parseFloat(paymentAmount);
      if (isNaN(pAmt) || pAmt <= 0) {
        throw new Error("Please enter a valid payment amount.");
      }

      await api.recordPayment(currentBusiness.id, {
        invoice_id: showPaymentModal.id,
        payment_date: new Date().toISOString().split("T")[0],
        amount: pAmt,
        currency: showPaymentModal.currency,
        payment_method: paymentMethod,
        reference_number: paymentRef || undefined,
      });

      setShowPaymentModal(null);
      setPaymentAmount("");
      setPaymentRef("");
      loadInvoices();
    } catch (err: any) {
      setFormError(err.message || "Failed to record payment.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredInvoices = invoices.filter((inv) => {
    if (filterStatus === "ALL") return true;
    return inv.status === filterStatus;
  });

  const currency = currentBusiness?.currency || "INR";
  const totalReceivables = invoices
    .filter((inv) => ["SENT", "PARTIALLY_PAID", "OVERDUE"].includes(inv.status))
    .reduce((sum, inv) => sum + (inv.total_amount - (inv.amount_paid || 0)), 0);

  return (
    <div className="space-y-6 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-theme-sage/20 text-theme-sage border border-theme-sage/30">
              RECEIVABLES & CASH INFLOW ENGINE
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-theme-text">
            Customer Invoices
          </h1>
          <p className="text-xs sm:text-sm text-theme-textMuted mt-1">
            Track customer billings, payment delay predictions, and cash collection settlements.
          </p>
        </div>

        <button
          onClick={() => {
            setInvoiceNumber(`INV-${Math.floor(1000 + Math.random() * 9000)}`);
            setShowCreateModal(true);
          }}
          className="px-4 py-2 rounded-xl text-xs font-bold bg-theme-sage hover:bg-theme-sageDark text-white shadow-sm flex items-center gap-2 transition-all self-start sm:self-auto"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Invoice</span>
        </button>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="spatial-card p-4">
          <span className="text-[10px] font-bold text-theme-textMuted uppercase tracking-wider block">
            Outstanding Receivables
          </span>
          <p className="text-2xl font-black text-theme-text mt-1">{formatCurrency(totalReceivables, currency)}</p>
          <span className="text-[10px] text-theme-textMuted mt-1 block">Unpaid invoices strictly excluded from cash</span>
        </div>

        <div className="spatial-card p-4">
          <span className="text-[10px] font-bold text-theme-textMuted uppercase tracking-wider block">Total Invoices</span>
          <p className="text-2xl font-black text-theme-text mt-1">{invoices.length}</p>
          <span className="text-[10px] text-theme-textMuted mt-1 block">Active billing records</span>
        </div>

        <div className="spatial-card p-4">
          <span className="text-[10px] font-bold text-theme-textMuted uppercase tracking-wider block">Overdue Invoices</span>
          <p className="text-2xl font-black text-red-500 mt-1">
            {invoices.filter((i) => i.status === "OVERDUE").length}
          </p>
          <span className="text-[10px] text-theme-textMuted mt-1 block">Action required for cash acceleration</span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1.5 p-1 rounded-xl bg-theme-secondary border border-theme-border w-fit">
        {["ALL", "SENT", "PARTIALLY_PAID", "PAID", "OVERDUE"].map((st) => (
          <button
            key={st}
            onClick={() => setFilterStatus(st)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              filterStatus === st
                ? "bg-theme-surface text-theme-text shadow-sm"
                : "text-theme-textMuted hover:text-theme-text"
            }`}
          >
            {st.replace("_", " ")}
          </button>
        ))}
      </div>

      {/* Invoices Table */}
      <div className="spatial-panel p-5">
        {isLoading ? (
          <div className="py-12 flex justify-center">
            <Loader2 className="w-6 h-6 text-theme-sage animate-spin" />
          </div>
        ) : filteredInvoices.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-theme-border text-theme-textMuted uppercase text-[10px]">
                  <th className="py-2.5 px-3">Invoice #</th>
                  <th className="py-2.5 px-3">Customer</th>
                  <th className="py-2.5 px-3">Due Date</th>
                  <th className="py-2.5 px-3">Predicted Delay</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Total</th>
                  <th className="py-2.5 px-3 text-right">Paid</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-theme-border">
                {filteredInvoices.map((inv) => {
                  const unpaid = inv.total_amount - (inv.amount_paid || 0);
                  return (
                    <tr key={inv.id} className="hover:bg-theme-secondary/40 transition-colors">
                      <td className="py-3 px-3 font-bold text-theme-text">{inv.invoice_number}</td>
                      <td className="py-3 px-3 font-semibold text-theme-text">
                        {inv.customer_name}
                        {inv.customer_email && (
                          <span className="block text-[10px] text-theme-textMuted font-normal">
                            {inv.customer_email}
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-3 text-theme-textMuted">{formatDate(inv.due_date)}</td>
                      <td className="py-3 px-3">
                        {inv.predicted_delay_days > 0 ? (
                          <span className="text-amber-500 font-semibold text-[11px] flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            +{inv.predicted_delay_days} days
                          </span>
                        ) : (
                          <span className="text-theme-textMuted text-[11px]">On time</span>
                        )}
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`text-[9px] font-bold uppercase px-2 py-0.5 rounded ${
                            inv.status === "PAID"
                              ? "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400"
                              : inv.status === "OVERDUE"
                              ? "bg-red-500/20 text-red-500"
                              : "bg-amber-500/20 text-amber-600"
                          }`}
                        >
                          {inv.status}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right font-extrabold text-theme-text">
                        {formatCurrency(inv.total_amount, inv.currency)}
                      </td>
                      <td className="py-3 px-3 text-right font-semibold text-emerald-600 dark:text-emerald-400">
                        {formatCurrency(inv.amount_paid || 0, inv.currency)}
                      </td>
                      <td className="py-3 px-3 text-right">
                        {unpaid > 0 && (
                          <button
                            onClick={() => {
                              setShowPaymentModal(inv);
                              setPaymentAmount(unpaid.toString());
                            }}
                            className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-theme-sage text-white hover:bg-theme-sageDark transition-colors"
                          >
                            Record Payment
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center text-xs text-theme-textMuted">
            <Receipt className="w-8 h-8 text-theme-textMuted mx-auto mb-2 opacity-50" />
            <p>No invoices match the selected filter.</p>
          </div>
        )}
      </div>

      {/* CREATE INVOICE MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="spatial-panel p-6 max-w-md w-full shadow-2xl">
            <h2 className="text-base font-bold text-theme-text mb-4">Create Customer Invoice</h2>
            {formError && (
              <div className="p-3 mb-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-500 text-xs">
                {formError}
              </div>
            )}
            <form onSubmit={handleCreateInvoice} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-theme-textMuted font-bold uppercase text-[10px] mb-1">
                  Invoice Number
                </label>
                <input
                  type="text"
                  required
                  value={invoiceNumber}
                  onChange={(e) => setInvoiceNumber(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-theme-surface border border-theme-border text-theme-text focus:border-theme-sage outline-none"
                />
              </div>
              <div>
                <label className="block text-theme-textMuted font-bold uppercase text-[10px] mb-1">
                  Customer / Client Name
                </label>
                <input
                  type="text"
                  required
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  placeholder="e.g. Acme Technologies"
                  className="w-full px-3 py-2 rounded-xl bg-theme-surface border border-theme-border text-theme-text focus:border-theme-sage outline-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-theme-textMuted font-bold uppercase text-[10px] mb-1">
                    Issue Date
                  </label>
                  <input
                    type="date"
                    required
                    value={issueDate}
                    onChange={(e) => setIssueDate(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-theme-surface border border-theme-border text-theme-text focus:border-theme-sage outline-none"
                  />
                </div>
                <div>
                  <label className="block text-theme-textMuted font-bold uppercase text-[10px] mb-1">
                    Due Date
                  </label>
                  <input
                    type="date"
                    required
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-theme-surface border border-theme-border text-theme-text focus:border-theme-sage outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="block text-theme-textMuted font-bold uppercase text-[10px] mb-1">
                  Total Amount ({currency} ₹)
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="e.g. 50000.00"
                  className="w-full px-3 py-2 rounded-xl bg-theme-surface border border-theme-border text-theme-text focus:border-theme-sage outline-none"
                />
              </div>
              <div>
                <label className="block text-theme-textMuted font-bold uppercase text-[10px] mb-1">
                  Notes / Terms
                </label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Net 15 days"
                  className="w-full px-3 py-2 rounded-xl bg-theme-surface border border-theme-border text-theme-text focus:border-theme-sage outline-none"
                />
              </div>

              <div className="flex justify-end gap-2.5 pt-3 border-t border-theme-border">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl text-theme-textMuted hover:bg-theme-secondary font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-theme-sage hover:bg-theme-sageDark text-white font-bold transition-all disabled:opacity-50"
                >
                  {isSubmitting ? "Creating..." : "Save Invoice"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* RECORD PAYMENT MODAL */}
      {showPaymentModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="spatial-panel p-6 max-w-md w-full shadow-2xl">
            <h2 className="text-base font-bold text-theme-text mb-1">Record Payment</h2>
            <p className="text-xs text-theme-textMuted mb-4">
              Allocate cash received for {showPaymentModal.invoice_number} ({showPaymentModal.customer_name})
            </p>

            {formError && (
              <div className="p-3 mb-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-500 text-xs">
                {formError}
              </div>
            )}

            <form onSubmit={handleRecordPayment} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-theme-textMuted font-bold uppercase text-[10px] mb-1">
                  Payment Amount ({showPaymentModal.currency} ₹)
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-theme-surface border border-theme-border text-theme-text focus:border-theme-sage outline-none"
                />
              </div>
              <div>
                <label className="block text-theme-textMuted font-bold uppercase text-[10px] mb-1">
                  Payment Method
                </label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-theme-surface border border-theme-border text-theme-text focus:border-theme-sage outline-none"
                >
                  <option value="BANK_TRANSFER">Bank Transfer (NEFT/RTGS/IMPS)</option>
                  <option value="UPI">UPI / QR Code</option>
                  <option value="CREDIT_CARD">Credit Card</option>
                  <option value="CHEQUE">Cheque</option>
                  <option value="CASH">Cash</option>
                </select>
              </div>
              <div>
                <label className="block text-theme-textMuted font-bold uppercase text-[10px] mb-1">
                  Reference Number / UTR
                </label>
                <input
                  type="text"
                  value={paymentRef}
                  onChange={(e) => setPaymentRef(e.target.value)}
                  placeholder="e.g. UTR-982141"
                  className="w-full px-3 py-2 rounded-xl bg-theme-surface border border-theme-border text-theme-text focus:border-theme-sage outline-none"
                />
              </div>

              <div className="flex justify-end gap-2.5 pt-3 border-t border-theme-border">
                <button
                  type="button"
                  onClick={() => setShowPaymentModal(null)}
                  className="px-4 py-2 rounded-xl text-theme-textMuted hover:bg-theme-secondary font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-theme-sage hover:bg-theme-sageDark text-white font-bold transition-all disabled:opacity-50"
                >
                  {isSubmitting ? "Allocating..." : "Confirm Payment"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
