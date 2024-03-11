"""Add language column

Revision ID: c14d2d0d8719
Revises: 5e3c023b2898
Create Date: 2020-03-25 17:18:55.234967

"""

# revision identifiers, used by Alembic.
revision = 'c14d2d0d8719'
down_revision = '5e3c023b2898'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column('document_reference', sa.Column('language', sa.String()))


def downgrade():
    op.drop_column('document_reference', 'language')
