import uuid

from decimal import Decimal

from pydantic import BaseModel


class CreateMembershipOrderRequest(BaseModel):
    gym_id: uuid.UUID
    plan_id: uuid.UUID


class CreateMembershipOrderResponse(BaseModel):
    payment_id: uuid.UUID
    razorpay_order_id: str
    razorpay_key_id: str
    amount: Decimal
    currency: str


class VerifyMembershipPaymentRequest(BaseModel):
    payment_id: uuid.UUID
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
