"""referral workflow table

Revision ID: 20260813_000002
Revises: 20260813_000001
Create Date: 2026-08-13 00:00:02
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260813_000002"
down_revision = "20260813_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "referral_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("needed_speciality", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("proposed_dest_id", sa.String(), nullable=True),
        sa.Column("accepted_dest_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("feedback_diagnosis", sa.Text(), nullable=True),
        sa.Column("feedback_treatment", sa.Text(), nullable=True),
        sa.Column("feedback_followup", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["centres.id"]),
        sa.ForeignKeyConstraint(["proposed_dest_id"], ["centres.id"]),
        sa.ForeignKeyConstraint(["accepted_dest_id"], ["centres.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("referral_requests")
