from typing import Dict, Any, List, Optional
import base64
import httpx


class GitHubIntegration:
    """
    Production GitHub integration for the AI GitHub Repository Auditor.

    Supports:
    - GitHub Issue generation
    - GitHub Issue creation
    - PR preview generation
    - Repository/branch lookup
    - Branch creation
    - File retrieval
    - Full-file commit
    - Pull Request creation
    - Complete verified AutoFix -> PR workflow
    """

    API_BASE = "https://api.github.com"
    API_VERSION = "2022-11-28"
    USER_AGENT = "AI-GitHub-Auditor"

    # ================================================================
    # COMMON HELPERS
    # ================================================================

    @staticmethod
    def _headers(token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GitHubIntegration.API_VERSION,
            "User-Agent": GitHubIntegration.USER_AGENT,
        }

    @staticmethod
    def _repo_url(
        owner: str,
        repo: str,
        path: str = "",
    ) -> str:
        base_url = (
            f"{GitHubIntegration.API_BASE}"
            f"/repos/{owner}/{repo}"
        )

        if path:
            return f"{base_url}/{path.lstrip('/')}"

        return base_url

    # ================================================================
    # ISSUE GENERATION
    # ================================================================

    @staticmethod
    def generate_issue_markdown(
        finding: Dict[str, Any],
        repo_url: str = "",
    ) -> Dict[str, Any]:

        category = finding.get(
            "category",
            "General",
        )

        severity = finding.get(
            "severity",
            "Medium",
        )

        title = (
            f"[{severity.upper()}] "
            f"{finding.get('title', 'Repository Issue')}"
        )

        file_path = finding.get(
            "file_path",
            "unknown",
        )

        line_no = finding.get(
            "line_number",
            1,
        )

        problem = finding.get(
            "problem",
            "",
        )

        recommendation = finding.get(
            "recommendation",
            "",
        )

        evidence = finding.get(
            "evidence_code",
            "",
        )

        cwe = finding.get(
            "cwe_id",
            "",
        )

        confidence = int(
            finding.get(
                "confidence",
                0.9,
            ) * 100
        )

        language = (
            file_path.split(".")[-1]
            if "." in file_path
            else "text"
        )

        body_lines = [
            (
                "## 🚨 Automated Audit Finding: "
                f"{finding.get('title')}"
            ),
            "",
            (
                f"**Category:** `{category}` | "
                f"**Severity:** `{severity}` | "
                f"**Confidence:** `{confidence}%`"
            ),
            "",
            "### 📍 Location",
            f"- **File:** `{file_path}`",
            f"- **Line:** `{line_no}`",
        ]

        if cwe:
            body_lines.append(
                f"- **Vulnerability Standard:** `{cwe}`"
            )

        if repo_url:
            body_lines.extend(
                [
                    f"- **Repository:** {repo_url}",
                ]
            )

        body_lines.extend(
            [
                "",
                "### ⚠️ Problem Description",
                problem,
                "",
                "### 🔍 Evidence Code Snippet",
                f"```{language}",
                (
                    evidence
                    if evidence
                    else "# (Snippet unavailable)"
                ),
                "```",
                "",
                "### 💡 Recommended Fix",
                recommendation,
                "",
                "---",
                (
                    "*Reported automatically by "
                    "[AI GitHub Repository Auditor]"
                    "(https://github.com/aashutoshkumarr/"
                    "ai-github-repository-auditorr)*"
                ),
            ]
        )

        labels = [
            "audit-finding",
            category.lower().replace(" ", "-"),
            severity.lower(),
        ]

        return {
            "title": title,
            "body_markdown": "\n".join(body_lines),
            "labels": labels,
        }

    # ================================================================
    # PR PREVIEW
    # ================================================================

    @staticmethod
    def generate_fix_pr(
        finding: Dict[str, Any],
        diff_patch: str = "",
        branch_name: Optional[str] = None,
    ) -> Dict[str, Any]:

        file_path = finding.get(
            "file_path",
            "file.txt",
        )

        rule_id = (
            finding.get(
                "rule_id",
                "FIX",
            )
            or "FIX"
        )

        safe_rule_id = (
            rule_id
            .lower()
            .replace("_", "-")
            .replace(" ", "-")
        )

        line_number = finding.get(
            "line_number",
            1,
        )

        if not branch_name:
            branch_name = (
                f"fix/{safe_rule_id}-{line_number}"
            )

        title = (
            f"fix: resolve "
            f"{finding.get('title', 'security finding')}"
        )

        # This is only a fallback preview.
        # The real AutoFix endpoint should provide
        # the actual generated diff.
        if not diff_patch:

            evidence = finding.get(
                "evidence_code",
                "",
            )

            diff_patch = (
                f"--- a/{file_path}\n"
                f"+++ b/{file_path}\n"
                f"@@ -{line_number},1 "
                f"+{line_number},1 @@\n"
                f"- {evidence}\n"
                f"+[Run AutoFix to generate "
                f"the verified patch]"
            )

        body = (
            "## 🤖 Automated Fix Proposal\n\n"
            f"This PR addresses the finding "
            f"**{finding.get('title')}** "
            f"in `{file_path}`.\n\n"
            f"**Recommendation:** "
            f"{finding.get('recommendation', '')}\n\n"
            "### Verification\n\n"
            "- Patch generated in isolated sandbox\n"
            "- Security verification performed\n"
            "- Repository tests evaluated\n"
            "- Only verified candidates may be "
            "submitted automatically\n\n"
            "Generated by "
            "AI GitHub Repository Auditor."
        )

        return {
            "title": title,
            "branch_name": branch_name,
            "diff_patch": diff_patch,
            "body_markdown": body,
        }

    # ================================================================
    # GET REPOSITORY
    # ================================================================

    @staticmethod
    async def get_repository(
        owner: str,
        repo: str,
        token: str,
    ) -> Dict[str, Any]:

        url = GitHubIntegration._repo_url(
            owner,
            repo,
        )

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.get(
                url,
                headers=GitHubIntegration._headers(
                    token
                ),
            )

        if response.status_code != 200:
            raise RuntimeError(
                "GitHub repository lookup failed "
                f"({response.status_code}): "
                f"{response.text}"
            )

        return response.json()

    # ================================================================
    # GET BRANCH
    # ================================================================

    @staticmethod
    async def get_branch(
        owner: str,
        repo: str,
        branch: str,
        token: str,
    ) -> Dict[str, Any]:

        url = GitHubIntegration._repo_url(
            owner,
            repo,
            f"branches/{branch}",
        )

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.get(
                url,
                headers=GitHubIntegration._headers(
                    token
                ),
            )

        if response.status_code != 200:
            raise RuntimeError(
                "GitHub branch lookup failed "
                f"({response.status_code}): "
                f"{response.text}"
            )

        return response.json()

    # ================================================================
    # CREATE BRANCH
    # ================================================================

    @staticmethod
    async def create_branch(
        owner: str,
        repo: str,
        branch_name: str,
        base_branch: str,
        token: str,
    ) -> Dict[str, Any]:

        base_branch_data = (
            await GitHubIntegration.get_branch(
                owner=owner,
                repo=repo,
                branch=base_branch,
                token=token,
            )
        )

        base_sha = (
            base_branch_data
            .get("commit", {})
            .get("sha")
        )

        if not base_sha:
            raise RuntimeError(
                "Could not determine the SHA "
                f"for base branch '{base_branch}'."
            )

        url = GitHubIntegration._repo_url(
            owner,
            repo,
            "git/refs",
        )

        payload = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha,
        }

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.post(
                url,
                json=payload,
                headers=GitHubIntegration._headers(
                    token
                ),
            )

        if response.status_code in {200, 201}:
            return response.json()

        # Branch already exists.
        if response.status_code == 422:

            return await GitHubIntegration.get_branch(
                owner=owner,
                repo=repo,
                branch=branch_name,
                token=token,
            )

        raise RuntimeError(
            "GitHub branch creation failed "
            f"({response.status_code}): "
            f"{response.text}"
        )

    # ================================================================
    # GET FILE FROM GITHUB
    # ================================================================

    @staticmethod
    async def get_file(
        owner: str,
        repo: str,
        file_path: str,
        branch: str,
        token: str,
    ) -> Dict[str, Any]:

        url = GitHubIntegration._repo_url(
            owner,
            repo,
            f"contents/{file_path}",
        )

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.get(
                url,
                params={
                    "ref": branch,
                },
                headers=GitHubIntegration._headers(
                    token
                ),
            )

        if response.status_code != 200:
            raise RuntimeError(
                "GitHub file lookup failed "
                f"({response.status_code}): "
                f"{response.text}"
            )

        return response.json()

    # ================================================================
    # COMMIT COMPLETE FILE
    # ================================================================

    @staticmethod
    async def commit_file(
        owner: str,
        repo: str,
        branch: str,
        file_path: str,
        content: str,
        commit_message: str,
        token: str,
    ) -> Dict[str, Any]:

        existing_file = None

        try:

            existing_file = (
                await GitHubIntegration.get_file(
                    owner=owner,
                    repo=repo,
                    file_path=file_path,
                    branch=branch,
                    token=token,
                )
            )

        except RuntimeError as exc:

            # 404 means the file does not exist.
            # That is okay for file creation.
            if "404" not in str(exc):
                raise

        encoded_content = (
            base64.b64encode(
                content.encode("utf-8")
            )
            .decode("ascii")
        )

        payload = {
            "message": commit_message,
            "content": encoded_content,
            "branch": branch,
        }

        if existing_file:

            file_sha = existing_file.get(
                "sha"
            )

            if file_sha:
                payload["sha"] = file_sha

        url = GitHubIntegration._repo_url(
            owner,
            repo,
            f"contents/{file_path}",
        )

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.put(
                url,
                json=payload,
                headers=GitHubIntegration._headers(
                    token
                ),
            )

        if response.status_code in {
            200,
            201,
        }:
            return response.json()

        raise RuntimeError(
            "GitHub file commit failed "
            f"({response.status_code}): "
            f"{response.text}"
        )

    # ================================================================
    # CREATE PULL REQUEST
    # ================================================================

    @staticmethod
    async def create_pull_request(
        owner: str,
        repo: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str,
        token: str,
    ) -> Dict[str, Any]:

        url = GitHubIntegration._repo_url(
            owner,
            repo,
            "pulls",
        )

        payload = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
        }

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.post(
                url,
                json=payload,
                headers=GitHubIntegration._headers(
                    token
                ),
            )

        if response.status_code in {
            200,
            201,
        }:
            return response.json()

        raise RuntimeError(
            "GitHub Pull Request creation failed "
            f"({response.status_code}): "
            f"{response.text}"
        )

    # ================================================================
    # COMPLETE VERIFIED FIX -> PR
    # ================================================================

    @staticmethod
    async def create_verified_fix_pr(
        owner: str,
        repo: str,
        token: str,
        base_branch: str,
        branch_name: str,
        file_path: str,
        patched_file_content: str,
        finding: Dict[str, Any],
        diff_patch: str,
    ) -> Dict[str, Any]:

        if not token:
            raise ValueError(
                "GitHub Personal Access Token "
                "is required."
            )

        if not owner or not repo:
            raise ValueError(
                "Repository owner and name are required."
            )

        if not patched_file_content:
            raise ValueError(
                "Complete patched file content "
                "is required."
            )

        # ------------------------------------------------------------
        # 1. Verify repository access
        # ------------------------------------------------------------

        await GitHubIntegration.get_repository(
            owner=owner,
            repo=repo,
            token=token,
        )

        # ------------------------------------------------------------
        # 2. Create branch
        # ------------------------------------------------------------

        await GitHubIntegration.create_branch(
            owner=owner,
            repo=repo,
            branch_name=branch_name,
            base_branch=base_branch,
            token=token,
        )

        # ------------------------------------------------------------
        # 3. Commit COMPLETE patched file
        # ------------------------------------------------------------

        commit_message = (
            "fix: "
            f"{finding.get('title', 'automated audit fix')}"
        )

        commit_result = (
            await GitHubIntegration.commit_file(
                owner=owner,
                repo=repo,
                branch=branch_name,
                file_path=file_path,
                content=patched_file_content,
                commit_message=commit_message,
                token=token,
            )
        )

        # ------------------------------------------------------------
        # 4. Generate PR description
        # ------------------------------------------------------------

        pr_data = (
            GitHubIntegration.generate_fix_pr(
                finding=finding,
                diff_patch=diff_patch,
                branch_name=branch_name,
            )
        )

        commit_url = (
            commit_result
            .get("commit", {})
            .get("html_url")
        )

        body = (
            f"{pr_data['body_markdown']}\n\n"
            "### 🔐 AutoFix Verification\n\n"
            "The candidate patch was generated in an "
            "isolated sandbox and passed the required "
            "verification gates before PR creation.\n\n"
            "### 📁 Changed File\n\n"
            f"`{file_path}`\n\n"
            "### 📝 Commit\n\n"
            f"{commit_url or 'N/A'}"
        )

        # ------------------------------------------------------------
        # 5. Create Pull Request
        # ------------------------------------------------------------

        pr_result = (
            await GitHubIntegration.create_pull_request(
                owner=owner,
                repo=repo,
                title=pr_data["title"],
                body=body,
                head_branch=branch_name,
                base_branch=base_branch,
                token=token,
            )
        )

        return {
            "status": "success",
            "branch_name": branch_name,
            "base_branch": base_branch,
            "file_path": file_path,
            "commit_sha": (
                commit_result
                .get("commit", {})
                .get("sha")
            ),
            "commit_url": commit_url,
            "pr_number": pr_result.get(
                "number"
            ),
            "pr_url": pr_result.get(
                "html_url"
            ),
            "pr_title": pr_result.get(
                "title"
            ),
        }

    # ================================================================
    # CREATE GITHUB ISSUE
    # ================================================================

    @staticmethod
    async def create_github_issue(
        owner: str,
        repo: str,
        token: str,
        title: str,
        body: str,
        labels: List[str],
    ) -> Dict[str, Any]:

        url = GitHubIntegration._repo_url(
            owner,
            repo,
            "issues",
        )

        headers = (
            GitHubIntegration._headers(
                token
            )
        )

        payload = {
            "title": title,
            "body": body,
            "labels": labels,
        }

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.post(
                url,
                json=payload,
                headers=headers,
            )

        if response.status_code in {
            200,
            201,
        }:
            return response.json()

        raise RuntimeError(
            "GitHub API Error "
            f"({response.status_code}): "
            f"{response.text}"
        )