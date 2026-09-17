"""add membership plans

Revision ID: d7df2815cbd1
Revises: 525197480200
Create Date: 2026-09-16 17:45:48.697955

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d7df2815cbd1"
down_revision: Union[str, Sequence[str], None] = "525197480200"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "membership_plans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("gym_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["gym_id"],
            ["gyms.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_membership_plans_gym_id"),
        "membership_plans",
        ["gym_id"],
        unique=False,
    )

    op.add_column(
        "memberships",
        sa.Column(
            "membership_plan_id",
            sa.UUID(),
            nullable=True,
        ),
    )

    op.create_index(
        op.f("ix_memberships_membership_plan_id"),
        "memberships",
        ["membership_plan_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_memberships_membership_plan_id",
        "memberships",
        "membership_plans",
        ["membership_plan_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "fk_memberships_membership_plan_id",
        "memberships",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_memberships_membership_plan_id"),
        table_name="memberships",
    )

    op.drop_column(
        "memberships",
        "membership_plan_id",
    )

    op.drop_index(
        op.f("ix_membership_plans_gym_id"),
        table_name="membership_plans",
    )

    op.drop_table("membership_plans")
