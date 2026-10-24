"use client";

import React, { useEffect, useState, useRef } from "react";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

interface GoogleSignInButtonProps {
  buttonText?: string;
  onSuccess?: () => void;
  onError?: (msg: string) => void;
  disabled?: boolean;
}

declare global {
  interface Window {
    google?: any;
    _googleGsiLoaded?: boolean;
  }
}

export function GoogleSignInButton({
  buttonText = "Continue with Google",
  onSuccess,
  onError,
  disabled = false,
}: GoogleSignInButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [clientId, setClientId] = useState<string | null>(
    process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || null
  );
  const [isConfigLoaded, setIsConfigLoaded] = useState(false);
  const { login } = useAuth();
  const hiddenBtnRef = useRef<HTMLDivElement>(null);

  // Fetch server Google OAuth config if not defined in env
  useEffect(() => {
    let isMounted = true;
    const fetchConfig = async () => {
      try {
        if (!clientId) {
          const cfg = await api.getGoogleConfig();
          if (isMounted && cfg.client_id) {
            setClientId(cfg.client_id);
          }
        }
      } catch {
        // Ignore network errors on initial config fetch
      } finally {
        if (isMounted) setIsConfigLoaded(true);
      }
    };
    fetchConfig();
    return () => {
      isMounted = false;
    };
  }, [clientId]);

  // Load Google Identity Services script
  useEffect(() => {
    if (!clientId) return;

    if (window.google?.accounts?.id) {
      initGsi();
      return;
    }

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => {
      initGsi();
    };
    document.body.appendChild(script);

    function initGsi() {
      if (!window.google?.accounts?.id || !clientId) return;
      try {
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: handleCredentialResponse,
          auto_select: false,
          cancel_on_tap_outside: true,
        });

        if (hiddenBtnRef.current) {
          window.google.accounts.id.renderButton(hiddenBtnRef.current, {
            theme: "outline",
            size: "large",
            type: "standard",
          });
        }
      } catch (err) {
        console.warn("GIS initialization error:", err);
      }
    }
  }, [clientId]);

  const handleCredentialResponse = async (response: any) => {
    if (!response?.credential) {
      onError?.("Google authentication was cancelled or returned no credentials.");
      return;
    }

    setIsLoading(true);
    try {
      const data = await api.googleAuth(response.credential);
      const user = await api.getMe();
      await login(data.access_token, user);
      onSuccess?.();
    } catch (err: any) {
      onError?.(err.message || "Failed to authenticate with Google. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClick = () => {
    if (disabled || isLoading) return;

    if (!clientId) {
      onError?.(
        "Google Authentication is not configured. Please set NEXT_PUBLIC_GOOGLE_CLIENT_ID and GOOGLE_CLIENT_ID in your environment variables. See .env.example for details."
      );
      return;
    }

    if (window.google?.accounts?.id) {
      // Trigger prompt / account selector
      window.google.accounts.id.prompt((notification: any) => {
        if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
          // If One Tap is suppressed by browser or user preference, click the rendered hidden button
          const btn = hiddenBtnRef.current?.querySelector("div[role=button]") as HTMLElement;
          if (btn) {
            btn.click();
          }
        }
      });
    } else {
      onError?.("Google authentication service is loading. Please try again in a moment.");
    }
  };

  return (
    <div>
      {/* Hidden container for GIS native render if fallback click is needed */}
      <div ref={hiddenBtnRef} className="hidden" aria-hidden="true" />

      <button
        type="button"
        onClick={handleClick}
        disabled={disabled || isLoading}
        className="w-full flex items-center justify-center gap-3 py-2.5 px-4 rounded-xl text-xs font-bold text-theme-text bg-theme-surface hover:bg-theme-secondary border border-theme-border shadow-sm transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 disabled:pointer-events-none"
        aria-label={buttonText}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin text-theme-sage" />
            <span>Verifying Google Account...</span>
          </>
        ) : (
          <>
            <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
            <span>{buttonText}</span>
          </>
        )}
      </button>
    </div>
  );
}
