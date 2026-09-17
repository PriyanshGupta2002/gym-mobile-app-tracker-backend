import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

from app.schemas.payment import (
    CreateMembershipOrderRequest,
    CreateMembershipOrderResponse,
    VerifyMembershipPaymentRequest,
    GymPaymentsResponse,
)

from app.services.payment import (
    create_membership_order,
    verify_membership_payment,
    get_gym_payments,
)

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


# =========================================================
# CREATE MEMBERSHIP ORDER
# =========================================================


@router.post(
    "/membership/order",
    response_model=CreateMembershipOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_membership_order_endpoint(
    request: CreateMembershipOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    payment = await create_membership_order(
        db=db,
        current_user=current_user,
        gym_id=request.gym_id,
        plan_id=request.plan_id,
    )

    return CreateMembershipOrderResponse(
        payment_id=payment.id,
        razorpay_order_id=payment.razorpay_order_id,
        razorpay_key_id=settings.RAZORPAY_KEY_ID,
        amount=payment.amount,
        currency=payment.currency,
    )


# =========================================================
# VERIFY MEMBERSHIP PAYMENT
# =========================================================


@router.post(
    "/membership/verify",
    status_code=status.HTTP_200_OK,
)
async def verify_membership_payment_endpoint(
    request: VerifyMembershipPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    payment = await verify_membership_payment(
        db=db,
        current_user=current_user,
        payment_id=request.payment_id,
        razorpay_order_id=request.razorpay_order_id,
        razorpay_payment_id=request.razorpay_payment_id,
        razorpay_signature=request.razorpay_signature,
    )

    return {
        "message": "Membership payment verified successfully.",
        "payment_id": payment.id,
        "status": payment.status,
    }


@router.get(
    "/gyms/{gym_id}",
    response_model=GymPaymentsResponse,
)
async def get_gym_payments_endpoint(
    gym_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_gym_payments(
        db=db,
        current_user=current_user,
        gym_id=gym_id,
    )
