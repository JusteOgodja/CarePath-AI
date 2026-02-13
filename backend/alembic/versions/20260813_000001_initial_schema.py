"""initial schema

Revision ID: 20260813_000001
Revises:
Create Date: 2026-08-13 00:00:01
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260813_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "centres",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lon", sa.Float(), nullable=True),
        sa.Column("osm_type", sa.String(length=32), nullable=True),
        sa.Column("osm_id", sa.String(length=64), nullable=True),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("specialities", sa.String(length=255), nullable=False),
        sa.Column("raw_tags_json", sa.Text(), nullable=True),
        sa.Column("capacity_max", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("capacity_available", sa.Integer(), nullable=False),
        sa.Column("estimated_wait_minutes", sa.Integer(), nullable=False),
        sa.Column("catchment_population", sa.Integer(), nullable=True, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("osm_type", "osm_id", name="uq_centre_osm_identity"),
    )
    op.create_index("idx_centres_osm_identity", "centres", ["osm_type", "osm_id"], unique=True)

    op.create_table(
        "country_indicators",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("country_code", sa.String(length=8), nullable=False),
        sa.Column("indicator_code", sa.String(length=64), nullable=False),
        sa.Column("indicator_name", sa.String(length=255), nullable=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("source_file", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("country_code", "indicator_code", "year", name="uq_country_indicator_year"),
    )

    op.create_table(
        "patients",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("symptoms", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "references",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("dest_id", sa.String(), nullable=False),
        sa.Column("travel_minutes", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["dest_id"], ["centres.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["centres.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "episodes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("recommended_dest_id", sa.String(), nullable=False),
        sa.Column("reward", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["recommended_dest_id"], ["centres.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["centres.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("episodes")
    op.drop_table("references")
    op.drop_table("patients")
    op.drop_table("country_indicators")
    op.drop_index("idx_centres_osm_identity", table_name="centres")
    op.drop_table("centres")
