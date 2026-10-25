import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * India-first currency formatter with fallback for international currencies.
 * Resilient to undefined, null, non-finite numbers, and string values.
 */
export function formatCurrency(amount: number | string | null | undefined, currency: string = "INR"): string {
  const curr = (currency || "INR").toUpperCase();
  if (amount === null || amount === undefined || amount === "") {
    return curr === "INR" ? "₹ 0.00" : `${curr} 0.00`;
  }
  
  const num = typeof amount === "number" ? amount : parseFloat(String(amount));
  if (!Number.isFinite(num) || isNaN(num)) {
    return curr === "INR" ? "₹ 0.00" : `${curr} 0.00`;
  }
  
  if (curr === "INR") {
    try {
      return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2,
      }).format(num);
    } catch {
      return `₹ ${num.toFixed(2)}`;
    }
  }

  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: curr,
      maximumFractionDigits: 2,
    }).format(num);
  } catch {
    return `${curr} ${num.toFixed(2)}`;
  }
}

export function formatDate(dateStr: string): string {
  if (!dateStr) return "-";
  try {
    const d = new Date(dateStr);
    return new Intl.DateTimeFormat("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }).format(d);
  } catch {
    return dateStr;
  }
}

export function formatDateTime(dateTimeStr: string): string {
  if (!dateTimeStr) return "-";
  try {
    const d = new Date(dateTimeStr);
    return new Intl.DateTimeFormat("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(d);
  } catch {
    return dateTimeStr;
  }
}

export function formatBytes(bytes: number, decimals: number = 1): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
}
