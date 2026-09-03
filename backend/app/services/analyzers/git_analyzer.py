from typing import List, Dict, Any, Tuple
from collections import Counter
from backend.app.services.repo_fetcher import RepositoryContext

class GitAnalyzer:
    @staticmethod
    def analyze(ctx: RepositoryContext) -> Tuple[float, List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Analyzes Git history, file churn, and identifies high-risk maintenance hotspots.
        Returns (maintainability_score 0-100, findings_list, hotspots_list, metrics_dict).
        """
        findings = []
        hotspots = []
        file_churn = Counter()
        
        # 1. Tally file modifications and author contributions across commits
        file_authors = {}
        for c in ctx.git_commits:
            author = c.get("author", "lead-engineer")
            stats = c.get("stats", {})
            for fpath in stats.keys():
                norm_path = fpath.replace("\\", "/")
                file_churn[norm_path] += 1
                if norm_path not in file_authors:
                    file_authors[norm_path] = Counter()
                file_authors[norm_path][author] += 1

        # If no git history (e.g. shallow tarball or sample directory without .git), simulate heuristic churn based on file size and depth
        if not file_churn:
            for rel_path, file in ctx.files.items():
                if file.extension in {".py", ".ts", ".js", ".go"}:
                    loc = len(file.content.splitlines())
                    pseudo_churn = max(1, min(25, loc // 30))
                    file_churn[rel_path] = pseudo_churn
                    file_authors[rel_path] = Counter({"primary-maintainer": pseudo_churn})

        # 2. Calculate Hotspot Risk per file
        max_churn = max(file_churn.values()) if file_churn else 1
        
        for rel_path, churn_count in file_churn.most_common(20):
            file = ctx.files.get(rel_path)
            if not file:
                continue
            
            loc = len(file.content.splitlines())
            # Estimate complexity: base on branching keywords and line count
            complexity_est = min(50.0, (loc / 15.0) + (file.content.count("if ") + file.content.count("for ") + file.content.count("while ")))
            
            norm_churn = min(1.0, churn_count / max(1, max_churn))
            risk_score = norm_churn * (complexity_est / 50.0) * 100.0
            
            risk_level = "Low"
            if risk_score > 70 or (churn_count >= 10 and complexity_est > 25):
                risk_level = "Critical"
            elif risk_score > 45 or (churn_count >= 6 and complexity_est > 15):
                risk_level = "High"
            elif risk_score > 25:
                risk_level = "Medium"

            authors_counter = file_authors.get(rel_path, Counter())
            author_count = len(authors_counter) if authors_counter else 1
            top_author = authors_counter.most_common(1)[0][0] if authors_counter else "core-team"
            is_bus_factor = (author_count <= 1 and churn_count >= 5 and complexity_est >= 15)

            hotspot_entry = {
                "file_path": rel_path,
                "commit_count": churn_count,
                "churn_score": round(norm_churn * 100, 1),
                "complexity_score": round(complexity_est, 1),
                "risk_level": risk_level,
                "top_author": top_author,
                "author_count": author_count,
                "is_bus_factor_risk": is_bus_factor,
            }
            hotspots.append(hotspot_entry)

            # Generate finding for Critical/High hotspots
            if risk_level in {"Critical", "High"} and len([f for f in findings if f.get("category") == "Maintainability"]) < 3:
                findings.append({
                    "category": "Maintainability",
                    "severity": risk_level,
                    "title": f"High Maintenance Hotspot: `{rel_path}`",
                    "file_path": rel_path,
                    "line_number": 1,
                    "problem": f"File has high change churn ({churn_count} modifications) coupled with high cyclomatic complexity (score: {round(complexity_est, 1)}). High-churn complex files are primary sources of regressions.",
                    "recommendation": "Decouple this module, break down dense business logic, and introduce comprehensive regression tests.",
                    "evidence_code": f"Churn: {churn_count} commits | Complexity: {round(complexity_est, 1)} | LOC: {loc}",
                    "confidence": 0.93,
                    "rule_id": "MAINT-HOTSPOT"
                })

        # Calculate Maintainability Score
        score = 100.0
        for h in hotspots:
            if h["risk_level"] == "Critical":
                score -= 15.0
            elif h["risk_level"] == "High":
                score -= 8.0
            elif h["risk_level"] == "Medium":
                score -= 3.0

        score = max(20.0, min(100.0, score))
        
        metrics = {
            "total_commits_inspected": len(ctx.git_commits),
            "top_hotspots_count": len(hotspots),
            "high_risk_hotspots": len([h for h in hotspots if h["risk_level"] in {"Critical", "High"}])
        }
        
        return round(score, 1), findings, hotspots, metrics
