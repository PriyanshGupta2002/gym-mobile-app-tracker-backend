import uuid

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class MembershipPlanCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )

    duration_days: int = Field(
        gt=0,
    )

    price: Decimal = Field(
        ge=0,
    )


class MembershipPlanUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    duration_days: int | None = Field(
        default=None,
        gt=0,
    )

    price: Decimal | None = Field(
        default=None,
        ge=0,
    )

    is_active: bool | None = None


class MembershipPlanResponse(BaseModel):
    id: uuid.UUID
    gym_id: uuid.UUID
    name: str
    duration_days: int
    price: Decimal
    is_active: bool
    created_at: datetime
