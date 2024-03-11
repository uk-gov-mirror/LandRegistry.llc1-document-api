import json
from datetime import datetime

from flask import Blueprint, Response, current_app, g, request
from llc1_document_api import config
from llc1_document_api.dependencies.pdf_generation_service import \
    PdfGenerationService
from llc1_document_api.exceptions import ApplicationError
from llc1_document_api.extensions import db
from llc1_document_api.models import SearchItem
from llc1_document_api.validators.payload_validator import PayloadValidator

generate = Blueprint('generate', __name__, url_prefix='/v1.0')


@generate.route("/generate_async", methods=['POST'])
def generate_llc1_async():
    """Generates an LLC1 document from the given extents and returns the URL to it's location in the file store."""
    current_app.logger.info("Endpoint called, validating payload")

    if not PayloadValidator.validate(request.get_data()):
        raise ApplicationError('The request body was invalid', None, 400)

    request_json = request.get_json()
    request_format = request_json.get('format', 'PDF')

    search_item = SearchItem(datetime.now(), request_json.get('source'),
                             parent_search_id=request_json.get('parent_search_id'),
                             search_area_description=request_json.get('description'),
                             search_extent=request_json.get('extents'),
                             contact_id=request_json.get('contact_id'),
                             language=request_json.get('language'))

    if request_format == 'PDF':
        current_app.logger.info("Payload validated, generating PDF")
        PdfGenerationService.generate_pdf(request_json, search_item)
        return Response(json.dumps({"status": search_item.generation_status,
                                    "search_reference": search_item.formatted_id()}), 202, mimetype="application/json")
    else:
        current_app.logger.info("Alternative format requested {}".format(request_format))
        charges = request_json.get('charges', None)
        if charges is None:
            current_app.logger.error('Alternative format requests must contain a list of charges')
            raise ApplicationError('Alternative format requests must contain a list of charges', 'AF-01', 400)
        search_item.charges = charges
        search_item.generation_status = 'not required'
        try:
            db.session.add(search_item)
            db.session.commit()
            current_app.logger.info("Alternative format LLC1 completed for reference {}".format(search_item.id))
        except Exception as ex:
            db.session.rollback()
            current_app.logger.exception('Failed to record LLC1. TraceID : {} - Exception :{}'.format(
                g.trace_id,
                ex))
            raise ApplicationError("Error recording LLC1", "LLC1-01", 500)
        return Response(json.dumps({"status": "created",
                                    "search_reference": search_item.formatted_id()}), 201, mimetype="application/json")


@generate.route("/poll_llc1/<search_ref>", methods=['GET'])
def poll_llc1(search_ref):
    """Polls for LLC1 document PDF"""

    return_supporting_docs = False
    if request.args.get('return_supporting_docs') and request.args.get('return_supporting_docs').lower() == 'true':
        return_supporting_docs = True

    current_app.logger.info("Payload validated, polling for PDF")

    search_item = SearchItem.query.get(int(search_ref.replace(' ', '')))
    if not search_item:
        raise ApplicationError("Requested search reference not found", "POL-01", 404)

    pdf = PdfGenerationService.check_for_result(search_item, config.ASYNC_PDF_TIMEOUT, return_supporting_docs)

    if not pdf:
        return Response(json.dumps({"status": "generating"}), 202, mimetype="application/json")

    return Response(json.dumps(pdf), 201, mimetype="application/json")


@generate.route("/pdf_callback/<search_ref>", methods=['POST'])
def callback_llc1(search_ref):
    """Callback for LLC1 document PDF"""
    current_app.logger.info("Endpoint called, validating payload")

    if not PayloadValidator.validate_callback(request.get_data()):
        raise ApplicationError('The request body was invalid', None, 400)

    current_app.logger.info("Payload validated, polling for PDF")

    search_item = SearchItem.query.get(int(search_ref.replace(' ', '')))
    if not search_item:
        raise ApplicationError("Requested search reference not found", "CBAC-01", 404)

    PdfGenerationService.callback(search_item, request.get_json())

    return Response(json.dumps({"status": "accepted"}), 202, mimetype="application/json")


@generate.route("/llc1_languages", methods=['GET'])
def llc1_languages():
    """Retrieve available languages from pdf generator"""
    current_app.logger.info("Endpoint called, polling for PDF languages")

    return Response(PdfGenerationService.get_languages(), 200, mimetype="application/json")
