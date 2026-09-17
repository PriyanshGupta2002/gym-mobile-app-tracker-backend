"""fix payment method enum values

Revision ID: 28a2b5e07ba1
Revises: cf63cc67b74a
Create Date: 2026-09-17 12:41:16.367834

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "28a2b5e07ba1"
down_revision: Union[str, Sequence[str], None] = "cf63cc67b74a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TYPE paymentmethod RENAME TO paymentmethod_old;
    """)

    op.execute("""
        CREATE TYPE paymentmethod AS ENUM (
            'cash',
            'upi',
            'card',
            'other'
        );
    """)

    op.execute("""
        ALTER TABLE memberships
        ALTER COLUMN payment_method
        TYPE paymentmethod
        USING LOWER(payment_method::text)::paymentmethod;
    """)

    op.execute("""
        DROP TYPE paymentmethod_old;
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TYPE paymentmethod RENAME TO paymentmethod_old;
    """)

    op.execute("""
        CREATE TYPE paymentmethod AS ENUM (
            'CASH',
            'UPI',
            'CARD',
            'OTHER'
        );
    """)

    op.execute("""
        ALTER TABLE memberships
        ALTER COLUMN payment_method
        TYPE paymentmethod
        USING UPPER(payment_method::text)::paymentmethod;
    """)

    op.execute("""
        DROP TYPE paymentmethod_old;
    """)
