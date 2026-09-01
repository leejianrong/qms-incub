"""add todo item approval state fields

Revision ID: b28d782d78b4
Revises: fbe0bf11bcfb
Create Date: 2026-09-01 17:34:13.930457

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b28d782d78b4'
down_revision: Union[str, Sequence[str], None] = 'fbe0bf11bcfb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default only backfills existing rows on upgrade (an existing
    # local dev DB may already have todo_items); the ORM model itself uses
    # a Python-side default for rows created going forward, matching this
    # repo's usual style, so the server_default is dropped right after.
    op.add_column(
        "todo_items",
        sa.Column("approval_state", sa.String(), nullable=False, server_default="not_started"),
    )
    op.add_column(
        "todo_items",
        sa.Column("approval_authority", sa.String(), nullable=False, server_default="QA Office"),
    )
    op.add_column("todo_items", sa.Column("sla_target", sa.DateTime(timezone=True), nullable=True))
    op.add_column("todo_items", sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("todo_items", "approval_state", server_default=None)
    op.alter_column("todo_items", "approval_authority", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("todo_items", "decided_at")
    op.drop_column("todo_items", "sla_target")
    op.drop_column("todo_items", "approval_authority")
    op.drop_column("todo_items", "approval_state")
