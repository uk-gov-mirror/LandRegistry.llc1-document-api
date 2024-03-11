"""add parent ID column

Revision ID: 1cfcdca9f54b
Revises: a42fd4cb0ff4
Create Date: 2018-10-25 13:20:00.423072

"""

# revision identifiers, used by Alembic.
revision = '1cfcdca9f54b'
down_revision = 'a42fd4cb0ff4'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column('document_reference', sa.Column('parent_search_id', sa.BigInteger(), nullable=True))
    op.add_column('document_reference', sa.Column('search_area_description', sa.VARCHAR(1000), nullable=True))
    op.create_foreign_key(None, 'document_reference', 'document_reference', ['parent_search_id'], ['id'])


def downgrade():
    op.drop_constraint(None, 'document_reference', type_='foreignkey')
    op.drop_column('document_reference', 'parent_search_id')
    op.drop_column('document_reference', 'search_area_description')
