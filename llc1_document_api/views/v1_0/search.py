import json
import uuid
from datetime import datetime
from threading import Thread

from dateutil.parser import parse
from flask import Blueprint, Response, current_app, g, request
from geoalchemy2 import shape
from llc1_document_api.dependencies.search_local_land_charge_service import \
    SearchLocalLandChargeService
from llc1_document_api.dependencies.storage_api_service import \
    StorageAPIService
from llc1_document_api.exceptions import ApplicationError
from llc1_document_api.extensions import db
from llc1_document_api.models import SearchItem, SearchQuery
from shapely.geometry import shape as shapely_shape
from shapely.geometry.collection import GeometryCollection
from sqlalchemy import func
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import sessionmaker

search = Blueprint('search', __name__, url_prefix='/v1.0/paid-searches')


@search.route("/<search_id>", methods=['GET'])
def get_paid_search_by_id(search_id):
    """Get paid search by ID

    Returns the paid search item with search_id
    """

    current_app.logger.info("Endpoint called, retrieving data for search {}".format(search_id))

    paid_searches_query = SearchItem.query \
        .filter(SearchItem.id == search_id, SearchItem.generation_status.in_(('success', 'not required')))

    paid_searches = paid_searches_query.all()

    if not paid_searches:
        return "Paid search with id {} not found".format(search_id), 404

    return Response(json.dumps(paid_searches[0].to_dict()), 200, mimetype='application/json')


@search.route("/query", methods=['POST'])
def post_paid_search_query():
    """Query paid searches with some parameters"""

    current_app.logger.info("Endpoint called, retrieving data based on supplied parameters")

    request_json = request.get_json()

    if not request_json:
        raise ApplicationError('The request body was invalid', None, 400)

    start_timestamp = request_json.get('start_timestamp')
    end_timestamp = request_json.get('end_timestamp')
    extent = request_json.get('extent')
    customer_id = request_json.get('customer_id')
    uuid = request_json.get('uuid')

    contact_id = None
    if uuid:
        contact_id = uuid
    elif customer_id:
        contact_id = customer_id

    if not (start_timestamp and end_timestamp):
        raise ApplicationError('The request body was invalid', None, 400)

    start_datetime = parse(start_timestamp)
    end_datetime = parse(end_timestamp)

    search_query_obj = SearchQuery(datetime.utcnow(), None, g.jwt.principle.principle_id, None, None, "STARTED")
    db.session.add(search_query_obj)
    db.session.flush()
    db.session.refresh(search_query_obj)

    session_factory = sessionmaker(bind=db.engine)
    session = scoped_session(session_factory)

    current_app.logger.info("Querying for charges with filter {}".format(request_json))

    extract_thread = Thread(target=search_query, args=(
        search_query_obj.id, start_datetime, end_datetime, extent, contact_id, session,
        current_app.config['SEARCH_QUERY_TIMEOUT'], current_app.config['SEARCH_QUERY_BUCKET'], current_app.logger,
        g.requests), daemon=True)
    extract_thread.start()

    db.session.commit()

    return json.dumps(search_query_obj.to_dict(), sort_keys=True), 202, \
        {"Content-Type": "application/json"}


@search.route("/query/<query_id>", methods=["GET"])
def get_paid_search_query(query_id):

    current_app.logger.info("Querying for query {}".format(query_id))

    search_query_request_result = SearchQuery.query.filter(SearchQuery.id == query_id).one_or_none()

    if not search_query_request_result:
        raise ApplicationError("Extract request not found", None, 404)

    return json.dumps(search_query_request_result.to_dict(), sort_keys=True), 200, \
        {"Content-Type": "application/json"}


