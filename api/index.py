"""Vercel entrypoint that exposes the WSGI app."""
from main import app

__all__ = ["app"]
