"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowRight, Lock, KeyRound, AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import { Logo } from "@/components/Logo";
import { api } from "@/lib/api";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const t = searchParams.get("token");
    if (t) setToken(t);
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!token.trim()) {
      setError("Password reset token is missing.");
      return;
    }

    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsLoading(true);

    try {
      const res = await api.resetPassword(token, newPassword);
      setSuccess(res.message);
    } catch (err: any) {
      setError(err.message || "Failed to reset password. The link may have expired.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 py-8 px-4 shadow-xl sm:rounded-2xl sm:px-10">
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {success ? (
        <div className="text-center space-y-6">
          <div className="w-12 h-12 bg-emerald-500/20 text-[#10A86B] rounded-2xl flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white mb-2">Password Reset Successfully</h3>
            <p className="text-xs text-slate-400 leading-relaxed">{success}</p>
          </div>
          <Link
            href="/login"
            className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm font-semibold text-white bg-[#10A86B] hover:bg-[#0D8554] transition-colors shadow-md"
          >
            <span>Sign In with New Password</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      ) : (
        <form className="space-y-5" onSubmit={handleSubmit}>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
              Reset Token
            </label>
            <div className="mt-1.5 relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                <KeyRound className="w-4 h-4" />
              </div>
              <input
                type="text"
                required
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Paste your reset token"
                className="block w-full pl-9 pr-3 py-2.5 bg-slate-950/60 border border-slate-700 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-[#10A86B] focus:border-transparent transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
              New Password
            </label>
            <div className="mt-1.5 relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                <Lock className="w-4 h-4" />
              </div>
              <input
                type="password"
                required
                minLength={8}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="At least 8 characters"
                className="block w-full pl-9 pr-3 py-2.5 bg-slate-950/60 border border-slate-700 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-[#10A86B] focus:border-transparent transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
              Confirm New Password
            </label>
            <div className="mt-1.5 relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                <Lock className="w-4 h-4" />
              </div>
              <input
                type="password"
                required
                minLength={8}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat new password"
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
                <span>Resetting Password...</span>
              </>
            ) : (
              <>
                <span>Update Password</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>
      )}
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen bg-[#111820] flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-block mb-6">
          <Logo size="lg" showTagline={true} href="/" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Create a new password
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          Enter your security token and select a new secure password.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Suspense fallback={<div className="p-8 text-center text-slate-400">Loading reset parameters...</div>}>
          <ResetPasswordForm />
        </Suspense>
      </div>
    </div>
  );
}
