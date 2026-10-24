"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowRight, Lock, Mail, AlertCircle, Loader2 } from "lucide-react";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const data = await api.login({ email, password });
      const user = await api.getMe();
      await login(data.access_token, user);
    } catch (err: any) {
      setError(err.message || "Failed to sign in. Please verify your email and password.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-theme-bg text-theme-text flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative">
      <div className="absolute top-6 right-6">
        <ThemeToggle />
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-block mb-6">
          <Logo size="lg" showTagline={true} href="/" />
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-theme-text">
          Sign in to your account
        </h2>
        <p className="mt-2 text-xs sm:text-sm text-theme-textMuted">
          Or{" "}
          <Link
            href="/register"
            className="font-semibold text-theme-sage hover:underline transition-colors"
          >
            create a new business account
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="spatial-panel py-8 px-6 sm:px-10 shadow-xl">
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-500 text-xs flex items-start gap-3">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="email"
                className="block text-xs font-bold text-theme-text uppercase tracking-wider mb-1.5"
              >
                Work Email
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-theme-textMuted">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-theme-surface border border-theme-border text-theme-text placeholder-theme-textMuted/60 text-xs focus:outline-none focus:border-theme-sage transition-all"
                  placeholder="name@company.com"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="password"
                  className="block text-xs font-bold text-theme-text uppercase tracking-wider"
                >
                  Password
                </label>
                <div className="text-xs">
                  <Link
                    href="/forgot-password"
                    className="font-medium text-theme-sage hover:underline"
                  >
                    Forgot password?
                  </Link>
                </div>
              </div>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-theme-textMuted">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-theme-surface border border-theme-border text-theme-text placeholder-theme-textMuted/60 text-xs focus:outline-none focus:border-theme-sage transition-all"
                  placeholder="••••••••••••"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex justify-center items-center gap-2 py-2.5 px-4 rounded-xl text-xs font-bold text-white bg-theme-sage hover:bg-theme-sageDark focus:outline-none shadow-md transition-all disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Signing in...</span>
                  </>
                ) : (
                  <>
                    <span>Sign In</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
