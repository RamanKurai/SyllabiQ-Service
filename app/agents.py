"""
Compatibility shim: re-export agents from the new package location.
Keep this file so older imports like `from app.agents import IntentAgent` continue to work.
"""
from app.agents.core import IntentAgent, RetrievalAgent, GenerationAgent, ValidationAgent

__all__ = ["IntentAgent", "RetrievalAgent", "GenerationAgent", "ValidationAgent"]

