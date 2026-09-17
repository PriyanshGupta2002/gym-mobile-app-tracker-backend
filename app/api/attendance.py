from fastapi import APIRouter, Depends, Query

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, date
from app.db.session import get_db
from app.schemas.attendance import (
    CheckInRequest,
    CheckInResponse,
    AttendanceSummaryResponse,
    AttendanceHistoryResponse,
    AttendanceHistoryItem,
    GymAttendanceItemResponse,
    GymAttendanceMemberResponse,
    GymAttendanceResponse,
)
from app.services.attendance import (
    check_in_member,
    get_member_attendance_summary,
    get_member_attendance_history,
    get_gym_attendance,
)
from app.api.deps import get_current_user
from app.models.user import User
from uuid import UUID

router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"],
)


@router.post(
    "/check-in",
    response_model=CheckInResponse,
)
async def check_in(
    data: CheckInRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    attendance = await check_in_member(
        db=db,
        user_id=current_user.id,
        gym_id=data.gym_id,
    )

    return CheckInResponse(
        success=True,
        message="Checked in successfully.",
        attendance_id=attendance.id,
        gym_id=attendance.gym_id,
        checked_in_at=attendance.checked_in_at,
    )


@router.get(
    "/me/summary",
    response_model=AttendanceSummaryResponse,
)
async def get_my_attendance_summary_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_member_attendance_summary(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/me",
    response_model=AttendanceHistoryResponse,
)
async def get_attendance_history(
    year: int | None = Query(
        default=None,
        ge=2020,
        le=2100,
    ),
    month: int | None = Query(
        default=None,
        ge=1,
        le=12,
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get member attendance history for a specific month.

    If year/month are not provided,
    the current month is returned.
    """

    now = datetime.now(timezone.utc)

    if year is None:
        year = now.year

    if month is None:
        month = now.month

    records = await get_member_attendance_history(
        db=db,
        user_id=current_user.id,
        year=year,
        month=month,
    )

    return AttendanceHistoryResponse(
        year=year,
        month=month,
        total_visits=len(records),
        month_name=datetime(
            year,
            month,
            1,
        ).strftime("%B"),
        records=[AttendanceHistoryItem.model_validate(record) for record in records],
    )


@router.get(
    "/gyms/{gym_id}",
    response_model=GymAttendanceResponse,
)
async def get_gym_attendance_endpoint(
    gym_id: UUID,
    attendance_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # ---------------------------------------------------------
    # Default to today
    # ---------------------------------------------------------

    if attendance_date is None:
        attendance_date = datetime.now(timezone.utc).date()

    # ---------------------------------------------------------
    # Service handles gym ownership verification
    # ---------------------------------------------------------

    records = await get_gym_attendance(
        db=db,
        gym_id=gym_id,
        owner_id=current_user.id,
        attendance_date=attendance_date,
    )

    return GymAttendanceResponse(
        gym_id=gym_id,
        date=attendance_date.isoformat(),
        total_check_ins=len(records),
        records=[
            GymAttendanceItemResponse(
                id=record.id,
                checked_in_at=record.checked_in_at,
                member=GymAttendanceMemberResponse(
                    id=record.user.id,
                    name=record.user.name,
                    phone=record.user.phone,
                ),
            )
            for record in records
        ],
    )
