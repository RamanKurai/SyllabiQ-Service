from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class Institution(SQLModel, table=True):
    """
    Represents a university/college/school tenant.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, nullable=False, unique=True)
    slug: Optional[str] = Field(index=True, nullable=False, unique=True)
    type: Optional[str] = Field(default="college")
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    users: List["User"] = Relationship(back_populates="institution")

