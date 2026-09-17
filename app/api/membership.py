from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.membership import (
    GymResponse,
    JoinGymRequest,
    MembershipResponse,
    MembershipPlanResponse,
    AssignMembershipPlanRequest,
)
from app.services.membership import join_gym, assign_membership_plan
from uuid import UUID

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


@router.patch(
    "/{gym_id}/{membership_id}/plan",
    response_model=MembershipResponse,
)
async def assign_membership_plan_endpoint(
    gym_id: UUID,
    membership_id: UUID,
    request: AssignMembershipPlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    membership = await assign_membership_plan(
        db=db,
        current_user=current_user,
        gym_id=gym_id,
        membership_id=membership_id,
        data=request,
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
        membership_plan=(
            MembershipPlanResponse(
                id=membership.membership_plan.id,
                name=membership.membership_plan.name,
                duration_days=membership.membership_plan.duration_days,
                price=membership.membership_plan.price,
            )
            if membership.membership_plan
            else None
        ),
        starts_at=membership.starts_at,
        expires_at=membership.expires_at,
        payment_method=membership.payment_method,
        amount_paid=membership.amount_paid,
    )
