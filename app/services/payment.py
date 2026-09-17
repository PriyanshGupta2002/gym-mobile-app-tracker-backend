import uuid

from decimal import Decimal

import razorpay

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.membership_plan import MembershipPlan
from app.models.membership import Membership, MembershipStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User, UserRole

razorpay_client = razorpay.Client(
    auth=(
        settings.RAZORPAY_KEY_ID,
        settings.RAZORPAY_KEY_SECRET,
    )
)


async def create_membership_order(
    db: AsyncSession,
    current_user: User,
    gym_id: uuid.UUID,
    plan_id: uuid.UUID,
) -> Payment:

    if current_user.role != UserRole.MEMBER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only members can purchase membership plans.",
        )

    result = await db.execute(
        select(MembershipPlan).where(
            MembershipPlan.id == plan_id,
            MembershipPlan.gym_id == gym_id,
            MembershipPlan.is_active.is_(True),
        )
    )

    plan = result.scalar_one_or_none()

    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership plan not found.",
        )

    amount = Decimal(plan.price)

    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Membership plan price must be greater than zero.",
        )

    # Razorpay expects amount in paise.
    amount_in_paise = int(amount * 100)

    razorpay_order = razorpay_client.order.create(
        {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": str(uuid.uuid4()),
            "notes": {
                "user_id": str(current_user.id),
                "gym_id": str(gym_id),
                "plan_id": str(plan_id),
            },
        }
    )

    payment = Payment(
        user_id=current_user.id,
        gym_id=gym_id,
        membership_plan_id=plan.id,
        razorpay_order_id=razorpay_order["id"],
        amount=amount,
        currency="INR",
        status=PaymentStatus.CREATED,
    )

    db.add(payment)

    await db.commit()
    await db.refresh(payment)

    return payment
