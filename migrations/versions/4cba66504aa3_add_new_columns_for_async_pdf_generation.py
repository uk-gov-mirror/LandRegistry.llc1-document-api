"""Add new columns for async pdf generation

Revision ID: 4cba66504aa3
Revises: 1cfcdca9f54b
Create Date: 2019-07-31 12:23:04.822509

"""

# revision identifiers, used by Alembic.
revision = '4cba66504aa3'
down_revision = '1cfcdca9f54b'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column('document_reference', sa.Column('generation_status', sa.String(), nullable=True, server_default="success"))
    op.add_column('document_reference', sa.Column('charges', postgresql.JSONB(), nullable=True))
    op.add_column('document_reference', sa.Column('external_url', sa.String(), nullable=True))
    op.alter_column('document_reference', 'date_of_search', existing_type=sa.Date(), type_=sa.DateTime())
    op.alter_column('document_reference', 'date_of_search', existing_type=sa.Date(), type_=sa.DateTime())
    op.alter_column('document_reference', 'generation_status', server_default=None)


def downgrade():
    op.drop_column('document_reference', 'generation_status')
    op.drop_column('document_reference', 'charges')
    op.drop_column('document_reference', 'external_url')
    op.alter_column('document_reference', 'date_of_search', existing_type=sa.DateTime(), type_=sa.Date())
