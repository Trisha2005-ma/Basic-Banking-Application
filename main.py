"""Root entry point for running the API with `uvicorn main:app --reload`."""

from app.main import app

__all__ = ["app"]