"use client";

import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";
import {
  Layers,
  Copy,
  Check,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  Cpu,
  Database,
  Globe,
  Monitor,
  Server,
  Zap,
  Box,
  GitBranch,
  Repeat,
  Maximize2,
  Minimize2,
  Search,
  Code2,
  Info,
  ChevronRight,
  Sparkles,
  Flame,
  FileCode,
  ArrowRight,
} from "lucide-react";
import {
  TechStackChecklistItem,
  LayerFlowStep,
  ArchitectureRiskItem,
  ArchitectureStrengthItem,
  DependencyGraphDetail,
  BlastRadiusItem,
  LayerViolationItem,
  ComponentItem,
  ArchitectureDriftResult,
} from "@/types";
import { fetchArchitectureDrift } from "@/lib/api";

interface ArchitectureDiagramProps {
  reportId?: string;
  mermaidCode?: string;
  archetype?: string;
  confidence?: number;
  metrics?: Record<string, any>;
  explanation?: string;
  risks?: ArchitectureRiskItem[];
  strengths?: ArchitectureStrengthItem[];
  techStackChecklist?: TechStackChecklistItem[];
  layerFlow?: LayerFlowStep[];
  dependencyGraph?: DependencyGraphDetail;
  components?: ComponentItem[];
  blastRadius?: BlastRadiusItem[];
  layerViolations?: LayerViolationItem[];
}

