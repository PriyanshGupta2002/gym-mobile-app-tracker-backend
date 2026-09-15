import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.gym import Gym
    from app.models.membership import Membership
    from app.models.attendance import Attendance


class UserRole(str, enum.Enum):
    MEMBER = "member"
    OWNER = "owner"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("id", name="uq_memberships_user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    phone: Mapped[str] = mapped_column(
        String(15),
        unique=True,
        index=True,
        nullable=False,
    )

    name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Gyms owned by this user
    gyms: Mapped[list["Gym"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    # Gym memberships belonging to this user
    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    attendances: Mapped[list["Attendance"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
