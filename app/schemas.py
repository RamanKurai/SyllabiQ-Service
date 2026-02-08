"""
Compatibility shim: re-export schema models from the new package location.
Keep this file so imports like `from app.schemas import QueryRequest` continue to work.
"""
from app.schemas import QueryRequest, QueryResponse, Citation  # noqa: F401

