import re
from typing import List, Dict, Any, Tuple
from backend.app.services.repo_fetcher import RepositoryContext

TEST_DIR_PATTERNS = ["tests", "test", "__tests__", "spec", "specs", "e2e"]
TEST_FILE_PATTERNS = [
    r"^test_.*\.py$", r".*_test\.py$", r".*\.test\.(js|ts|jsx|tsx)$",
    r".*\.spec\.(js|ts|jsx|tsx)$", r".*_test\.go$", r".*Test\.java$"
]

class TestingAnalyzer:
    @staticmethod
    def analyze(ctx: RepositoryContext) -> Tuple[float, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Analyzes test presence, test-to-code ratio, test frameworks, and CI workflow validation.
        Returns (testing_score 0-100, findings_list, metrics_dict).
        """
        findings = []
        test_files = []
        src_files = []
        test_loc = 0
        src_loc = 0
        
        detected_frameworks = set()
        has_ci_test_workflow = False

        for rel_path, file in ctx.files.items():
            is_test = False
            
            # Check directory
            parts = rel_path.lower().split("/")
            if any(p in TEST_DIR_PATTERNS for p in parts[:-1]):
                is_test = True
                
            # Check filename
            filename = parts[-1]
            if any(re.match(pattern, filename, re.IGNORECASE) for pattern in TEST_FILE_PATTERNS):
                is_test = True

            # Check CI workflows
            if ".github/workflows" in rel_path.lower():
                content_lower = file.content.lower()
                if any(k in content_lower for k in ["pytest", "npm test", "npm run test", "yarn test", "cargo test", "go test", "mvn test"]):
                    has_ci_test_workflow = True

            loc = len(file.content.splitlines())
            if is_test:
                test_files.append(rel_path)
                test_loc += loc
                # Detect framework inside test file
                content = file.content
                if "pytest" in content or "def test_" in content:
                    detected_frameworks.add("pytest")
                if "unittest" in content or "TestCase" in content:
                    detected_frameworks.add("unittest")
                if "describe(" in content or "it(" in content or "test(" in content:
                    if "jest" in content or "@jest" in content:
                        detected_frameworks.add("Jest")
                    elif "vitest" in content:
                        detected_frameworks.add("Vitest")
                    else:
                        detected_frameworks.add("Jest/Mocha")
            else:
                if file.extension in {".py", ".ts", ".js", ".tsx", ".jsx", ".go", ".java", ".rs", ".cs"}:
                    src_files.append(rel_path)
                    src_loc += loc

        # Compute Test-to-Code Ratio
        test_to_code_ratio = (test_loc / max(1, src_loc)) if src_loc > 0 else 0.0
        
        # Scoring Logic
        score = 0.0
        
        if len(test_files) == 0:
            score = 15.0
            findings.append({
                "category": "Testing",
                "severity": "Critical",
                "title": "No automated test suite detected",
                "file_path": "repository_root",
                "line_number": 1,
                "problem": "Repository contains no identifiable test directory or test files (e.g., tests/, test_*.py, *.test.ts).",
                "recommendation": "Add a dedicated `tests/` directory and configure an automated testing framework (e.g. pytest or Vitest).",
                "evidence_code": "",
                "confidence": 0.99,
                "rule_id": "TEST-NO-TESTS"
            })
        else:
            # Base points for having tests
            score += 40.0
            
            # Ratio points (up to 30 points)
            if test_to_code_ratio >= 0.50:
                score += 30.0
            elif test_to_code_ratio >= 0.25:
                score += 20.0
            elif test_to_code_ratio >= 0.10:
                score += 10.0
            else:
                score += 5.0
                findings.append({
                    "category": "Testing",
                    "severity": "High",
                    "title": f"Low test-to-code volume ratio ({round(test_to_code_ratio * 100, 1)}%)",
                    "file_path": "tests",
                    "line_number": 1,
                    "problem": f"Test code LOC ({test_loc}) is only {round(test_to_code_ratio * 100, 1)}% of source code LOC ({src_loc}). Recommended target is > 30%.",
                    "recommendation": "Increase test coverage by writing unit and integration test suites for core business logic.",
                    "evidence_code": f"Test LOC: {test_loc} | Source LOC: {src_loc}",
                    "confidence": 0.92,
                    "rule_id": "TEST-LOW-RATIO"
                })

            # CI Test Workflow Points (up to 30 points)
            if has_ci_test_workflow:
                score += 30.0
            else:
                findings.append({
                    "category": "Testing",
                    "severity": "Medium",
                    "title": "No CI automated test workflow found in `.github/workflows`",
                    "file_path": ".github/workflows",
                    "line_number": 1,
                    "problem": "Repository does not have a GitHub Actions workflow configured to run test suites on PRs / pushes.",
                    "recommendation": "Create a `.github/workflows/test.yml` workflow to automatically execute tests on every pull request.",
                    "evidence_code": "",
                    "confidence": 0.95,
                    "rule_id": "TEST-NO-CI"
                })

        score = max(10.0, min(100.0, score))
        
        metrics = {
            "test_files_count": len(test_files),
            "test_loc": test_loc,
            "source_loc": src_loc,
            "test_to_code_ratio_pct": round(test_to_code_ratio * 100, 1),
            "detected_frameworks": list(detected_frameworks),
            "has_ci_test_workflow": has_ci_test_workflow
        }
        
        return round(score, 1), findings, metrics
