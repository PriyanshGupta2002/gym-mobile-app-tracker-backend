from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.membership import MembershipStatus


class CreateGymRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    city: str = Field(min_length=1, max_length=100)


class GymResponse(BaseModel):
    id: UUID
    name: str
    city: str


class GymMemberResponse(BaseModel):
    id: UUID
    name: str | None
    phone: str

    class Config:
        from_attributes = True


class GymMemberWithMembershipResponse(BaseModel):
    id: UUID
    status: MembershipStatus
    joined_at: datetime
    member: GymMemberResponse


class GymMembersResponse(BaseModel):
    gym_id: UUID
    total: int
    members: list[GymMemberWithMembershipResponse]
    today_attendance: int
