"""add process_step grouping

Revision ID: b7f1bcb2917f
Revises: b28d782d78b4
Create Date: 2026-09-01 17:28:08.024775

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7f1bcb2917f'
down_revision: Union[str, Sequence[str], None] = 'b28d782d78b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Fixed, config-seeded PM-workflow phases (Q41) — same six rows for every
# org, never user-authored. Hand-adjusted from autogenerate: adds the seed
# data and a server_default so existing requirements/todo_items backfill
# to 'initiation' instead of failing NOT NULL.
PROCESS_STEPS = [
    ("initiation", "Initiation", 0),
    ("design", "Design", 1),
    ("build", "Build", 2),
    ("test", "Test", 3),
    ("deploy", "Deploy", 4),
    ("closure", "Closure", 5),
]

process_steps_table = sa.table(
    "process_steps",
    sa.column("id", sa.String),
    sa.column("title", sa.String),
    sa.column("ordering", sa.Integer),
)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('process_steps',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('ordering', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.bulk_insert(
        process_steps_table,
        [{"id": step_id, "title": title, "ordering": ordering} for step_id, title, ordering in PROCESS_STEPS],
    )
    op.add_column(
        'requirements',
        sa.Column('process_step_id', sa.String(), nullable=False, server_default='initiation'),
    )
    op.create_foreign_key(None, 'requirements', 'process_steps', ['process_step_id'], ['id'])
    op.add_column(
        'todo_items',
        sa.Column('process_step_id', sa.String(), nullable=False, server_default='initiation'),
    )
    op.create_foreign_key(None, 'todo_items', 'process_steps', ['process_step_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, 'todo_items', type_='foreignkey')
    op.drop_column('todo_items', 'process_step_id')
    op.drop_constraint(None, 'requirements', type_='foreignkey')
    op.drop_column('requirements', 'process_step_id')
    op.drop_table('process_steps')
