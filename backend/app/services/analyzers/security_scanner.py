import re
import ast
import math
from typing import List, Dict, Any, Tuple
from backend.app.services.repo_fetcher import RepositoryContext, RepoFile

# High-entropy / Secret Patterns
SECRET_REGEXES = [
    {
        "id": "SEC-AWS-KEY",
        "title": "Hardcoded AWS Access Key ID",
        "pattern": r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
        "severity": "Critical",
        "cwe": "CWE-798",
        "confidence": 0.98,
        "recommendation": "Revoke this AWS key immediately, store credentials in AWS IAM Roles or environment variables (AWS_ACCESS_KEY_ID), and add secrets to .gitignore."
    },
    {
        "id": "SEC-GITHUB-TOKEN",
        "title": "Hardcoded GitHub Personal Access Token",
        "pattern": r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,255}|github_pat_[0-9a-zA-Z_]{82}",
        "severity": "Critical",
        "cwe": "CWE-798",
        "confidence": 0.99,
        "recommendation": "Revoke this token from GitHub Settings > Developer Settings and use environment variables (GITHUB_TOKEN) or GitHub Secrets."
    },
    {
        "id": "SEC-OPENAI-KEY",
        "title": "Hardcoded OpenAI / API Service Key",
        "pattern": r"sk-(?:proj-)?[a-zA-Z0-9\-_]{32,70}",
        "severity": "Critical",
        "cwe": "CWE-798",
        "confidence": 0.96,
        "recommendation": "Rotate this API key immediately in the OpenAI console and inject via environment variables (OPENAI_API_KEY)."
    },
    {
        "id": "SEC-PRIVATE-KEY",
        "title": "Unencrypted Private Key in Repository",
        "pattern": r"-----BEGIN (?:RSA|OPENSSH|DSA|EC|PGP)?\s?PRIVATE KEY-----",
        "severity": "Critical",
        "cwe": "CWE-312",
        "confidence": 1.0,
        "recommendation": "Remove private key from source control immediately. Use a secret manager (HashiCorp Vault, AWS Secrets Manager) and purge Git history."
    },
    {
        "id": "SEC-GENERIC-PASSWORD",
        "title": "Hardcoded Credential / Secret in Source Code",
        "pattern": r"""(?i)(?:password|passwd|secret_key|api_secret|auth_token|db_pass)\s*[:=]\s*["'](?!(?:true|false|none|null|dummy|test|example|changeme|123456|password|default))([^"']{8,})["']""",
        "severity": "High",
        "cwe": "CWE-798",
        "confidence": 0.90,
        "recommendation": "Move hardcoded secrets to an external `.env` file and read via configuration management (e.g., `os.getenv` or `pydantic-settings`)."
    }
]

def shannon_entropy(data: str) -> float:
    """Calculate Shannon entropy to detect high-randomness secret strings."""
    if not data:
        return 0.0
    entropy = 0.0
    for x in set(data):
        p_x = float(data.count(x)) / len(data)
        if p_x > 0:
            entropy += - p_x * math.log(p_x, 2)
    return entropy

