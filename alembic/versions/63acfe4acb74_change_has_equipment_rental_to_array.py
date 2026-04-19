"""change has_equipment_rental to array

Revision ID: 63acfe4acb74
Revises: e97562523958
Create Date: 2026-04-19 15:50:45.907862

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "63acfe4acb74"
down_revision: Union[str, None] = "e97562523958"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "spots",
        "has_equipment_rental",
        existing_type=sa.BOOLEAN(),
        type_=postgresql.ARRAY(sa.String()),
        existing_nullable=True,
        postgresql_using="NULL::character varying[]",
    )


def downgrade() -> None:
    op.alter_column(
        "spots",
        "has_equipment_rental",
        existing_type=postgresql.ARRAY(sa.String()),
        type_=sa.BOOLEAN(),
        existing_nullable=True,
        postgresql_using="NULL::boolean",
    )
