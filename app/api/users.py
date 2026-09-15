from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.membership import Membership
from app.models.gym import Gym
from app.schemas.user import (
    UpdateProfileRequest,
    UpdateProfileResponse,
    CurrentUserResponse,
    MembershipResponse,
    GymResponse,
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=CurrentUserResponse,
)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # -----------------------------------------
    # Get active membership for member
    # -----------------------------------------
    print("current_user", current_user)
    result = await db.execute(
        select(Membership)
        .options(selectinload(Membership.gym))
        .where(
            Membership.user_id == current_user.id,
            Membership.status == "ACTIVE",
        )
        .order_by(Membership.joined_at.desc())
    )

    membership = result.scalars().first()

    membership_response = None

    if membership:
        membership_response = MembershipResponse(
            id=membership.id,
            status=membership.status,
            joined_at=membership.joined_at,
            gym=GymResponse(
                id=membership.gym.id,
                name=membership.gym.name,
                city=membership.gym.city,
            ),
        )

    # -----------------------------------------
    # Get ALL gyms owned by this user
    # -----------------------------------------

    gym_result = await db.execute(
        select(Gym)
        .where(Gym.owner_id == current_user.id)
        .order_by(Gym.created_at.desc())
    )

    gyms = gym_result.scalars().all()

    gym_response = [
        GymResponse(
            id=gym.id,
            name=gym.name,
            city=gym.city,
        )
        for gym in gyms
    ]

    # -----------------------------------------
    # Return current user
    # -----------------------------------------

    return CurrentUserResponse(
        id=current_user.id,
        phone=current_user.phone,
        name=current_user.name,
        role=current_user.role,
        membership=membership_response,
        gym=gym_response,
    )


@router.patch(
    "/me",
    response_model=UpdateProfileResponse,
)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.name = request.name.strip()

    await db.commit()
    await db.refresh(current_user)

    return UpdateProfileResponse(
        name=current_user.name,
    )
