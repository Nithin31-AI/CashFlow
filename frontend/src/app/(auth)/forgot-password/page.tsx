"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight, Mail, AlertCircle, CheckCircle2, Loader2, KeyRound } from "lucide-react";
import { Logo } from "@/components/Logo";
import { api } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [devToken, setDevToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setDevToken(null);
    setIsLoading(true);

    try {
      const res = await api.forgotPassword(email);
      setMessage(res.message);
      if (res.dev_reset_token) {
        setDevToken(res.dev_reset_token);
      }
    } catch (err: any) {
      setError(err.message || "Failed to process password recovery request.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#111820] flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-block mb-6">
          <Logo size="lg" showTagline={true} href="/" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Reset your password
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          Enter your registered email address to receive reset instructions.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-slate-900 border border-slate-800 py-8 px-4 shadow-xl sm:rounded-2xl sm:px-10">
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-start gap-3">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {message ? (
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-emerald-300">Instructions Sent</p>
                  <p className="mt-1 text-slate-300 text-xs leading-relaxed">{message}</p>
                </div>
              </div>

              {devToken && (
                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs">
                  <div className="flex items-center gap-1.5 font-bold text-amber-400 mb-1">
                    <KeyRound className="w-4 h-4" />
                    <span>Development Environment Recovery Token</span>
                  </div>
                  <p className="text-slate-300 mb-3">
                    In development mode without an SMTP provider, use this direct link to complete testing:
                  </p>
                  <Link
                    href={`/reset-password?token=${devToken}`}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#10A86B] hover:bg-[#0D8554] text-white rounded-lg font-semibold text-xs transition-colors"
                  >
                    Open Reset Password Page
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              )}

              <div className="text-center pt-2">
                <Link
                  href="/login"
                  className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" /> Back to Sign In
                </Link>
              </div>
            </div>
          ) : (
            <form className="space-y-5" onSubmit={handleSubmit}>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Registered Email Address
                </label>
                <div className="mt-1.5 relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@company.com"
                    className="block w-full pl-9 pr-3 py-2.5 bg-slate-950/60 border border-slate-700 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-[#10A86B] focus:border-transparent transition-colors"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm font-semibold text-white bg-[#10A86B] hover:bg-[#0D8554] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 focus:ring-[#10A86B] transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <span>Send Recovery Link</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>

              <div className="text-center pt-2">
                <Link
                  href="/login"
                  className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
                >
                  <ArrowLeft className="w-3.5 h-3.5" /> Return to Login
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
