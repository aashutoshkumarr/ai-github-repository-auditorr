import re
import ast
from typing import List, Dict, Any, Tuple
from backend.app.services.repo_fetcher import RepositoryContext

README_SECTIONS = [
    ("installation", r"(?i)(installation|getting started|setup|prerequisites|install)"),
    ("usage", r"(?i)(usage|quickstart|examples|how to use|running)"),
    ("architecture", r"(?i)(architecture|system design|overview|how it works|components)"),
    ("environment", r"(?i)(environment|configuration|\.env|config|settings)"),
    ("license", r"(?i)(license|copyright)"),
    ("contributing", r"(?i)(contributing|guidelines|development)")
]

class DocsAnalyzer:
    @staticmethod
    def analyze(ctx: RepositoryContext) -> Tuple[float, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Evaluates repository documentation, README completeness, and docstring coverage.
        Returns (docs_score 0-100, findings_list, metrics_dict).
        """
        findings = []
        readme_file = None
        
        # Find README
        for rel_path, file in ctx.files.items():
            if rel_path.lower() in {"readme.md", "readme.rst", "readme.txt", "readme"}:
                readme_file = file
                break

        # Compute docstring coverage on code files
        total_functions = 0
        documented_functions = 0
        for rel_path, file in ctx.files.items():
            if file.extension == ".py":
                try:
                    tree = ast.parse(file.content)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                            total_functions += 1
                            if ast.get_docstring(node):
                                documented_functions += 1
                except Exception:
                    pass

        docstring_coverage = (documented_functions / max(1, total_functions)) if total_functions > 0 else 1.0

        score = 0.0
        missing_sections = []

        if not readme_file:
            score = 15.0
            findings.append({
                "category": "Documentation",
                "severity": "Critical",
                "title": "Missing README file",
                "file_path": "README.md",
                "line_number": 1,
                "problem": "Repository lacks a README.md explaining the project purpose, setup, and usage.",
                "recommendation": "Add a comprehensive README.md with quickstart, architecture, and configuration guides.",
                "evidence_code": "",
                "confidence": 1.0,
                "rule_id": "DOCS-NO-README"
            })
        else:
            score += 40.0  # Base README presence
            content = readme_file.content
            
            # Check sections
            for sec_name, pattern in README_SECTIONS:
                if not re.search(pattern, content):
                    missing_sections.append(sec_name)
                    findings.append({
                        "category": "Documentation",
                        "severity": "Low",
                        "title": f"README missing '{sec_name.capitalize()}' section",
                        "file_path": readme_file.relative_path,
                        "line_number": 1,
                        "problem": f"README does not contain an explicit section for {sec_name.capitalize()}.",
                        "recommendation": f"Add a '{sec_name.capitalize()}' section in README.md to help developers onboard quickly.",
                        "evidence_code": "",
                        "confidence": 0.85,
                        "rule_id": f"DOCS-MISSING-{sec_name.upper()}"
                    })
                else:
                    score += 7.0  # Up to 42 points for sections

            # Add points for docstring coverage (up to 18 points)
            score += round(docstring_coverage * 18.0, 1)

            if docstring_coverage < 0.20 and total_functions > 5:
                findings.append({
                    "category": "Documentation",
                    "severity": "Medium",
                    "title": f"Low public API docstring coverage ({round(docstring_coverage * 100, 1)}%)",
                    "file_path": "src",
                    "line_number": 1,
                    "problem": f"Only {documented_functions} out of {total_functions} functions/classes have docstrings.",
                    "recommendation": "Add docstrings to all exported functions and classes explaining arguments, return types, and exceptions.",
                    "evidence_code": f"Documented: {documented_functions}/{total_functions}",
                    "confidence": 0.90,
                    "rule_id": "DOCS-LOW-DOCSTRINGS"
                })

        score = max(10.0, min(100.0, score))
        
        metrics = {
            "has_readme": readme_file is not None,
            "readme_length": len(readme_file.content) if readme_file else 0,
            "missing_sections": missing_sections,
            "docstring_coverage_pct": round(docstring_coverage * 100, 1),
            "total_functions_checked": total_functions
        }
        
        return round(score, 1), findings, metrics
