from datetime import date, datetime

from pydantic import BaseModel, EmailStr

from src.schemas.user import UserResponse


class ContactModel(BaseModel):
    name: str
    surname: str
    email: EmailStr
    phone: str
    birthday: datetime


class ContactResponse(BaseModel):
    id: int = 1
    name: str
    surname: str
    email: EmailStr
    phone: str
    birthday: date
    created_at: datetime | None
    updated_at: datetime | None
    user: UserResponse | None

    class Config:
        from_attributes = True
