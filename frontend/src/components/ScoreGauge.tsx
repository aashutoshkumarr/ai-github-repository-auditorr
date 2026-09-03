"use client";

import { getScoreGrade, cn } from "@/lib/utils";
import { Calculator } from "lucide-react";

interface ScoreGaugeProps {
  score: number;
  criticalCount: number;
  highCount: number;
  mediumCount: number;
  lowCount: number;
  onOpenScoreLedger?: () => void;
}

export default function ScoreGauge({
  score,
  criticalCount,
  highCount,
  mediumCount,
  lowCount,
  onOpenScoreLedger
}: ScoreGaugeProps) {
  const { grade, color, label } = getScoreGrade(score);
  const radius = 68;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  let strokeColor = "#10b981"; // Emerald
  if (score < 60) strokeColor = "#f43f5e"; // Rose
  else if (score < 70) strokeColor = "#f97316"; // Orange
  else if (score < 80) strokeColor = "#eab308"; // Amber
  else if (score < 90) strokeColor = "#22c55e"; // Green

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 flex flex-col md:flex-row items-center justify-between gap-8 backdrop-blur-sm shadow-xl">
      <div className="flex items-center gap-6">
        {/* Radial SVG Meter */}
        <div className="relative w-40 h-40 flex items-center justify-center">
          <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 160 160">
            <circle
              cx="80"
              cy="80"
              r={radius}
              stroke="currentColor"
              strokeWidth="12"
              fill="transparent"
              className="text-slate-800/80"
            />
            <circle
              cx="80"
              cy="80"
              r={radius}
              stroke={strokeColor}
              strokeWidth="12"
              fill="transparent"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              className="transition-all duration-1000 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-3xl font-extrabold text-white tracking-tight">{Math.round(score)}</span>
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Health Score</span>
          </div>
        </div>

        {/* Grade & Description */}
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <span className={cn("px-3 py-1 text-sm font-extrabold rounded-lg border", color)}>
              Grade {grade}
            </span>
            <span className="text-lg font-bold text-slate-100">{label}</span>
          </div>
          <p className="text-xs text-slate-400 max-w-xs leading-relaxed">
            Composite health calculated across Security, Code Quality, Testing, Docs, Dependencies, Architecture & Maintainability.
          </p>

          {onOpenScoreLedger && (
            <button
              onClick={onOpenScoreLedger}
              className="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1.5 pt-1 transition-colors"
            >
              <Calculator className="w-3.5 h-3.5" />
              <span>Inspect Point Deductions Ledger</span>
            </button>
          )}
        </div>
      </div>

      {/* Findings Breakdown Stats */}
      <div className="flex items-center gap-3 bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
        <div className="text-center px-3 py-1 border-r border-slate-800">
          <div className="text-xl font-bold text-rose-400">{criticalCount}</div>
          <div className="text-[11px] text-slate-400 flex items-center justify-center gap-1">
            <span>🔴</span> Critical
          </div>
        </div>
        <div className="text-center px-3 py-1 border-r border-slate-800">
          <div className="text-xl font-bold text-orange-400">{highCount}</div>
          <div className="text-[11px] text-slate-400 flex items-center justify-center gap-1">
            <span>🟠</span> High
          </div>
        </div>
        <div className="text-center px-3 py-1 border-r border-slate-800">
          <div className="text-xl font-bold text-amber-400">{mediumCount}</div>
          <div className="text-[11px] text-slate-400 flex items-center justify-center gap-1">
            <span>🟡</span> Med
          </div>
        </div>
        <div className="text-center px-3 py-1">
          <div className="text-xl font-bold text-blue-400">{lowCount}</div>
          <div className="text-[11px] text-slate-400 flex items-center justify-center gap-1">
            <span>🔵</span> Low
          </div>
        </div>
      </div>
    </div>
  );
}
