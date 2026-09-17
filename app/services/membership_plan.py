import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gym import Gym
from app.models.membership_plan import MembershipPlan
from app.models.user import User, UserRole
from app.schemas.membership_plan import (
    MembershipPlanCreate,
    MembershipPlanUpdate,
)
from app.models.membership import Membership, MembershipStatus


async def verify_gym_owner(
    db: AsyncSession,
    gym_id: uuid.UUID,
    current_user: User,
) -> Gym:

    if current_user.role != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only gym owners can manage membership plans.",
        )

    result = await db.execute(
        select(Gym).where(
            Gym.id == gym_id,
            Gym.owner_id == current_user.id,
        )
    )

    gym = result.scalar_one_or_none()

    if gym is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gym not found.",
        )

    return gym


async def create_membership_plan(
    db: AsyncSession,
    current_user: User,
    gym_id: uuid.UUID,
    data: MembershipPlanCreate,
) -> MembershipPlan:

    await verify_gym_owner(
        db=db,
        gym_id=gym_id,
        current_user=current_user,
    )

    plan = MembershipPlan(
        gym_id=gym_id,
        name=data.name.strip(),
        duration_days=data.duration_days,
        price=data.price,
        is_active=True,
    )

    db.add(plan)

    await db.commit()
    await db.refresh(plan)

    return plan


async def get_membership_plans(
    db: AsyncSession,
    current_user: User,
    gym_id: uuid.UUID,
) -> list[MembershipPlan]:

    await verify_gym_owner(
        db=db,
        gym_id=gym_id,
        current_user=current_user,
    )

    result = await db.execute(
        select(MembershipPlan)
        .where(
            MembershipPlan.gym_id == gym_id,
            MembershipPlan.is_active.is_(True),
        )
        .order_by(MembershipPlan.created_at.desc())
    )

    return list(result.scalars().all())


async def get_membership_plan(
    db: AsyncSession,
    current_user: User,
    gym_id: uuid.UUID,
    plan_id: uuid.UUID,
) -> MembershipPlan:

    await verify_gym_owner(
        db=db,
        gym_id=gym_id,
        current_user=current_user,
    )

    result = await db.execute(
        select(MembershipPlan).where(
            MembershipPlan.id == plan_id,
            MembershipPlan.gym_id == gym_id,
        )
    )

    plan = result.scalar_one_or_none()

    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership plan not found.",
        )

    return plan


async def update_membership_plan(
    db: AsyncSession,
    current_user: User,
    gym_id: uuid.UUID,
    plan_id: uuid.UUID,
    data: MembershipPlanUpdate,
) -> MembershipPlan:

    plan = await get_membership_plan(
        db=db,
        current_user=current_user,
        gym_id=gym_id,
        plan_id=plan_id,
    )

    update_data = data.model_dump(
        exclude_unset=True,
    )

    if "name" in update_data and update_data["name"] is not None:
        update_data["name"] = update_data["name"].strip()

    for field, value in update_data.items():
        setattr(plan, field, value)

    await db.commit()
    await db.refresh(plan)

    return plan


async def delete_membership_plan(
    db: AsyncSession,
    current_user: User,
    gym_id: uuid.UUID,
    plan_id: uuid.UUID,
) -> MembershipPlan:

    plan = await get_membership_plan(
        db=db,
        current_user=current_user,
        gym_id=gym_id,
        plan_id=plan_id,
    )

    if not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Membership plan is already inactive.",
        )

    plan.is_active = False

    await db.commit()
    await db.refresh(plan)

    return plan


async def get_available_membership_plans(
    db: AsyncSession, current_user: User, gym_id: uuid.UUID
):
    if current_user.role != UserRole.MEMBER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only gym members can view available membership plans.",
        )

    membership_result = await db.execute(
        select(Membership).where(
            Membership.user_id == current_user.id,
            Membership.gym_id == gym_id,
            Membership.status.in_(
                [
                    MembershipStatus.PENDING,
                    MembershipStatus.ACTIVE,
                ]
            ),
        )
    )
    membership = membership_result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this gym",
        )
    result = await db.execute(
        select(MembershipPlan)
        .where(
            MembershipPlan.gym_id == gym_id,
            MembershipPlan.is_active.is_(True),
        )
        .order_by(MembershipPlan.created_at.desc())
    )

    return list(result.scalars().all())
