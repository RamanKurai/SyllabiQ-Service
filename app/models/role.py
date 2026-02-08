from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User  # pragma: no cover


class RoleAssignment(SQLModel, table=True):
    """
    Assigns a Role to a User, optionally scoped to an Institution.
    """
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    role_id: Optional[int] = Field(default=None, foreign_key="role.id", primary_key=True)
    institution_id: Optional[int] = Field(default=None, foreign_key="institution.id", index=True)
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class Role(SQLModel, table=True):
    """
    Canonical role (e.g. SuperAdmin, InstitutionAdmin, Principal, Teacher, Student).
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, nullable=False, unique=True)
    description: Optional[str] = None
    is_system: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # users via RoleAssignment
    users: List["User"] = Relationship(back_populates="roles", link_model=RoleAssignment)

