import uuid

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.membership import MembershipStatus, PaymentMethod


class JoinGymRequest(BaseModel):
    gym_id: uuid.UUID


class GymResponse(BaseModel):
    id: uuid.UUID
    name: str
    city: str


class MembershipPlanResponse(BaseModel):
    id: uuid.UUID
    name: str
    duration_days: int
    price: Decimal


class AssignMembershipPlanRequest(BaseModel):
    membership_plan_id: uuid.UUID

    payment_method: PaymentMethod

    amount_paid: Decimal = Field(
        ge=0,
    )


class MembershipResponse(BaseModel):
    id: uuid.UUID
    status: MembershipStatus
    joined_at: datetime

    gym: GymResponse

    membership_plan: MembershipPlanResponse | None = None

    starts_at: datetime | None = None
    expires_at: datetime | None = None

    payment_method: PaymentMethod | None = None
    amount_paid: Decimal | None = None
