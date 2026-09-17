"""change membership status enum to lowercase values

Revision ID: 84ffce002451
Revises: 73c62fe9712a
Create Date: 2026-09-16 20:41:45.826641
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "84ffce002451"
down_revision: Union[str, Sequence[str], None] = "73c62fe9712a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove the default temporarily.
    op.execute("""
        ALTER TABLE memberships
        ALTER COLUMN status DROP DEFAULT
        """)

    # Create the new enum type.
    op.execute("""
        CREATE TYPE membershipstatus_new AS ENUM (
            'pending',
            'active',
            'expired',
            'suspended'
        )
        """)

    # Convert existing values from uppercase enum values
    # to the new lowercase enum.
    op.execute("""
        ALTER TABLE memberships
        ALTER COLUMN status TYPE membershipstatus_new
        USING (
            CASE status::text
                WHEN 'ACTIVE' THEN 'active'
                WHEN 'EXPIRED' THEN 'expired'
                WHEN 'SUSPENDED' THEN 'suspended'
            END
        )::membershipstatus_new
        """)

    # Remove the old enum.
    op.execute("""
        DROP TYPE membershipstatus
        """)

    # Rename the new enum to the original name.
    op.execute("""
        ALTER TYPE membershipstatus_new
        RENAME TO membershipstatus
        """)

    # Set pending as the database default.
    op.execute("""
        ALTER TABLE memberships
        ALTER COLUMN status SET DEFAULT 'pending'
        """)


def downgrade() -> None:
    # Remove default first.
    op.execute("""
        ALTER TABLE memberships
        ALTER COLUMN status DROP DEFAULT
        """)

    # Create old enum.
    op.execute("""
        CREATE TYPE membershipstatus_old AS ENUM (
            'ACTIVE',
            'EXPIRED',
            'SUSPENDED'
        )
        """)

    # Convert lowercase values back to uppercase.
    op.execute("""
        ALTER TABLE memberships
        ALTER COLUMN status TYPE membershipstatus_old
        USING (
            CASE status::text
                WHEN 'pending' THEN 'ACTIVE'
                WHEN 'active' THEN 'ACTIVE'
                WHEN 'expired' THEN 'EXPIRED'
                WHEN 'suspended' THEN 'SUSPENDED'
            END
        )::membershipstatus_old
        """)

    op.execute("""
        DROP TYPE membershipstatus
        """)

    op.execute("""
        ALTER TYPE membershipstatus_old
        RENAME TO membershipstatus
        """)
