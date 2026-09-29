from datetime import datetime
from typing import Annotated

from pydantic import EmailStr, StringConstraints, field_validator

from app.schemas.base import CamelModel

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class RegisterRequest(CamelModel):
    name: Name
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes long")
        if not any(c.islower() for c in value):
            raise ValueError("Password must contain a lowercase letter")
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain an uppercase letter")
        if not any(c.isdigit() for c in value):
            raise ValueError("Password must contain a digit")
        return value


class LoginRequest(CamelModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        return value.lower()


class RegisterResponse(CamelModel):
    id: int
    name: str
    email: str
    account_number: str
    created_at: datetime


class TokenResponse(CamelModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(CamelModel):
    message: str
