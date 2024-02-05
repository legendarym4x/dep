from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class UserModel(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=10)


class UserResponse(BaseModel):
    id: int = 1
    username: str
    email: EmailStr
    avatar: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class RequestEmail(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    reset_password_token: str
    new_password: str
    confirm_password: str
