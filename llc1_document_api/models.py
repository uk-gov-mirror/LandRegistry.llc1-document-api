from geoalchemy2 import Geometry, shape
from llc1_document_api.extensions import db
from shapely.geometry import mapping
from shapely.geometry import shape as shapely_shape
from shapely.geometry.collection import GeometryCollection
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property


class SearchItem(db.Model):
    __tablename__ = 'document_reference'

    id = db.Column(db.BigInteger, primary_key=True)
    date_of_search = db.Column(db.DateTime)
    document = db.Column(db.String)
    source = db.Column(db.String)
    parent_search_id = db.Column(db.BigInteger, db.ForeignKey('document_reference.id'), nullable=True)
    search_area_description = db.Column(db.String)
    generation_status = db.Column(db.DateTime)
    external_url = db.Column(db.String)
    charges = db.Column(JSONB)
    search_geom = db.Column(Geometry(srid=27700))
    contact_id = db.Column(db.String)
    language = db.Column(db.String)

    def __init__(self, date_of_search, source, document=None, parent_search_id=None, search_area_description=None,
                 generation_status=None, external_url=None, charges=None, search_extent=None, contact_id=None,
                 language=None):
        self.date_of_search = date_of_search
        self.source = source
        self.document = document
        self.parent_search_id = parent_search_id
        self.search_area_description = search_area_description
        self.generation_status = generation_status
        self.external_url = external_url
        self.charges = charges
        self.search_extent = search_extent
        self.contact_id = contact_id
        self.language = language

    def formatted_id(self):
        padded_id = '{}'.format(self.id).zfill(9)
        formatted_id = ' '.join(padded_id[i:i + 3] for i in range(0, len(padded_id), 3))
        # Limiting to 11 characters (9 for reference number + 3 spaces)
        return formatted_id[:11]

    # Convert geom column to geojson
    @hybrid_property
    def search_extent(self):
        if self.search_geom is None:
            return None
        extents = mapping(shape.to_shape(self.search_geom))
        features = []
        if extents.get('type') == 'GeometryCollection':
            for geo in extents.get('geometries'):
                features.append({"type": "Feature", "properties": {}, "geometry": geo})
        else:
            features.append({"type": "Feature", "properties": {}, "geometry": extents})
        return {"type": "FeatureCollection", "features": features}

    # Convert geojson to geom column
    @search_extent.setter
    def search_extent(self, extents):
        if extents is None:
            return None
        geometries = []
        for feature in extents.get("features"):
            geometry = feature.get("geometry")
            if geometry.get("type") == "GeometryCollection":
                for geo in geometry.get("geometries"):
                    geometries.append(shapely_shape(geo))
            else:
                geometries.append(shapely_shape(geometry))
        self.search_geom = shape.from_shape(GeometryCollection(geometries), srid=27700)

    def to_dict(self):
        dict_obj = {"id": self.id,
                    "date_of_search": self.date_of_search.isoformat(),
                    "document": self.document,
                    "source": self.source,
                    "parent_search_id": self.parent_search_id,
                    "search_area_description": self.search_area_description,
                    "generation_status": self.generation_status,
                    "external_url": self.external_url,
                    "charges": self.charges,
                    "search_extent": self.search_extent,
                    "contact_id": self.contact_id,
                    "language": self.language,
                    "formatted_id": self.formatted_id()}
        return dict_obj


class SearchQuery(db.Model):
    __tablename__ = 'search_query'

    id = db.Column(db.BigInteger, primary_key=True)
    request_timestamp = db.Column(db.DateTime, nullable=False)
    completion_timestamp = db.Column(db.DateTime, nullable=True)
    userid = db.Column(db.String, nullable=False)
    document = db.Column(db.String, nullable=True)
    external_url = db.Column(db.String, nullable=True)
    status = db.Column(db.String, nullable=False)

    def __init__(self, request_timestamp, completion_timestamp, userid, document, external_url, status):
        self.request_timestamp = request_timestamp
        self.completion_timestamp = completion_timestamp
        self.userid = userid
        self.document = document
        self.external_url = external_url
        self.status = status

    def to_dict(self):
        result = {"id": self.id,
                  "request_timestamp": self.request_timestamp.isoformat(),
                  "userid": self.userid,
                  "status": self.status}
        append_to_dict_if_exists(result, 'completion_timestamp', format_timestamp_if_exists(self.completion_timestamp))
        append_to_dict_if_exists(result, 'document', self.document)
        append_to_dict_if_exists(result, 'external_url', self.external_url)

        return result


def append_to_dict_if_exists(item, key, value):
    if value is not None:
        item[key] = value


def format_timestamp_if_exists(timestamp):
    return timestamp.isoformat() if timestamp is not None else None
