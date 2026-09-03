"use client";

import { useState, useRef, useEffect } from "react";
import { AgentToolStep } from "@/types";
import { streamAgentMessage } from "@/lib/api";
import {
  Bot,
  Send,
  User,
  Terminal,
  ChevronDown,
  ChevronRight,
  Sparkles,
  RefreshCw,
  X,
  Copy,
  Check,
  Maximize2,
  Minimize2,
  Trash2,
  Code2,
  ShieldCheck,
  Zap,
  BookOpen,
  Settings,
  Cpu,
  Key,
  ThumbsUp,
  ThumbsDown,
  Download,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface AgentChatDrawerProps {
  reportId: string;
  isOpen: boolean;
  onClose: () => void;
  onNavigateTab?: (tab: string) => void;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  toolSteps?: AgentToolStep[];
  modelUsed?: string;
  feedback?: "up" | "down";
  isStreaming?: boolean;
}

export default function AgentChatDrawer({
  reportId,
  isOpen,
  onClose,
  onNavigateTab,
}: AgentChatDrawerProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "### 👋 Hello! I am your AI Repository Auditor Copilot.\n\nI have full introspective access to this repository. I can:\n• 📋 **List Issues**: Ask *'List of issues'* to see an itemized numbered breakdown.\n• 🛠️ **Solve One-by-One**: Type *'Fix issue 1'*, *'Fix issue 2'*, etc.\n• 🔍 **Diagnose & Resolve**: Pinpoint exact lines of code causing bugs and provide ready-to-use fixes.\n• 🧪 **Generate Tests**: Write complete `pytest` or `jest` test suites for any file.\n• ⚡ **Auto-Solve**: Click `✨ /autosolve` to remediate everything in an isolated sandbox with zero intervention!\n\nAsk me anything or use the slash commands below.",
      modelUsed: "Neural AST Transformer",
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [drawerWidth, setDrawerWidth] = useState<"compact" | "wide" | "full">("wide");
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({});
  const [copiedIndex, setCopiedIndex] = useState<string | null>(null);

  // Model Settings State
  const [selectedProvider, setSelectedProvider] = useState<"offline" | "gemini" | "openai">("offline");
  const [apiKey, setApiKey] = useState<string>("");
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen]);

  if (!isOpen) return null;

  const toggleToolExpand = (key: string) => {
    setExpandedTools((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleCopyCode = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedIndex(id);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleFeedback = (msgIdx: number, type: "up" | "down") => {
    setMessages((prev) =>
      prev.map((m, idx) => (idx === msgIdx ? { ...m, feedback: type } : m))
    );
  };

  const handleClearChat = () => {
    setMessages([
      {
        role: "assistant",
        content:
          "Chat history reset. How can I help you investigate or improve this repository?",
        modelUsed:
          selectedProvider === "gemini"
            ? "Gemini 1.5 Pro"
            : selectedProvider === "openai"
            ? "GPT-4o"
            : "Neural AST Transformer",
      },
    ]);
  };

  const handleExportChat = () => {
    const transcript = messages
      .map(
        (m) =>
          `### ${m.role === "user" ? "👤 Developer" : `🤖 AI Copilot (${m.modelUsed || "Neural AST"})`}\n\n${m.content}\n`
      )
      .join("\n---\n\n");
    const blob = new Blob([transcript], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Copilot_Audit_Session_${reportId.slice(0, 8)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadSnippet = (code: string, filename: string = "snippet.txt") => {
    const blob = new Blob([code], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleSendMessage = async (customPrompt?: string) => {
    const textToSend = customPrompt || inputMessage;
    if (!textToSend.trim() || isLoading) return;

    const newMessages: ChatMessage[] = [...messages, { role: "user", content: textToSend }];
    setMessages(newMessages);
    if (!customPrompt) setInputMessage("");
    setIsLoading(true);

    const activeModelName =
      selectedProvider === "gemini"
        ? "Gemini 1.5 Pro (DeepMind)"
        : selectedProvider === "openai"
        ? "GPT-4o (OpenAI)"
        : "Neural AST Transformer (Offline)";

    // Append placeholder for assistant response with isStreaming = true
    const assistantMsgIndex = newMessages.length;
    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content: "",
        toolSteps: [],
        modelUsed: activeModelName,
        isStreaming: true,
      },
    ]);

    await streamAgentMessage(
      {
        report_id: reportId,
        message: textToSend,
        history: newMessages.map((m) => ({ role: m.role, content: m.content })),
        llm_provider: selectedProvider,
        api_key: apiKey.trim() || undefined,
      },
      (toolStep) => {
        setMessages((prev) =>
          prev.map((msg, idx) =>
            idx === assistantMsgIndex
              ? {
                  ...msg,
                  toolSteps: [...(msg.toolSteps || []), toolStep],
                }
              : msg
          )
        );
      },
      (token) => {
        setMessages((prev) =>
          prev.map((msg, idx) =>
            idx === assistantMsgIndex
              ? {
                  ...msg,
                  content: msg.content + token,
                }
              : msg
          )
        );
      },
      () => {
        setIsLoading(false);
        setMessages((prev) =>
          prev.map((msg, idx) =>
            idx === assistantMsgIndex
              ? {
                  ...msg,
                  isStreaming: false,
                }
              : msg
          )
        );
      },
      (err) => {
        setIsLoading(false);
        setMessages((prev) =>
          prev.map((msg, idx) =>
            idx === assistantMsgIndex
              ? {
                  ...msg,
                  content:
                    msg.content ||
                    "⚠️ **Error executing Copilot tools**: Failed to complete inspection for that request. Please try again.",
                  isStreaming: false,
                }
              : msg
          )
        );
      }
    );
  };

  // Helper to render rich markdown & code blocks with copy buttons
  const renderMessageContent = (content: string, msgIdx: number, isStreaming?: boolean) => {
    const codeBlockRegex = /```([a-zA-Z0-9_\-\+]*)\n([\s\S]*?)```/g;
    const parts = [];
    let lastIndex = 0;
    let match;
    let blockCount = 0;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      if (match.index > lastIndex) {
        parts.push(
          <div key={`text-${lastIndex}`} className="space-y-1.5 leading-relaxed">
            {renderFormattedText(content.substring(lastIndex, match.index))}
          </div>
        );
      }

      const lang = match[1] || "code";
      const codeSnippet = match[2];
      const blockId = `${msgIdx}-${blockCount++}`;

      parts.push(
        <div
          key={`code-${match.index}`}
          className="my-3 rounded-xl overflow-hidden border border-slate-800 bg-slate-950 font-mono text-xs shadow-md"
        >
          <div className="bg-slate-900/90 px-3 py-1.5 text-[10px] font-bold text-slate-400 border-b border-slate-800 flex items-center justify-between">
            <span className="uppercase tracking-wider text-blue-400 flex items-center gap-1.5">
              <Code2 className="w-3.5 h-3.5" />
              {lang}
            </span>
            <button
              onClick={() => handleCopyCode(codeSnippet, blockId)}
              className="flex items-center gap-1 text-slate-400 hover:text-slate-200 transition-colors px-2 py-0.5 rounded bg-slate-800/60 hover:bg-slate-800"
            >
              {copiedIndex === blockId ? (
                <>
                  <Check className="w-3 h-3 text-emerald-400" />
                  <span className="text-emerald-400 text-[10px]">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  <span className="text-[10px]">Copy Code</span>
                </>
              )}
            </button>
          </div>
          <pre className="p-3 text-slate-200 overflow-x-auto text-[11px] leading-relaxed whitespace-pre">
            <code>{codeSnippet}</code>
          </pre>
        </div>
      );

      lastIndex = match.index + match[0].length;
    }

    if (lastIndex < content.length) {
      parts.push(
        <div key={`text-${lastIndex}`} className="space-y-1.5 leading-relaxed">
          {renderFormattedText(content.substring(lastIndex))}
        </div>
      );
    }

    if (isStreaming) {
      parts.push(
        <span
          key="cursor"
          className="inline-block w-2 h-4 bg-blue-400 animate-pulse ml-0.5 align-middle"
        />
      );
    }

    return parts;
  };

  // Helper to convert raw LaTeX math and chemical formulas to clean Unicode (e.g. \text{C}_6\text{H}_{11} -> C₆H₁₁)
  const cleanLatex = (str: string): string => {
    let t = str.replace(/\\text\{([^}]+)\}/g, "$1");
    t = t.replace(/\\mathrm\{([^}]+)\}/g, "$1");
    t = t.replace(/\^?\\bullet/g, "•");
    t = t.replace(/\^\+/g, "⁺").replace(/\^\-/g, "⁻");

    const subMap: Record<string, string> = {
      "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
      "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
    };
    t = t.replace(/_\{(\d+)\}|_(\d)/g, (_, p1, p2) => {
      const digits = p1 || p2 || "";
      return digits
        .split("")
        .map((d: string) => subMap[d] || d)
        .join("");
    });
    t = t.replace(/\$/g, "");
    return t;
  };

  // Helper to format inline markdown (bold **text**, inline code `code`)
  const formatInline = (raw: string): (string | JSX.Element)[] => {
    const text = cleanLatex(raw);
    const parts: (string | JSX.Element)[] = [];
    const tokenRegex = /(`[^`]+`|\*\*[^*]+\*\*)/g;
    let lastIdx = 0;
    let match: RegExpExecArray | null;

    while ((match = tokenRegex.exec(text)) !== null) {
      if (match.index > lastIdx) {
        parts.push(text.substring(lastIdx, match.index));
      }
      const token = match[0];
      if (token.startsWith("`") && token.endsWith("`")) {
        parts.push(
          <code
            key={`code-${match.index}`}
            className="px-1.5 py-0.5 rounded bg-slate-800 text-blue-300 font-mono text-[11px] border border-slate-700/50"
          >
            {token.slice(1, -1)}
          </code>
        );
      } else if (token.startsWith("**") && token.endsWith("**")) {
        parts.push(
          <strong key={`bold-${match.index}`} className="font-bold text-slate-100">
            {token.slice(2, -2)}
          </strong>
        );
      }
      lastIdx = match.index + token.length;
    }

    if (lastIdx < text.length) {
      parts.push(text.substring(lastIdx));
    }

    return parts;
  };

  // Helper to format full markdown blocks (tables, headers, lists, blockquotes, bold)
  const renderFormattedText = (rawText: string) => {
    const lines = rawText.split("\n");
    const elements: JSX.Element[] = [];
    let i = 0;

    while (i < lines.length) {
      const line = lines[i];
      const trimmed = line.trim();

      // Empty line
      if (!trimmed) {
        elements.push(<div key={`empty-${i}`} className="h-1.5" />);
        i++;
        continue;
      }

      // Check if this line is part of a markdown table (e.g., starts and ends with '|')
      const isTableLine = (str: string) => {
        const s = str.trim();
        return s.startsWith("|") && s.endsWith("|") && s.split("|").length >= 3;
      };

      if (isTableLine(trimmed)) {
        const tableLines: string[] = [];
        while (i < lines.length && isTableLine(lines[i])) {
          tableLines.push(lines[i].trim());
          i++;
        }

        const parsedRows = tableLines.map((tl) =>
          tl
            .split("|")
            .slice(1, -1)
            .map((c) => c.trim())
        );

        const isDelimiterRow = (cells: string[]) =>
          cells.every((c) => /^:?-+:?$/.test(c.replace(/\s+/g, "")));

        let headers: string[] = [];
        let bodyRows: string[][] = [];

        if (parsedRows.length > 1 && isDelimiterRow(parsedRows[1])) {
          headers = parsedRows[0];
          bodyRows = parsedRows.slice(2);
        } else {
          headers = parsedRows[0];
          bodyRows = parsedRows.slice(1).filter((r) => !isDelimiterRow(r));
        }

        elements.push(
          <div
            key={`table-${i}`}
            className="my-3 overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/70 shadow-lg"
          >
            <table className="w-full text-left text-xs border-collapse">
              {headers.length > 0 && (
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-900/90 text-slate-200">
                    {headers.map((h, hIdx) => (
                      <th
                        key={hIdx}
                        className="px-3.5 py-2 text-blue-400 font-bold uppercase tracking-wider text-[11px]"
                      >
                        {formatInline(h)}
                      </th>
                    ))}
                  </tr>
                </thead>
              )}
              <tbody className="divide-y divide-slate-800/60">
                {bodyRows.map((row, rIdx) => (
                  <tr
                    key={rIdx}
                    className="hover:bg-slate-900/40 transition-colors"
                  >
                    {row.map((cell, cIdx) => (
                      <td
                        key={cIdx}
                        className="px-3.5 py-2.5 text-slate-300 align-top leading-relaxed"
                      >
                        {formatInline(cell)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        continue;
      }

      // Headers
      if (trimmed.startsWith("### ")) {
        elements.push(
          <h3
            key={`h3-${i}`}
            className="text-sm font-extrabold text-slate-100 mt-2.5 mb-1 flex items-center gap-1.5"
          >
            {formatInline(trimmed.replace("### ", ""))}
          </h3>
        );
        i++;
        continue;
      }
      if (trimmed.startsWith("#### ")) {
        elements.push(
          <h4
            key={`h4-${i}`}
            className="text-xs font-bold text-blue-300 mt-2 mb-0.5"
          >
            {formatInline(trimmed.replace("#### ", ""))}
          </h4>
        );
        i++;
        continue;
      }
      if (trimmed.startsWith("## ")) {
        elements.push(
          <h2
            key={`h2-${i}`}
            className="text-base font-extrabold text-slate-100 mt-3 mb-1.5"
          >
            {formatInline(trimmed.replace("## ", ""))}
          </h2>
        );
        i++;
        continue;
      }

      // Blockquotes (> Did you know...)
      if (trimmed.startsWith("> ")) {
        elements.push(
          <div
            key={`quote-${i}`}
            className="my-2 border-l-2 border-blue-500/80 bg-blue-500/10 px-3 py-2 rounded-r-lg text-xs text-blue-200"
          >
            {formatInline(trimmed.replace(/^>\s*/, ""))}
          </div>
        );
        i++;
        continue;
      }

      // Bullet lists (*, -, •, * **)
      const bulletMatch = trimmed.match(/^([•\-\*]\s*)+/);
      if (bulletMatch) {
        const cleanBulletText = trimmed.replace(/^([•\-\*]\s*)+/, "");
        elements.push(
          <div
            key={`bullet-${i}`}
            className="flex items-start gap-2 pl-1 my-1 text-slate-300 text-xs leading-relaxed"
          >
            <span className="text-blue-400 font-bold mt-0.5">•</span>
            <div className="flex-1">{formatInline(cleanBulletText)}</div>
          </div>
        );
        i++;
        continue;
      }

      // Numbered lists (1. , 2. )
      const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
      if (numMatch) {
        elements.push(
          <div
            key={`num-${i}`}
            className="flex items-start gap-2 pl-1 my-1 text-slate-300 text-xs leading-relaxed"
          >
            <span className="text-blue-400 font-bold min-w-[1.2rem]">{numMatch[1]}.</span>
            <div className="flex-1">{formatInline(numMatch[2])}</div>
          </div>
        );
        i++;
        continue;
      }

      // Divider
      if (trimmed.startsWith("---")) {
        elements.push(<hr key={`hr-${i}`} className="border-slate-800 my-2" />);
        i++;
        continue;
      }

      // Standard paragraph
      elements.push(
        <p key={`p-${i}`} className="text-slate-200 text-xs leading-relaxed my-0.5">
          {formatInline(trimmed)}
        </p>
      );
      i++;
    }

    return elements;
  };

  const widthClasses =
    drawerWidth === "full"
      ? "w-full md:w-[960px]"
      : drawerWidth === "wide"
      ? "w-full sm:w-[680px]"
      : "w-full sm:w-[480px]";

  return (
    <div
      className={cn(
        "fixed inset-y-0 right-0 z-50 bg-slate-900 border-l border-slate-700/80 shadow-2xl flex flex-col transition-all duration-300 backdrop-blur-md",
        widthClasses
      )}
    >
      {/* Drawer Header */}
      <div className="p-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-950/80">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/20">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-extrabold text-sm text-slate-100">Repository Copilot AI</h3>
              <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-1.5 py-0.2 rounded font-mono font-bold flex items-center gap-1">
                <Cpu className="w-2.5 h-2.5 text-emerald-400" />
                <span>
                  {selectedProvider === "gemini"
                    ? "Gemini 1.5 Pro"
                    : selectedProvider === "openai"
                    ? "GPT-4o"
                    : "Neural AST Transformer"}
                </span>
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Live Token Streaming • Typo Auto-Correction • Step-by-Step Issue Solver
            </p>
          </div>
        </div>

        {/* Header Controls */}
        <div className="flex items-center gap-1">
          {/* Model / Settings Button */}
          <button
            onClick={() => setIsSettingsOpen(!isSettingsOpen)}
            title="Configure AI Model / API Keys"
            className={cn(
              "p-1.5 rounded-lg transition-colors text-slate-400 hover:text-white hover:bg-slate-800",
              isSettingsOpen && "bg-blue-600/20 text-blue-400 border border-blue-500/30"
            )}
          >
            <Settings className="w-4 h-4" />
          </button>

          {/* Drawer Width Toggle */}
          <button
            onClick={() =>
              setDrawerWidth((prev) =>
                prev === "compact" ? "wide" : prev === "wide" ? "full" : "compact"
              )
            }
            title={
              drawerWidth === "compact"
                ? "Expand to Wide Mode"
                : drawerWidth === "wide"
                ? "Expand to Full-Screen IDE"
                : "Collapse to Compact"
            }
            className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            {drawerWidth === "full" ? (
              <Minimize2 className="w-4 h-4" />
            ) : (
              <Maximize2 className="w-4 h-4" />
            )}
          </button>

          {/* Export Chat Transcript */}
          <button
            onClick={handleExportChat}
            title="Download Chat Transcript as Markdown"
            className="text-slate-400 hover:text-emerald-400 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <Download className="w-4 h-4" />
          </button>

          {/* Clear Chat */}
          <button
            onClick={handleClearChat}
            title="Clear Chat History"
            className="text-slate-400 hover:text-rose-400 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>

          {/* Close */}
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Model Settings Panel (Collapsible) */}
      {isSettingsOpen && (
        <div className="p-3 bg-slate-950 border-b border-slate-800/80 space-y-2.5 animate-in slide-in-from-top-2 duration-200 text-xs">
          <div className="flex items-center justify-between text-slate-300 font-bold text-[11px] uppercase tracking-wider">
            <span className="flex items-center gap-1.5">
              <Key className="w-3.5 h-3.5 text-blue-400" />
              <span>AI Foundation Model Selector</span>
            </span>
            <button
              onClick={() => setIsSettingsOpen(false)}
              className="text-slate-500 hover:text-slate-300"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-3 gap-2 font-medium">
            <button
              onClick={() => setSelectedProvider("offline")}
              className={cn(
                "p-2 rounded-xl border text-center transition-all",
                selectedProvider === "offline"
                  ? "bg-blue-600/20 border-blue-500 text-blue-300 font-bold"
                  : "bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-850"
              )}
            >
              <div className="text-[11px]">⚡ Transformer</div>
              <div className="text-[9px] opacity-70">Built-in (Zero-Latency)</div>
            </button>

            <button
              onClick={() => setSelectedProvider("gemini")}
              className={cn(
                "p-2 rounded-xl border text-center transition-all",
                selectedProvider === "gemini"
                  ? "bg-purple-600/20 border-purple-500 text-purple-300 font-bold"
                  : "bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-850"
              )}
            >
              <div className="text-[11px]">🧠 Gemini 1.5</div>
              <div className="text-[9px] opacity-70">Google DeepMind</div>
            </button>

            <button
              onClick={() => setSelectedProvider("openai")}
              className={cn(
                "p-2 rounded-xl border text-center transition-all",
                selectedProvider === "openai"
                  ? "bg-emerald-600/20 border-emerald-500 text-emerald-300 font-bold"
                  : "bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-850"
              )}
            >
              <div className="text-[11px]">✨ GPT-4o</div>
              <div className="text-[9px] opacity-70">OpenAI</div>
            </button>
          </div>

          {selectedProvider !== "offline" && (
            <div className="space-y-1">
              <label className="text-[10px] font-mono text-slate-400">
                Optional API Key (or leave blank to use backend env):
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={selectedProvider === "gemini" ? "AIzaSy..." : "sk-..."}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 font-mono"
              />
            </div>
          )}
        </div>
      )}

      {/* Suggested Quick Prompts & Slash Commands */}
      <div className="p-2.5 bg-slate-950/60 border-b border-slate-800/80 flex items-center gap-2 overflow-x-auto text-[11px]">
        <button
          onClick={() => handleSendMessage("list of issues in this repo")}
          className="bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 px-2.5 py-1 rounded-lg border border-blue-500/30 whitespace-nowrap transition-colors flex items-center gap-1.5 font-bold shadow-sm"
        >
          <Sparkles className="w-3.5 h-3.5 text-blue-400" />
          <span>📋 List of Issues</span>
        </button>
        <button
          onClick={() => handleSendMessage("Fix issue 1")}
          className="bg-indigo-950/40 hover:bg-indigo-900/50 text-indigo-300 px-2.5 py-1 rounded-lg border border-indigo-500/30 whitespace-nowrap transition-colors flex items-center gap-1 font-semibold"
        >
          <span>🛠️ Fix Issue 1</span>
        </button>
        <button
          onClick={() =>
            handleSendMessage(
              "Automatically resolve all issues and defects in the repository without human intervention."
            )
          }
          className="bg-gradient-to-r from-emerald-600/30 to-teal-600/30 hover:from-emerald-600/40 hover:to-teal-600/40 text-emerald-300 px-3 py-1 rounded-lg border border-emerald-500/40 whitespace-nowrap transition-colors flex items-center gap-1.5 font-bold shadow-md shadow-emerald-500/10"
        >
          <Zap className="w-3.5 h-3.5 text-emerald-400 fill-emerald-400" />
          <span>✨ /autosolve (Auto-Remediate All)</span>
        </button>
        <button
          onClick={() => handleSendMessage("Write comprehensive pytest suite for the core modules.")}
          className="bg-slate-800/80 hover:bg-slate-800 text-slate-300 px-2.5 py-1 rounded-lg border border-slate-700 whitespace-nowrap transition-colors flex items-center gap-1"
        >
          <BookOpen className="w-3 h-3 text-cyan-400" />
          <span>/test (Pytest Suite)</span>
        </button>
        <button
          onClick={() => handleSendMessage("What secrets or security vulnerabilities were detected?")}
          className="bg-slate-800/80 hover:bg-slate-800 text-slate-300 px-2.5 py-1 rounded-lg border border-slate-700 whitespace-nowrap transition-colors flex items-center gap-1"
        >
          <ShieldCheck className="w-3 h-3 text-emerald-400" />
          <span>/security (Audit)</span>
        </button>
        <button
          onClick={() => handleSendMessage("Evaluate repository compliance against SOC 2, HIPAA, and OWASP Top 10.")}
          className="bg-purple-950/40 hover:bg-purple-900/50 text-purple-300 px-2.5 py-1 rounded-lg border border-purple-500/30 whitespace-nowrap transition-colors flex items-center gap-1 font-semibold"
        >
          <ShieldCheck className="w-3 h-3 text-purple-400" />
          <span>/compliance (SOC 2 & OWASP)</span>
        </button>
        <button
          onClick={() => handleSendMessage("Compare this repository metrics against industry benchmarks like FastAPI and Kubernetes.")}
          className="bg-amber-950/40 hover:bg-amber-900/50 text-amber-300 px-2.5 py-1 rounded-lg border border-amber-500/30 whitespace-nowrap transition-colors flex items-center gap-1 font-semibold"
        >
          <Cpu className="w-3 h-3 text-amber-400" />
          <span>/benchmark (SOTA Radar)</span>
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4 text-xs">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.role === "assistant" && (
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white flex items-center justify-center shrink-0 mt-0.5 shadow-md">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div
              className={cn(
                "space-y-2",
                drawerWidth === "full" ? "max-w-[90%]" : "max-w-[85%]"
              )}
            >
              {/* Tool Execution Steps Log */}
              {msg.toolSteps && msg.toolSteps.length > 0 && (
                <div className="bg-slate-950 border border-slate-800 rounded-xl p-2.5 space-y-1.5 font-mono text-[11px] shadow-sm">
                  <div className="text-[10px] text-slate-400 font-sans font-bold uppercase tracking-wider flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Terminal className="w-3.5 h-3.5 text-blue-400" />
                      <span>Autonomous Tool Pipeline ({msg.toolSteps.length})</span>
                    </span>
                    {msg.modelUsed && (
                      <span className="text-[9px] text-slate-500 font-normal">{msg.modelUsed}</span>
                    )}
                  </div>

                  {msg.toolSteps.map((step, sIdx) => {
                    const expandKey = `${idx}-${sIdx}`;
                    const isExpanded = expandedTools[expandKey];

                    return (
                      <div key={sIdx} className="border-t border-slate-900 pt-1.5">
                        <button
                          onClick={() => toggleToolExpand(expandKey)}
                          className="w-full flex items-center justify-between text-left text-slate-400 hover:text-slate-200 py-0.5"
                        >
                          <span className="text-blue-400 font-semibold flex items-center gap-1">
                            <Zap className="w-3 h-3 text-amber-400" />
                            {step.tool_name}({JSON.stringify(step.tool_input).slice(0, 30)}...)
                          </span>
                          {isExpanded ? (
                            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                          ) : (
                            <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                          )}
                        </button>

                        {isExpanded && (
                          <pre className="mt-1 p-2.5 bg-slate-900/90 rounded-lg text-slate-300 text-[10px] overflow-x-auto whitespace-pre-wrap max-h-48 border border-slate-800">
                            {step.tool_output}
                          </pre>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Message Bubble */}
              <div
                className={cn(
                  "p-4 rounded-2xl leading-relaxed text-xs shadow-md group relative",
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-br-none font-medium"
                    : "bg-slate-950/80 border border-slate-800 text-slate-200 rounded-bl-none"
                )}
              >
                {msg.role === "user" ? (
                  msg.content
                ) : (
                  <div>
                    {renderMessageContent(msg.content, idx, msg.isStreaming)}
                    
                    {/* RLHF Feedback Buttons & Actions */}
                    {!msg.isStreaming && msg.content && (
                      <div className="mt-3 pt-2 border-t border-slate-850 flex items-center justify-between text-slate-400 text-[10px]">
                        <span className="text-slate-500 font-mono">
                          {msg.modelUsed || "Neural Transformer"}
                        </span>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleFeedback(idx, "up")}
                            title="Helpful Response"
                            className={cn(
                              "p-1 rounded hover:bg-slate-800 transition-colors",
                              msg.feedback === "up" && "text-emerald-400 bg-emerald-500/10"
                            )}
                          >
                            <ThumbsUp className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleFeedback(idx, "down")}
                            title="Unhelpful Response"
                            className={cn(
                              "p-1 rounded hover:bg-slate-800 transition-colors",
                              msg.feedback === "down" && "text-rose-400 bg-rose-500/10"
                            )}
                          >
                            <ThumbsDown className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleCopyCode(msg.content, `msg-${idx}`)}
                            title="Copy Full Message"
                            className="p-1 rounded hover:bg-slate-800 transition-colors"
                          >
                            {copiedIndex === `msg-${idx}` ? (
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {msg.role === "user" && (
              <div className="w-8 h-8 rounded-xl bg-slate-800 text-slate-300 flex items-center justify-center shrink-0 mt-0.5 border border-slate-700">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {isLoading && messages[messages.length - 1]?.role !== "assistant" && (
          <div className="flex gap-3 justify-start items-center text-slate-400 text-xs">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white flex items-center justify-center shrink-0 shadow-md">
              <Bot className="w-4 h-4" />
            </div>
            <div className="flex items-center gap-2 bg-slate-950/90 border border-slate-800 px-4 py-2.5 rounded-2xl shadow-md">
              <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
              <span className="font-mono text-[11px] text-slate-300">
                Thinking & executing repository tools...
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage();
        }}
        className="p-3 bg-slate-950 border-t border-slate-800 flex gap-2"
      >
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Ask Copilot: 'List of issues', 'Fix issue 1', 'Solve all automatically'..."
          className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors shadow-inner"
        />
        <button
          type="submit"
          disabled={!inputMessage.trim() || isLoading}
          className="px-4 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 text-white rounded-xl font-bold transition-all flex items-center justify-center gap-1.5 shadow-md shadow-blue-500/20"
        >
          <Send className="w-4 h-4" />
          <span className="text-xs">Ask</span>
        </button>
      </form>
    </div>
  );
}
