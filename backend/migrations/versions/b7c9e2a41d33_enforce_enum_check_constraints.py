"""enforce enum CHECK constraints and widen enum columns

The initial migration created enum columns as plain VARCHAR with no
CHECK, because SQLAlchemy's Enum.create_constraint has defaulted to
False since 1.4. Any string that fit the column length was accepted.

This migration adds the missing constraints and widens each column to
VARCHAR(32) so that adding a longer enum member later needs only a
constraint change, not a column type change.

Alembic autogenerate does not diff CHECK constraints, so this file is
written by hand.

Revision ID: b7c9e2a41d33
Revises: 64de44f235c1
"""

from alembic import op
import sqlalchemy as sa

revision = "b7c9e2a41d33"
down_revision = "64de44f235c1"
branch_labels = None
depends_on = None

# (table, column, constraint name, allowed values, original length)
ENUM_COLUMNS = [
    ("users", "role", "ck_userrole", ["admin", "staff"], 5),
    ("patients", "gender", "ck_gender", ["male", "female", "other", "undisclosed"], 11),
    (
        "appointments",
        "appointment_type",
        "ck_appointmenttype",
        ["consultation", "check_up", "follow_up", "other"],
        12,
    ),
    (
        "appointments",
        "status",
        "ck_appointmentstatus",
        ["scheduled", "confirmed", "completed", "cancelled", "no_show"],
        9,
    ),
    ("follow_ups", "status", "ck_followupstatus", ["upcoming", "completed"], 9),
]

NEW_LENGTH = 32


def _check_expression(column: str, values: list[str]) -> str:
    # Values are hard-coded enum members from our own source, never user
    # input, but they are still quoted through a literal binding to keep
    # the pattern correct if this file is ever copied.
    quoted = ", ".join(sa.literal(v).compile(compile_kwargs={"literal_binds": True}).string for v in values)
    return f"{column} IN ({quoted})"


def upgrade():
    for table, column, name, values, _old_len in ENUM_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.String(length=NEW_LENGTH),
            existing_nullable=(table == "patients" and column == "gender"),
        )
        op.create_check_constraint(name, table, sa.text(_check_expression(column, values)))


def downgrade():
    for table, column, name, values, old_len in ENUM_COLUMNS:
        op.drop_constraint(name, table, type_="check")
        op.alter_column(
            table,
            column,
            type_=sa.String(length=old_len),
            existing_nullable=(table == "patients" and column == "gender"),
        )
