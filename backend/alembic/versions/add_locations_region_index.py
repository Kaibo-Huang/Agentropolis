"""add index on locations.region for fast region lookups

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-14

get_locations_by_region() is called twice per archetype per tick (work + home
district lookups). Without an index on `region`, each call is a full table scan.
This index eliminates those scans.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("idx_locations_region", "locations", ["region"])


def downgrade() -> None:
    op.drop_index("idx_locations_region", table_name="locations")
