import uuid
from datetime import datetime

from pydantic import BaseModel
from uuid import UUID
import enum


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    MISSED = "missed"
    UPCOMING = "upcoming"


class CheckInRequest(BaseModel):
    gym_id: uuid.UUID


class CheckInResponse(BaseModel):
    success: bool
    message: str
    attendance_id: uuid.UUID
    gym_id: uuid.UUID
    checked_in_at: datetime


class TodayAttendanceResponse(BaseModel):
    checked_in: bool
    checked_in_at: datetime | None = None


class WeeklyAttendanceResponse(BaseModel):
    visits: int
    goal: int


class StreakResponse(BaseModel):
    current: int


class AttendanceSummaryResponse(BaseModel):
    today: TodayAttendanceResponse
    this_week: WeeklyAttendanceResponse
    streak: StreakResponse


class AttendanceHistoryItem(BaseModel):
    id: UUID | None = None
    date: str
    status: AttendanceStatus
    checked_in_at: datetime | None = None

    class Config:
        from_attributes = True


class AttendanceHistoryResponse(BaseModel):
    year: int
    month: int
    month_name: str
    total_visits: int
    records: list[AttendanceHistoryItem]
