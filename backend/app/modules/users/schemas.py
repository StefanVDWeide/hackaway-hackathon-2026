from pydantic import EmailStr

from app.common.schemas.base import BaseSchema, CreateSchema, ReadSchema


class UserRegister(CreateSchema):
    email: EmailStr
    password: str
    display_name: str
    latitude: float | None = None
    longitude: float | None = None


class UserLogin(BaseSchema):
    email: EmailStr
    password: str


class UserRead(ReadSchema):
    email: str
    display_name: str
    latitude: float | None
    longitude: float | None
    is_active: bool
    is_verified: bool


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
