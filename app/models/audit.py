from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, Column, JSON


class AuditLog(SQLModel, table=True):
    """
    Simple audit log for admin actions.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, index=True)
    action: str
    entity: Optional[str] = None
    entity_id: Optional[str] = None
    details: Optional[str] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

