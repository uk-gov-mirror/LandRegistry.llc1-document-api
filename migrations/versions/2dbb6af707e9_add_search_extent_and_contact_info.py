"""add search extent and contact info

Revision ID: 2dbb6af707e9
Revises: 4cba66504aa3
Create Date: 2019-08-19 15:54:39.326485

"""

# revision identifiers, used by Alembic.
revision = '2dbb6af707e9'
down_revision = '4cba66504aa3'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column('document_reference', sa.Column('search_extent', postgresql.JSONB(), nullable=True))
    op.add_column('document_reference', sa.Column('contact_id', sa.String(), nullable=True))


def downgrade():
    op.drop_column('document_reference', 'search_extent')
    op.drop_column('document_reference', 'contact_id')
