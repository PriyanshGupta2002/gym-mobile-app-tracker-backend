import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.gym import Gym
from app.models.membership import Membership, MembershipStatus
from app.models.user import User, UserRole


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
        status=MembershipStatus.ACTIVE,
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
