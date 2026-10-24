"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Receipt,
  ArrowLeftRight,
  GitCompare,
  TrendingUp,
  UploadCloud,
  FileSpreadsheet,
  Settings,
  Users,
  LogOut,
  Building2,
  ChevronDown,
  Activity,
  Compass,
  Sparkles,
  Bell,
  Plus,
} from "lucide-react";
import { Logo } from "@/components/Logo";
import { StatusBadge } from "@/components/StatusBadge";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAuth } from "@/lib/auth";

export function Sidebar() {
  const pathname = usePathname();
  const { user, currentBusiness, businesses, switchBusiness, logout } = useAuth();
  const [bizDropdownOpen, setBizDropdownOpen] = useState(false);

  const navItems = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Invoices", href: "/invoices", icon: Receipt },
    { name: "Transactions", href: "/transactions", icon: ArrowLeftRight },
    { name: "Reconciliation", href: "/reconciliation", icon: GitCompare },
    { name: "Forecast & Risks", href: "/forecast", icon: TrendingUp },
    { name: "Monte Carlo Sim", href: "/simulation", icon: Activity },
    { name: "Decisions & Scenarios", href: "/decisions", icon: Compass },
    { name: "AI Financial Assistant", href: "/assistant", icon: Sparkles },
    { name: "Financial Alerts", href: "/alerts", icon: Bell },
    { name: "Multi-File Import", href: "/imports/new", icon: UploadCloud },
    { name: "Import History", href: "/imports", icon: FileSpreadsheet },
    { name: "Team & Roles", href: "/settings/members", icon: Users },
  ];

  return (
    <aside className="w-64 bg-theme-secondary text-theme-text flex flex-col shrink-0 border-r border-theme-border h-screen sticky top-0 z-30 transition-colors">
      {/* Brand & Logo Header */}
      <div className="p-4 border-b border-theme-border flex items-center justify-between">
        <Logo size="sm" showTagline={true} />
      </div>

      {/* Business Switcher */}
      <div className="p-3 border-b border-theme-border relative">
        <p className="text-[10px] uppercase font-bold text-theme-textMuted tracking-wider mb-1.5 px-1">
          Active Workspace
        </p>
        <button
          onClick={() => setBizDropdownOpen(!bizDropdownOpen)}
          className="w-full flex items-center justify-between p-2 rounded-xl bg-theme-surface hover:border-theme-sage border border-theme-border text-left transition-colors"
        >
          <div className="flex items-center gap-2 truncate">
            <div className="w-6 h-6 rounded-lg bg-theme-sage/20 border border-theme-sage/40 flex items-center justify-center shrink-0">
              <Building2 className="w-3.5 h-3.5 text-theme-sage" />
            </div>
            <div className="truncate">
              <p className="text-xs font-semibold text-theme-text truncate">
                {currentBusiness?.name || "Select Business"}
              </p>
              <span className="text-[10px] text-theme-textMuted block">
                {currentBusiness?.currency || "INR"} • {currentBusiness?.role || "OWNER"}
              </span>
            </div>
          </div>
          <ChevronDown className="w-3.5 h-3.5 text-theme-textMuted shrink-0 ml-1" />
        </button>

        {/* Business Dropdown */}
        {bizDropdownOpen && (
          <div className="absolute top-full left-3 right-3 mt-1.5 bg-theme-surface border border-theme-border rounded-xl shadow-xl z-50 p-1 space-y-1">
            {businesses.map((biz) => (
              <button
                key={biz.id}
                onClick={() => {
                  switchBusiness(biz);
                  setBizDropdownOpen(false);
                }}
                className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center justify-between ${
                  currentBusiness?.id === biz.id
                    ? "bg-theme-sage/20 text-theme-sage font-bold"
                    : "text-theme-text hover:bg-theme-secondary"
                }`}
              >
                <span className="truncate">{biz.name}</span>
                <span className="text-[10px] text-theme-textMuted">{biz.currency}</span>
              </button>
            ))}
            <Link
              href="/onboarding"
              onClick={() => setBizDropdownOpen(false)}
              className="w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium text-theme-sage hover:bg-theme-secondary flex items-center gap-1.5 pt-1.5 border-t border-theme-border"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New Business</span>
            </Link>
          </div>
        )}
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                isActive
                  ? "bg-theme-sage text-white shadow-sm font-semibold"
                  : "text-theme-textMuted hover:text-theme-text hover:bg-theme-surface"
              }`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Theme Toggle & User Footer */}
      <div className="p-3 border-t border-theme-border space-y-3">
        <div className="flex items-center justify-between px-1">
          <span className="text-[10px] font-semibold text-theme-textMuted uppercase tracking-wider">Theme</span>
          <ThemeToggle />
        </div>

        <div className="flex items-center justify-between px-1 pt-1">
          <div className="truncate">
            <p className="text-xs font-semibold text-theme-text truncate">{user?.full_name}</p>
            <p className="text-[10px] text-theme-textMuted truncate">{user?.email}</p>
          </div>
          <button
            onClick={logout}
            title="Log Out"
            className="p-1.5 text-theme-textMuted hover:text-red-500 rounded-lg hover:bg-theme-surface transition-colors shrink-0"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </aside>
  );
}
