import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.membership import Membership
    from app.models.user import User
    from app.models.attendance import Attendance


class Gym(Base):
    __tablename__ = "gyms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Owner of this gym
    owner: Mapped["User"] = relationship(
        back_populates="gyms",
    )

    # Members of this gym
    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="gym",
        cascade="all, delete-orphan",
    )

    # Attendance of the gym
    attendances: Mapped[list["Attendance"]] = relationship(
        back_populates="gym", cascade="all, delete-orphan"
    )
