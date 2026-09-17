import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.membership_plan import (
    MembershipPlanCreate,
    MembershipPlanResponse,
    MembershipPlanUpdate,
)
from app.services.membership_plan import (
    create_membership_plan,
    delete_membership_plan,
    get_membership_plan,
    get_membership_plans,
    update_membership_plan,
    get_available_membership_plans,
)

router = APIRouter(
    prefix="/membership-plans",
    tags=["Membership Plans"],
)


@router.post(
    "/{gym_id}",
    response_model=MembershipPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_membership_plan_endpoint(
    gym_id: uuid.UUID,
    request: MembershipPlanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_membership_plan(
        db=db,
        current_user=current_user,
        gym_id=gym_id,
        data=request,
    )


@router.get(
    "/{gym_id}",
    response_model=list[MembershipPlanResponse],
)
async def get_membership_plans_endpoint(
    gym_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_membership_plans(
        db=db,
        current_user=current_user,
        gym_id=gym_id,
    )


@router.get(
    "/{gym_id}/available",
    response_model=list[MembershipPlanResponse],
)
async def get_available_membership_plans_endpoint(
    gym_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_available_membership_plans(
        db=db,
        current_user=current_user,
        gym_id=gym_id,
    )


@router.get(
    "/{gym_id}/{plan_id}",
    response_model=MembershipPlanResponse,
)
async def get_membership_plan_endpoint(
    gym_id: uuid.UUID,
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_membership_plan(
        db=db,
        current_user=current_user,
        gym_id=gym_id,
        plan_id=plan_id,
    )


@router.patch(
    "/{gym_id}/{plan_id}",
    response_model=MembershipPlanResponse,
)
async def update_membership_plan_endpoint(
    gym_id: uuid.UUID,
    plan_id: uuid.UUID,
    request: MembershipPlanUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_membership_plan(
        db=db,
        current_user=current_user,
        gym_id=gym_id,
        plan_id=plan_id,
        data=request,
    )


@router.delete(
    "/{gym_id}/{plan_id}",
    response_model=MembershipPlanResponse,
)
async def delete_membership_plan_endpoint(
    gym_id: uuid.UUID,
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await delete_membership_plan(
        db=db,
        current_user=current_user,
        gym_id=gym_id,
        plan_id=plan_id,
    )
