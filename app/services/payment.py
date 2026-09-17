import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import razorpay
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.config import settings
from app.models.membership import (
    Membership,
    MembershipStatus,
    PaymentMethod,
)
from app.models.membership_plan import MembershipPlan
from app.models.payment import Payment, PaymentStatus
from app.models.user import User, UserRole
from app.models.gym import Gym

razorpay_client = razorpay.Client(
    auth=(
        settings.RAZORPAY_KEY_ID,
        settings.RAZORPAY_KEY_SECRET,
    )
)


# =========================================================
# CREATE MEMBERSHIP ORDER
# =========================================================


async def create_membership_order(
    db: AsyncSession,
    current_user: User,
    gym_id: uuid.UUID,
    plan_id: uuid.UUID,
) -> Payment:
    # -----------------------------------------------------
    # Only members can purchase membership plans
    # -----------------------------------------------------
    if current_user.role != UserRole.MEMBER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only members can purchase membership plans.",
        )

    # -----------------------------------------------------
    # Get membership plan
    # -----------------------------------------------------
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

    # -----------------------------------------------------
    # Get the pending membership for this user + gym
    # -----------------------------------------------------
    membership_result = await db.execute(
        select(Membership).where(
            Membership.user_id == current_user.id,
            Membership.gym_id == gym_id,
            Membership.status == MembershipStatus.PENDING,
        )
    )

    membership = membership_result.scalar_one_or_none()

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending membership not found.",
        )

    # -----------------------------------------------------
    # Make sure this membership isn't already associated
    # with an active/pending payment
    # -----------------------------------------------------
    payment_result = await db.execute(
        select(Payment).where(
            Payment.membership_id == membership.id,
            Payment.status == PaymentStatus.CREATED,
        )
    )

    existing_payment = payment_result.scalar_one_or_none()

    if existing_payment:
        if existing_payment.membership_plan_id != plan.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have a pending payment for another membership plan.",
            )

        return existing_payment

    # -----------------------------------------------------
    # Validate plan price
    # -----------------------------------------------------
    amount = Decimal(plan.price)

    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Membership plan price must be greater than zero.",
        )

    # -----------------------------------------------------
    # Razorpay expects amount in paise
    # -----------------------------------------------------
    amount_in_paise = int(amount * 100)

    # -----------------------------------------------------
    # Create Razorpay order
    # -----------------------------------------------------
    razorpay_order = razorpay_client.order.create(
        {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": str(uuid.uuid4()),
            "notes": {
                "user_id": str(current_user.id),
                "gym_id": str(gym_id),
                "plan_id": str(plan_id),
                "membership_id": str(membership.id),
            },
        }
    )

    # -----------------------------------------------------
    # Create payment record
    # -----------------------------------------------------
    payment = Payment(
        user_id=current_user.id,
        gym_id=gym_id,
        membership_plan_id=plan.id,
        membership_id=membership.id,
        razorpay_order_id=razorpay_order["id"],
        amount=amount,
        currency="INR",
        status=PaymentStatus.CREATED,
    )

    db.add(payment)

    await db.commit()
    await db.refresh(payment)

    return payment


# =========================================================
# VERIFY MEMBERSHIP PAYMENT
# =========================================================


