import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class QueryLog(SQLModel, table=True):
    __tablename__ = "querylog"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    subject_id: Optional[str] = Field(default=None, index=True)
    topic_id: Optional[str] = Field(default=None)
    intent: str = Field(default="qa")
    workflow: Optional[str] = Field(default=None)
    llm_provider: str = Field(default="none")
    chunks_retrieved: int = Field(default=0)
    response_time_ms: int = Field(default=0)
    success: bool = Field(default=True)
    error_type: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
