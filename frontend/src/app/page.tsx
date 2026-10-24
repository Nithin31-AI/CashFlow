"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, ShieldCheck, TrendingUp, Receipt, GitCompare, Layers } from "lucide-react";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAuth } from "@/lib/auth";

export default function HomePage() {
  const { user, token, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && token && user) {
      router.push("/dashboard");
    }
  }, [token, user, isLoading, router]);

  return (
    <div className="min-h-screen bg-theme-bg text-theme-text flex flex-col selection:bg-theme-sage selection:text-white transition-colors">
      {/* Top Navbar */}
      <header className="border-b border-theme-border px-6 py-4 flex items-center justify-between max-w-7xl mx-auto w-full">
        <Logo size="md" showTagline={true} href="/" />
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <Link
            href="/login"
            className="px-4 py-2 text-xs font-semibold text-theme-textMuted hover:text-theme-text transition-colors"
          >
            Sign In
          </Link>
          <Link
            href="/register"
            className="px-4 py-2 bg-theme-sage hover:bg-theme-sageDark text-white text-xs font-bold rounded-xl transition-all shadow-sm"
          >
            Get Started
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center text-center px-6 py-16 max-w-5xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-theme-sage/15 border border-theme-sage/30 text-theme-sage text-xs font-bold mb-8">
          <ShieldCheck className="w-4 h-4" />
          <span>Stage 2: Financial Engine, Reconciliation & Forecasting</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-theme-text mb-6 leading-tight max-w-4xl">
          PLAN • FORECAST • GROW with <span className="text-theme-sage">cashFlow</span>
        </h1>

        <p className="text-base sm:text-lg text-theme-textMuted max-w-2xl mx-auto mb-10 leading-relaxed">
          AI-powered financial intelligence SaaS platform for small service-based businesses. Understand your actual cash position, forecast runway, and accelerate receivables collection.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto mb-16">
          <Link
            href="/register"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 bg-theme-sage hover:bg-theme-sageDark text-white font-bold rounded-xl text-sm shadow-lg shadow-theme-sage/20 transition-all hover:scale-[1.02]"
          >
            <span>Launch Your Workspace</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/login"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 bg-theme-surface hover:bg-theme-secondary text-theme-text font-bold rounded-xl text-sm border border-theme-border transition-all"
          >
            <span>Access Dashboard</span>
          </Link>
        </div>

        {/* Feature Highlights Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full text-left">
          <div className="spatial-card p-6">
            <div className="w-10 h-10 rounded-xl bg-theme-sage/20 text-theme-sage flex items-center justify-center mb-4">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h2 className="text-sm font-bold text-theme-text mb-1">Cash-Flow Forecasting</h2>
            <p className="text-xs text-theme-textMuted leading-relaxed">
              7, 30, 90, 180, and 365-day cash projections with confidence bands and cash-shortage early warnings.
            </p>
          </div>

          <div className="spatial-card p-6">
            <div className="w-10 h-10 rounded-xl bg-theme-sage/20 text-theme-sage flex items-center justify-center mb-4">
              <GitCompare className="w-5 h-5" />
            </div>
            <h2 className="text-sm font-bold text-theme-text mb-1">Intelligent Reconciliation</h2>
            <p className="text-xs text-theme-textMuted leading-relaxed">
              Automated matching of bank statement transactions to customer invoices with explainable signals and review gates.
            </p>
          </div>

          <div className="spatial-card p-6">
            <div className="w-10 h-10 rounded-xl bg-theme-sage/20 text-theme-sage flex items-center justify-center mb-4">
              <Receipt className="w-5 h-5" />
            </div>
            <h2 className="text-sm font-bold text-theme-text mb-1">Receivables & Delays</h2>
            <p className="text-xs text-theme-textMuted leading-relaxed">
              Predictive customer payment latency models to forecast when customer invoices will genuinely convert to cash.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-theme-border py-6 px-6 text-center text-xs text-theme-textMuted">
        <p>© 2026 cashFlow. PLAN • FORECAST • GROW. All rights reserved.</p>
      </footer>
    </div>
  );
}
