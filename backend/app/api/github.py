from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.database_models import Finding, AuditReport
from backend.app.models.schemas import (
    CreateIssueRequest,
    CreatePRRequest,
    IssuePreviewResponse,
    PRPreviewResponse,
)
from backend.app.services.github_integration import GitHubIntegration
from backend.app.services.repo_fetcher import RepoFetcher
from backend.app.services.autofix_engine import AutoFixEngine


router = APIRouter(
    prefix="/github",
    tags=["GitHub Integration"],
)


# ================================================================
# Helpers
# ================================================================

def finding_to_dict(finding: Finding) -> dict:
    """
    Convert a Finding database object into a plain dictionary
    that can safely be passed to GitHubIntegration / AutoFixEngine.
    """
    return {
        "id": finding.id,
        "title": finding.title,
        "category": finding.category,
        "severity": finding.severity,
        "file_path": finding.file_path,
        "line_number": finding.line_number,
        "problem": finding.problem,
        "recommendation": finding.recommendation,
        "evidence_code": finding.evidence_code,
        "confidence": finding.confidence,
        "cwe_id": finding.cwe_id,
        "rule_id": finding.rule_id,
    }


def _autofix_result_dict(autofix_result) -> dict:
    """
    Safely convert an AutoFixResult into a response dictionary.

    AutoFixEngine is expected to expose to_dict(), but keeping this
    helper isolated prevents endpoint code from depending on the
    concrete implementation details of the result object.
    """
    if hasattr(autofix_result, "to_dict"):
        return autofix_result.to_dict()

    if isinstance(autofix_result, dict):
        return autofix_result

    return {
        "status": getattr(autofix_result, "status", "unknown"),
        "security_check_passed": getattr(
            autofix_result,
            "security_check_passed",
            False,
        ),
        "tests_passed": getattr(
            autofix_result,
            "tests_passed",
            False,
        ),
        "patched_file_content": getattr(
            autofix_result,
            "patched_file_content",
            None,
        ),
        "diff_patch": getattr(
            autofix_result,
            "diff_patch",
            None,
        ),
    }


def _get_autofix_status(autofix_result) -> str:
    """
    Normalize AutoFix verification status.

    The GitHub PR gate must only accept the explicit
    'verified' state.
    """
    status = getattr(autofix_result, "status", None)

    if status is None and isinstance(autofix_result, dict):
        status = autofix_result.get("status")

    if status is None:
        return "unknown"

    return str(status).strip().lower()


def _get_autofix_bool(
    autofix_result,
    attribute: str,
) -> bool:
    """
    Safely read boolean verification gates from AutoFixResult.
    """
    value = getattr(autofix_result, attribute, None)

    if value is None and isinstance(autofix_result, dict):
        value = autofix_result.get(attribute)

    return value is True


def _get_patched_file_content(autofix_result):
    """
    Get the complete patched file returned by AutoFixEngine.
    """
    content = getattr(
        autofix_result,
        "patched_file_content",
        None,
    )

    if content is None and isinstance(autofix_result, dict):
        content = autofix_result.get(
            "patched_file_content"
        )

    return content


def _get_diff_patch(autofix_result):
    """
    Get the generated diff patch, if available.
    """
    diff_patch = getattr(
        autofix_result,
        "diff_patch",
        None,
    )

    if diff_patch is None and isinstance(autofix_result, dict):
        diff_patch = autofix_result.get("diff_patch")

    return diff_patch


# ================================================================
# Preview Issue
# ================================================================

