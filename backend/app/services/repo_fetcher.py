import os
import shutil
import tempfile
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import git
import httpx

from backend.app.core.config import settings, REPOS_CACHE_DIR, BENCHMARKS_DIR
from backend.app.core.security import sanitize_repo_url, extract_owner_repo

IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build",
    ".next", ".nuxt", ".cache", "target", "vendor", ".idea", ".vscode", "coverage",
    ".pytest_cache", ".ruff_cache", ".mypy_cache"
}

IGNORE_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mp3", ".zip", ".tar", ".gz",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".iso", ".pdf", ".lock"
}

class RepoFile:
    def __init__(self, relative_path: str, absolute_path: str, size: int, extension: str, content: Optional[str] = None):
        self.relative_path = relative_path.replace("\\", "/")
        self.absolute_path = absolute_path
        self.size = size
        self.extension = extension
        self._content = content

    @property
    def content(self) -> str:
        if self._content is None:
            try:
                with open(self.absolute_path, "r", encoding="utf-8", errors="replace") as f:
                    self._content = f.read()
            except Exception:
                self._content = ""
        return self._content

class RepositoryContext:
    def __init__(self, url: str, local_path: str, owner: str, name: str, default_branch: str = "main"):
        self.url = url
        self.local_path = local_path
        self.owner = owner
        self.name = name
        self.default_branch = default_branch
        self.files: Dict[str, RepoFile] = {}
        self.total_lines: int = 0
        self.language_breakdown: Dict[str, int] = {}
        self.primary_language: str = "Unknown"
        self.git_commits: List[Dict[str, Any]] = []

    def index_files(self):
        root_path = Path(self.local_path)
        for root, dirs, filenames in os.walk(root_path):
            # Keep .github, filter other hidden/ignored dirs
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and (not d.startswith(".") or d == ".github")]
            
            for filename in filenames:
                file_path = Path(root) / filename
                rel_path = str(file_path.relative_to(root_path)).replace("\\", "/")
                ext = file_path.suffix.lower()
                
                if ext in IGNORE_EXTENSIONS:
                    continue
                
                try:
                    size = file_path.stat().st_size
                    if size > 1_000_000:  # Skip files > 1MB
                        continue
                    
                    repo_file = RepoFile(rel_path, str(file_path), size, ext)
                    self.files[rel_path] = repo_file
                except Exception:
                    pass

        self._compute_stats()
        self._extract_git_history()

    def _compute_stats(self):
        lang_counts: Dict[str, int] = {}
        total_loc = 0
        
        ext_to_lang = {
            ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
            ".ts": "TypeScript", ".tsx": "TypeScript", ".go": "Go",
            ".rs": "Rust", ".java": "Java", ".c": "C", ".cpp": "C++",
            ".cs": "C#", ".rb": "Ruby", ".php": "PHP", ".sql": "SQL",
            ".html": "HTML", ".css": "CSS", ".sh": "Shell"
        }
        
        for file in self.files.values():
            if file.extension in ext_to_lang:
                lang = ext_to_lang[file.extension]
                loc = len(file.content.splitlines())
                lang_counts[lang] = lang_counts.get(lang, 0) + loc
                total_loc += loc
                
        self.total_lines = total_loc
        self.language_breakdown = lang_counts
        if lang_counts:
            self.primary_language = max(lang_counts.items(), key=lambda x: x[1])[0]
        else:
            self.primary_language = "Generic"

    def _extract_git_history(self):
        try:
            repo = git.Repo(self.local_path)
            commits = list(repo.iter_commits(max_count=100))
            for c in commits:
                self.git_commits.append({
                    "hexsha": c.hexsha[:8],
                    "message": c.message.strip(),
                    "author": c.author.name,
                    "date": c.committed_datetime.isoformat(),
                    "stats": c.stats.files if hasattr(c, "stats") else {}
                })
        except Exception:
            self.git_commits = []

