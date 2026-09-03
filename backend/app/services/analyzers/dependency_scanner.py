import re
import json
from typing import List, Dict, Any, Tuple
from backend.app.services.repo_fetcher import RepositoryContext

# Known CVE database & advisories for common Python & Node.js packages
KNOWN_ADVISORIES = {
    "requests": {
        "vulnerable_below": "2.31.0",
        "recommended": "2.32.3",
        "severity": "High",
        "cve": "CVE-2023-32681",
        "title": "Unintended leak of Proxy-Authorization header during cross-origin redirect"
    },
    "urllib3": {
        "vulnerable_below": "1.26.18",
        "recommended": "2.2.2",
        "severity": "High",
        "cve": "CVE-2023-45803",
        "title": "Request body not stripped after HTTP 303 redirection"
    },
    "flask": {
        "vulnerable_below": "2.2.5",
        "recommended": "3.0.3",
        "severity": "Medium",
        "cve": "CVE-2023-30861",
        "title": "Missing Vary: Cookie header allows session hijacking via shared cache"
    },
    "django": {
        "vulnerable_below": "4.2.11",
        "recommended": "4.2.16",
        "severity": "High",
        "cve": "CVE-2024-27351",
        "title": "Regular expression Denial of Service (ReDoS) in django.utils.text.Truncator"
    },
    "cryptography": {
        "vulnerable_below": "41.0.6",
        "recommended": "42.0.8",
        "severity": "High",
        "cve": "CVE-2023-49083",
        "title": "NULL-pointer dereference in PKCS7 Certificate loading"
    },
    "paramiko": {
        "vulnerable_below": "3.4.0",
        "recommended": "3.4.1",
        "severity": "Critical",
        "cve": "CVE-2023-48795",
        "title": "Terrapin SSH prefix truncation attack"
    },
    "jinja2": {
        "vulnerable_below": "3.1.3",
        "recommended": "3.1.4",
        "severity": "Medium",
        "cve": "CVE-2024-22195",
        "title": "HTML attribute injection vulnerability"
    },
    "axios": {
        "vulnerable_below": "1.6.0",
        "recommended": "1.7.4",
        "severity": "High",
        "cve": "CVE-2023-45857",
        "title": "Cross-Site Request Forgery (CSRF) via unauthorized header transmission"
    },
    "lodash": {
        "vulnerable_below": "4.17.21",
        "recommended": "4.17.21",
        "severity": "Critical",
        "cve": "CVE-2019-10744",
        "title": "Prototype Pollution in defaultsDeep"
    },
    "express": {
        "vulnerable_below": "4.19.2",
        "recommended": "4.19.2",
        "severity": "High",
        "cve": "CVE-2024-29041",
        "title": "Open redirect vulnerability in res.redirect()"
    },
    "jsonwebtoken": {
        "vulnerable_below": "9.0.0",
        "recommended": "9.0.2",
        "severity": "High",
        "cve": "CVE-2022-23529",
        "title": "Insecure key validation leading to arbitrary remote execution"
    }
}

def parse_semver(v: str) -> List[int]:
    nums = re.findall(r"\d+", v)
    return [int(n) for n in nums[:3]] + [0] * (3 - len(nums[:3]))

def is_version_older(v1: str, v2: str) -> bool:
    """Returns True if v1 < v2 based on semver integers."""
    try:
        p1 = parse_semver(v1)
        p2 = parse_semver(v2)
        return p1 < p2
    except Exception:
        return False

