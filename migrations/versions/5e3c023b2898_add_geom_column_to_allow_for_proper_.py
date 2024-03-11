"""Add geom column to allow for proper spatial indexing

Revision ID: 5e3c023b2898
Revises: 2dbb6af707e9
Create Date: 2019-09-26 14:35:08.937630

"""

# revision identifiers, used by Alembic.
revision = '5e3c023b2898'
down_revision = '2dbb6af707e9'
branch_labels = None
depends_on = None

import json

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import shape, types
from shapely.geometry import shape as shapelyShape
from shapely.geometry.collection import GeometryCollection
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column('document_reference', sa.Column(
        'search_geom', types.Geometry(srid=27700), autoincrement=False, nullable=True))
    op.create_index('idx_search_geom_document_reference', 'document_reference', ['search_geom'], postgresql_using='gist')
    query = "SELECT id, search_extent FROM document_reference WHERE search_extent IS NOT NULL;"
    conn = op.get_bind()
    result = conn.execute(query).fetchall()
    for search in result:
        doc_id = search[0]
        search_extent = search[1]
        geometries = []
        for feature in search_extent.get("features"):
            if feature.get("geometry").get("type") == "GeometryCollection":
                for geo in feature.get("geometry").get("geometries"):
                    geometries.append(shapelyShape(geo))
            else:
                geometries.append(shapelyShape(feature.get("geometry")))
        update_query = "UPDATE document_reference SET search_geom = ST_GeomFromWKB(decode('{}', 'hex'), 27700) WHERE id = {}".format(
                shape.from_shape(GeometryCollection(geometries), srid=27700), doc_id)
        op.execute(update_query)
    op.drop_column('document_reference', 'search_extent')


def downgrade():
    op.drop_index('idx_search_geom_document_reference')
    op.add_column('document_reference', sa.Column('search_extent', postgresql.JSONB(), nullable=True))
    query = "SELECT id, ST_AsGeoJson(search_geom) FROM document_reference WHERE search_geom IS NOT NULL;"
    conn = op.get_bind()
    result = conn.execute(query).fetchall()
    for search in result:
        doc_id = search[0]
        search_json = json.loads(search[1])
        features = []
        if search_json.get('type') == 'GeometryCollection':
            for geo in search_json.get('geometries'):
                features.append({"type": "Feature", "properties": {}, "geometry": geo})
        else:
            features.append({"type": "Feature", "properties": {}, "geometry": search_json})
        feature_collection = {"type": "FeatureCollection", "features": features}
        update_query = "UPDATE document_reference SET search_extent = '{}' WHERE id = {}".format(
            json.dumps(feature_collection), doc_id)
        op.execute(update_query)
    op.drop_column('document_reference', 'search_geom')
