"""
CDR API Layer

FastAPI interface.
"""

from cdr.api.routes import create_app, router

__all__ = ["create_app", "router"]
