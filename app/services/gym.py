from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.gym import Gym
from app.models.user import User, UserRole
from app.models.membership import Membership
from app.models.attendance import Attendance
from datetime import datetime, timezone, timedelta


async def create_gym(
    db: AsyncSession,
    current_user: User,
    name: str,
    city: str,
) -> Gym:
    if current_user.role != UserRole.OWNER:
        raise HTTPException(
            status_code=403,
            detail="Only gym owners can create a gym.",
        )

    gym = Gym(
        owner_id=current_user.id,
        name=name.strip(),
        city=city.strip(),
    )

    db.add(gym)

    await db.commit()
    await db.refresh(gym)

    return gym


async def get_gym_by_owner(
    db: AsyncSession,
    gym_id: UUID,
    owner_id: UUID,
) -> Gym | None:
    result = await db.execute(
        select(Gym).where(
            Gym.id == gym_id,
            Gym.owner_id == owner_id,
        )
    )

    return result.scalar_one_or_none()


async def get_gym_members(
    db: AsyncSession,
    gym_id: UUID,
):
    # ---------------------------------------------------------
    # 1. Get memberships for this gym
    # ---------------------------------------------------------

    result = await db.execute(
        select(Membership)
        .options(
            selectinload(Membership.user),
        )
        .where(
            Membership.gym_id == gym_id,
        )
        .order_by(Membership.joined_at.desc())
    )

    memberships = result.scalars().all()

    # ---------------------------------------------------------
    # 2. Calculate today's attendance
    # ---------------------------------------------------------

    now = datetime.now(timezone.utc)

    today_start = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    tomorrow_start = today_start + timedelta(days=1)

    attendance_result = await db.execute(
        select(func.count(Attendance.id)).where(
            Attendance.gym_id == gym_id,
            Attendance.checked_in_at >= today_start,
            Attendance.checked_in_at < tomorrow_start,
        )
    )

    today_attendance = attendance_result.scalar_one()

    return memberships, today_attendance


async def update_gym(
    db: AsyncSession,
    gym_id: UUID,
    owner_id: UUID,
    name: str,
    city: str,
) -> Gym:
    gym = await get_gym_by_owner(
        db=db,
        gym_id=gym_id,
        owner_id=owner_id,
    )

    if gym is None:
        raise HTTPException(
            status_code=404,
            detail="Gym not found",
        )

    gym.name = name.strip()
    gym.city = city.strip()

    await db.commit()
    await db.refresh(gym)

    return gym