@router.get(
    "/preview-issue/{finding_id}",
    response_model=IssuePreviewResponse,
)
async def preview_issue(
    finding_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a GitHub Issue preview.

    No GitHub changes are made.
    """

    stmt = (
        select(Finding)
        .where(Finding.id == finding_id)
        .options(
            selectinload(Finding.report)
            .selectinload(AuditReport.repository)
        )
    )

    result = await db.execute(stmt)
    finding = result.scalars().first()

    if not finding:
        raise HTTPException(
            status_code=404,
            detail="Finding not found",
        )

    finding_dict = finding_to_dict(finding)

    repo_url = ""

    if finding.report and finding.report.repository:
        repo_url = finding.report.repository.url

    issue_data = GitHubIntegration.generate_issue_markdown(
        finding_dict,
        repo_url=repo_url,
    )

    return IssuePreviewResponse(
        title=issue_data["title"],
        body_markdown=issue_data["body_markdown"],
        labels=issue_data["labels"],
    )


# ================================================================
# Preview PR
# ================================================================

@router.get(
    "/preview-pr/{finding_id}",
    response_model=PRPreviewResponse,
)
async def preview_pr(
    finding_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a PR preview.

    This endpoint does NOT create:
        - a branch
        - a commit
        - a Pull Request
    """

    stmt = select(Finding).where(
        Finding.id == finding_id
    )

    result = await db.execute(stmt)
    finding = result.scalars().first()

    if not finding:
        raise HTTPException(
            status_code=404,
            detail="Finding not found",
        )

    finding_dict = finding_to_dict(finding)

    pr_data = GitHubIntegration.generate_fix_pr(
        finding_dict
    )

    return PRPreviewResponse(
        title=pr_data["title"],
        branch_name=pr_data["branch_name"],
        diff_patch=pr_data["diff_patch"],
        body_markdown=pr_data["body_markdown"],
    )


# ================================================================
# Run AutoFix
# ================================================================

@router.post(
    "/autofix/{finding_id}"
)
async def run_autofix_loop(
    finding_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Execute the AutoFix verification pipeline.

    Flow:

        Finding
            ->
        Generate Patch
            ->
        Sandbox
            ->
        Syntax Validation
            ->
        Repository Tests
            ->
        Security Verification
            ->
        Verified / Unverified / Failed

    IMPORTANT:
    This endpoint does NOT create a GitHub branch or Pull Request.
    """

    stmt = (
        select(Finding)
        .where(Finding.id == finding_id)
        .options(
            selectinload(Finding.report)
            .selectinload(AuditReport.repository)
        )
    )

    result = await db.execute(stmt)
    finding = result.scalars().first()

    if (
        not finding
        or not finding.report
        or not finding.report.repository
    ):
        raise HTTPException(
            status_code=404,
            detail="Finding or repository not found",
        )

    try:
        ctx = await RepoFetcher.fetch_repository(
            finding.report.repository.url
        )

        finding_dict = finding_to_dict(finding)

        autofix_result = (
            await AutoFixEngine.run_autofix_pipeline(
                ctx,
                finding_dict,
            )
        )

        return _autofix_result_dict(
            autofix_result
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AutoFix failed: {str(exc)}",
        )


# ================================================================
# Create GitHub Issue
# ================================================================

@router.post(
    "/create-issue"
)
async def create_issue_on_github(
    request: CreateIssueRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a GitHub Issue from an audit finding.
    """

    if not request.github_token:
        raise HTTPException(
            status_code=400,
            detail=(
                "GitHub Personal Access Token "
                "is required."
            ),
        )

    stmt = (
        select(Finding)
        .where(
            Finding.id == request.finding_id
        )
        .options(
            selectinload(Finding.report)
            .selectinload(AuditReport.repository)
        )
    )

    result = await db.execute(stmt)
    finding = result.scalars().first()

    if (
        not finding
        or not finding.report
        or not finding.report.repository
    ):
        raise HTTPException(
            status_code=404,
            detail="Finding or repository not found",
        )

    repo = finding.report.repository

    finding_dict = finding_to_dict(finding)

    issue_data = GitHubIntegration.generate_issue_markdown(
        finding_dict,
        repo_url=repo.url,
    )

    try:
        github_result = (
            await GitHubIntegration.create_github_issue(
                owner=repo.owner,
                repo=repo.name,
                token=request.github_token,
                title=issue_data["title"],
                body=issue_data["body_markdown"],
                labels=issue_data["labels"],
            )
        )

        return {
            "status": "success",
            "issue_url": github_result.get(
                "html_url"
            ),
            "issue_number": github_result.get(
                "number"
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "GitHub Issue creation failed: "
                f"{str(exc)}"
            ),
        )


# ================================================================
# Create Verified Pull Request
# ================================================================

@router.post(
    "/create-pr"
)
async def create_verified_pull_request(
    request: CreatePRRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Complete verified AutoFix -> GitHub PR pipeline.

    Flow:

        Finding
            ->
        AutoFix
            ->
        Sandbox
            ->
        Tests
            ->
        Security Verification
            ->
        VERIFIED?
            ->
        Create Branch
            ->
        Commit Complete Patched File
            ->
        Create Pull Request

    IMPORTANT:
    A PR is NEVER created when the AutoFix result is
    pending, unverified, failed, or otherwise not explicitly
    verified.
    """

    # ------------------------------------------------------------
    # Token validation
    # ------------------------------------------------------------

    if not request.github_token:
        raise HTTPException(
            status_code=400,
            detail=(
                "GitHub Personal Access Token "
                "is required."
            ),
        )

    # ------------------------------------------------------------
    # Finding lookup
    # ------------------------------------------------------------

    stmt = (
        select(Finding)
        .where(
            Finding.id == request.finding_id
        )
        .options(
            selectinload(Finding.report)
            .selectinload(AuditReport.repository)
        )
    )

    result = await db.execute(stmt)
    finding = result.scalars().first()

    if (
        not finding
        or not finding.report
        or not finding.report.repository
    ):
        raise HTTPException(
            status_code=404,
            detail="Finding or repository not found",
        )

    repo = finding.report.repository

    # ------------------------------------------------------------
    # Determine base branch
    # ------------------------------------------------------------

    base_branch = (
        request.branch_name
        or getattr(
            repo,
            "default_branch",
            None,
        )
        or "main"
    )

    # ------------------------------------------------------------
    # Fetch repository
    # ------------------------------------------------------------

    try:
        ctx = await RepoFetcher.fetch_repository(
            repo.url
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Repository fetch failed: {str(exc)}"
            ),
        )

    # ------------------------------------------------------------
    # Run AutoFix
    # ------------------------------------------------------------

    finding_dict = finding_to_dict(finding)

    try:
        autofix_result = (
            await AutoFixEngine.run_autofix_pipeline(
                ctx,
                finding_dict,
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"AutoFix execution failed: {str(exc)}"
            ),
        )

    autofix_data = _autofix_result_dict(
        autofix_result
    )

    # ------------------------------------------------------------
    # SECURITY GATE
    # ------------------------------------------------------------
    #
    # Security verification must explicitly pass.
    # Anything else rejects the PR.
    #

    security_passed = _get_autofix_bool(
        autofix_result,
        "security_check_passed",
    )

    if not security_passed:
        return {
            "status": "rejected",
            "verification_status": "failed",
            "reason": (
                "Security verification failed. "
                "Pull Request was not created."
            ),
            "autofix": autofix_data,
        }

    # ------------------------------------------------------------
    # TEST GATE
    # ------------------------------------------------------------
    #
    # Tests must explicitly pass.
    # Missing / None / False is NOT treated as success.
    #

    tests_passed = _get_autofix_bool(
        autofix_result,
        "tests_passed",
    )

    if not tests_passed:
        return {
            "status": "unverified",
            "verification_status": "pending",
            "reason": (
                "Repository tests did not pass "
                "or were unavailable. "
                "Pull Request was not created."
            ),
            "autofix": autofix_data,
        }

    # ------------------------------------------------------------
    # FINAL VERIFICATION GATE
    # ------------------------------------------------------------
    #
    # Only an explicit "verified" result is accepted.
    #
    # pending  -> DO NOT create PR
    # failed   -> DO NOT create PR
    # unknown  -> DO NOT create PR
    # verified -> continue
    #

    autofix_status = _get_autofix_status(
        autofix_result
    )

    if autofix_status != "verified":
        verification_status = (
            "failed"
            if autofix_status in {
                "failed",
                "rejected",
                "error",
            }
            else "pending"
        )

        return {
            "status": (
                "rejected"
                if verification_status == "failed"
                else "unverified"
            ),
            "verification_status": verification_status,
            "reason": (
                "AutoFix candidate was not verified. "
                "Pull Request was not created."
            ),
            "autofix": autofix_data,
        }

    # ------------------------------------------------------------
    # Complete patched file
    # ------------------------------------------------------------

    patched_file_content = _get_patched_file_content(
        autofix_result
    )

    if not patched_file_content:
        raise HTTPException(
            status_code=500,
            detail=(
                "AutoFix returned no complete "
                "patched file content."
            ),
        )

    # ------------------------------------------------------------
    # Branch name
    # ------------------------------------------------------------

    pr_preview = GitHubIntegration.generate_fix_pr(
        finding_dict
    )

    branch_name = (
        request.branch_name
        if request.branch_name
        else pr_preview["branch_name"]
    )

    # Prevent accidentally using main/master as
    # the AutoFix branch.

    if branch_name in {
        "main",
        "master",
        base_branch,
    }:
        branch_name = (
            f"fix/"
            f"{finding.rule_id or 'audit'}-"
            f"{finding.id[:8]}"
        )

    # ------------------------------------------------------------
    # Create verified PR
    # ------------------------------------------------------------

    diff_patch = _get_diff_patch(
        autofix_result
    )

    try:
        github_result = (
            await GitHubIntegration.create_verified_fix_pr(
                owner=repo.owner,
                repo=repo.name,
                token=request.github_token,
                base_branch=base_branch,
                branch_name=branch_name,
                file_path=finding.file_path,
                patched_file_content=patched_file_content,
                finding=finding_dict,
                diff_patch=diff_patch,
            )
        )

        return {
            "status": "success",
            "verification_status": "verified",
            "message": (
                "Verified AutoFix committed "
                "and Pull Request created."
            ),
            "finding_id": finding.id,
            "branch_name": branch_name,
            "base_branch": base_branch,
            "file_path": finding.file_path,
            "commit_sha": github_result.get(
                "commit_sha"
            ),
            "commit_url": github_result.get(
                "commit_url"
            ),
            "pr_number": github_result.get(
                "pr_number"
            ),
            "pr_url": github_result.get(
                "pr_url"
            ),
            "pr_title": github_result.get(
                "pr_title"
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "GitHub Pull Request creation failed: "
                f"{str(exc)}"
            ),
        )