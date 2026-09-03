import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
WORKSPACE_DIR = BASE_DIR.parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
REPOS_CACHE_DIR = STORAGE_DIR / "repos"
REPOS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
BENCHMARKS_DIR = WORKSPACE_DIR / "benchmark_suite"

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI GitHub Repository Auditor"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database / service runtime
    DATABASE_URL: str = f"sqlite+aiosqlite:///{STORAGE_DIR}/auditor.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    POSTGRES_URL: str = "postgresql+psycopg://auditor:auditor@localhost:5432/auditor"
    STORAGE_BACKEND: str = "local"
    S3_ENDPOINT: str = ""
    S3_BUCKET: str = "auditor-artifacts"
    JOB_QUEUE_NAME: str = "auditor:jobs"
    
    # LLM Settings
    DEFAULT_LLM_PROVIDER: str = "offline"  # Options: offline, gemini, openai, anthropic
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "gemini-1.5-pro"
    
    # GitHub Integration
    GITHUB_TOKEN: str = ""
    API_KEYS_RAW: str = ""  # comma-separated APIKEY:tenant pairs for quick setup (e.g. key1:tenantA,key2:tenantB)
    API_KEYS: dict = {}
    
    # Cloner / Worker
    MAX_REPO_SIZE_MB: int = 150
    CLONE_TIMEOUT_SECONDS: int = 60
    MAX_PARSED_FILES: int = 500
    RATE_LIMIT_PER_MIN: int = 60
    # Job queue visibility and reclaim
    JOB_VISIBILITY_SECONDS: int = 300
    JOB_RECLAIM_INTERVAL_SECONDS: int = 60
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        extra="ignore"
    )

settings = Settings()
# Post-processing for convenience: parsed API_KEYS map and backwards-compat helpers
try:
    raw = settings.API_KEYS_RAW or os.getenv('API_KEYS', '')
    mapping = {}
    if raw:
        for pair in raw.split(','):
            if ':' in pair:
                k, t = pair.split(':', 1)
                mapping[k.strip()] = t.strip()
    settings.API_KEYS = mapping
except Exception:
    settings.API_KEYS = {}

# Build a safe DATABASE_URL variable for the rest of the app without mutating Settings
_postgres_env = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL') or settings.POSTGRES_URL
if _postgres_env and _postgres_env.startswith('postgresql+psycopg'):
    # convert common psycopg sync DSN form to asyncpg dialect
    _postgres_env = _postgres_env.replace('postgresql+psycopg', 'postgresql+asyncpg')

DATABASE_URL = os.getenv('DATABASE_URL') or _postgres_env or settings.DATABASE_URL

# Backwards-compatible alias for callers using STORAGE_DIR from module
STORAGE_DIR = STORAGE_DIR

