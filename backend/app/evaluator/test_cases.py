from typing import List, Dict, Any

BENCHMARK_CASES = [
    {
        "name": "repo_vulnerable_py",
        "repo_alias": "repo_vulnerable_py",
        "description": "Python web application seeded with 5 security vulnerabilities, 3 quality issues, and 3 vulnerable dependencies.",
        "expected_findings": [
            {"category": "Security", "rule_id": "SEC-AWS-KEY"},
            {"category": "Security", "rule_id": "SEC-OPENAI-KEY"},
            {"category": "Security", "rule_id": "SEC-GENERIC-PASSWORD"},
            {"category": "Security", "rule_id": "VULN-SQL-INJECTION"},
            {"category": "Security", "rule_id": "VULN-EVAL-EXEC"},
            {"category": "Security", "rule_id": "VULN-PICKLE-DESERIALIZATION"},
            {"category": "Security", "rule_id": "VULN-OS-COMMAND"},
            {"category": "Code Quality", "rule_id": "QUAL-BARE-EXCEPT"},
            {"category": "Dependencies", "rule_id": "DEP-CVE-2023-32681"},
            {"category": "Testing", "rule_id": "TEST-NO-TESTS"}
        ]
    },
    {
        "name": "repo_clean_modular_ts",
        "repo_alias": "repo_clean_modular_ts",
        "description": "Clean modular TypeScript repository with tests, documentation, and zero high-severity issues.",
        "expected_findings": []
    },
    {
        "name": "repo_missing_docs_deps",
        "repo_alias": "repo_missing_docs_deps",
        "description": "Repository lacking README documentation, containing outdated dependencies, and lacking test suites.",
        "expected_findings": [
            {"category": "Documentation", "rule_id": "DOCS-NO-README"},
            {"category": "Testing", "rule_id": "TEST-NO-TESTS"},
            {"category": "Dependencies", "rule_id": "DEP-CVE-2023-32681"}
        ]
    }
]
