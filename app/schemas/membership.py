import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.membership import MembershipStatus


class JoinGymRequest(BaseModel):
    gym_id: uuid.UUID


class GymResponse(BaseModel):
    id: uuid.UUID
    name: str
    city: str


class MembershipResponse(BaseModel):
    id: uuid.UUID
    status: MembershipStatus
    joined_at: datetime
    gym: GymResponse
