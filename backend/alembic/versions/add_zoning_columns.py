"""add home_neighborhood and work_district zoning columns

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-14

Non-destructive migration: adds new nullable columns alongside existing
`region` column. No columns are dropped. Old sessions continue to work
via fallback logic in the application layer.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Archetypes: add home_neighborhood and work_district
    op.add_column(
        "archetypes",
        sa.Column("home_neighborhood", sa.String(128), nullable=True),
    )
    op.add_column(
        "archetypes",
        sa.Column("work_district", sa.String(128), nullable=True),
    )
    # Backfill from region for existing rows
    op.execute(
        "UPDATE archetypes SET home_neighborhood = region, work_district = region "
        "WHERE home_neighborhood IS NULL"
    )

    # Followers: add home_neighborhood and work_district
    op.add_column(
        "followers",
        sa.Column("home_neighborhood", sa.String(128), nullable=True),
    )
    op.add_column(
        "followers",
        sa.Column("work_district", sa.String(128), nullable=True),
    )

    # Companies: add work_district
    op.add_column(
        "companies",
        sa.Column("work_district", sa.String(128), nullable=True),
    )
    # Backfill from region for existing rows
    op.execute(
        "UPDATE companies SET work_district = region "
        "WHERE work_district IS NULL"
    )

    # Demographics: add home_neighborhood and work_district
    op.add_column(
        "demographics",
        sa.Column("home_neighborhood", sa.String(128), nullable=True),
    )
    op.add_column(
        "demographics",
        sa.Column("work_district", sa.String(128), nullable=True),
    )
    # Backfill from region for existing rows
    op.execute(
        "UPDATE demographics SET home_neighborhood = region, work_district = region "
        "WHERE home_neighborhood IS NULL"
    )


def downgrade() -> None:
    op.drop_column("demographics", "work_district")
    op.drop_column("demographics", "home_neighborhood")
    op.drop_column("companies", "work_district")
    op.drop_column("followers", "work_district")
    op.drop_column("followers", "home_neighborhood")
    op.drop_column("archetypes", "work_district")
    op.drop_column("archetypes", "home_neighborhood")
