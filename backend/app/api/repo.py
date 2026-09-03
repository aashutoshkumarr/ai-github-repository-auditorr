from typing import List

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.core.security import extract_owner_repo, sanitize_repo_url

router = APIRouter(prefix="/repo", tags=["Repository"])


class RepoPreviewRequest(BaseModel):
    github_url: str = Field(..., description="GitHub repository URL to preview")


class RepoPreviewResponse(BaseModel):
    owner: str
    name: str
    url: str
    description: str
    default_branch: str
    language: str
    stars: int
    forks: int
    topics: List[str] = []
    tech_stack: List[str] = []
    summary: str
    readme_excerpt: str


async def _fetch_github_json(client: httpx.AsyncClient, url: str) -> dict:
    resp = await client.get(url, headers={"User-Agent": "AI-GitHub-Auditor", "Accept": "application/vnd.github+json"})
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=f"GitHub API request failed for {url}")
    return resp.json()


@router.post("/preview", response_model=RepoPreviewResponse)
async def preview_repository(request: RepoPreviewRequest):
    clean_url = sanitize_repo_url(request.github_url)
    owner, name = extract_owner_repo(clean_url)
    if not owner or not name:
        raise HTTPException(status_code=400, detail="Please provide a valid GitHub repository URL")

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            meta = await _fetch_github_json(client, f"https://api.github.com/repos/{owner}/{name}")
            contents = await _fetch_github_json(client, f"https://api.github.com/repos/{owner}/{name}/contents")
            default_branch = meta.get("default_branch") or "main"
            readme_url = f"https://raw.githubusercontent.com/{owner}/{name}/{default_branch}/README.md"
            readme_excerpt = ""
            try:
                readme_resp = await client.get(readme_url, timeout=20.0)
                if readme_resp.status_code == 200:
                    readme_text = readme_resp.text
                    text = readme_text.replace("\r", "").strip()
                    readme_excerpt = " ".join(text.split())[:500]
            except Exception:
                readme_excerpt = ""

            root_filenames = []
            if isinstance(contents, list):
                root_filenames = [item.get("name", "") for item in contents if isinstance(item, dict)]

            tech_stack = []
            for candidate in [
                "package.json", "requirements.txt", "pyproject.toml", "poetry.lock", "go.mod",
                "Cargo.toml", "pom.xml", "build.gradle", "Dockerfile", "docker-compose.yml",
                "next.config.js", "vite.config.ts", "tsconfig.json", "vercel.json", "terraform.tfvars"
            ]:
                if candidate in root_filenames:
                    tech_stack.append(candidate)

            language = meta.get("language") or "Unknown"
            if language and language not in tech_stack:
                tech_stack.insert(0, language)

            topics = meta.get("topics") or []
            if not tech_stack:
                tech_stack = [language] if language else ["Repository"]

            summary = meta.get("description") or "Repository overview is not provided. The codebase likely contains a full application workflow, test suite, and deployment configuration."
            if not readme_excerpt:
                summary = summary[:280]

            return RepoPreviewResponse(
                owner=owner,
                name=name,
                url=clean_url,
                description=meta.get("description") or "No project description provided.",
                default_branch=default_branch,
                language=language,
                stars=meta.get("stargazers_count", 0),
                forks=meta.get("forks_count", 0),
                topics=topics[:8],
                tech_stack=tech_stack[:10],
                summary=summary,
                readme_excerpt=readme_excerpt or "Repository preview generated from GitHub metadata. Run the full auditor for a detailed static and security analysis.",
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate repository preview: {str(exc)}")
