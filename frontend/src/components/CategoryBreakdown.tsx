"use client";

import { ShieldAlert, Code2, CheckCircle2, FileText, PackageCheck, Layers, Cpu } from "lucide-react";
import { getScoreBgColor, cn } from "@/lib/utils";

interface CategoryBreakdownProps {
  scores: {
    security: number;
    quality: number;
    testing: number;
    docs: number;
    deps: number;
    arch: number;
    maintainability: number;
  };
  activeCategory?: string;
  onSelectCategory?: (category: string) => void;
}

export default function CategoryBreakdown({
  scores,
  activeCategory,
  onSelectCategory
}: CategoryBreakdownProps) {
  const categories = [
    {
      id: "Security",
      name: "Security",
      score: scores.security,
      weight: "20%",
      icon: ShieldAlert,
      desc: "Secrets, injection patterns, CWEs"
    },
    {
      id: "Code Quality",
      name: "Code Quality",
      score: scores.quality,
      weight: "20%",
      icon: Code2,
      desc: "AST complexity, nesting, debt"
    },
    {
      id: "Testing",
      name: "Testing",
      score: scores.testing,
      weight: "15%",
      icon: CheckCircle2,
      desc: "Test LOC ratio, suites, CI"
    },
    {
      id: "Documentation",
      name: "Documentation",
      score: scores.docs,
      weight: "15%",
      icon: FileText,
      desc: "README completeness & docstrings"
    },
    {
      id: "Dependencies",
      name: "Dependencies",
      score: scores.deps,
      weight: "10%",
      icon: PackageCheck,
      desc: "CVE advisories & outdated packages"
    },
    {
      id: "Architecture",
      name: "Architecture",
      score: scores.arch,
      weight: "10%",
      icon: Layers,
      desc: "Topology, tiers & modularity"
    },
    {
      id: "Maintainability",
      name: "Maintainability",
      score: scores.maintainability,
      weight: "10%",
      icon: Cpu,
      desc: "Churn vs complexity hotspots"
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {categories.map((cat) => {
        const Icon = cat.icon;
        const isSelected = activeCategory === cat.id;

        return (
          <button
            key={cat.id}
            onClick={() => onSelectCategory && onSelectCategory(isSelected ? "" : cat.id)}
            className={cn(
              "text-left p-4 rounded-xl border transition-all duration-200 flex flex-col justify-between group",
              isSelected
                ? "bg-blue-950/40 border-blue-500 shadow-lg shadow-blue-500/20 ring-1 ring-blue-500/50"
                : "bg-slate-900/40 border-slate-800/80 hover:bg-slate-900/80 hover:border-slate-700"
            )}
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className={cn(
                    "p-1.5 rounded-lg text-blue-400 group-hover:text-blue-300",
                    isSelected ? "bg-blue-600/30 text-blue-300" : "bg-slate-800/80"
                  )}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="font-semibold text-sm text-slate-200">{cat.name}</span>
                </div>
                <span className="text-xs text-slate-500 font-mono">{cat.weight}</span>
              </div>

              <p className="text-[11px] text-slate-400 mb-3">{cat.desc}</p>
            </div>

            <div>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="text-slate-400">Score</span>
                <span className="font-bold text-slate-100">{Math.round(cat.score)}/100</span>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className={cn("h-full rounded-full transition-all duration-700", getScoreBgColor(cat.score))}
                  style={{ width: `${Math.max(5, cat.score)}%` }}
                />
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
