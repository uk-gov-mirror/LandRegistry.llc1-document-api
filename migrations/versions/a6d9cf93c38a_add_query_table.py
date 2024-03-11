"""Add query table

Revision ID: a6d9cf93c38a
Revises: c53e6da2e709
Create Date: 2022-05-19 12:00:30.527666

"""

# revision identifiers, used by Alembic.
revision = 'a6d9cf93c38a'
down_revision = 'c53e6da2e709'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op
from flask import current_app


def upgrade():
    op.create_table('search_query',
                    sa.Column('id', sa.BigInteger(), primary_key=True),
                    sa.Column('request_timestamp', sa.DateTime(), nullable=False),
                    sa.Column('completion_timestamp', sa.DateTime(), nullable=True),
                    sa.Column('userid', sa.String(), nullable=False),
                    sa.Column('document', sa.String(), nullable=True),
                    sa.Column('external_url', sa.String(), nullable=True),
                    sa.Column('status', sa.String(), nullable=False))
    op.execute("GRANT ALL ON search_query TO " + current_app.config.get("APP_SQL_USERNAME"))
    op.execute("GRANT ALL ON SEQUENCE search_query_id_seq TO {};".format(current_app.config.get('APP_SQL_USERNAME')))


def downgrade():
    op.drop_table('search_query')
