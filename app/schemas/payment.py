from uuid import UUID

from decimal import Decimal

from pydantic import BaseModel
from app.models.payment import PaymentStatus
from datetime import datetime


class CreateMembershipOrderRequest(BaseModel):
    gym_id: UUID
    plan_id: UUID


class CreateMembershipOrderResponse(BaseModel):
    payment_id: UUID
    razorpay_order_id: str
    razorpay_key_id: str
    amount: Decimal
    currency: str


class VerifyMembershipPaymentRequest(BaseModel):
    payment_id: UUID
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class OwnerPaymentMemberResponse(BaseModel):
    id: UUID
    name: str | None
    phone: str


class OwnerPaymentPlanResponse(BaseModel):
    id: UUID
    name: str


class OwnerPaymentResponse(BaseModel):
    id: UUID
    amount: Decimal
    currency: str
    status: PaymentStatus
    razorpay_payment_id: str | None
    paid_at: datetime | None
    created_at: datetime

    member: OwnerPaymentMemberResponse
    plan: OwnerPaymentPlanResponse


class GymPaymentsResponse(BaseModel):
    gym_id: UUID
    total_collected: Decimal
    today_collected: Decimal
    total_payments: int
    payments: list[OwnerPaymentResponse]
