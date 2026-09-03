import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getScoreGrade(score: number): { grade: string; color: string; label: string } {
  if (score >= 90) return { grade: "A+", color: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10", label: "Exceptional" };
  if (score >= 80) return { grade: "A", color: "text-green-400 border-green-500/30 bg-green-500/10", label: "Strong" };
  if (score >= 70) return { grade: "B", color: "text-yellow-400 border-yellow-500/30 bg-yellow-500/10", label: "Good" };
  if (score >= 60) return { grade: "C", color: "text-orange-400 border-orange-500/30 bg-orange-500/10", label: "Needs Attention" };
  return { grade: "F", color: "text-rose-400 border-rose-500/30 bg-rose-500/10", label: "Critical Risk" };
}

export function getScoreBgColor(score: number): string {
  if (score >= 90) return "bg-emerald-500";
  if (score >= 80) return "bg-green-500";
  if (score >= 70) return "bg-yellow-500";
  if (score >= 60) return "bg-orange-500";
  return "bg-rose-500";
}

export function getSeverityBadge(severity: string): { bg: string; text: string; border: string; icon: string } {
  switch (severity?.toLowerCase()) {
    case "critical":
      return { bg: "bg-rose-950/80", text: "text-rose-400", border: "border-rose-800/80", icon: "🔴" };
    case "high":
      return { bg: "bg-orange-950/80", text: "text-orange-400", border: "border-orange-800/80", icon: "🟠" };
    case "medium":
      return { bg: "bg-amber-950/80", text: "text-amber-400", border: "border-amber-800/80", icon: "🟡" };
    case "low":
      return { bg: "bg-blue-950/80", text: "text-blue-400", border: "border-blue-800/80", icon: "🔵" };
    default:
      return { bg: "bg-slate-900", text: "text-slate-400", border: "border-slate-800", icon: "⚪" };
  }
}