class SecurityScanner:
    @staticmethod
    def analyze(ctx: RepositoryContext) -> Tuple[float, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Execute static security scanning (secret detection, AST vulnerability inspection, CWE mapping).
        Returns (security_score 0-100, findings_list, metrics_dict).
        """
        findings = []
        secrets_detected = 0
        vulnerabilities_detected = 0

        for rel_path, file in ctx.files.items():
            # Skip documentation or binary/mock files for deep secret penalty if explicitly mock
            is_test_file = "test" in rel_path.lower() or "mock" in rel_path.lower()
            
            # 1. Regex & Entropy Secret Scanning
            SecurityScanner._scan_secrets(rel_path, file, findings, is_test_file)
            
            # 2. AST & Code Pattern Vulnerability Analysis
            if file.extension == ".py":
                SecurityScanner._scan_python_ast_security(rel_path, file, findings)
            elif file.extension in {".js", ".jsx", ".ts", ".tsx"}:
                SecurityScanner._scan_js_security(rel_path, file, findings)

        # Count types
        for f in findings:
            if "SEC-" in f.get("rule_id", ""):
                secrets_detected += 1
            else:
                vulnerabilities_detected += 1

        # Calculate Score
        score = 100.0
        for f in findings:
            if f["severity"] == "Critical":
                score -= 25.0
            elif f["severity"] == "High":
                score -= 12.0
            elif f["severity"] == "Medium":
                score -= 5.0
            elif f["severity"] == "Low":
                score -= 2.0

        score = max(5.0, min(100.0, score))
        
        metrics = {
            "secrets_detected": secrets_detected,
            "vulnerabilities_detected": vulnerabilities_detected,
            "total_security_issues": len(findings)
        }
        
        return round(score, 1), findings, metrics

    @staticmethod
    def _scan_secrets(rel_path: str, file: RepoFile, findings: List[Dict[str, Any]], is_test_file: bool):
        lines = file.content.splitlines()
        for idx, line in enumerate(lines, start=1):
            if len(line.strip()) == 0 or line.strip().startswith("//") or line.strip().startswith("#"):
                continue
                
            for rule in SECRET_REGEXES:
                match = re.search(rule["pattern"], line)
                if match:
                    # In test files, reduce severity unless it's a real AWS/GitHub key format
                    severity = rule["severity"]
                    confidence = rule["confidence"]
                    if is_test_file and rule["id"] == "SEC-GENERIC-PASSWORD":
                        severity = "Low"
                        confidence = 0.70

                    # Mask sensitive portion in evidence snippet
                    matched_str = match.group(0)
                    masked = matched_str[:4] + "*" * (len(matched_str) - 8) + matched_str[-4:] if len(matched_str) > 10 else "********"
                    evidence = line.replace(matched_str, masked).strip()

                    findings.append({
                        "category": "Security",
                        "severity": severity,
                        "title": rule["title"],
                        "file_path": rel_path,
                        "line_number": idx,
                        "problem": f"A potential hard-coded secret ({rule['title']}) was detected in source code.",
                        "recommendation": rule["recommendation"],
                        "evidence_code": evidence,
                        "confidence": confidence,
                        "cwe_id": rule["cwe"],
                        "rule_id": rule["id"]
                    })
                    break  # Avoid double reporting same line

    @staticmethod
    def _scan_python_ast_security(rel_path: str, file: RepoFile, findings: List[Dict[str, Any]]):
        try:
            tree = ast.parse(file.content, filename=rel_path)
        except Exception:
            return

        lines = file.content.splitlines()

        for node in ast.walk(tree):
            # 1. Unsafe Command Execution (subprocess shell=True, os.system)
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                    if isinstance(node.func.value, ast.Name):
                        func_name = f"{node.func.value.id}.{node.func.attr}"

                # os.system, os.popen
                if func_name in {"os.system", "os.popen"}:
                    evidence = lines[node.lineno-1] if node.lineno-1 < len(lines) else func_name
                    findings.append({
                        "category": "Security",
                        "severity": "High",
                        "title": f"Insecure Command Execution with `{func_name}`",
                        "file_path": rel_path,
                        "line_number": node.lineno,
                        "problem": f"`{func_name}` executes shell commands without input sanitization, leaving the application vulnerable to Command Injection.",
                        "recommendation": "Use `subprocess.run(['command', 'arg1', ...], shell=False, check=True)` passing arguments as a list.",
                        "evidence_code": evidence.strip(),
                        "confidence": 0.97,
                        "cwe_id": "CWE-78",
                        "rule_id": "VULN-OS-COMMAND"
                    })

                # subprocess with shell=True
                elif "subprocess" in func_name or func_name in {"Popen", "run", "call", "check_output"}:
                    for kw in node.keywords:
                        if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                            evidence = lines[node.lineno-1] if node.lineno-1 < len(lines) else "subprocess.run(..., shell=True)"
                            findings.append({
                                "category": "Security",
                                "severity": "High",
                                "title": "Subprocess called with `shell=True`",
                                "file_path": rel_path,
                                "line_number": node.lineno,
                                "problem": "Passing `shell=True` to subprocess functions allows attackers to chain arbitrary shell commands if unvalidated user input is passed.",
                                "recommendation": "Set `shell=False` and pass command arguments as an array of discrete strings.",
                                "evidence_code": evidence.strip(),
                                "confidence": 0.98,
                                "cwe_id": "CWE-78",
                                "rule_id": "VULN-SHELL-TRUE"
                            })

                # eval() or exec()
                elif func_name in {"eval", "exec"}:
                    evidence = lines[node.lineno-1] if node.lineno-1 < len(lines) else f"{func_name}(...)"
                    findings.append({
                        "category": "Security",
                        "severity": "Critical",
                        "title": f"Dangerous dynamic code execution via `{func_name}()`",
                        "file_path": rel_path,
                        "line_number": node.lineno,
                        "problem": f"Using `{func_name}()` evaluates arbitrary strings as executable code, enabling Remote Code Execution (RCE).",
                        "recommendation": "Refactor to use `ast.literal_eval()` for safe data parsing, or use structured JSON serialization.",
                        "evidence_code": evidence.strip(),
                        "confidence": 0.99,
                        "cwe_id": "CWE-95",
                        "rule_id": "VULN-EVAL-EXEC"
                    })

                # Unsafe Deserialization: pickle.loads, yaml.load without SafeLoader
                elif func_name in {"pickle.loads", "pickle.load", "_pickle.loads"}:
                    evidence = lines[node.lineno-1] if node.lineno-1 < len(lines) else func_name
                    findings.append({
                        "category": "Security",
                        "severity": "Critical",
                        "title": "Insecure Deserialization via `pickle`",
                        "file_path": rel_path,
                        "line_number": node.lineno,
                        "problem": "Python's `pickle` library is not secure against untrusted data and can execute arbitrary payloads during unpickling.",
                        "recommendation": "Use safe data formats such as JSON, Protocol Buffers, or messagepack with strict schema validation.",
                        "evidence_code": evidence.strip(),
                        "confidence": 0.96,
                        "cwe_id": "CWE-502",
                        "rule_id": "VULN-PICKLE-DESERIALIZATION"
                    })

                # Weak Hashing: hashlib.md5 or hashlib.sha1
                elif func_name in {"hashlib.md5", "hashlib.sha1"}:
                    evidence = lines[node.lineno-1] if node.lineno-1 < len(lines) else func_name
                    findings.append({
                        "category": "Security",
                        "severity": "Medium",
                        "title": f"Cryptographically Weak Hash Algorithm ({func_name})",
                        "file_path": rel_path,
                        "line_number": node.lineno,
                        "problem": "MD5 and SHA-1 have known collision vulnerabilities and are unsuitable for security-sensitive contexts.",
                        "recommendation": "Upgrade to SHA-256 (`hashlib.sha256()`) for integrity checks or Argon2id/bcrypt for password hashing.",
                        "evidence_code": evidence.strip(),
                        "confidence": 0.92,
                        "cwe_id": "CWE-328",
                        "rule_id": "VULN-WEAK-HASH"
                    })

            # 2. SQL Injection Patterns (String concatenation in database execute calls)
            if isinstance(node, ast.Call):
                func_name = getattr(node.func, "attr", "")
                if func_name in {"execute", "raw", "executescript"} and node.args:
                    first_arg = node.args[0]
                    # Check if first arg is JoinedStr (f-string) or BinOp (%) or BinOp (+)
                    if isinstance(first_arg, ast.JoinedStr) or (isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, (ast.Mod, ast.Add))):
                        evidence = lines[node.lineno-1] if node.lineno-1 < len(lines) else f"cursor.execute(...)"
                        findings.append({
                            "category": "Security",
                            "severity": "Critical",
                            "title": "SQL Injection vulnerability via formatted query string",
                            "file_path": rel_path,
                            "line_number": node.lineno,
                            "problem": "SQL query is constructed using dynamic string formatting / interpolation instead of parameterized placeholders.",
                            "recommendation": "Use parameterized queries with placeholder binding (e.g., `cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))`).",
                            "evidence_code": evidence.strip(),
                            "confidence": 0.98,
                            "cwe_id": "CWE-89",
                            "rule_id": "VULN-SQL-INJECTION"
                        })

    @staticmethod
    def _scan_js_security(rel_path: str, file: RepoFile, findings: List[Dict[str, Any]]):
        lines = file.content.splitlines()
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            
            # dangerouslySetInnerHTML in React
            if "dangerouslySetInnerHTML" in stripped:
                findings.append({
                    "category": "Security",
                    "severity": "High",
                    "title": "Potential Cross-Site Scripting (XSS) via `dangerouslySetInnerHTML`",
                    "file_path": rel_path,
                    "line_number": idx,
                    "problem": "Directly rendering raw HTML bypasses React's XSS protections and allows malicious script injection if user content is passed.",
                    "recommendation": "Sanitize HTML using DOMPurify before rendering, or prefer standard JSX text bindings.",
                    "evidence_code": stripped,
                    "confidence": 0.92,
                    "cwe_id": "CWE-79",
                    "rule_id": "VULN-REACT-DANGEROUS-HTML"
                })

            # eval() in JS
            if re.search(r"\beval\(", stripped):
                findings.append({
                    "category": "Security",
                    "severity": "Critical",
                    "title": "Dangerous dynamic execution via JavaScript `eval()`",
                    "file_path": rel_path,
                    "line_number": idx,
                    "problem": "`eval()` executes arbitrary code with full caller privileges, creating severe XSS/RCE vectors.",
                    "recommendation": "Parse data with `JSON.parse()` instead of `eval()`.",
                    "evidence_code": stripped,
                    "confidence": 0.98,
                    "cwe_id": "CWE-95",
                    "rule_id": "VULN-JS-EVAL"
                })
