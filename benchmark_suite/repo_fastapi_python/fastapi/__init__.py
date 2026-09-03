"""FastAPI framework entrypoint."""
from .applications import FastAPI
from .routing import APIRouter
from .exceptions import HTTPException

__version__ = "0.115.0"
__all__ = ["FastAPI", "APIRouter", "HTTPException"]
