"""document to relative

Revision ID: c53e6da2e709
Revises: c14d2d0d8719
Create Date: 2021-02-11 12:13:54.533763

"""

# revision identifiers, used by Alembic.
import sqlalchemy as sa
from alembic import op

revision = 'c53e6da2e709'
down_revision = 'c14d2d0d8719'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('document_reference', 'document', nullable=True, new_column_name='document_old')
    op.add_column('document_reference', sa.Column('document', sa.String(), nullable=True))
    op.execute("UPDATE document_reference SET document = "
               "regexp_replace(document_old, "
               "'https?:\/\/[^\/:]+(:[0-9]+)?\/v1\.0\/storage\/([^\/]+)\/([^\/]+)', '/\\2/\\3');")


def downgrade():
    op.drop_column('document_reference', 'document')
    op.alter_column('document_reference', 'document_old', nullable=True, new_column_name='document')
