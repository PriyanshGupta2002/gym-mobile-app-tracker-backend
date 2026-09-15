from uuid import UUID

from pydantic import BaseModel, Field

from app.models.user import UserRole
from datetime import datetime


class GymResponse(BaseModel):
    id: UUID
    name: str
    city: str


class MembershipResponse(BaseModel):
    id: UUID
    status: str
    joined_at: datetime
    gym: GymResponse


class CurrentUserResponse(BaseModel):
    id: UUID
    phone: str
    name: str | None
    role: UserRole
    membership: MembershipResponse | None = None
    gym: list[GymResponse] | None = None


class UpdateProfileRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )


class UpdateProfileResponse(BaseModel):
    name: str
