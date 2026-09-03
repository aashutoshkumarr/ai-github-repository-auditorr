from typing import Any, Callable, Dict, List, Optional

class APIRoute:
    def __init__(self, path: str, endpoint: Callable, methods: List[str]):
        self.path = path
        self.endpoint = endpoint
        self.methods = methods

class APIRouter:
    """Modular route collection with dependency injection support."""
    def __init__(self, prefix: str = "", tags: Optional[List[str]] = None):
        self.prefix = prefix
        self.tags = tags or []
        self.routes: List[APIRoute] = []

    def get(self, path: str, **kwargs):
        def decorator(func: Callable):
            self.routes.append(APIRoute(self.prefix + path, func, ["GET"]))
            return func
        return decorator

    def post(self, path: str, **kwargs):
        def decorator(func: Callable):
            self.routes.append(APIRoute(self.prefix + path, func, ["POST"]))
            return func
        return decorator

    def include_router(self, router: 'APIRouter', prefix: str = ""):
        for route in router.routes:
            self.routes.append(APIRoute(prefix + route.path, route.endpoint, route.methods))
