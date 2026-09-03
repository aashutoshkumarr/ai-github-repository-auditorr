import pytest
from backend.app.services.repo_fetcher import RepositoryContext, RepoFetcher
from backend.app.services.analyzers.code_quality import CodeQualityAnalyzer
from backend.app.services.analyzers.security_scanner import SecurityScanner
from backend.app.services.analyzers.dependency_scanner import DependencyScanner
from backend.app.services.analyzers.testing_analyzer import TestingAnalyzer
from backend.app.services.analyzers.docs_analyzer import DocsAnalyzer
from backend.app.services.analyzers.architecture import ArchitectureAnalyzer
from backend.app.services.analyzers.git_analyzer import GitAnalyzer

@pytest.mark.asyncio
async def test_vulnerable_repository_detection():
    ctx = await RepoFetcher.fetch_repository("repo_vulnerable_py")
    
    # 1. Security Scanner
    sec_score, sec_findings, sec_metrics = SecurityScanner.analyze(ctx)
    rule_ids = [f["rule_id"] for f in sec_findings]
    
    assert "SEC-AWS-KEY" in rule_ids
    assert "SEC-OPENAI-KEY" in rule_ids
    assert "VULN-SQL-INJECTION" in rule_ids
    assert "VULN-EVAL-EXEC" in rule_ids
    assert "VULN-PICKLE-DESERIALIZATION" in rule_ids
    assert sec_score < 50.0  # Heavy security penalties applied

    # 2. Dependency Scanner
    dep_score, dep_findings, dep_vulns, dep_metrics = DependencyScanner.analyze(ctx)
    assert len(dep_vulns) >= 2
    vuln_pkg_names = [v["package_name"].lower() for v in dep_vulns]
    assert "requests" in vuln_pkg_names
    assert "paramiko" in vuln_pkg_names

    # 3. Code Quality
    qual_score, qual_findings, qual_metrics = CodeQualityAnalyzer.analyze(ctx)
    qual_rules = [f["rule_id"] for f in qual_findings]
    assert "QUAL-BARE-EXCEPT" in qual_rules

@pytest.mark.asyncio
async def test_clean_modular_repository():
    ctx = await RepoFetcher.fetch_repository("repo_clean_modular_ts")
    
    sec_score, sec_findings, _ = SecurityScanner.analyze(ctx)
    assert sec_score >= 90.0
    assert len([f for f in sec_findings if f["severity"] in {"Critical", "High"}]) == 0

    test_score, test_findings, test_metrics = TestingAnalyzer.analyze(ctx)
    assert test_score >= 70.0
    assert test_metrics["test_files_count"] >= 1

    docs_score, docs_findings, docs_metrics = DocsAnalyzer.analyze(ctx)
    assert docs_score >= 80.0
    assert docs_metrics["has_readme"] is True

    arch_score, _, mermaid, arch_metrics = ArchitectureAnalyzer.analyze(ctx)
    assert arch_score >= 80.0
    assert "graph TD" in mermaid
