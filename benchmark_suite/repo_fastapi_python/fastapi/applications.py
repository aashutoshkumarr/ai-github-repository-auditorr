from typing import Any, Callable, Dict, List, Optional
from .routing import APIRouter

class FastAPI:
    """High-performance async web framework application."""
    def __init__(
        self,
        title: str = "FastAPI",
        description: str = "",
        version: str = "0.1.0",
        docs_url: Optional[str] = "/docs",
        redoc_url: Optional[str] = "/redoc"
    ):
        self.title = title
        self.description = description
        self.version = version
        self.docs_url = docs_url
        self.redoc_url = redoc_url
        self.router = APIRouter()
        self.middleware_stack: List[Callable] = []

    def get(self, path: str, **kwargs):
        return self.router.get(path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.router.post(path, **kwargs)

    def include_router(self, router: APIRouter, prefix: str = ""):
        self.router.include_router(router, prefix=prefix)