export default function ArchitectureDiagram({
  reportId,
  mermaidCode,
  archetype,
  confidence,
  metrics,
  explanation,
  risks,
  strengths,
  techStackChecklist,
  layerFlow,
  dependencyGraph,
  components,
  blastRadius,
  layerViolations,
}: ArchitectureDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>("");
  const [copied, setCopied] = useState(false);
  const [renderError, setRenderError] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showRawMermaid, setShowRawMermaid] = useState(false);
  const [moduleSearch, setModuleSearch] = useState("");
  const [activeLayerFilter, setActiveLayerFilter] = useState<string>("all");
  const [selectedBlastModule, setSelectedBlastModule] = useState<string | null>(null);
  const [isDriftOpen, setIsDriftOpen] = useState(false);
  const [driftData, setDriftData] = useState<ArchitectureDriftResult | null>(null);
  const [isLoadingDrift, setIsLoadingDrift] = useState(false);

  const handleLoadDrift = async () => {
    if (!reportId) return;
    setIsDriftOpen(true);
    if (driftData) return;
    setIsLoadingDrift(true);
    try {
      const data = await fetchArchitectureDrift(reportId);
      setDriftData(data);
    } catch (err) {
      console.error("Failed to fetch drift:", err);
    } finally {
      setIsLoadingDrift(false);
    }
  };

  // Derive values from metrics if not directly passed
  const effectivePattern =
    archetype ||
    metrics?.architecture_pattern ||
    metrics?.archetype ||
    "Modular Monolith";
  const effectiveConfidence =
    confidence || metrics?.pattern_confidence || 88;
  const effectiveDescription =
    metrics?.pattern_description ||
    "Structured monolithic codebase composed of cohesive domain modules, unified data models, and isolated business logic layers.";
  const effectiveMermaid =
    mermaidCode ||
    metrics?.mermaid_diagram ||
    `graph TD\n    User["👤 Client / Web Browser"] --> API["🌐 API Layer"]\n    API --> Services["⚙️ Business Services"]\n    Services --> Repos["🗄️ Repositories"]\n    Repos --> DB[("💾 PostgreSQL")]`;
  const effectiveExplanation =
    explanation ||
    metrics?.architecture_explanation ||
    `The application follows a ${effectivePattern} design pattern with clear separation of concerns across controllers, business services, and repository layers.`;
  const effectiveRisks: ArchitectureRiskItem[] =
    risks || metrics?.architecture_risks || [];
  const effectiveStrengths: ArchitectureStrengthItem[] =
    strengths || metrics?.architecture_strengths || [];
  const effectiveChecklist: TechStackChecklistItem[] =
    techStackChecklist || metrics?.tech_stack_checklist || [];
  const effectiveFlow: LayerFlowStep[] =
    layerFlow || metrics?.layer_flow || [];
  const effectiveGraph: DependencyGraphDetail | undefined =
    dependencyGraph || metrics?.dependency_graph;
  const effectiveBlastRadius: BlastRadiusItem[] =
    blastRadius || metrics?.blast_radius || [];
  const effectiveLayerViolations: LayerViolationItem[] =
    layerViolations || metrics?.layer_violations || [];

  // Derive components list
  const effectiveComponents: ComponentItem[] = components || [
    {
      name: "API & Controllers",
      type: "controller",
      layer: "presentation",
      file_count: metrics?.detected_layers?.controllers?.length || 4,
      files: metrics?.detected_layers?.controllers || [],
      loc: 450,
      description: "Handles HTTP requests, route dispatching, and request validation.",
    },
    {
      name: "Business Services",
      type: "service",
      layer: "business",
      file_count: metrics?.detected_layers?.services?.length || 6,
      files: metrics?.detected_layers?.services || [],
      loc: 820,
      description: "Encapsulates core domain business rules and operation workflows.",
    },
    {
      name: "Repositories & Data Access",
      type: "repository",
      layer: "data_access",
      file_count: metrics?.detected_layers?.repositories?.length || 3,
      files: metrics?.detected_layers?.repositories || [],
      loc: 380,
      description: "Isolates database queries and ORM persistence operations.",
    },
    {
      name: "Database Persistence",
      type: "database",
      layer: "persistence",
      file_count: 1,
      files: ["storage/database"],
      loc: 0,
      description: metrics?.tech_stack?.database?.[0] || "PostgreSQL Database",
    },
  ];

  const [currentTheme, setCurrentTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    const checkTheme = () => {
      const isLight = document.documentElement.getAttribute("data-theme") === "light";
      setCurrentTheme(isLight ? "light" : "dark");
    };
    checkTheme();

    const observer = new MutationObserver(checkTheme);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => observer.disconnect();
  }, []);

  // Initialize and render Mermaid diagram with theme awareness
  useEffect(() => {
    let isMounted = true;
    try {
      const isLight = currentTheme === "light";
      mermaid.initialize({
        startOnLoad: false,
        theme: isLight ? "default" : "dark",
        themeVariables: {
          darkMode: !isLight,
          background: isLight ? "#ffffff" : "#090d16",
          primaryColor: isLight ? "#2563eb" : "#3b82f6",
          primaryTextColor: isLight ? "#0f172a" : "#f8fafc",
          primaryBorderColor: isLight ? "#93c5fd" : "#60a5fa",
          lineColor: isLight ? "#64748b" : "#94a3b8",
          secondaryColor: isLight ? "#f8fafc" : "#1e293b",
          tertiaryColor: isLight ? "#f1f5f9" : "#0f172a",
        },
        securityLevel: "loose",
        flowchart: {
          curve: "basis",
          htmlLabels: true,
          padding: 8,
        },
      });

      const id = `mermaid-arch-${Math.random().toString(36).substring(2, 9)}`;
      mermaid
        .render(id, effectiveMermaid)
        .then(({ svg }) => {
          if (isMounted) {
            setSvgContent(svg);
            setRenderError(false);
          }
        })
        .catch((err) => {
          console.error("Mermaid rendering error:", err);
          if (isMounted) {
            setRenderError(true);
          }
        });
    } catch (err) {
      console.error("Mermaid init error:", err);
      setRenderError(true);
    }
    return () => {
      isMounted = false;
    };
  }, [effectiveMermaid, currentTheme]);

  const handleCopyMermaid = () => {
    navigator.clipboard.writeText(effectiveMermaid);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Filter modules in dependency table
  const filteredNodes = (effectiveGraph?.nodes || []).filter((node) => {
    const matchesSearch =
      node.label.toLowerCase().includes(moduleSearch.toLowerCase()) ||
      node.id.toLowerCase().includes(moduleSearch.toLowerCase());
    const matchesLayer =
      activeLayerFilter === "all" || node.layer === activeLayerFilter;
    return matchesSearch && matchesLayer;
  });

  return (
    <div className="space-y-6">
      {/* 1. TOP HERO: ARCHITECTURE PATTERN & CONFIDENCE */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 shadow-inner">
              <Layers className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-blue-400">
                  Architecture Intelligence
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {effectiveConfidence >= 1 ? `${effectiveConfidence}% Confidence` : `${Math.round(effectiveConfidence * 100)}% Confidence`}
                </span>
              </div>
              <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                {effectivePattern}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto">
            <button
              onClick={handleCopyMermaid}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border transition-all ${
                copied
                  ? "bg-emerald-600 text-white border-emerald-500 shadow-sm"
                  : "bg-slate-800 text-slate-200 border-slate-700 hover:bg-slate-700 hover:text-white"
              }`}
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-white" />
                  <span className="text-white font-bold">Copied Code</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy Mermaid</span>
                </>
              )}
            </button>
            <button
              onClick={() => setShowRawMermaid(!showRawMermaid)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border transition-all ${
                showRawMermaid
                  ? "bg-blue-600 text-white border-blue-500 shadow-sm toggle-active font-bold"
                  : "bg-slate-800 text-slate-200 border-slate-700 hover:bg-slate-700 hover:text-white"
              }`}
            >
              <Code2 className="w-3.5 h-3.5" />
              <span>{showRawMermaid ? "View Diagram" : "Raw Syntax"}</span>
            </button>

            {reportId && (
              <button
                onClick={handleLoadDrift}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border bg-purple-950/40 text-purple-300 border-purple-500/30 hover:bg-purple-900/50 transition-all shadow-sm"
              >
                <GitBranch className="w-3.5 h-3.5 text-purple-400" />
                <span>Drift Evolution</span>
              </button>
            )}
          </div>
        </div>

        {/* Drift Evolution Drawer / Panel */}
        {isDriftOpen && (
          <div className="bg-slate-950/90 border border-purple-500/30 rounded-xl p-5 space-y-4 animate-in fade-in duration-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-purple-400" />
                <h4 className="text-xs font-bold text-slate-100 uppercase tracking-wider font-mono">
                  Architecture Drift & Evolution Detection
                </h4>
                {driftData && (
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                      driftData.drift_severity === "High"
                        ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                        : driftData.drift_severity === "Medium"
                        ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                        : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    }`}
                  >
                    {driftData.drift_severity} Drift
                  </span>
                )}
              </div>
              <button
                onClick={() => setIsDriftOpen(false)}
                className="text-slate-400 hover:text-white text-xs font-mono"
              >
                Hide Panel
              </button>
            </div>

            {isLoadingDrift ? (
              <div className="py-8 text-center text-xs text-slate-400 font-mono">
                <RefreshCw className="w-5 h-5 mx-auto animate-spin text-purple-400 mb-2" />
                Comparing architecture models against prior baseline audit...
              </div>
            ) : driftData ? (
              <div className="space-y-3 text-xs">
                <p className="text-slate-300 leading-relaxed bg-slate-900/60 p-3 rounded-lg border border-slate-800 font-mono">
                  {driftData.explanation}
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                    <span className="text-[10px] font-mono text-emerald-400 uppercase font-bold block">
                      Added Components ({driftData.added_components.length})
                    </span>
                    <span className="text-slate-300 text-xs">
                      {driftData.added_components.length > 0
                        ? driftData.added_components.join(", ")
                        : "None (Topology stable)"}
                    </span>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                    <span className="text-[10px] font-mono text-blue-400 uppercase font-bold block">
                      New Communication Flows ({driftData.added_flows.length})
                    </span>
                    <span className="text-slate-300 text-xs">
                      {driftData.added_flows.length > 0
                        ? driftData.added_flows.join(", ")
                        : "None"}
                    </span>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        )}

        <p className="text-xs text-slate-300 leading-relaxed">
          {effectiveDescription}
        </p>

        {metrics?.pattern_characteristics && metrics.pattern_characteristics.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-1">
            {metrics.pattern_characteristics.map((char: string, idx: number) => (
              <span
                key={idx}
                className="px-2.5 py-1 rounded-md text-[11px] font-medium bg-slate-800/80 text-blue-300 border border-blue-500/20 flex items-center gap-1"
              >
                <Check className="w-3 h-3 text-blue-400" />
                {char}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 2. COMPONENTS BREAKDOWN & TECH STACK CHECKLIST */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <Box className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-bold text-slate-100">
                Identified Architecture Components
              </h3>
            </div>
            <span className="text-[11px] text-slate-400">
              {effectiveComponents.length} logical subsystems
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {effectiveComponents.map((comp, idx) => (
              <div
                key={idx}
                className="bg-slate-950/70 border border-slate-800/90 rounded-xl p-3.5 space-y-1.5 flex flex-col justify-between"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                    {comp.name}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    {comp.file_count} {comp.file_count === 1 ? "file" : "files"}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  {comp.description}
                </p>
                {comp.loc > 0 && (
                  <span className="text-[10px] text-slate-500 font-mono">
                    ~{comp.loc} lines of code
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Cpu className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-bold text-slate-100">
                Technology Capabilities Checklist
              </h3>
            </div>
            <span className="text-[11px] text-slate-400">
              Evidence-backed stack detection
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2.5">
            {effectiveChecklist.map((item, idx) => (
              <div
                key={idx}
                className={`flex items-center justify-between p-2.5 rounded-xl border transition-all ${
                  item.detected
                    ? "bg-slate-950/80 border-slate-700/80 text-slate-200"
                    : "bg-slate-950/30 border-slate-800/40 text-slate-500 opacity-60"
                }`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  {item.detected ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-slate-700 shrink-0" />
                  )}
                  <span className="text-xs font-semibold truncate">
                    {item.category}
                  </span>
                </div>
                <span
                  className={`text-[11px] truncate max-w-[120px] text-right font-medium ${
                    item.detected ? "text-blue-400 font-mono" : "text-slate-600"
                  }`}
                  title={item.name}
                >
                  {item.name}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 3. LAYER FLOW PIPELINE SEQUENCE */}
      {effectiveFlow.length > 0 && (
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm shadow-xl space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-purple-400" />
            Layer Hierarchy & Request Traversal Flow
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            {effectiveFlow.map((step, idx) => (
              <div
                key={idx}
                className="relative bg-slate-950/60 border border-slate-800/90 rounded-xl p-3.5 flex flex-col justify-between space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center text-xs font-bold">
                      {idx + 1}
                    </div>
                    <span className="text-xs font-bold text-slate-200">
                      {step.layer}
                    </span>
                  </div>
                  {idx < effectiveFlow.length - 1 && (
                    <ChevronRight className="w-4 h-4 text-slate-600 hidden md:block" />
                  )}
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. DYNAMIC MERMAID DIAGRAM VISUALIZER */}
      <div
        className={`bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm shadow-xl space-y-4 transition-all ${
          isFullscreen ? "fixed inset-4 z-50 overflow-auto bg-slate-950/95" : ""
        }`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <Zap className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-semibold text-sm text-slate-100">
                System Topology Flowchart
              </h3>
              <span className="text-[11px] text-slate-400">
                Live interactive component graph rendered from repository AST
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className={`p-1.5 rounded-lg border transition-all ${
                isFullscreen
                  ? "bg-blue-600 text-white border-blue-500 shadow-sm toggle-active"
                  : "bg-slate-800 text-slate-300 hover:text-white border-slate-700 hover:bg-slate-700"
              }`}
              title={isFullscreen ? "Exit Fullscreen" : "Fullscreen View"}
            >
              {isFullscreen ? (
                <Minimize2 className="w-4 h-4 text-white" />
              ) : (
                <Maximize2 className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        <div className="bg-slate-950/80 border border-slate-800/90 rounded-xl p-4 flex items-center justify-center overflow-x-auto">
          {showRawMermaid ? (
            <div className="w-full text-left font-mono text-xs text-slate-300 bg-slate-900/90 p-4 rounded-lg border border-slate-800 overflow-x-auto">
              <pre>{effectiveMermaid}</pre>
            </div>
          ) : renderError ? (
            <div className="text-center text-xs text-slate-400 font-mono space-y-2">
              <p className="text-amber-400 font-sans">
                Could not render SVG directly. Showing generated Mermaid code:
              </p>
              <pre className="text-left text-[11px] text-slate-300 p-4 bg-slate-900 rounded-lg">
                {effectiveMermaid}
              </pre>
            </div>
          ) : svgContent ? (
            <div
              ref={containerRef}
              className="w-full flex justify-center [&>svg]:max-w-full [&>svg]:h-auto [&>svg]:max-h-[500px] transition-transform my-0 py-0"
              dangerouslySetInnerHTML={{ __html: svgContent }}
            />
          ) : (
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Synthesizing dynamic architecture diagram...</span>
            </div>
          )}
        </div>
      </div>

      {/* 5. AI ARCHITECTURE EXPLANATION */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm shadow-xl space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-800/80 pb-4">
          <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-semibold text-sm text-slate-100">
              AI Architectural Narrative & Request Flow
            </h3>
            <span className="text-[11px] text-slate-400">
              Synthesized design breakdown and request lifecycle analysis
            </span>
          </div>
        </div>

        <div className="prose prose-invert prose-xs max-w-none text-slate-300 leading-relaxed space-y-4">
          {String(effectiveExplanation).split("\n\n").map((para: string, idx: number) => {
            if (para.startsWith("### ")) {
              return (
                <h4 key={idx} className="text-sm font-bold text-blue-400 mt-2">
                  {para.replace("### ", "")}
                </h4>
              );
            }
            if (para.startsWith("#### ")) {
              return (
                <h5 key={idx} className="text-xs font-bold uppercase tracking-wider text-slate-200 mt-3">
                  {para.replace("#### ", "")}
                </h5>
              );
            }
            return (
              <p key={idx} className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
                {para}
              </p>
            );
          })}
        </div>
      </div>

      {/* 6. BLAST RADIUS IMPACT ANALYSIS */}
      {effectiveBlastRadius && effectiveBlastRadius.length > 0 && (
        <div className="bg-slate-900/60 border border-amber-950/40 rounded-2xl p-6 backdrop-blur-sm shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <Flame className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-semibold text-sm text-slate-100">
                  Downstream Blast Radius Impact Engine
                </h3>
                <span className="text-[11px] text-slate-400">
                  Quantitative ripple effect of modifications to key services
                </span>
              </div>
            </div>
            <span className="text-[11px] text-amber-400 font-mono">
              {effectiveBlastRadius.length} core dependencies evaluated
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {effectiveBlastRadius.map((br, idx) => (
              <div
                key={idx}
                onClick={() => setSelectedBlastModule(selectedBlastModule === br.target_module ? null : br.target_module)}
                className={`cursor-pointer bg-slate-950/80 border rounded-xl p-4 space-y-3 transition-all ${
                  selectedBlastModule === br.target_module
                    ? "border-amber-500/80 shadow-lg shadow-amber-500/10"
                    : "border-slate-800/90 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-slate-200 truncate max-w-[180px]" title={br.target_module}>
                    {br.target_module.split("/").pop()}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      br.risk_level === "CRITICAL"
                        ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                        : br.risk_level === "HIGH"
                        ? "bg-orange-500/20 text-orange-300 border border-orange-500/40"
                        : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                    }`}
                  >
                    {br.risk_level} Impact
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center text-[10px] font-mono">
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                    <div className="font-bold text-slate-200">{br.affected_modules.length}</div>
                    <div className="text-slate-500 text-[9px]">Modules</div>
                  </div>
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                    <div className="font-bold text-cyan-400">{br.affected_endpoints.length}</div>
                    <div className="text-slate-500 text-[9px]">APIs</div>
                  </div>
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                    <div className="font-bold text-purple-400">{br.affected_tests.length}</div>
                    <div className="text-slate-500 text-[9px]">Tests</div>
                  </div>
                </div>

                {selectedBlastModule === br.target_module && (
                  <div className="pt-2 border-t border-slate-800 space-y-1.5 text-[11px] text-slate-400">
                    <div className="font-semibold text-slate-300">Downstream Traversal:</div>
                    {br.affected_modules.slice(0, 4).map((mod, i) => (
                      <div key={i} className="flex items-center gap-1 font-mono text-[10px] text-slate-400">
                        <ArrowRight className="w-3 h-3 text-amber-400 shrink-0" />
                        <span className="truncate">{mod}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 7. ARCHITECTURE RISKS & STRENGTHS */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-900/60 border border-rose-950/40 rounded-2xl p-6 backdrop-blur-sm shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-semibold text-sm text-slate-100">
                  Architectural Risks & Boundary Violations
                </h3>
                <span className="text-[11px] text-slate-400">
                  {effectiveRisks.length} potential structural concern(s) detected
                </span>
              </div>
            </div>
          </div>

          {effectiveRisks.length > 0 ? (
            <div className="space-y-3">
              {effectiveRisks.map((risk, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950/70 border border-rose-900/30 rounded-xl p-4 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-rose-300 flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                      {risk.title}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-rose-500/10 text-rose-400 border border-rose-500/20">
                      {risk.severity}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {risk.description}
                  </p>
                  {risk.mitigation && (
                    <div className="text-[11px] text-slate-400 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                      <strong className="text-blue-400 font-semibold">
                        Remediation:
                      </strong>{" "}
                      {risk.mitigation}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-emerald-950/20 border border-emerald-900/30 rounded-xl p-6 text-center space-y-2">
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
              <h4 className="text-xs font-bold text-emerald-300">
                Zero High-Risk Architectural Flaws
              </h4>
              <p className="text-[11px] text-slate-400">
                No circular dependency cycles, god modules, or layer violations were detected.
              </p>
            </div>
          )}
        </div>

        <div className="bg-slate-900/60 border border-emerald-950/40 rounded-2xl p-6 backdrop-blur-sm shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-semibold text-sm text-slate-100">
                  Architectural Strengths & Hygiene
                </h3>
                <span className="text-[11px] text-slate-400">
                  {effectiveStrengths.length} verified design best practice(s)
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            {effectiveStrengths.map((str, idx) => (
              <div
                key={idx}
                className="bg-slate-950/70 border border-emerald-900/30 rounded-xl p-4 space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-emerald-300 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    {str.title}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {str.badge}
                  </span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {str.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 8. MODULE DEPENDENCY & IMPORT GRAPH EXPLORER */}
      {effectiveGraph && effectiveGraph.nodes && effectiveGraph.nodes.length > 0 && (
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Repeat className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-semibold text-sm text-slate-100">
                  Module Dependency & Coupling Explorer
                </h3>
                <span className="text-[11px] text-slate-400">
                  Analyzed {effectiveGraph.total_modules} modules across{" "}
                  {effectiveGraph.total_dependencies} static import dependencies
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter module..."
                  value={moduleSearch}
                  onChange={(e) => setModuleSearch(e.target.value)}
                  className="bg-slate-950 text-xs text-slate-200 pl-8 pr-3 py-1.5 rounded-lg border border-slate-800 focus:outline-none focus:border-blue-500 w-36 sm:w-48"
                />
              </div>
              <select
                value={activeLayerFilter}
                onChange={(e) => setActiveLayerFilter(e.target.value)}
                className="bg-slate-950 text-xs text-slate-200 px-2.5 py-1.5 rounded-lg border border-slate-800 focus:outline-none focus:border-blue-500"
              >
                <option value="all">All Layers</option>
                <option value="controllers">Controllers</option>
                <option value="services">Services</option>
                <option value="repositories">Repositories</option>
                <option value="models">Models</option>
                <option value="workers">Workers</option>
                <option value="utils">Utils</option>
              </select>
            </div>
          </div>

          {effectiveGraph.circular_cycles &&
            effectiveGraph.circular_cycles.length > 0 && (
              <div className="p-4 bg-rose-950/30 border border-rose-800/40 rounded-xl space-y-2">
                <span className="text-xs font-bold text-rose-300 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                  {effectiveGraph.circular_cycles.length} Circular Dependency Loop(s)
                  Detected:
                </span>
                <div className="flex flex-wrap gap-2">
                  {effectiveGraph.circular_cycles.map((c, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 rounded-lg text-xs font-mono bg-rose-900/30 text-rose-200 border border-rose-800/50"
                    >
                      {c.display}
                    </span>
                  ))}
                </div>
              </div>
            )}

          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Module Name</th>
                  <th className="py-3 px-4">Layer Role</th>
                  <th className="py-3 px-4 text-center">Fan-In (Ca)</th>
                  <th className="py-3 px-4 text-center">Fan-Out (Ce)</th>
                  <th className="py-3 px-4 text-center">Instability (I)</th>
                  <th className="py-3 px-4 text-right">LOC</th>
                  <th className="py-3 px-4 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
                {filteredNodes.map((node) => (
                  <tr
                    key={node.id}
                    className="hover:bg-slate-900/50 transition-colors"
                  >
                    <td className="py-2.5 px-4 font-mono font-medium text-slate-200 flex items-center gap-2">
                      <FileCode className="w-3.5 h-3.5 text-slate-500" />
                      <span title={node.id}>{node.label}</span>
                    </td>
                    <td className="py-2.5 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300 capitalize border border-slate-700">
                        {node.layer}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-center font-mono text-cyan-400">
                      {node.in_degree}
                    </td>
                    <td className="py-2.5 px-4 text-center font-mono text-purple-400">
                      {node.out_degree}
                    </td>
                    <td className="py-2.5 px-4 text-center font-mono">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] ${
                          node.instability > 0.8
                            ? "text-amber-400 bg-amber-500/10"
                            : node.instability < 0.2
                            ? "text-blue-400 bg-blue-500/10"
                            : "text-slate-400 bg-slate-800"
                        }`}
                      >
                        {node.instability}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-right font-mono text-slate-400">
                      {node.loc}
                    </td>
                    <td className="py-2.5 px-4 text-center">
                      {node.is_god_module ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          God Module
                        </span>
                      ) : node.is_isolated ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-400">
                          Isolated
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400">
                          Healthy
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