class RepoFetcher:
    @staticmethod
    async def fetch_repository(url: str, branch: Optional[str] = None) -> RepositoryContext:
        clean_url = sanitize_repo_url(url)
        
        # 1. Check if mapping to built-in sample/benchmark repos
        url_lower = clean_url.lower()
        if "repo_vulnerable_py" in url_lower or "repo_vulnerable_python" in url_lower or "vulnerable-python-app" in url_lower or "sample/vulnerable" in url_lower:
            local_dir = BENCHMARKS_DIR / "repo_vulnerable_py"
            ctx = RepositoryContext("https://github.com/sample/vulnerable-python-app", str(local_dir), "sample", "vulnerable-python-app")
            ctx.index_files()
            return ctx
        elif "fastapi" in url_lower:
            local_dir = BENCHMARKS_DIR / "repo_fastapi_python"
            ctx = RepositoryContext("https://github.com/tiangolo/fastapi", str(local_dir), "tiangolo", "fastapi")
            ctx.index_files()
            return ctx
        elif "shadcn" in url_lower or "shadcn-ui" in url_lower or "ui-library" in url_lower or url_lower.rstrip("/").endswith("/ui"):
            local_dir = BENCHMARKS_DIR / "repo_shadcn_ui_ts"
            ctx = RepositoryContext("https://github.com/shadcn-ui/ui", str(local_dir), "shadcn-ui", "ui")
            ctx.index_files()
            return ctx
        elif "express" in url_lower:
            local_dir = BENCHMARKS_DIR / "repo_express_js"
            ctx = RepositoryContext("https://github.com/expressjs/express", str(local_dir), "expressjs", "express")
            ctx.index_files()
            return ctx
        elif "repo_clean_modular_ts" in url_lower or "clean-modular-ts" in url_lower or "sample/clean" in url_lower:
            local_dir = BENCHMARKS_DIR / "repo_clean_modular_ts"
            ctx = RepositoryContext("https://github.com/sample/clean-modular-ts", str(local_dir), "sample", "clean-modular-ts")
            ctx.index_files()
            return ctx
        elif "repo_missing_docs_deps" in url_lower or "missing-docs-deps" in url_lower or "sample/missing" in url_lower:
            local_dir = BENCHMARKS_DIR / "repo_missing_docs_deps"
            ctx = RepositoryContext("https://github.com/sample/missing-docs-deps", str(local_dir), "sample", "missing-docs-deps")
            ctx.index_files()
            return ctx
        elif "repo_microservices_go" in url_lower or "microservices-go" in url_lower:
            local_dir = BENCHMARKS_DIR / "repo_microservices_go"
            ctx = RepositoryContext("https://github.com/sample/microservices-go-backend", str(local_dir), "sample", "microservices-go-backend")
            ctx.index_files()
            return ctx
        elif "repo_ml_pipeline_py" in url_lower or "ml-predictive-pipeline" in url_lower:
            local_dir = BENCHMARKS_DIR / "repo_ml_pipeline_py"
            ctx = RepositoryContext("https://github.com/sample/ml-predictive-pipeline", str(local_dir), "sample", "ml-predictive-pipeline")
            ctx.index_files()
            return ctx

        owner, name = extract_owner_repo(clean_url)
        if not owner or not name:
            raise ValueError(f"Invalid GitHub repository URL: {url}")

        target_dir = REPOS_CACHE_DIR / f"{owner}_{name}"
        
        if target_dir.exists() and (target_dir / ".git").exists():
            ctx = RepositoryContext(clean_url, str(target_dir), owner, name)
            ctx.index_files()
            return ctx

        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
            
        target_dir.mkdir(parents=True, exist_ok=True)
        
        loop = asyncio.get_event_loop()
        try:
            # Ultra-fast shallow single-branch clone
            clone_kwargs = {"depth": 1, "single_branch": True}
            if branch:
                clone_kwargs["branch"] = branch
                
            await loop.run_in_executor(
                None,
                lambda: git.Repo.clone_from(
                    f"https://github.com/{owner}/{name}.git",
                    str(target_dir),
                    **clone_kwargs
                )
            )
        except Exception as e:
            try:
                tarball_url = f"https://api.github.com/repos/{owner}/{name}/tarball"
                headers = {"User-Agent": "AI-GitHub-Auditor"}
                if settings.GITHUB_TOKEN:
                    headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
                    
                async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                    resp = await client.get(tarball_url, headers=headers)
                    if resp.status_code == 200:
                        import tarfile
                        import io
                        with tarfile.open(fileobj=io.BytesIO(resp.content), mode="r:gz") as tar:
                            for member in tar.getmembers():
                                parts = Path(member.name).parts
                                if len(parts) > 1:
                                    member.name = str(Path(*parts[1:]))
                                    tar.extract(member, path=str(target_dir))
                    else:
                        raise RuntimeError(f"Could not clone repository: {str(e)}")
            except Exception as tar_err:
                raise RuntimeError(f"Failed to fetch repository: {str(e)} / {str(tar_err)}")

        ctx = RepositoryContext(clean_url, str(target_dir), owner, name)
        ctx.index_files()
        return ctx
