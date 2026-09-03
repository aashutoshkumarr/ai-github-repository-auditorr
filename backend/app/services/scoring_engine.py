from typing import Dict, List, Any

WEIGHTS = {
    "security": 0.20,
    "quality": 0.20,
    "testing": 0.15,
    "docs": 0.15,
    "deps": 0.10,
    "arch": 0.10,
    "maintainability": 0.10
}

class ScoringEngine:
    @staticmethod
    def calculate_overall_score(category_scores: Dict[str, float]) -> float:
        """
        Calculates weighted composite Repository Health Score (0-100).
        """
        overall = sum(category_scores.get(cat, 50.0) * weight for cat, weight in WEIGHTS.items())
        return round(max(5.0, min(100.0, overall)), 1)

    @staticmethod
    def generate_score_ledger(category_scores: Dict[str, float], findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates an itemized, mathematical score deduction breakdown.
        Provides complete score transparency answering: 'Why did I get this score?'
        """
        ledger = {
            "base_score": 100.0,
            "overall_score": ScoringEngine.calculate_overall_score(category_scores),
            "weights": {k: f"{int(v * 100)}%" for k, v in WEIGHTS.items()},
            "categories": {}
        }

        for cat, score in category_scores.items():
            cat_findings = [f for f in findings if f.get("category", "").lower() == cat.lower() or (cat == "quality" and f.get("category") == "Code Quality")]
            deductions = []
            
            for f in cat_findings:
                sev = f.get("severity", "Medium")
                penalty = 0
                if sev == "Critical":
                    penalty = -25.0
                elif sev == "High":
                    penalty = -12.0
                elif sev == "Medium":
                    penalty = -5.0
                elif sev == "Low":
                    penalty = -2.0

                deductions.append({
                    "title": f.get("title", "Finding"),
                    "severity": sev,
                    "file_path": f.get("file_path", ""),
                    "line_number": f.get("line_number", 1),
                    "penalty": penalty,
                    "rule_id": f.get("rule_id", "GENERAL")
                })

            ledger["categories"][cat] = {
                "score": round(score, 1),
                "weight": f"{int(WEIGHTS.get(cat, 0.1) * 100)}%",
                "deductions_count": len(deductions),
                "itemized_deductions": deductions[:8]  # top 8 deductions
            }

        return ledger

    @staticmethod
    def generate_fix_roadmap(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generates a prioritized step-by-step action plan to raise repository health score.
        Priority:
        1. Critical Security (Secrets / Injections / RCE)
        2. High Security
        3. Vulnerable Outdated Dependencies
        4. High-risk Maintainability Hotspots
        5. Severe Code Quality / Bare Excepts / High Complexity
        6. Testing Deficits & Missing CI
        7. Missing Documentation
        """
        severity_order = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4, "Informational": 5}
        
        sorted_findings = sorted(
            findings,
            key=lambda x: (
                severity_order.get(x.get("severity"), 5),
                0 if x.get("category") == "Security" else (1 if x.get("category") == "Dependencies" else 2)
            )
        )

        roadmap = []
        for idx, f in enumerate(sorted_findings[:12], start=1):
            roadmap.append({
                "order": idx,
                "severity": f.get("severity", "Medium"),
                "category": f.get("category", "General"),
                "title": f.get("title", "Fix item"),
                "file_path": f.get("file_path", ""),
                "action_summary": f.get("recommendation", "Review and remediate issue.")
            })

        return roadmap
