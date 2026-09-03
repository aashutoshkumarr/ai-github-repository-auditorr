"use client";

import { useState } from "react";
import { FixRoadmapStep } from "@/types";
import { getSeverityBadge, cn } from "@/lib/utils";
import { CheckSquare, Square, ListOrdered, ArrowRight } from "lucide-react";

interface FixRoadmapProps {
  steps: FixRoadmapStep[];
}

export default function FixRoadmap({ steps }: FixRoadmapProps) {
  const [completedSteps, setCompletedSteps] = useState<Record<number, boolean>>({});

  const toggleStep = (order: number) => {
    setCompletedSteps((prev) => ({
      ...prev,
      [order]: !prev[order],
    }));
  };

  if (!steps || steps.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 text-center text-xs text-slate-500">
        No immediate fixes required. Repository health is in excellent standing.
      </div>
    );
  }

  const completedCount = Object.values(completedSteps).filter(Boolean).length;
  const progressPercent = Math.round((completedCount / steps.length) * 100);

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-sm shadow-xl space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <ListOrdered className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-semibold text-sm text-slate-100">Recommended Fix Order Roadmap</h3>
            <p className="text-[11px] text-slate-400">
              Prioritized by severity, exploitability, and architectural impact.
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400 font-mono">
            {completedCount}/{steps.length} Resolved ({progressPercent}%)
          </span>
          <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-emerald-500 rounded-full transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      <div className="space-y-2">
        {steps.map((step) => {
          const isDone = !!completedSteps[step.order];
          const badge = getSeverityBadge(step.severity);

          return (
            <div
              key={step.order}
              onClick={() => toggleStep(step.order)}
              className={cn(
                "flex items-start gap-3 p-3.5 rounded-xl border transition-all cursor-pointer group",
                isDone
                  ? "bg-slate-950/40 border-slate-900 opacity-60 line-through"
                  : "bg-slate-950/80 border-slate-800/90 hover:border-slate-700 hover:bg-slate-900/80"
              )}
            >
              <button className="mt-0.5 text-slate-500 group-hover:text-blue-400 transition-colors">
                {isDone ? (
                  <CheckSquare className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Square className="w-4 h-4" />
                )}
              </button>

              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-mono font-bold text-slate-400">#{step.order}</span>
                  <span className={cn("px-2 py-0.2 text-[10px] font-bold rounded border inline-flex items-center gap-1", badge.bg, badge.text, badge.border)}>
                    <span>{badge.icon}</span> {step.severity}
                  </span>
                  <span className="text-xs font-semibold text-slate-100">{step.title}</span>
                  {step.file_path && (
                    <span className="text-[11px] font-mono text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded">
                      {step.file_path}
                    </span>
                  )}
                </div>

                <p className="text-xs text-slate-300 leading-relaxed pl-6">
                  {step.action_summary}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
