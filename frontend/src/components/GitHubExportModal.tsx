"use client";

import { useState, useEffect } from "react";
import { Finding } from "@/types";
import { getIssuePreview, getPRPreview, createGitHubIssue } from "@/lib/api";
import { X, Copy, Check, Github, ExternalLink, GitPullRequest, AlertCircle, RefreshCw } from "lucide-react";

interface GitHubExportModalProps {
  finding: Finding | null;
  onClose: () => void;
}

export default function GitHubExportModal({ finding, onClose }: GitHubExportModalProps) {
  const [activeTab, setActiveTab] = useState<"issue" | "pr">("issue");
  const [issueData, setIssueData] = useState<{ title: string; body_markdown: string; labels: string[] } | null>(null);
  const [prData, setPRData] = useState<{ title: string; branch_name: string; diff_patch: string; body_markdown: string } | null>(null);
  
  const [token, setToken] = useState("");
  const [copied, setCopied] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createdUrl, setCreatedUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!finding) return;

    // Load previews
    getIssuePreview(finding.id).then(setIssueData).catch(console.error);
    getPRPreview(finding.id).then(setPRData).catch(console.error);
  }, [finding]);

  if (!finding) return null;

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCreateOnGitHub = async () => {
    if (!token.trim()) {
      setErrorMessage("Please enter your GitHub Personal Access Token (PAT).");
      return;
    }
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const res = await createGitHubIssue({
        finding_id: finding.id,
        github_token: token.trim(),
      });
      setCreatedUrl(res.issue_url);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to post issue to GitHub.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl p-6 relative flex flex-col">
        {/* Close */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 mb-4">
          <div className="p-2 rounded-xl bg-slate-800 text-white border border-slate-700">
            <Github className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100">GitHub Automation & Export</h2>
            <p className="text-xs text-slate-400">Generate structured issues or proposed PR patches</p>
          </div>
        </div>

        {/* Tab switcher */}
        <div className="flex items-center gap-2 border-b border-slate-800 mb-4 pb-2">
          <button
            onClick={() => setActiveTab("issue")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-colors ${
              activeTab === "issue" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <AlertCircle className="w-3.5 h-3.5" />
            <span>GitHub Issue</span>
          </button>
          <button
            onClick={() => setActiveTab("pr")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-colors ${
              activeTab === "pr" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <GitPullRequest className="w-3.5 h-3.5" />
            <span>Fix PR Patch</span>
          </button>
        </div>

        {/* Issue View */}
        {activeTab === "issue" && (
          <div className="space-y-4 flex-1">
            {issueData ? (
              <>
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold uppercase text-slate-400">Issue Title</label>
                  <div className="bg-slate-950 border border-slate-800 p-2.5 rounded-lg text-xs font-mono text-slate-200">
                    {issueData.title}
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <label className="text-[11px] font-semibold uppercase text-slate-400">Markdown Body</label>
                    <button
                      onClick={() => handleCopy(issueData.body_markdown)}
                      className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                    >
                      {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copied ? "Copied Markdown" : "Copy Markdown"}</span>
                    </button>
                  </div>
                  <pre className="bg-slate-950 border border-slate-800 p-3 rounded-lg text-[11px] text-slate-300 font-mono overflow-x-auto whitespace-pre-wrap max-h-52">
                    {issueData.body_markdown}
                  </pre>
                </div>

                {/* Direct Post Section */}
                <div className="bg-slate-950/60 border border-slate-800/80 p-4 rounded-xl space-y-3">
                  <h4 className="text-xs font-semibold text-slate-200">Publish Directly via GitHub API</h4>
                  
                  {createdUrl ? (
                    <div className="bg-emerald-950/40 border border-emerald-800/60 p-3 rounded-lg flex items-center justify-between">
                      <span className="text-xs text-emerald-300 font-medium">Issue created successfully!</span>
                      <a
                        href={createdUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-emerald-400 hover:underline flex items-center gap-1"
                      >
                        <span>View on GitHub</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <input
                        type="password"
                        value={token}
                        onChange={(e) => setToken(e.target.value)}
                        placeholder="Enter GitHub Personal Access Token (ghp_...)"
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                      />
                      {errorMessage && (
                        <p className="text-xs text-rose-400">{errorMessage}</p>
                      )}
                      <button
                        onClick={handleCreateOnGitHub}
                        disabled={isSubmitting}
                        className="w-full py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition-colors flex items-center justify-center gap-2"
                      >
                        {isSubmitting ? (
                          <>
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                            <span>Posting Issue to GitHub...</span>
                          </>
                        ) : (
                          <>
                            <Github className="w-3.5 h-3.5" />
                            <span>Create Issue on GitHub</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-xs text-slate-500">Generating issue preview...</div>
            )}
          </div>
        )}

        {/* PR Diff View */}
        {activeTab === "pr" && (
          <div className="space-y-4 flex-1">
            {prData ? (
              <>
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold uppercase text-slate-400">Branch Name</label>
                  <div className="bg-slate-950 border border-slate-800 p-2.5 rounded-lg text-xs font-mono text-emerald-400">
                    git checkout -b {prData.branch_name}
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <label className="text-[11px] font-semibold uppercase text-slate-400">Proposed Unified Git Diff</label>
                    <button
                      onClick={() => handleCopy(prData.diff_patch)}
                      className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                    >
                      {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copied ? "Copied Patch" : "Copy Diff"}</span>
                    </button>
                  </div>
                  <pre className="bg-slate-950 border border-slate-800 p-3 rounded-lg text-[11px] text-slate-300 font-mono overflow-x-auto whitespace-pre-wrap max-h-60">
                    {prData.diff_patch}
                  </pre>
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-xs text-slate-500">Generating fix PR patch...</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
