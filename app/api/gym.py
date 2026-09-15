from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.gym import (
    CreateGymRequest,
    GymResponse,
    GymMemberResponse,
    GymMembersResponse,
    GymMemberWithMembershipResponse,
)
from app.services.gym import create_gym, get_gym_by_owner, get_gym_members

router = APIRouter(
    prefix="/gyms",
    tags=["Gyms"],
)


@router.post(
    "",
    response_model=GymResponse,
)
async def create_gym_endpoint(
    request: CreateGymRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    gym = await create_gym(
        db=db,
        current_user=current_user,
        name=request.name,
        city=request.city,
    )

    return GymResponse(
        id=gym.id,
        name=gym.name,
        city=gym.city,
    )


@router.get(
    "/{gym_id}/members",
    response_model=GymMembersResponse,
)
async def get_members_for_gym(
    gym_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # ---------------------------------------------------------
    # 1. Verify that the gym belongs to the current owner
    # ---------------------------------------------------------

    gym = await get_gym_by_owner(
        db=db,
        gym_id=gym_id,
        owner_id=current_user.id,
    )

    if gym is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gym not found",
        )

    # ---------------------------------------------------------
    # 2. Get memberships + today's attendance
    # ---------------------------------------------------------

    memberships, today_attendance = await get_gym_members(
        db=db,
        gym_id=gym_id,
    )

    # ---------------------------------------------------------
    # 3. Build member response
    # ---------------------------------------------------------

    members = [
        GymMemberWithMembershipResponse(
            id=membership.id,
            status=membership.status,
            joined_at=membership.joined_at,
            member=membership.user,
        )
        for membership in memberships
    ]

    # ---------------------------------------------------------
    # 4. Return response
    # ---------------------------------------------------------

    return GymMembersResponse(
        gym_id=gym_id,
        total=len(members),
        today_attendance=today_attendance,
        members=members,
    )
