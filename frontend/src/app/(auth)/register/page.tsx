"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowRight, Lock, Mail, User, AlertCircle, Loader2, Eye, EyeOff } from "lucide-react";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { GoogleSignInButton } from "@/components/GoogleSignInButton";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function RegisterPage() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match. Please re-enter your password.");
      return;
    }

    setIsLoading(true);

    try {
      const newUser = await api.register({
        email,
        password,
        full_name: fullName,
      });

      // Automatically sign in upon registration
      const loginData = await api.login({ email, password });
      await login(loginData.access_token, newUser);
    } catch (err: any) {
      setError(err.message || "Failed to create account. Please check your details.");
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
        <div className="inline-block mb-4">
          <Logo size="lg" showTagline={true} href="/" />
        </div>
        <p className="text-xs sm:text-sm text-theme-textMuted font-medium mb-4">
          Turn financial data into confident business decisions.
        </p>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-theme-text">
          Create your business account
        </h2>
        <p className="mt-2 text-xs sm:text-sm text-theme-textMuted">
          Already registered?{" "}
          <Link
            href="/login"
            className="font-semibold text-theme-sage hover:underline transition-colors"
          >
            Sign in here
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

          {/* Google Sign In */}
          <div className="mb-6">
            <GoogleSignInButton
              buttonText="Continue with Google"
              onError={(err) => setError(err)}
              disabled={isLoading}
            />

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-theme-border" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-theme-surface px-3 text-theme-textMuted font-semibold tracking-wider text-[11px]">
                  Or register with email
                </span>
              </div>
            </div>
          </div>

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="name"
                className="block text-xs font-bold text-theme-text uppercase tracking-wider mb-1.5"
              >
                Full Name
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-theme-textMuted">
                  <User className="h-4 w-4" />
                </div>
                <input
                  id="name"
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="block w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-theme-surface border border-theme-border text-theme-text placeholder-theme-textMuted/60 text-xs focus:outline-none focus:border-theme-sage transition-all"
                  placeholder="e.g. Rahul Sharma"
                />
              </div>
            </div>

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
              <label
                htmlFor="password"
                className="block text-xs font-bold text-theme-text uppercase tracking-wider mb-1.5"
              >
                Password (min 8 characters)
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-theme-textMuted">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="new-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-10 pr-10 py-2.5 rounded-xl bg-theme-surface border border-theme-border text-theme-text placeholder-theme-textMuted/60 text-xs focus:outline-none focus:border-theme-sage transition-all"
                  placeholder="••••••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-theme-textMuted hover:text-theme-text focus:outline-none transition-colors"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  tabIndex={0}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-xs font-bold text-theme-text uppercase tracking-wider mb-1.5"
              >
                Confirm Password
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-theme-textMuted">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  autoComplete="new-password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="block w-full pl-10 pr-10 py-2.5 rounded-xl bg-theme-surface border border-theme-border text-theme-text placeholder-theme-textMuted/60 text-xs focus:outline-none focus:border-theme-sage transition-all"
                  placeholder="••••••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-theme-textMuted hover:text-theme-text focus:outline-none transition-colors"
                  aria-label={showConfirmPassword ? "Hide confirm password" : "Show confirm password"}
                  tabIndex={0}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex justify-center items-center gap-2 py-2.5 px-4 rounded-xl text-xs font-bold text-white bg-theme-sage hover:bg-theme-sageDark focus:outline-none shadow-md transition-all disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Creating account...</span>
                  </>
                ) : (
                  <>
                    <span>Create Account & Continue</span>
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