class DependencyScanner:
    @staticmethod
    def analyze(ctx: RepositoryContext) -> Tuple[float, List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Scans dependency manifests (requirements.txt, package.json, pyproject.toml) for outdated/vulnerable libraries.
        Returns (deps_score 0-100, findings_list, vuln_items_list, metrics_dict).
        """
        findings = []
        vuln_items = []
        parsed_deps = {}

        # 1. Parse requirements.txt
        for rel_path, file in ctx.files.items():
            if "requirements" in rel_path.lower() and file.extension == ".txt":
                DependencyScanner._parse_requirements_txt(rel_path, file.content, parsed_deps)
            elif rel_path.lower() == "package.json":
                DependencyScanner._parse_package_json(rel_path, file.content, parsed_deps)
            elif "pyproject.toml" in rel_path.lower():
                DependencyScanner._parse_pyproject_toml(rel_path, file.content, parsed_deps)

        # 2. Check advisories
        for pkg, meta in parsed_deps.items():
            pkg_clean = pkg.lower().strip()
            version = meta.get("version", "0.0.0")
            manifest = meta.get("file", "manifest")
            
            if pkg_clean in KNOWN_ADVISORIES:
                advisory = KNOWN_ADVISORIES[pkg_clean]
                if is_version_older(version, advisory["vulnerable_below"]):
                    is_major_bump = False
                    try:
                        p_curr = parse_semver(version)
                        p_rec = parse_semver(advisory["recommended"])
                        if p_rec[0] > p_curr[0]:
                            is_major_bump = True
                    except Exception:
                        pass

                    upgrade_cmd = (
                        f"pip install {pkg}>={advisory['recommended']}"
                        if ("requirements" in manifest or "pyproject" in manifest)
                        else f"npm install {pkg}@^{advisory['recommended']}"
                    )

                    vuln_entry = {
                        "package_name": pkg,
                        "current_version": version,
                        "recommended_version": advisory["recommended"],
                        "severity": advisory["severity"],
                        "advisory_title": advisory["title"],
                        "cve_id": advisory["cve"],
                        "is_breaking_risk": is_major_bump,
                        "upgrade_command": upgrade_cmd,
                    }
                    vuln_items.append(vuln_entry)

                    findings.append({
                        "category": "Dependencies",
                        "severity": advisory["severity"],
                        "title": f"Vulnerable dependency: {pkg}=={version} ({advisory['cve']})",
                        "file_path": manifest,
                        "line_number": meta.get("line", 1),
                        "problem": f"Package '{pkg}' version {version} is vulnerable to: {advisory['title']} ({advisory['cve']}).",
                        "recommendation": f"Upgrade '{pkg}' to version >={advisory['recommended']} or latest stable release.",
                        "evidence_code": meta.get("evidence", f"{pkg}=={version}"),
                        "confidence": 0.98,
                        "cwe_id": "CWE-1395",
                        "rule_id": f"DEP-{advisory['cve']}"
                    })

        # Calculate Score
        score = 100.0
        if not parsed_deps:
            # Missing manifest deduction
            score = 65.0
            findings.append({
                "category": "Dependencies",
                "severity": "Medium",
                "title": "No standard dependency manifest detected",
                "file_path": "repository_root",
                "line_number": 1,
                "problem": "Could not locate standard dependency manifests (e.g. requirements.txt, package.json, pyproject.toml).",
                "recommendation": "Add a structured dependency lockfile or manifest to declare required packages explicitly.",
                "evidence_code": "",
                "confidence": 0.85,
                "rule_id": "DEP-MISSING-MANIFEST"
            })
        else:
            for v in vuln_items:
                if v["severity"] == "Critical":
                    score -= 25.0
                elif v["severity"] == "High":
                    score -= 15.0
                elif v["severity"] == "Medium":
                    score -= 7.0
                elif v["severity"] == "Low":
                    score -= 3.0

        score = max(10.0, min(100.0, score))
        
        metrics = {
            "total_dependencies_detected": len(parsed_deps),
            "vulnerabilities_detected": len(vuln_items),
            "manifest_files": list(set(m.get("file") for m in parsed_deps.values()))
        }
        
        return round(score, 1), findings, vuln_items, metrics

    @staticmethod
    def _parse_requirements_txt(file_path: str, content: str, parsed_deps: Dict[str, Any]):
        for idx, line in enumerate(content.splitlines(), start=1):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            
            match = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*([=><~^!]+)\s*([0-9a-zA-Z_\-\.]+)", line)
            if match:
                pkg_name, op, version = match.groups()
                parsed_deps[pkg_name.lower()] = {
                    "version": version,
                    "file": file_path,
                    "line": idx,
                    "evidence": line
                }
            else:
                pkg_match = re.match(r"^([a-zA-Z0-9_\-\.]+)", line)
                if pkg_match:
                    pkg_name = pkg_match.group(1)
                    parsed_deps[pkg_name.lower()] = {
                        "version": "unpinned",
                        "file": file_path,
                        "line": idx,
                        "evidence": line
                    }

    @staticmethod
    def _parse_package_json(file_path: str, content: str, parsed_deps: Dict[str, Any]):
        try:
            data = json.loads(content)
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            for pkg, ver_str in deps.items():
                ver_clean = re.sub(r"[^0-9\.]", "", ver_str)
                parsed_deps[pkg.lower()] = {
                    "version": ver_clean or "0.0.0",
                    "file": file_path,
                    "line": 1,
                    "evidence": f'"{pkg}": "{ver_str}"'
                }
        except Exception:
            pass

    @staticmethod
    def _parse_pyproject_toml(file_path: str, content: str, parsed_deps: Dict[str, Any]):
        for idx, line in enumerate(content.splitlines(), start=1):
            match = re.search(r'["\']([a-zA-Z0-9_\-\.]+)\s*([=><~^]+)\s*([0-9\.]+)["\']', line)
            if match:
                pkg, op, ver = match.groups()
                parsed_deps[pkg.lower()] = {
                    "version": ver,
                    "file": file_path,
                    "line": idx,
                    "evidence": line.strip()
                }
