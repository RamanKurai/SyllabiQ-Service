from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    institution_id: Optional[int] = None


class UserRead(BaseModel):
    # allow creating this Pydantic model from ORM objects / attributes
    model_config = ConfigDict(from_attributes=True)
    id: int
    # use plain string here to avoid strict validation on reserved/internal domains
    email: str
    full_name: Optional[str] = None
    is_active: bool
    status: Optional[str] = None
    institution_id: Optional[int] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

    # optional roles returned at login to allow immediate client-side routing
    roles: Optional[list[str]] = None


class LoginPayload(BaseModel):
    # allow non-strict emails for login (admins may use non-public domains)
    email: str
    password: str


class UserProfile(UserRead):
    roles: Optional[list[str]] = None

