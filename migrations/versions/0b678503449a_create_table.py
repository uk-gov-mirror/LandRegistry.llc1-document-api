"""Create Document Reference Table

Revision ID: 0b678503449a
Revises: 
Create Date: 2017-09-21 11:02:47.697579

"""

# revision identifiers, used by Alembic.
revision = '0b678503449a'
down_revision = None
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op
from flask import current_app


def upgrade():
    op.create_table('document_reference',
                    sa.Column('id', sa.BigInteger(), primary_key=True),
                    sa.Column('date_of_search', sa.Date()),
                    sa.Column('document', sa.String()),
                    sa.Column('source', sa.String()))
    op.create_index('ix_document_reference_id', 'document_reference', ['id'])
    op.execute("GRANT ALL ON ALL TABLES IN SCHEMA public TO " + current_app.config.get("APP_SQL_USERNAME"))
    op.execute("GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO " + current_app.config.get("APP_SQL_USERNAME"))


def downgrade():
    op.drop_index('ix_document_reference_id')
    op.drop_table('document_reference')
