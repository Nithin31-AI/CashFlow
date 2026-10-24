"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Building2, ArrowRight, ShieldCheck, Loader2, AlertCircle } from "lucide-react";
import { Logo } from "@/components/Logo";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function OnboardingPage() {
  const [businessName, setBusinessName] = useState("");
  const [currency, setCurrency] = useState("INR");
  const [country, setCountry] = useState("IN");
  const [timezone, setTimezone] = useState("Asia/Kolkata");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { refreshBusinesses, switchBusiness } = useAuth();
  const router = useRouter();

  const handleCreateBusiness = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const biz = await api.createBusiness({
        name: businessName,
        currency,
        country,
        timezone,
      });

      await refreshBusinesses();
      switchBusiness(biz);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to create business profile.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-lg text-center mb-8">
        <div className="inline-block mb-4">
          <Logo size="lg" showTagline={true} href="/" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          Set up your business workspace
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          cashFlow provides isolated financial intelligence for every business you manage.
        </p>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-lg">
        <div className="bg-white border border-slate-200/80 rounded-2xl shadow-sm p-6 sm:p-10">
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start gap-3">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form className="space-y-6" onSubmit={handleCreateBusiness}>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
                Business / Company Name
              </label>
              <div className="mt-1.5 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Building2 className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  required
                  value={businessName}
                  onChange={(e) => setBusinessName(e.target.value)}
                  placeholder="e.g. Apex Consulting LLP"
                  className="block w-full pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-[#10A86B] focus:border-transparent transition-colors"
                />
              </div>
              <p className="mt-1 text-xs text-slate-500">
                You will be granted OWNER permissions for this business.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
                  Default Currency
                </label>
                <select
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                  className="mt-1.5 block w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-[#10A86B] focus:border-transparent"
                >
                  <option value="INR">INR (₹ - Indian Rupee)</option>
                  <option value="USD">USD ($ - US Dollar)</option>
                  <option value="EUR">EUR (€ - Euro)</option>
                  <option value="GBP">GBP (£ - British Pound)</option>
                  <option value="AED">AED (د.إ - UAE Dirham)</option>
                  <option value="SGD">SGD (S$ - Singapore Dollar)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
                  Country
                </label>
                <select
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className="mt-1.5 block w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-[#10A86B] focus:border-transparent"
                >
                  <option value="IN">India</option>
                  <option value="US">United States</option>
                  <option value="UK">United Kingdom</option>
                  <option value="AE">United Arab Emirates</option>
                  <option value="SG">Singapore</option>
                </select>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-[#E8F8F1] border border-[#A3E6CD]/60 text-xs text-[#0D8554] flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 shrink-0" />
              <span>
                Tenant Isolation: Your data will be isolated and only accessible to authorized members.
              </span>
            </div>

            <button
              type="submit"
              disabled={isLoading || !businessName.trim()}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm font-semibold text-white bg-[#10A86B] hover:bg-[#0D8554] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#10A86B] transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Creating Workspace...</span>
                </>
              ) : (
                <>
                  <span>Create Workspace & Enter</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
