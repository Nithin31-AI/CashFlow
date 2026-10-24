"use client";

import React from "react";
import Link from "next/link";
import { UploadCloud, ShieldCheck } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { StatusBadge } from "@/components/StatusBadge";

interface NavbarProps {
  title?: string;
  subtitle?: string;
}

export function Navbar({ title = "Dashboard", subtitle }: NavbarProps) {
  const { currentBusiness } = useAuth();

  return (
    <header className="h-16 border-b border-slate-200 bg-white/90 backdrop-blur-sm sticky top-0 z-30 px-6 flex items-center justify-between">
      <div>
        <h1 className="text-lg font-bold text-slate-900 tracking-tight leading-tight">
          {title}
        </h1>
        {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        {currentBusiness && (
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200/80 text-xs text-slate-600">
            <span className="font-medium text-slate-800">{currentBusiness.name}</span>
            <span className="text-slate-300">•</span>
            <span className="font-semibold text-[#10A86B]">{currentBusiness.currency}</span>
            {currentBusiness.role && (
              <StatusBadge status={currentBusiness.role} type="role" className="py-0 px-1.5 text-[10px]" />
            )}
          </div>
        )}

        <Link
          href="/imports/new"
          className="inline-flex items-center gap-2 px-3.5 py-1.5 bg-[#10A86B] hover:bg-[#0D8554] text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
        >
          <UploadCloud className="w-3.5 h-3.5" />
          <span>Import Data</span>
        </Link>
      </div>
    </header>
  );
}
