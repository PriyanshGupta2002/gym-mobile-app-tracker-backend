from uuid import UUID

from pydantic import BaseModel, Field
from decimal import Decimal

from app.models.user import UserRole
from datetime import datetime
from app.schemas.membership_plan import MembershipPlanResponse
from app.models.membership import PaymentMethod


class GymResponse(BaseModel):
    id: UUID
    name: str
    city: str


class MembershipResponse(BaseModel):
    id: UUID
    status: str
    joined_at: datetime

    gym: GymResponse

    # Membership plan
    plan: MembershipPlanResponse | None = None

    # Purchase details
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    payment_method: PaymentMethod | None = None
    amount_paid: Decimal | None = None


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