def search_query(id, start_datetime, end_datetime, extent, contact_id, session, timeout, bucket, logger, requests):

    logger.info("Starting search query")

    try:

        # prevent query taking too long
        session.connection().execute("SET statement_timeout={}".format(timeout * 1000))

        if extent:
            geometries = []
            if extent.get('type') == 'FeatureCollection':
                for feature in extent.get("features"):
                    geometry = feature.get("geometry")
                    if geometry.get("type") == "GeometryCollection":
                        for geo in geometry.get("geometries"):
                            geometries.append(shapely_shape(geo))
                    else:
                        geometries.append(shapely_shape(feature.get("geometry")))
                search_geom = shape.from_shape(GeometryCollection(geometries), srid=27700)
            elif extent.get('type') == 'Feature':
                search_geom = shape.from_shape(shapely_shape(extent.get("geometry")), srid=27700)
            else:
                search_geom = shape.from_shape(shapely_shape(extent), srid=27700)

            if contact_id:
                paid_searches = session.query(SearchItem) \
                    .filter(func.ST_DWithin(SearchItem.search_geom, search_geom, 0)) \
                    .filter(SearchItem.contact_id == contact_id) \
                    .filter(SearchItem.date_of_search >= start_datetime) \
                    .filter(SearchItem.date_of_search <= end_datetime) \
                    .filter(SearchItem.generation_status.in_(['success', 'not required'])) \
                    .order_by(SearchItem.date_of_search).all()
            else:
                paid_searches = session.query(SearchItem) \
                    .filter(func.ST_DWithin(SearchItem.search_geom, search_geom, 0)) \
                    .filter(SearchItem.date_of_search >= start_datetime) \
                    .filter(SearchItem.date_of_search <= end_datetime) \
                    .filter(SearchItem.generation_status.in_(['success', 'not required'])) \
                    .order_by(SearchItem.date_of_search).all()
        else:
            # allow no extent, in which case do not filter searches by an extent
            if contact_id:
                paid_searches = session.query(SearchItem) \
                    .filter(SearchItem.contact_id == contact_id) \
                    .filter(SearchItem.date_of_search >= start_datetime) \
                    .filter(SearchItem.date_of_search <= end_datetime) \
                    .filter(SearchItem.generation_status.in_(['success', 'not required'])) \
                    .order_by(SearchItem.date_of_search).all()
            else:
                paid_searches = session.query(SearchItem) \
                    .filter(SearchItem.date_of_search >= start_datetime) \
                    .filter(SearchItem.date_of_search <= end_datetime) \
                    .filter(SearchItem.generation_status.in_(['success', 'not required'])) \
                    .order_by(SearchItem.date_of_search).all()

        logger.info("Query completed for {} searches".format(len(paid_searches)))

        logger.info("Looking up emails")
        user_info_cache = {}
        results_json = [paid_search.to_dict() for paid_search in paid_searches]
        for result in results_json:
            if result.get("source") == "SEARCH":
                result['email'] = get_email(result.get('contact_id'), user_info_cache, logger, requests)

        logger.info("Storing results")
        storage_result = StorageAPIService.save_files(
            {'file': (uuid.uuid4().hex + ".json", json.dumps(results_json),
                      "application/json")}, bucket, logger, requests)

        search_query_obj = session.query(SearchQuery).filter(SearchQuery.id == id).one_or_none()
        if not search_query_obj:
            raise ApplicationError("Search query object not found", None, 500)

        search_query_obj.document = "/" + storage_result['file'][0]['reference']
        search_query_obj.external_url = storage_result['file'][0]['external_reference']
        search_query_obj.completion_timestamp = datetime.utcnow()
        search_query_obj.status = "COMPLETED"

        session.commit()

        logger.info("Results stored")

    except Exception:
        logger.exception("Failed to complete search query")
        search_query_obj = session.query(SearchQuery).filter(SearchQuery.id == id).one_or_none()
        if not search_query_obj:
            raise ApplicationError("Search query object not found", None, 500)

        search_query_obj.completion_timestamp = datetime.utcnow()
        search_query_obj.status = "FAILED"

        session.commit()

    finally:
        session.rollback()
        session.close()


def get_email(user_id, user_info_cache, logger, requests):
    if not user_id:
        return "N/A"
    if user_id not in user_info_cache:
        user_info_cache[user_id] = SearchLocalLandChargeService.get_user_information(user_id, logger, requests)
    user_info = user_info_cache[user_id]
    if user_info:
        return user_info.get("email")
    return None
