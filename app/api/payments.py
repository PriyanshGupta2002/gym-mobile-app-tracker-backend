import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.payment import (
    CreateMembershipOrderRequest,
    CreateMembershipOrderResponse,
)
from app.services.payment import create_membership_order

from app.core.config import settings

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


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
