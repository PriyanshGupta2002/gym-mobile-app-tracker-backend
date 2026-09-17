"""add membership purchase details

Revision ID: 359f0b1c5f42
Revises: d7df2815cbd1
Create Date: 2026-09-16 18:15:51.671722
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "359f0b1c5f42"
down_revision: Union[str, Sequence[str], None] = "d7df2815cbd1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ---------------------------------------------------------
    # 1. Create payment method enum
    # ---------------------------------------------------------

    payment_method_enum = postgresql.ENUM(
        "CASH",
        "UPI",
        "CARD",
        "OTHER",
        name="paymentmethod",
    )

    payment_method_enum.create(
        op.get_bind(),
        checkfirst=True,
    )

    # ---------------------------------------------------------
    # 2. Add membership purchase details
    # ---------------------------------------------------------

    op.add_column(
        "memberships",
        sa.Column(
            "starts_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "memberships",
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "memberships",
        sa.Column(
            "payment_method",
            payment_method_enum,
            nullable=True,
        ),
    )

    op.add_column(
        "memberships",
        sa.Column(
            "amount_paid",
            sa.Numeric(
                precision=10,
                scale=2,
            ),
            nullable=True,
        ),
    )

    # ---------------------------------------------------------
    # 3. Index
    # ---------------------------------------------------------

    op.create_index(
        op.f("ix_memberships_expires_at"),
        "memberships",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    # ---------------------------------------------------------
    # 1. Remove index
    # ---------------------------------------------------------

    op.drop_index(
        op.f("ix_memberships_expires_at"),
        table_name="memberships",
    )

    # ---------------------------------------------------------
    # 2. Remove columns
    # ---------------------------------------------------------

    op.drop_column(
        "memberships",
        "amount_paid",
    )

    op.drop_column(
        "memberships",
        "payment_method",
    )

    op.drop_column(
        "memberships",
        "expires_at",
    )

    op.drop_column(
        "memberships",
        "starts_at",
    )

    # ---------------------------------------------------------
    # 3. Remove enum type
    # ---------------------------------------------------------

    payment_method_enum = postgresql.ENUM(
        "CASH",
        "UPI",
        "CARD",
        "OTHER",
        name="paymentmethod",
    )

    payment_method_enum.drop(
        op.get_bind(),
        checkfirst=True,
    )
