from pydantic import BaseModel, EmailStr
from typing import Optional
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    institution_id: Optional[int] = None


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    status: Optional[str] = None
    institution_id: Optional[int] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

