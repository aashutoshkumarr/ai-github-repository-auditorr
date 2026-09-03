import pytest
from fastapi import FastAPI, HTTPException

def test_fastapi_initialization():
    app = FastAPI(title="Benchmark API", version="1.0.0")
    assert app.title == "Benchmark API"
    assert app.version == "1.0.0"

def test_route_registration():
    app = FastAPI()
    @app.get("/health")
    def health():
        return {"status": "ok"}
    assert len(app.router.routes) == 1
    assert app.router.routes[0].path == "/health"

def test_http_exception():
    exc = HTTPException(status_code=404, detail="Not found")
    assert exc.status_code == 404
    assert exc.detail == "Not found"
