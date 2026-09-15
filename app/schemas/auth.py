from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


class UserRole(str, Enum):
    MEMBER = "member"
    OWNER = "owner"


class SendOTPRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=15)


class SendOTPResponse(BaseModel):
    message: str


class VerifyOTPRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=15)
    otp: str = Field(min_length=6, max_length=6)
    role: UserRole


class AuthUserResponse(BaseModel):
    id: UUID
    phone: str
    role: UserRole


class VerifyOTPResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_new_user: bool
    user: AuthUserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
