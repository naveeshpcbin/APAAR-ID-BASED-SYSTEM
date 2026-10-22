from typing import Optional
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str
    full_name: str
    institution_id: Optional[int] = None
    institution_name: Optional[str] = None
    aicte_id: Optional[str] = None

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    institution_id: Optional[int] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    institution_id: Optional[int] = None
    institution_name: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True
