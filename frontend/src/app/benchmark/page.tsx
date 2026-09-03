"use client";

import { useState, useEffect } from "react";
import { BenchmarkResult } from "@/types";
import { runBenchmarkEvaluation } from "@/lib/api";
import {
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  Play,
  RefreshCw,
  Zap,
  Target,
  ShieldAlert,
  Percent,
  Clock,
  TrendingUp
} from "lucide-react";

export default function BenchmarkPage() {
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunEvaluation = async () => {
    setIsRunning(true);
    setError(null);
    try {
      const data = await runBenchmarkEvaluation();
      setBenchmarkData(data);
    } catch (err: any) {
      setError(err.message || "Failed to execute benchmark evaluation.");
    } finally {
      setIsRunning(false);
    }
  };

  useEffect(() => {
    handleRunEvaluation();
  }, []);

  return (
    <div className="space-y-8 pb-16">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <BarChart3 className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-bold text-slate-100">Benchmark & Ground-Truth Evaluation</h1>
          </div>
          <p className="text-xs text-slate-400">
            Empirically measured Precision, Recall, and F1 accuracy across seeded test repositories.
          </p>
        </div>

        <button
          onClick={handleRunEvaluation}
          disabled={isRunning}
          className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-lg shadow-blue-600/20 transition-colors flex items-center gap-2"
        >
          {isRunning ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Running Evaluation...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              <span>Rerun Benchmark Suite</span>
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="bg-rose-950/40 border border-rose-800/60 p-4 rounded-xl text-xs text-rose-300">
          {error}
        </div>
      )}

      {benchmarkData && (
        <>
          {/* Key Metrics Overview Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-sm space-y-1">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Precision</span>
                <Target className="w-4 h-4 text-blue-400" />
              </div>
              <div className="text-2xl font-extrabold text-blue-400 font-mono">
                {benchmarkData.overall_precision}%
              </div>
              <p className="text-[11px] text-slate-500">True Positives / (TP + False Positives)</p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-sm space-y-1">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Recall</span>
                <Zap className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-extrabold text-emerald-400 font-mono">
                {benchmarkData.overall_recall}%
              </div>
              <p className="text-[11px] text-slate-500">True Positives / (TP + False Negatives)</p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-sm space-y-1">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>F1 Score</span>
                <TrendingUp className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-2xl font-extrabold text-purple-400 font-mono">
                {benchmarkData.overall_f1}%
              </div>
              <p className="text-[11px] text-slate-500">Harmonic mean of Precision and Recall</p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-sm space-y-1">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Latency</span>
                <Clock className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-2xl font-extrabold text-amber-400 font-mono">
                {benchmarkData.total_execution_time_s}s
              </div>
              <p className="text-[11px] text-slate-500">Full 3-repo multi-engine pipeline</p>
            </div>
          </div>

          {/* Side-by-Side Comparison: Our Multi-Engine vs Naive LLM */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm space-y-4">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Target className="w-4 h-4 text-blue-400" />
              <span>Multi-Engine Pipeline vs. Naive LLM Baseline</span>
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Our Hybrid System */}
              <div className="bg-blue-950/20 border border-blue-500/40 rounded-xl p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-blue-400 uppercase tracking-wider">Our System</span>
                  <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-blue-500/10 text-blue-300 border border-blue-500/20">
                    Production Architecture
                  </span>
                </div>
                <h3 className="font-bold text-sm text-slate-100">
                  Static AST + Security Regex + RAG + LLM
                </h3>
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1 border-b border-blue-900/40">
                    <span className="text-slate-400">Precision:</span>
                    <span className="text-emerald-400 font-bold">{benchmarkData.comparison_vs_naive_llm.our_system.precision}%</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-blue-900/40">
                    <span className="text-slate-400">Recall:</span>
                    <span className="text-emerald-400 font-bold">{benchmarkData.comparison_vs_naive_llm.our_system.recall}%</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-blue-900/40">
                    <span className="text-slate-400">F1 Score:</span>
                    <span className="text-purple-400 font-bold">{benchmarkData.comparison_vs_naive_llm.our_system.f1_score}%</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-blue-900/40">
                    <span className="text-slate-400">Finding Groundedness:</span>
                    <span className="text-emerald-400 font-bold">{benchmarkData.comparison_vs_naive_llm.our_system.finding_groundedness}%</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">False Positive Rate:</span>
                    <span className="text-emerald-400 font-bold">{benchmarkData.comparison_vs_naive_llm.our_system.false_positive_rate}%</span>
                  </div>
                </div>
              </div>

              {/* Naive LLM Baseline */}
              <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-5 space-y-3 opacity-80">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Naive Baseline</span>
                  <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-slate-800 text-slate-400">
                    Prompt-Only (repo → GPT)
                  </span>
                </div>
                <h3 className="font-bold text-sm text-slate-300">
                  Raw Code Dump to LLM
                </h3>
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">Precision:</span>
                    <span className="text-amber-400">{benchmarkData.comparison_vs_naive_llm.naive_llm_baseline.precision}%</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">Recall:</span>
                    <span className="text-amber-400">{benchmarkData.comparison_vs_naive_llm.naive_llm_baseline.recall}%</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">F1 Score:</span>
                    <span className="text-amber-400">{benchmarkData.comparison_vs_naive_llm.naive_llm_baseline.f1_score}%</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800">
                    <span className="text-slate-400">Finding Groundedness:</span>
                    <span className="text-rose-400">{benchmarkData.comparison_vs_naive_llm.naive_llm_baseline.finding_groundedness}%</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">False Positive Rate:</span>
                    <span className="text-rose-400">{benchmarkData.comparison_vs_naive_llm.naive_llm_baseline.false_positive_rate}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Seeded Repository Breakdown Table */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm space-y-4">
            <h2 className="text-base font-bold text-slate-100">Seeded Benchmark Cases</h2>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse font-mono">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-semibold text-[11px] uppercase tracking-wider font-sans">
                    <th className="py-2.5 px-3">Test Case</th>
                    <th className="py-2.5 px-3">True Positives</th>
                    <th className="py-2.5 px-3">False Positives</th>
                    <th className="py-2.5 px-3">False Negatives</th>
                    <th className="py-2.5 px-3">Precision</th>
                    <th className="py-2.5 px-3">Recall</th>
                    <th className="py-2.5 px-3">F1</th>
                    <th className="py-2.5 px-3 text-right">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {benchmarkData.test_results.map((res, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-3">
                        <div className="font-bold text-slate-100">{res.case_name}</div>
                        <div className="text-[11px] text-slate-400 font-sans">{res.description}</div>
                      </td>
                      <td className="py-3 px-3 text-emerald-400 font-bold">{res.true_positives}</td>
                      <td className="py-3 px-3 text-rose-400 font-bold">{res.false_positives}</td>
                      <td className="py-3 px-3 text-amber-400 font-bold">{res.false_negatives}</td>
                      <td className="py-3 px-3 text-blue-400 font-bold">{res.precision}%</td>
                      <td className="py-3 px-3 text-blue-400 font-bold">{res.recall}%</td>
                      <td className="py-3 px-3 text-purple-400 font-bold">{res.f1_score}%</td>
                      <td className="py-3 px-3 text-right text-slate-400">{res.execution_time_s}s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
