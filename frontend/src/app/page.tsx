"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { SampleRepo, RepoPreview } from "@/types";
import { fetchSamples, analyzeRepository, previewRepository, submitAuditJob, getJobStatus } from "@/lib/api";
import CommandPalette from "@/components/CommandPalette";
import {
  ShieldCheck,
  Search,
  Sparkles,
  ArrowRight,
  Code,
  FileCheck,
  Package,
  Layers,
  Cpu,
  RefreshCw,
  AlertCircle,
  CheckCircle2
} from "lucide-react";

const DEFAULT_SAMPLES: (SampleRepo & { stars?: number; primary_language?: string; expected_profile?: string })[] = [
  {
    id: "vulnerable-python-app",
    name: "vulnerable-python-app",
    owner: "sample",
    alias: "vulnerable-python-app",
    url: "https://github.com/sample/vulnerable-python-app",
    description: "Intentionally vulnerable Flask web application with leaked AWS keys, SQL injection (CWE-89), command injection, bare excepts, and CVE-compromised dependencies.",
    badge: "Security Deficits",
    language: "Python",
    tags: ["python", "flask", "cwe-89"],
    stars: 1240,
  },
  {
    id: "clean-modular-ts",
    name: "clean-modular-ts",
    owner: "sample",
    alias: "clean-modular-ts",
    url: "https://github.com/sample/clean-modular-ts",
    description: "Production-grade modular TypeScript microservice with 100% unit tests, Zod validation, GitHub Actions CI, and clean architecture.",
    badge: "Clean Architecture",
    language: "TypeScript",
    tags: ["typescript", "clean-architecture"],
    stars: 3850,
  },
  {
    id: "fastapi-framework",
    name: "fastapi",
    owner: "tiangolo",
    alias: "fastapi",
    url: "https://github.com/tiangolo/fastapi",
    description: "High-performance, easy to learn, fast to code Python web framework for APIs based on standard Python type hints.",
    badge: "⭐ 82k Stars",
    language: "Python",
    tags: ["python", "fastapi", "async"],
    stars: 82400,
  },
  {
    id: "shadcn-ui-library",
    name: "shadcn-ui",
    owner: "shadcn-ui",
    alias: "shadcn-ui",
    url: "https://github.com/shadcn-ui/ui",
    description: "Beautifully designed, accessible components built with Radix UI and Tailwind CSS. The gold standard for modern React frontend architecture.",
    badge: "⭐ 86k Stars",
    language: "TypeScript",
    tags: ["react", "tailwind", "ui"],
    stars: 86500,
  },
  {
    id: "express-framework",
    name: "express",
    owner: "expressjs",
    alias: "express",
    url: "https://github.com/expressjs/express",
    description: "Fast, unopinionated, minimalist web framework for Node.js powering millions of backend microservices worldwide.",
    badge: "⭐ 66k Stars",
    language: "JavaScript",
    tags: ["nodejs", "express", "backend"],
    stars: 66200,
  },
  {
    id: "microservices-go-backend",
    name: "microservices-go-backend",
    owner: "sample",
    alias: "microservices-go-backend",
    url: "https://github.com/sample/microservices-go-backend",
    description: "Distributed event-driven Go microservices architecture with gRPC, Redis Pub/Sub, and PostgreSQL order state management.",
    badge: "Distributed Go",
    language: "Go",
    tags: ["go", "grpc", "microservices"],
    stars: 2410,
  },
  {
    id: "ml-predictive-pipeline",
    name: "ml-predictive-pipeline",
    owner: "sample",
    alias: "ml-predictive-pipeline",
    url: "https://github.com/sample/ml-predictive-pipeline",
    description: "End-to-end PyTorch deep learning training and inference pipeline with data preprocessing, scaling, and feature engineering.",
    badge: "PyTorch / ML",
    language: "Python",
    tags: ["python", "pytorch", "ml"],
    stars: 1670,
  },
  {
    id: "missing-docs-deps",
    name: "missing-docs-deps",
    owner: "sample",
    alias: "missing-docs-deps",
    url: "https://github.com/sample/missing-docs-deps",
    description: "Legacy Python backend with zero automated tests, missing README documentation, and outdated dependencies.",
    badge: "Needs Docs/Tests",
    language: "Python",
    tags: ["python", "legacy"],
    stars: 420,
  },
];

