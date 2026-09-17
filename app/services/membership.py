import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.gym import Gym
from app.models.membership import Membership, MembershipStatus
from app.models.user import User, UserRole

from datetime import datetime, timezone, timedelta
from app.models.membership_plan import MembershipPlan
from app.schemas.membership import AssignMembershipPlanRequest


async def join_gym(
    db: AsyncSession,
    current_user: User,
    gym_id: uuid.UUID,
) -> Membership:
    # Only members can join gyms.
    if current_user.role != UserRole.MEMBER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only members can join a gym.",
        )

    # Check that the gym exists.
    gym_result = await db.execute(select(Gym).where(Gym.id == gym_id))

    gym = gym_result.scalar_one_or_none()

    if gym is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gym not found.",
        )

    # Check if the user already has an active membership.
    membership_result = await db.execute(
        select(Membership).where(
            Membership.user_id == current_user.id,
            Membership.status == MembershipStatus.ACTIVE,
        )
    )

    existing_membership = membership_result.scalars().first()

    if existing_membership is not None:
        if existing_membership.gym_id == gym.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are already a member of this gym.",
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active gym membership.",
        )

    # Create the membership.
    membership = Membership(
        user_id=current_user.id,
        gym_id=gym.id,
        status=MembershipStatus.PENDING,
    )

    db.add(membership)

    await db.commit()

    # Reload the membership with its gym relationship.
    result = await db.execute(
        select(Membership)
        .options(selectinload(Membership.gym))
        .where(Membership.id == membership.id)
    )

    membership = result.scalar_one()

    return membership


async def assign_membership_plan(
    db: AsyncSession,
    current_user: User,
    gym_id: uuid.UUID,
    membership_id: uuid.UUID,
    data: AssignMembershipPlanRequest,
) -> Membership:

    # ---------------------------------------------------------
    # 1. Verify owner owns this gym
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # 2. Find membership belonging to this gym
    # ---------------------------------------------------------

    membership_result = await db.execute(
        select(Membership).where(
            Membership.id == membership_id,
            Membership.gym_id == gym_id,
        )
    )

    membership = membership_result.scalar_one_or_none()

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found.",
        )

    # ---------------------------------------------------------
    # 3. Verify membership plan belongs to same gym
    # ---------------------------------------------------------

    plan_result = await db.execute(
        select(MembershipPlan).where(
            MembershipPlan.id == data.membership_plan_id,
            MembershipPlan.gym_id == gym_id,
            MembershipPlan.is_active.is_(True),
        )
    )

    plan = plan_result.scalar_one_or_none()

    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership plan not found or inactive.",
        )

    # ---------------------------------------------------------
    # 4. Set membership purchase details
    # ---------------------------------------------------------

    starts_at = datetime.now(timezone.utc)

    expires_at = starts_at + timedelta(
        days=plan.duration_days,
    )

    membership.membership_plan_id = plan.id
    membership.starts_at = starts_at
    membership.expires_at = expires_at
    membership.payment_method = data.payment_method
    membership.amount_paid = data.amount_paid

    # ---------------------------------------------------------
    # 5. Membership becomes active
    # ---------------------------------------------------------

    membership.status = MembershipStatus.ACTIVE

    await db.commit()

    # ---------------------------------------------------------
    # 6. Reload relationships
    # ---------------------------------------------------------

    result = await db.execute(
        select(Membership)
        .options(
            selectinload(Membership.gym),
            selectinload(Membership.membership_plan),
        )
        .where(
            Membership.id == membership.id,
        )
    )

    return result.scalar_one()
