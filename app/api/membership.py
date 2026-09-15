from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.membership import (
    GymResponse,
    JoinGymRequest,
    MembershipResponse,
)
from app.services.membership import join_gym

router = APIRouter(
    prefix="/memberships",
    tags=["Memberships"],
)


@router.post(
    "/join",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
)
async def join_gym_endpoint(
    request: JoinGymRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    membership = await join_gym(
        db=db,
        current_user=current_user,
        gym_id=request.gym_id,
    )

    return MembershipResponse(
        id=membership.id,
        status=membership.status,
        joined_at=membership.joined_at,
        gym=GymResponse(
            id=membership.gym.id,
            name=membership.gym.name,
            city=membership.gym.city,
        ),
    )