async def verify_membership_payment(
    db: AsyncSession,
    current_user: User,
    payment_id: uuid.UUID,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
) -> Payment:

    # -----------------------------------------------------
    # Only members can verify membership payments
    # -----------------------------------------------------

    if current_user.role != UserRole.MEMBER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only members can verify membership payments.",
        )

    # -----------------------------------------------------
    # Find payment belonging to current user
    # -----------------------------------------------------

    payment_result = await db.execute(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.user_id == current_user.id,
            Payment.razorpay_order_id == razorpay_order_id,
        )
    )

    payment = payment_result.scalar_one_or_none()

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    # -----------------------------------------------------
    # Idempotency
    #
    # If frontend calls verify twice after successful
    # payment, don't activate the membership twice.
    # -----------------------------------------------------

    if payment.status == PaymentStatus.PAID:
        return payment

    # -----------------------------------------------------
    # Payment must still be in CREATED state
    # -----------------------------------------------------

    if payment.status != PaymentStatus.CREATED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment cannot be verified in its current state.",
        )

    # -----------------------------------------------------
    # Verify Razorpay signature
    # -----------------------------------------------------

    try:
        razorpay_client.utility.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        )

    except razorpay.errors.SignatureVerificationError:
        payment.status = PaymentStatus.FAILED

        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed.",
        )

    # -----------------------------------------------------
    # Get the exact membership associated with payment
    # -----------------------------------------------------

    if payment.membership_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment is not associated with a membership.",
        )

    membership_result = await db.execute(
        select(Membership).where(
            Membership.id == payment.membership_id,
            Membership.user_id == current_user.id,
        )
    )

    membership = membership_result.scalar_one_or_none()

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found.",
        )

    # -----------------------------------------------------
    # Make sure this membership is still pending
    # -----------------------------------------------------

    if membership.status != MembershipStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Membership is not in a pending state.",
        )

    # -----------------------------------------------------
    # Get membership plan
    # -----------------------------------------------------

    plan_result = await db.execute(
        select(MembershipPlan).where(
            MembershipPlan.id == payment.membership_plan_id,
            MembershipPlan.gym_id == payment.gym_id,
        )
    )

    plan = plan_result.scalar_one_or_none()

    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership plan not found.",
        )

    # -----------------------------------------------------
    # Calculate membership dates
    # -----------------------------------------------------

    now = datetime.now(timezone.utc)

    starts_at = now
    expires_at = starts_at + timedelta(days=plan.duration_days)

    # -----------------------------------------------------
    # Update payment
    # -----------------------------------------------------

    payment.status = PaymentStatus.PAID
    payment.razorpay_payment_id = razorpay_payment_id
    payment.paid_at = now

    # -----------------------------------------------------
    # Activate membership
    # -----------------------------------------------------

    membership.status = MembershipStatus.ACTIVE
    membership.membership_plan_id = plan.id
    membership.starts_at = starts_at
    membership.expires_at = expires_at
    membership.amount_paid = payment.amount

    # -----------------------------------------------------
    # Payment method
    #
    # Razorpay can support multiple payment methods.
    # We're keeping OTHER for now because the checkout
    # response we're using doesn't determine the method
    # here.
    # -----------------------------------------------------

    membership.payment_method = PaymentMethod.OTHER

    # -----------------------------------------------------
    # Link payment to membership
    # -----------------------------------------------------

    payment.membership_id = membership.id

    # -----------------------------------------------------
    # Save everything atomically
    # -----------------------------------------------------

    await db.commit()
    await db.refresh(payment)

    return payment


async def get_gym_payments(
    db: AsyncSession,
    current_user: User,
    gym_id: UUID,
):
    # -----------------------------------------------------
    # 1. Only owners can view gym payments
    # -----------------------------------------------------

    if current_user.role != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only gym owners can view payments.",
        )

    # -----------------------------------------------------
    # 2. Verify gym belongs to current owner
    # -----------------------------------------------------

    gym_result = await db.execute(
        select(Gym).where(
            Gym.id == gym_id,
            Gym.owner_id == current_user.id,
        )
    )

    gym = gym_result.scalar_one_or_none()

    if gym is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gym not found.",
        )

    # -----------------------------------------------------
    # 3. Get payments
    # -----------------------------------------------------

    result = await db.execute(
        select(Payment, User, MembershipPlan)
        .join(User, Payment.user_id == User.id)
        .join(
            MembershipPlan,
            Payment.membership_plan_id == MembershipPlan.id,
        )
        .where(
            Payment.gym_id == gym_id,
        )
        .order_by(Payment.created_at.desc())
    )

    rows = result.all()

    # -----------------------------------------------------
    # 4. Calculate total collected
    # -----------------------------------------------------

    total_collected_result = await db.execute(
        select(
            func.coalesce(
                func.sum(Payment.amount),
                0,
            )
        ).where(
            Payment.gym_id == gym_id,
            Payment.status == PaymentStatus.PAID,
        )
    )

    total_collected = total_collected_result.scalar_one()

    # -----------------------------------------------------
    # 5. Calculate today's collection
    # -----------------------------------------------------

    now = datetime.now(timezone.utc)

    start_of_day = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    end_of_day = start_of_day + timedelta(days=1)

    today_collected_result = await db.execute(
        select(
            func.coalesce(
                func.sum(Payment.amount),
                0,
            )
        ).where(
            Payment.gym_id == gym_id,
            Payment.status == PaymentStatus.PAID,
            Payment.paid_at >= start_of_day,
            Payment.paid_at < end_of_day,
        )
    )

    today_collected = today_collected_result.scalar_one()

    # -----------------------------------------------------
    # 6. Build payment response
    # -----------------------------------------------------

    payments = []

    for payment, user, plan in rows:
        payments.append(
            {
                "id": payment.id,
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.status,
                "razorpay_payment_id": payment.razorpay_payment_id,
                "paid_at": payment.paid_at,
                "created_at": payment.created_at,
                "member": {
                    "id": user.id,
                    "name": user.name,
                    "phone": user.phone,
                },
                "plan": {
                    "id": plan.id,
                    "name": plan.name,
                },
            }
        )

    return {
        "gym_id": gym_id,
        "total_collected": Decimal(total_collected),
        "today_collected": Decimal(today_collected),
        "total_payments": len(payments),
        "payments": payments,
    }
