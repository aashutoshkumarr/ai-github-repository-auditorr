import pytest
from backend.app.services.scoring_engine import ScoringEngine

def test_scoring_engine_calculation():
    scores = {
        "security": 80.0,
        "quality": 90.0,
        "testing": 60.0,
        "docs": 100.0,
        "deps": 70.0,
        "arch": 85.0,
        "maintainability": 75.0
    }
    overall = ScoringEngine.calculate_overall_score(scores)
    # 80*0.2 + 90*0.2 + 60*0.15 + 100*0.15 + 70*0.1 + 85*0.1 + 75*0.1 = 16 + 18 + 9 + 15 + 7 + 8.5 + 7.5 = 81.0
    assert overall == 81.0

def test_scoring_engine_roadmap_priority():
    findings = [
        {"severity": "Low", "category": "Documentation", "title": "Missing License", "recommendation": "Add MIT license"},
        {"severity": "Critical", "category": "Security", "title": "Exposed AWS Key", "recommendation": "Revoke key"},
        {"severity": "High", "category": "Dependencies", "title": "Vulnerable requests", "recommendation": "Upgrade requests"},
        {"severity": "Medium", "category": "Code Quality", "title": "Long Function", "recommendation": "Refactor"}
    ]
    roadmap = ScoringEngine.generate_fix_roadmap(findings)
    assert len(roadmap) == 4
    # First item must be Critical Security
    assert roadmap[0]["severity"] == "Critical"
    assert roadmap[0]["title"] == "Exposed AWS Key"
    # Second item High
    assert roadmap[1]["severity"] == "High"
