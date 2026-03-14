"""add follower avatar fields

Revision ID: a1b2c3d4e5f6
Revises: cc6e82843068
Create Date: 2026-03-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "cc6e82843068"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "followers",
        sa.Column("avatar_seed", sa.Integer(), nullable=True),
    )
    op.add_column(
        "followers",
        sa.Column(
            "avatar_params",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("followers", "avatar_params")
    op.drop_column("followers", "avatar_seed")
