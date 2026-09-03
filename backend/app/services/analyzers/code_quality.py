import ast
import re
from typing import List, Dict, Any, Tuple
from backend.app.services.repo_fetcher import RepositoryContext, RepoFile

class CodeQualityAnalyzer:
    @staticmethod
    def analyze(ctx: RepositoryContext) -> Tuple[float, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Analyze code quality across repository files using AST and static metrics.
        Returns (quality_score 0-100, findings_list, metrics_dict).
        """
        findings = []
        total_functions = 0
        complex_functions = 0
        long_functions = 0
        deeply_nested_blocks = 0
        empty_excepts = 0
        wildcard_imports = 0
        todo_count = 0
        
        for rel_path, file in ctx.files.items():
            if file.extension == ".py":
                CodeQualityAnalyzer._analyze_python_file(
                    rel_path, file, findings,
                    stats_ref={
                        "total_functions": total_functions,
                        "complex_functions": complex_functions,
                        "long_functions": long_functions,
                        "deeply_nested": deeply_nested_blocks,
                        "empty_excepts": empty_excepts,
                        "wildcard_imports": wildcard_imports
                    }
                )
            elif file.extension in {".js", ".jsx", ".ts", ".tsx", ".go", ".java", ".cpp", ".cs"}:
                CodeQualityAnalyzer._analyze_generic_code_file(rel_path, file, findings)
            
            # Count TODOs/FIXMEs
            for idx, line in enumerate(file.content.splitlines(), start=1):
                if re.search(r"\b(TODO|FIXME|XXX|HACK)\b", line, re.IGNORECASE):
                    todo_count += 1
                    if len(findings) < 25 and todo_count <= 3:
                        findings.append({
                            "category": "Code Quality",
                            "severity": "Low",
                            "title": f"Unresolved technical debt marker ({line.strip()[:30]}...)",
                            "file_path": rel_path,
                            "line_number": idx,
                            "problem": f"Found unresolved task marker in source code: '{line.strip()}'",
                            "recommendation": "Address or file a tracking issue for this technical debt item.",
                            "evidence_code": line.strip(),
                            "confidence": 0.95,
                            "rule_id": "DEBT-TODO"
                        })

        # Calculate score (Base 100 with weighted deductions)
        score = 100.0
        for f in findings:
            if f["severity"] == "Critical":
                score -= 15.0
            elif f["severity"] == "High":
                score -= 8.0
            elif f["severity"] == "Medium":
                score -= 3.0
            elif f["severity"] == "Low":
                score -= 1.0

        score = max(10.0, min(100.0, score))
        
        metrics = {
            "total_files_audited": len(ctx.files),
            "total_loc": ctx.total_lines,
            "todo_markers_count": todo_count,
            "quality_findings_count": len(findings)
        }
        
        return round(score, 1), findings, metrics

    @staticmethod
    def _analyze_python_file(rel_path: str, file: RepoFile, findings: List[Dict[str, Any]], stats_ref: Dict[str, int]):
        try:
            tree = ast.parse(file.content, filename=rel_path)
        except Exception:
            return  # Skip files with syntax errors

        lines = file.content.splitlines()

        for node in ast.walk(tree):
            # 1. Function Length & Complexity
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                stats_ref["total_functions"] += 1
                func_length = (node.end_lineno - node.lineno + 1) if hasattr(node, "end_lineno") and node.end_lineno else len(node.body)
                
                # Check long function (> 50 LOC)
                if func_length > 50:
                    stats_ref["long_functions"] += 1
                    evidence = "\n".join(lines[node.lineno-1:min(node.lineno+5, len(lines))])
                    findings.append({
                        "category": "Code Quality",
                        "severity": "Medium",
                        "title": f"Oversized function '{node.name}' ({func_length} lines)",
                        "file_path": rel_path,
                        "line_number": node.lineno,
                        "problem": f"Function '{node.name}' spans {func_length} lines, violating the Single Responsibility Principle and impairing readability.",
                        "recommendation": f"Refactor '{node.name}' into smaller, focused helper functions or modular subroutines.",
                        "evidence_code": evidence,
                        "confidence": 0.95,
                        "rule_id": "QUAL-LONG-FUNC"
                    })

                # Check cyclomatic complexity heuristic (branching nodes)
                branch_count = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With, ast.Assert, ast.BoolOp)):
                        branch_count += 1
                
                if branch_count > 10:
                    stats_ref["complex_functions"] += 1
                    evidence = lines[node.lineno-1] if node.lineno-1 < len(lines) else ""
                    findings.append({
                        "category": "Code Quality",
                        "severity": "High" if branch_count > 15 else "Medium",
                        "title": f"High Cyclomatic Complexity in '{node.name}' (Score: {branch_count})",
                        "file_path": rel_path,
                        "line_number": node.lineno,
                        "problem": f"Function '{node.name}' has a cyclomatic complexity of {branch_count} (threshold: 10). High branch paths make testing and maintenance error-prone.",
                        "recommendation": "Simplify conditional branches, use lookup tables/polymorphism, or extract complex sub-branches into helper methods.",
                        "evidence_code": evidence,
                        "confidence": 0.92,
                        "rule_id": "QUAL-HIGH-COMPLEXITY"
                    })

                # Check parameter count (> 6 parameters)
                param_count = len(node.args.args)
                if param_count > 6:
                    evidence = lines[node.lineno-1] if node.lineno-1 < len(lines) else ""
                    findings.append({
                        "category": "Code Quality",
                        "severity": "Low",
                        "title": f"Too many parameters in '{node.name}' ({param_count} args)",
                        "file_path": rel_path,
                        "line_number": node.lineno,
                        "problem": f"Function '{node.name}' accepts {param_count} arguments, which indicates high coupling.",
                        "recommendation": "Encapsulate parameters into a dataclass, Pydantic schema, or configuration object.",
                        "evidence_code": evidence,
                        "confidence": 0.94,
                        "rule_id": "QUAL-TOO-MANY-PARAMS"
                    })

            # 2. Empty or Bare Except Clauses
            elif isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    stats_ref["empty_excepts"] += 1
                    lineno = node.lineno
                    evidence = lines[lineno-1] if lineno-1 < len(lines) else "except:"
                    findings.append({
                        "category": "Code Quality",
                        "severity": "High",
                        "title": "Bare 'except:' clause suppresses unexpected exceptions",
                        "file_path": rel_path,
                        "line_number": lineno,
                        "problem": "Catching generic exceptions with bare 'except:' catches KeyboardInterrupt and SystemExit, hiding critical runtime bugs.",
                        "recommendation": "Catch explicit exception types (e.g. `except (ValueError, KeyError) as e:`) and log the stack trace.",
                        "evidence_code": evidence,
                        "confidence": 0.98,
                        "rule_id": "QUAL-BARE-EXCEPT"
                    })

            # 3. Wildcard Imports (from module import *)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        stats_ref["wildcard_imports"] += 1
                        lineno = node.lineno
                        evidence = lines[lineno-1] if lineno-1 < len(lines) else f"from {node.module} import *"
                        findings.append({
                            "category": "Code Quality",
                            "severity": "Low",
                            "title": f"Wildcard import 'from {node.module} import *'",
                            "file_path": rel_path,
                            "line_number": lineno,
                            "problem": "Wildcard imports pollute the namespace and make variable origins ambiguous to static analyzers and developers.",
                            "recommendation": "Explicitly import the specific classes or functions needed.",
                            "evidence_code": evidence,
                            "confidence": 0.99,
                            "rule_id": "QUAL-WILDCARD-IMPORT"
                        })

    @staticmethod
    def _analyze_generic_code_file(rel_path: str, file: RepoFile, findings: List[Dict[str, Any]]):
        lines = file.content.splitlines()
        brace_depth = 0
        
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            
            # Check console.log in production JS/TS
            if file.extension in {".js", ".jsx", ".ts", ".tsx"} and re.search(r"\bconsole\.(log|debug|warn)\(", stripped):
                if not ("test" in rel_path.lower() or "spec" in rel_path.lower()):
                    if len([f for f in findings if f.get("rule_id") == "QUAL-CONSOLE-LOG"]) < 2:
                        findings.append({
                            "category": "Code Quality",
                            "severity": "Low",
                            "title": "Leftover debug `console.log` statement",
                            "file_path": rel_path,
                            "line_number": idx,
                            "problem": "Unstripped console logging statements can leak internal state and clutter client output.",
                            "recommendation": "Remove console statements or replace with a dedicated structured logger.",
                            "evidence_code": stripped,
                            "confidence": 0.90,
                            "rule_id": "QUAL-CONSOLE-LOG"
                        })

            # Check excessive indentation / nesting level (> 5 levels)
            indent_spaces = len(line) - len(line.lstrip(" "))
            if indent_spaces >= 20 and len(stripped) > 0 and not stripped.startswith("//") and not stripped.startswith("#"):
                if len([f for f in findings if f.get("rule_id") == "QUAL-DEEP-NESTING"]) < 3:
                    findings.append({
                        "category": "Code Quality",
                        "severity": "Medium",
                        "title": "Excessively deep nesting level (> 4 levels)",
                        "file_path": rel_path,
                        "line_number": idx,
                        "problem": "Deeply nested code blocks (arrow anti-pattern) significantly increase cognitive load and defect probability.",
                        "recommendation": "Use guard clauses, early returns, or decompose into helper functions.",
                        "evidence_code": line.rstrip(),
                        "confidence": 0.88,
                        "rule_id": "QUAL-DEEP-NESTING"
                    })
