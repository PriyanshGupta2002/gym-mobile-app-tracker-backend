import uuid
from datetime import date, datetime, timezone, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance
from app.models.membership import Membership, MembershipStatus
from calendar import monthrange

WEEKLY_GOAL = 4


async def check_in_member(
    db: AsyncSession,
    user_id: uuid.UUID,
    gym_id: uuid.UUID,
) -> Attendance:

    # ---------------------------------------------------------
    # 1. Verify that the user has an ACTIVE membership
    #    for this gym
    # ---------------------------------------------------------

    membership_result = await db.execute(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.gym_id == gym_id,
            Membership.status == MembershipStatus.ACTIVE,
        )
    )

    membership = membership_result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have an active membership at this gym.",
        )

    # ---------------------------------------------------------
    # 2. Get today's date
    # ---------------------------------------------------------

    now = datetime.now(timezone.utc)
    today = now.date()

    # ---------------------------------------------------------
    # 3. Check whether member already checked in today
    # ---------------------------------------------------------

    attendance_result = await db.execute(
        select(Attendance).where(
            Attendance.user_id == user_id,
            Attendance.gym_id == gym_id,
            Attendance.attendance_date == today,
        )
    )

    existing_attendance = attendance_result.scalar_one_or_none()

    if existing_attendance:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already checked in today.",
        )

    # ---------------------------------------------------------
    # 4. Create attendance
    # ---------------------------------------------------------

    attendance = Attendance(
        user_id=user_id,
        gym_id=gym_id,
        attendance_date=today,
        checked_in_at=now,
    )

    db.add(attendance)

    await db.commit()
    await db.refresh(attendance)

    return attendance


async def get_member_attendance_summary(
    db: AsyncSession,
    user_id,
):
    now = datetime.now(timezone.utc)

    # ---------------------------------------------------------
    # TODAY
    # ---------------------------------------------------------

    start_of_day = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    end_of_day = start_of_day + timedelta(days=1)

    today_result = await db.execute(
        select(Attendance)
        .where(
            Attendance.user_id == user_id,
            Attendance.checked_in_at >= start_of_day,
            Attendance.checked_in_at < end_of_day,
        )
        .order_by(Attendance.checked_in_at.desc())
    )

    today_attendance = today_result.scalars().first()

    # ---------------------------------------------------------
    # THIS WEEK
    # ---------------------------------------------------------

    # Monday = start of week
    start_of_week = start_of_day - timedelta(days=start_of_day.weekday())

    weekly_result = await db.execute(
        select(func.count(Attendance.id)).where(
            Attendance.user_id == user_id,
            Attendance.checked_in_at >= start_of_week,
            Attendance.checked_in_at < end_of_day,
        )
    )

    weekly_visits = weekly_result.scalar_one()

    # ---------------------------------------------------------
    # CURRENT STREAK
    # ---------------------------------------------------------

    attendance_result = await db.execute(
        select(Attendance.checked_in_at)
        .where(
            Attendance.user_id == user_id,
        )
        .order_by(Attendance.checked_in_at.desc())
    )

    attendance_dates = attendance_result.scalars().all()

    unique_dates = {
        attendance_date.astimezone(timezone.utc).date()
        for attendance_date in attendance_dates
    }

    current_date = now.date()

    # If the member hasn't checked in today,
    # the streak starts from yesterday.
    if current_date not in unique_dates:
        current_date -= timedelta(days=1)

    streak = 0

    while current_date in unique_dates:
        streak += 1
        current_date -= timedelta(days=1)

    # ---------------------------------------------------------
    # RESPONSE
    # ---------------------------------------------------------

    return {
        "today": {
            "checked_in": today_attendance is not None,
            "checked_in_at": (
                today_attendance.checked_in_at if today_attendance else None
            ),
        },
        "this_week": {
            "visits": weekly_visits,
            "goal": WEEKLY_GOAL,
        },
        "streak": {
            "current": streak,
        },
    }


async def get_member_attendance_history(
    db: AsyncSession,
    user_id,
    year: int,
    month: int,
):
    """
    Get attendance history for a member for a specific month.

    Status:
    - present  -> member checked in
    - missed   -> date has passed and member did not check in
    - upcoming -> date has not happened yet

    Dates before the member joined the gym are not included.
    """

    # ---------------------------------------------------------
    # 1. Get the member's membership
    # ---------------------------------------------------------

    membership_result = await db.execute(
        select(Membership).where(
            Membership.user_id == user_id,
        )
    )

    membership = membership_result.scalar_one_or_none()

    if not membership:
        return []

    joined_date = membership.joined_at.date()

    # ---------------------------------------------------------
    # 2. Calculate month boundaries
    # ---------------------------------------------------------

    start_date = datetime(
        year,
        month,
        1,
        tzinfo=timezone.utc,
    )

    if month == 12:
        end_date = datetime(
            year + 1,
            1,
            1,
            tzinfo=timezone.utc,
        )
    else:
        end_date = datetime(
            year,
            month + 1,
            1,
            tzinfo=timezone.utc,
        )

    # ---------------------------------------------------------
    # 3. Get actual attendance records
    # ---------------------------------------------------------

    result = await db.execute(
        select(Attendance)
        .where(
            Attendance.user_id == user_id,
            Attendance.checked_in_at >= start_date,
            Attendance.checked_in_at < end_date,
        )
        .order_by(Attendance.checked_in_at.desc())
    )

    attendances = result.scalars().all()

    # ---------------------------------------------------------
    # 4. Map attendance by calendar date
    # ---------------------------------------------------------

    attendance_by_date = {
        attendance.checked_in_at.date(): attendance for attendance in attendances
    }

    # ---------------------------------------------------------
    # 5. Current date
    # ---------------------------------------------------------

    today = datetime.now(timezone.utc).date()

    # ---------------------------------------------------------
    # 6. Generate monthly history
    # ---------------------------------------------------------

    days_in_month = monthrange(year, month)[1]

    records = []

    for day in range(days_in_month, 0, -1):

        current_date = date(year, month, day)

        # Don't show dates before membership started
        if current_date < joined_date:
            continue

        attendance = attendance_by_date.get(current_date)

        if attendance:
            status = "present"

        elif current_date < today:
            status = "missed"

        else:
            status = "upcoming"

        records.append(
            {
                "date": current_date.isoformat(),
                "status": status,
                "id": attendance.id if attendance else None,
                "checked_in_at": (attendance.checked_in_at if attendance else None),
            }
        )

    return records
