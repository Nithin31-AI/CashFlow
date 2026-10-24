"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { useTheme } from "@/lib/theme";

interface LogoProps {
  className?: string;
  size?: "sm" | "md" | "lg" | "xl";
  showTagline?: boolean;
  href?: string;
}

export function Logo({
  className = "",
  size = "md",
  showTagline = false,
  href = "/dashboard",
}: LogoProps) {
  const { resolvedTheme } = useTheme();

  const sizeMap = {
    sm: { width: 32, height: 32, text: "text-lg", tag: "text-[9px]" },
    md: { width: 40, height: 40, text: "text-xl", tag: "text-[10px]" },
    lg: { width: 56, height: 56, text: "text-2xl", tag: "text-xs" },
    xl: { width: 80, height: 80, text: "text-3xl", tag: "text-sm" },
  };

  const current = sizeMap[size];
  const logoSrc =
    resolvedTheme === "dark"
      ? "/images/cashflow-logo-dark.png"
      : "/images/cashflow-logo-light.png";

  const content = (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="relative shrink-0 overflow-hidden rounded-xl p-0.5">
        <Image
          src={logoSrc}
          alt="cashFlow Logo"
          width={current.width}
          height={current.height}
          priority
          className="object-contain"
        />
      </div>
      <div>
        <div className="flex items-baseline leading-none">
          <span className={`font-bold tracking-tight text-theme-text ${current.text}`}>
            cash<span className="text-[#10A86B] dark:text-[#A3B18A]">Flow</span>
          </span>
        </div>
        {showTagline && (
          <p className={`font-semibold tracking-wider text-theme-textMuted uppercase mt-1 ${current.tag}`}>
            PLAN • FORECAST • GROW
          </p>
        )}
      </div>
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="inline-block transition-opacity hover:opacity-90">
        {content}
      </Link>
    );
  }

  return content;
}
