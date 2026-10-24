"use client";

import React, { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { useAuth } from "@/lib/auth";
import { Loader2 } from "lucide-react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, token, isLoading, currentBusiness, businesses } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading) {
      if (!token || !user) {
        router.push("/login");
      } else if (businesses.length === 0 && pathname !== "/onboarding") {
        router.push("/onboarding");
      }
    }
  }, [token, user, isLoading, businesses, pathname, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-theme-bg flex flex-col items-center justify-center text-theme-text">
        <Loader2 className="w-8 h-8 text-theme-sage animate-spin mb-4" />
        <p className="text-sm text-theme-textMuted">Loading your cashFlow workspace...</p>
      </div>
    );
  }

  if (!token || !user) {
    return null;
  }

  // If on onboarding, render without sidebar
  if (pathname === "/onboarding") {
    return <main className="min-h-screen bg-theme-bg text-theme-text">{children}</main>;
  }

  return (
    <div className="flex min-h-screen bg-theme-bg text-theme-text">
      {/* Sidebar is sticky to viewport, does not hijack content scrolling */}
      <Sidebar />
      {/* Main content flows naturally vertically with zero viewport locks */}
      <div className="flex-1 flex flex-col min-w-0">
        <main className="flex-1 p-6 sm:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
