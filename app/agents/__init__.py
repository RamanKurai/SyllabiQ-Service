"""
agents package shim.

Expose the legacy names so older imports like `from app.agents import IntentAgent`
continue to work while keeping the implementation inside `app/agents/core.py`.
"""
from .core import IntentAgent, RetrievalAgent, GenerationAgent, ValidationAgent

__all__ = ["IntentAgent", "RetrievalAgent", "GenerationAgent", "ValidationAgent"]

