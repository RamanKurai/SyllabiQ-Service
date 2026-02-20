from datetime import datetime
from enum import Enum
from typing import List, Optional
import uuid

from sqlmodel import Field, Relationship, SQLModel
from app.models.role import Role, RoleAssignment
from app.models.institution import Institution


class UserStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    denied = "denied"
    suspended = "suspended"


class User(SQLModel, table=True):
    """
    Enhanced User model with RBAC relationship to `Role` and multi-tenant support.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, nullable=False, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Each user may belong to one institution (nullable for system users)
    institution_id: Optional[int] = Field(default=None, foreign_key="institution.id", index=True)
    # Students bind to a department within their institution
    department_id: Optional[uuid.UUID] = Field(default=None, foreign_key="department.department_id", index=True)
    status: UserStatus = Field(default=UserStatus.pending, index=True)

    institution: Optional[Institution] = Relationship(back_populates="users")
    roles: List[Role] = Relationship(back_populates="users", link_model=RoleAssignment)