export default function HomePage() {
  const router = useRouter();
  const [repoUrl, setRepoUrl] = useState("");
  const [samples, setSamples] = useState<SampleRepo[]>(DEFAULT_SAMPLES);
  const [preview, setPreview] = useState<RepoPreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [llmProvider, setLlmProvider] = useState("offline");
  const [apiKey, setApiKey] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const steps = [
    "Cloning repository & extracting source tree...",
    "Parsing AST & measuring cyclomatic complexity...",
    "Scanning secrets, credentials, and injection CWEs...",
    "Evaluating dependency manifests & CVE advisories...",
    "Inspecting test coverage, ratios & CI workflows...",
    "Analyzing Git churn hotspots & architecture topology...",
    "Synthesizing evidence-backed audit report with AI..."
  ];

  useEffect(() => {
    fetchSamples()
      .then(setSamples)
      .catch((err) => console.error("Error loading sample repos:", err));
  }, []);

  useEffect(() => {
    const trimmed = repoUrl.trim();
    if (!trimmed || !/^https?:\/\/(www\.)?github\.com\//i.test(trimmed)) {
      setPreview(null);
      return;
    }

    const timer = setTimeout(async () => {
      setPreviewLoading(true);
      try {
        const data = await previewRepository(trimmed);
        setPreview(data);
      } catch (err) {
        console.error("Preview failed:", err);
        setPreview(null);
      } finally {
        setPreviewLoading(false);
      }
    }, 700);

    return () => clearTimeout(timer);
  }, [repoUrl]);

  const handleStartAudit = async (targetUrl?: string) => {
    const url = targetUrl || repoUrl;
    if (!url.trim()) {
      setErrorMessage("Please enter a valid GitHub repository URL.");
      return;
    }

    setErrorMessage(null);
    setIsLoading(true);
    setLoadingStep(0);

    const interval = setInterval(() => {
      setLoadingStep((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
    }, 600);

    try {
      const report = await analyzeRepository({
        github_url: url.trim(),
        llm_provider: llmProvider,
        api_key: apiKey.trim() || undefined,
      });

      clearInterval(interval);
      setLoadingStep(steps.length - 1);
      setTimeout(() => {
        router.push(`/audit/${report.id}`);
      }, 300);
    } catch (err: any) {
      clearInterval(interval);
      setIsLoading(false);
      setErrorMessage(err.message || "Failed to analyze repository. Please verify the URL or select a sample repository.");
    }
  };

  return (
    <div className="space-y-16 pb-12">
      {/* Hero Section */}
      <section className="text-center space-y-6 pt-8 max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-semibold">
          <Sparkles className="w-4 h-4" />
          <span>Self-Healing Auditor • Enterprise-grade repository intelligence</span>
        </div>

        <h1 className="text-5xl sm:text-6xl font-extrabold text-slate-100 tracking-tight leading-tight">
          Audit any GitHub repository with <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400">Deterministic AI</span>
        </h1>

        <p className="text-base sm:text-lg text-slate-400 leading-relaxed max-w-2xl mx-auto">
          Audit → Diagnose → Fix → Test → Verify. The platform understands repository architecture, hidden bug propagation paths, predictive risk, and autonomous remediation loops with evidence-backed guardrails.
        </p>

        {/* URL Input Box */}
        <div className="bg-slate-900/80 border border-slate-700/80 rounded-2xl p-3 shadow-2xl backdrop-blur-md max-w-2xl mx-auto space-y-3">
          <div className="flex flex-col sm:flex-row gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repository"
                disabled={isLoading}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-3 py-3 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
              />
            </div>

            <button
              onClick={() => handleStartAudit()}
              disabled={isLoading || !repoUrl.trim()}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 text-white font-bold text-xs sm:text-sm rounded-xl shadow-lg shadow-blue-600/30 transition-all flex items-center justify-center gap-2 whitespace-nowrap"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Auditing...</span>
                </>
              ) : (
                <>
                  <span>Audit Repo</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>

          {/* Provider Settings Toggle */}
          <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800/80 text-xs px-1 text-slate-400">
            <div className="flex items-center gap-2">
              <span>AI Provider:</span>
              <select
                value={llmProvider}
                onChange={(e) => setLlmProvider(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-xs text-slate-300 focus:outline-none focus:border-blue-500"
              >
                <option value="offline">Offline / Local Engine (Zero API Key)</option>
                <option value="gemini">Google Gemini 1.5</option>
                <option value="openai">OpenAI GPT-4o</option>
              </select>
            </div>

            {llmProvider !== "offline" && (
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={`Enter ${llmProvider.toUpperCase()} API Key`}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-xs text-slate-300 focus:outline-none focus:border-blue-500 w-48"
              />
            )}
          </div>
        </div>

        {previewLoading && repoUrl.trim() && (
          <div className="max-w-2xl mx-auto rounded-2xl border border-blue-500/30 bg-blue-500/5 p-3 text-left text-sm text-blue-200">
            <div className="flex items-center gap-2"><RefreshCw className="w-4 h-4 animate-spin" /> Generating repository summary...</div>
          </div>
        )}

        {preview && (
          <div className="max-w-4xl mx-auto rounded-3xl border border-slate-700/80 bg-slate-900/80 p-5 shadow-2xl backdrop-blur-sm">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="text-[11px] uppercase tracking-[0.16em] text-blue-300 font-semibold">Repository snapshot</div>
                <h3 className="mt-2 text-2xl font-extrabold text-slate-100">{preview.owner} / {preview.name}</h3>
              </div>
              <div className="inline-flex items-center gap-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 text-xs font-semibold text-emerald-300">
                <CheckCircle2 className="w-4 h-4" />
                {preview.stars} stars • {preview.forks} forks
              </div>
            </div>

            <p className="mt-4 text-base text-slate-300 leading-relaxed">{preview.summary}</p>

            <div className="mt-5 grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                <div className="text-[11px] uppercase tracking-[0.14em] text-slate-400">Primary Language</div>
                <div className="mt-2 text-lg font-bold text-slate-100">{preview.language || "Unknown"}</div>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                <div className="text-[11px] uppercase tracking-[0.14em] text-slate-400">Default Branch</div>
                <div className="mt-2 text-lg font-bold text-slate-100">{preview.default_branch}</div>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                <div className="text-[11px] uppercase tracking-[0.14em] text-slate-400">Project Type</div>
                <div className="mt-2 text-lg font-bold text-slate-100">{preview.topics[0] || preview.language || "Codebase"}</div>
              </div>
            </div>

            <div className="mt-5 grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                <div className="text-[11px] uppercase tracking-[0.14em] text-slate-400">Tech stack</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {preview.tech_stack.map((stackItem) => (
                    <span key={stackItem} className="rounded-full border border-blue-500/30 bg-blue-500/10 px-2.5 py-1 text-xs font-semibold text-blue-200">
                      {stackItem}
                    </span>
                  ))}
                </div>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                <div className="text-[11px] uppercase tracking-[0.14em] text-slate-400">Topics</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(preview.topics.length ? preview.topics : ["repository", "software"]).map((topic) => (
                    <span key={topic} className="rounded-full border border-violet-500/30 bg-violet-500/10 px-2.5 py-1 text-xs font-semibold text-violet-200">
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
              <div className="text-[11px] uppercase tracking-[0.14em] text-slate-400">Readme excerpt</div>
              <p className="mt-3 text-sm text-slate-300 leading-relaxed">
                {preview.readme_excerpt || "This repository has no easily parseable README excerpt, but the audit engine can still evaluate its architecture, dependencies, and security posture."}
              </p>
            </div>
          </div>
        )}

        {/* Error message */}
        {errorMessage && (
          <div className="bg-rose-950/40 border border-rose-800/60 p-3 rounded-xl max-w-2xl mx-auto flex items-center gap-2 text-xs text-rose-300 text-left">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Live Loading Stepper */}
        {isLoading && (
          <div className="bg-slate-900/90 border border-blue-500/40 rounded-2xl p-6 max-w-xl mx-auto space-y-4 text-left shadow-2xl animate-pulse-slow">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-blue-400 flex items-center gap-2">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Pipeline Step {loadingStep + 1} of {steps.length}
              </span>
              <span className="font-mono text-slate-400">{Math.round(((loadingStep + 1) / steps.length) * 100)}%</span>
            </div>

            <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 rounded-full transition-all duration-300"
                style={{ width: `${((loadingStep + 1) / steps.length) * 100}%` }}
              />
            </div>

            <p className="text-xs font-mono text-slate-200">
              ➜ {steps[loadingStep]}
            </p>
          </div>
        )}
      </section>

      {/* Sample Repositories Showcase */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-100">Try Instant Sample Repositories</h2>
            <p className="text-sm text-slate-400">Click any pre-configured repository to run an instant benchmark audit</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {samples.map((s) => (
            <div
              key={s.id}
              onClick={() => {
                setRepoUrl(s.url);
                handleStartAudit(s.url);
              }}
              className="bg-slate-900/50 hover:bg-slate-900/90 border border-slate-800/80 hover:border-blue-500/50 rounded-2xl p-4 transition-all duration-200 cursor-pointer flex flex-col justify-between group backdrop-blur-sm"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-800 text-blue-400 border border-slate-700">
                    {s.badge || (s as any).expected_profile || "Sample"}
                  </span>
                  <div className="flex items-center gap-2">
                    {Boolean((s as any).stars) && (
                      <span className="text-[11px] font-semibold text-amber-400 flex items-center gap-0.5">
                        ⭐ {((s as any).stars >= 1000 ? `${((s as any).stars / 1000).toFixed(0)}k` : (s as any).stars)}
                      </span>
                    )}
                    <span className="text-[11px] font-mono text-slate-500">{s.language || (s as any).primary_language}</span>
                  </div>
                </div>

                <h3 className="font-bold text-sm text-slate-100 group-hover:text-blue-400 transition-colors mb-1">
                  {s.name}
                </h3>
                <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed mb-4">
                  {s.description}
                </p>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-slate-800/60 text-xs font-semibold text-blue-400 group-hover:text-blue-300">
                <span>Run Audit</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Auditor-as-a-Service */}
      <section className="space-y-6 pt-4">
        <div className="text-center max-w-4xl mx-auto space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-violet-500/30 bg-violet-500/10 text-violet-300 text-sm font-semibold">
            <Layers className="w-4 h-4" />
            Auditor-as-a-Service
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100">One architecture for 1 repo or 1 million repos</h2>
          <p className="text-base text-slate-400 max-w-3xl mx-auto">
            The platform is designed around queue-driven workers, shared analyzers, pluggable execution, and cached results so the system scales by adding workers—not by rewriting the architecture.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
              <Code className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-slate-100">Queue-based parallel analysis</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Repos enter a durable task queue and independent workers fan out analysis across files, modules, dependencies, and security signals in parallel.
            </p>
          </div>

          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-slate-100">Pluggable analyzer mesh</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Security, architecture, bug detection, performance, quality, and AI evaluation become independently swappable modules behind the same orchestration contract.
            </p>
          </div>

          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <Package className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-slate-100">Incremental audits</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Analyze only changed files, AST paths, or dependency deltas to reduce compute and keep repeated scans fast and deterministic.
            </p>
          </div>

          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 space-y-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-slate-100">Horizontal worker scale</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              The same job contract works for a single repo and a fleet of millions—only queue concurrency, caching, and worker count change.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-[1.25fr_1fr] gap-6">
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6">
            <h3 className="text-xl font-bold text-slate-100 mb-4">Default production stack</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                <div className="text-xs uppercase tracking-[0.12em] text-blue-300 mb-2">PostgreSQL</div>
                <p className="text-sm text-slate-300 leading-relaxed">Users, repos, audits, findings, scoring history, permissions, snapshots metadata, and job ownership.</p>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                <div className="text-xs uppercase tracking-[0.12em] text-cyan-300 mb-2">Redis</div>
                <p className="text-sm text-slate-300 leading-relaxed">Queue orchestration, rate limits, deduplication, short-lived job state, and distributed locking.</p>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                <div className="text-xs uppercase tracking-[0.12em] text-emerald-300 mb-2">S3-compatible object storage</div>
                <p className="text-sm text-slate-300 leading-relaxed">Repository snapshots, logs, raw analyzer output, large reports, and export bundles.</p>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                <div className="text-xs uppercase tracking-[0.12em] text-violet-300 mb-2">pgvector</div>
                <p className="text-sm text-slate-300 leading-relaxed">Code embeddings, semantic search, architectural similarity, and “find similar risky patterns” queries.</p>
              </div>
            </div>
          </div>

          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6">
            <h3 className="text-xl font-bold text-slate-100 mb-4">Optional large-scale tier</h3>
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
              <div className="text-xs uppercase tracking-[0.12em] text-rose-300 mb-2">ClickHouse</div>
              <p className="text-sm text-slate-300 leading-relaxed">
                Add ClickHouse only when audit/event volume requires very large-scale analytics, historical trends, and real-time dashboards across millions of audits.
              </p>
            </div>
            <ul className="mt-5 space-y-3 text-sm text-slate-300">
              <li>• Cached AST and semantic embeddings to avoid repeat work</li>
              <li>• Async GitHub webhooks for automatic repos and PR audits</li>
              <li>• Sandboxed execution for untrusted repositories</li>
              <li>• Centralized historical risk trends and repository health snapshots</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Architectural Value Pillars */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 space-y-2">
          <div className="w-8 h-8 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
            <Code className="w-4 h-4" />
          </div>
          <h3 className="font-bold text-sm text-slate-100">Deterministic Static AST</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Never hallucinates file issues. Inspects real AST complexity, bare excepts, wildcard imports, and nesting depth with line-by-line evidence.
          </p>
        </div>

        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 space-y-2">
          <div className="w-8 h-8 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
            <Cpu className="w-4 h-4" />
          </div>
          <h3 className="font-bold text-sm text-slate-100">Interactive Agent Tool-Calling</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Equipped with 8 runtime tools. Ask why files are difficult to maintain and watch the agent inspect churn, read functions, and run live AST metrics.
          </p>
        </div>

        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 space-y-2">
          <div className="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <h3 className="font-bold text-sm text-slate-100">Actionable GitHub Automation</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Generates copy-paste GitHub issue markdown, proposed PR unified diff patches, and publishes directly via GitHub REST API with one click.
          </p>
        </div>
      </section>

      {/* Global Command Palette */}
      <CommandPalette />
    </div>
  );
}
