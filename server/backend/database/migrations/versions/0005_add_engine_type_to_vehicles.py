"""add engine_type to vehicles table

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-14

Menambahkan kolom engine_type pada tabel vehicles.
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("vehicles", sa.Column("engine_type", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("vehicles", "engine_type")

