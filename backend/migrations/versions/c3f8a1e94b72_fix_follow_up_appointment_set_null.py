"""fix ON DELETE SET NULL on the follow_ups → appointments composite key

The original constraint used a bare "ON DELETE SET NULL". On a composite
foreign key Postgres nulls every referencing column, so deleting an
appointment attempted to set follow_ups.clinic_id to NULL as well — a
NOT NULL column. The delete failed with NotNullViolation, meaning any
appointment referenced by a follow-up could never be removed.

PostgreSQL 15 added the column-list form, which nulls only the columns
named. This migration recreates the constraint with
"SET NULL (appointment_id)" so the appointment link is cleared while the
follow-up keeps its clinic scope and its outstanding commitment.

Alembic autogenerate does not compare ON DELETE actions, so this file is
written by hand.

Revision ID: c3f8a1e94b72
Revises: b7c9e2a41d33
"""

from alembic import op

revision = "c3f8a1e94b72"
down_revision = "b7c9e2a41d33"
branch_labels = None
depends_on = None

CONSTRAINT = "fk_follow_ups_appointment_clinic"


def upgrade():
    op.drop_constraint(CONSTRAINT, "follow_ups", type_="foreignkey")
    op.execute(
        f'ALTER TABLE follow_ups ADD CONSTRAINT "{CONSTRAINT}" '
        "FOREIGN KEY (appointment_id, clinic_id) "
        "REFERENCES appointments (id, clinic_id) "
        "ON DELETE SET NULL (appointment_id)"
    )


def downgrade():
    op.drop_constraint(CONSTRAINT, "follow_ups", type_="foreignkey")
    op.execute(
        f'ALTER TABLE follow_ups ADD CONSTRAINT "{CONSTRAINT}" '
        "FOREIGN KEY (appointment_id, clinic_id) "
        "REFERENCES appointments (id, clinic_id) "
        "ON DELETE SET NULL"
    )
