import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number) {
  return new Intl.NumberFormat("en-EG", { style: "currency", currency: "EGP" }).format(amount);
}

export function formatDate(date: string) {
  return new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function resolveAssetUrl(path?: string) {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  if (typeof window !== "undefined") return `${window.location.origin}${path}`;
  return path;
}
