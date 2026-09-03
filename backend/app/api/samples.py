from fastapi import APIRouter
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/samples", tags=["Sample Repositories"])

class SampleRepo(BaseModel):
    id: str
    name: str
    owner: str
    url: str
    description: str
    primary_language: str
    expected_profile: str  # e.g., "Vulnerable", "Clean / Production Ready", "Needs Documentation"
    stars: int

@router.get("", response_model=List[SampleRepo])
async def list_sample_repositories():
    """
    Returns curated ground-truth repositories for instant 1-click auditing across diverse architectures.
    """
    return [
        SampleRepo(
            id="vulnerable-python-app",
            name="vulnerable-python-app",
            owner="sample",
            url="https://github.com/sample/vulnerable-python-app",
            description="Intentionally vulnerable Flask web application with leaked AWS keys, SQL injection (CWE-89), command injection, bare excepts, and CVE-compromised dependencies.",
            primary_language="Python",
            expected_profile="Critical Vulnerabilities (Score ~45)",
            stars=1240
        ),
        SampleRepo(
            id="clean-modular-ts",
            name="clean-modular-ts",
            owner="sample",
            url="https://github.com/sample/clean-modular-ts",
            description="Production-grade modular TypeScript microservice with 100% unit tests, Zod validation, GitHub Actions CI, and clean architecture.",
            primary_language="TypeScript",
            expected_profile="Clean / Production Grade (Score ~95)",
            stars=3850
        ),
        SampleRepo(
            id="microservices-go-backend",
            name="microservices-go-backend",
            owner="sample",
            url="https://github.com/sample/microservices-go-backend",
            description="Distributed event-driven Go microservices architecture with gRPC, Redis Pub/Sub, and PostgreSQL order state management.",
            primary_language="Go",
            expected_profile="High Performance Microservices (Score ~90)",
            stars=2410
        ),
        SampleRepo(
            id="ml-predictive-pipeline",
            name="ml-predictive-pipeline",
            owner="sample",
            url="https://github.com/sample/ml-predictive-pipeline",
            description="End-to-end PyTorch deep learning training and inference pipeline with data preprocessing, scaling, and feature engineering.",
            primary_language="Python",
            expected_profile="ML Pipeline & Data Engineering (Score ~88)",
            stars=1670
        ),
        SampleRepo(
            id="missing-docs-deps",
            name="missing-docs-deps",
            owner="sample",
            url="https://github.com/sample/missing-docs-deps",
            description="Legacy Python backend with zero automated tests, missing README documentation, and outdated dependencies.",
            primary_language="Python",
            expected_profile="Documentation & Testing Deficits (Score ~60)",
            stars=420
        )
    ]
