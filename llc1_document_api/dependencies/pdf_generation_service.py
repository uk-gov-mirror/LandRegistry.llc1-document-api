import json
from datetime import datetime, timedelta

from flask import current_app, g, url_for
from llc1_document_api.config import CALLBACK_PREFIX, PDF_GENERATION_API
from llc1_document_api.dependencies.storage_api_service import \
    StorageAPIService
from llc1_document_api.exceptions import ApplicationError
from llc1_document_api.extensions import db


class PdfGenerationService(object):
    @staticmethod
    def generate_pdf(extents, search_item):
        """Generates the llc1 PDF"""
        db.session.add(search_item)
        db.session.flush()
        try:
            extents['reference_number'] = search_item.id

            current_app.logger.info("Calling pdf-generation-api")

            response = g.requests.post(PDF_GENERATION_API,
                                       data=json.dumps(extents),
                                       headers={'X-Trace-ID': g.trace_id, 'Content-Type': 'application/json',
                                                'ReplyTo': CALLBACK_PREFIX + url_for('generate.callback_llc1',
                                                                                     search_ref=search_item.id)})

            if response.status_code != 202:
                current_app.logger.error(
                    'Failed to generate PDF. TraceID : {} - Status code:{}, message:{}'
                    .format(g.trace_id,
                            response.status_code,
                            response.text))
                raise ApplicationError("Error generating PDF", "GEN-01", response.status_code)

            search_item.generation_status = 'generating'

            current_app.logger.info('Committing SearchItem with id: {}'.format(search_item.id))
        except Exception as ex:
            current_app.logger.exception('Failed to generate PDF. TraceID : {} - Exception :{}'.format(
                g.trace_id,
                ex))
            search_item.generation_status = 'failed'

        db.session.commit()

    @staticmethod
    def check_for_result(search_item, timeout, return_supporting_docs=False):

        current_app.logger.info('Checking for results for search reference {}'.format(search_item.id))

        expired = PdfGenerationService.expired_search(search_item, timeout)

        if search_item.generation_status != 'success':
            if expired:
                raise ApplicationError("PDF generation timed out for search reference {}".format(search_item.id),
                                       "GEN-03", 500)
            elif search_item.generation_status == 'generating':
                return None
            else:
                raise ApplicationError("PDF generation failed for search reference {}".format(search_item.id),
                                       "GEN-04", 500)

        response_obj = {
            "reference_number": search_item.formatted_id(),
            "document_url": search_item.document,
            "external_url": search_item.external_url,
            "number_of_charges": len(search_item.charges)
        }

        if return_supporting_docs:
            supporting_documents = {}

            for item in search_item.charges:
                charge = item['item']
                if 'Light obstruction notice' in charge['charge-type']:
                    supporting_documents[item['display-id']] = PdfGenerationService.url_for_documents(
                        charge['documents-filed'])

            if supporting_documents:
                response_obj['supporting_documents'] = supporting_documents

        return response_obj

    @staticmethod
    def callback(search_item, response):
        current_app.logger.info('Handling callback for search reference {}'.format(search_item.id))
        status = response.get("status", None)
        search_item.generation_status = status

        if status == 'success':
            pdf_result = response.get('result', None)
            search_item.document = pdf_result.get('document_url', None)
            search_item.charges = pdf_result.get('included_charges', None)
            search_item.external_url = pdf_result.get('external_url', None)
            db.session.commit()
        else:
            db.session.commit()
            raise ApplicationError("PDF generation failed for search reference {} response was {}"
                                   .format(search_item.id, response),
                                   "GEN-04", 500)

    @staticmethod
    def url_for_documents(documents_filed):
        form_a = documents_filed['form-a'][0]

        return StorageAPIService.get_external_url(form_a["subdirectory"], form_a['bucket'])

    @staticmethod
    def expired_search(search_item, timeout):
        return search_item.date_of_search < (datetime.now() - timedelta(seconds=timeout))

    @staticmethod
    def get_languages():
        """Gets list of available languages"""
        response = g.requests.get("{}/languages".format(PDF_GENERATION_API),
                                  headers={'X-Trace-ID': g.trace_id})

        if response.status_code != 200:
            current_app.logger.error(
                'Failed to retrieve languages list. TraceID : {} - Status code:{}, message:{}'
                .format(g.trace_id,
                        response.status_code,
                        response.text))
            raise ApplicationError("Failed to retrieve languages list", "LANG-01", response.status_code)

        return response.text
