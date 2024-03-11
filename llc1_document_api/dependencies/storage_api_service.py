from flask import current_app, g
from llc1_document_api.config import STORAGE_API
from llc1_document_api.exceptions import ApplicationError


class StorageAPIService(object):

    @staticmethod
    def get_external_url(file, bucket, subdirectories=None):
        current_app.logger.info("Generate external URL for {}".format(file))
        params = {}
        if subdirectories:
            params["subdirectories"] = subdirectories

        request_path = "{}/{}/{}/external-url".format(current_app.config['STORAGE_API'], bucket, file)

        current_app.logger.info("Calling storage api via this URL: {}".format(request_path))
        response = g.requests.get(request_path, params=params)

        current_app.logger.info("Calling storage api responded with status: {}".format(response.status_code))

        if response.status_code == 200:
            json = response.json()
            return json['external_reference']
        if response.status_code == 404:
            return None

        current_app.logger.warning(
            'Failed to get external url - TraceID : {} - Status: {}, Message: {}'.format(
                g.trace_id,
                response.status_code,
                response.text))
        raise ApplicationError('Failed to get external url', 'STORAGE-01', 500)

    @staticmethod
    def save_files(files, bucket, logger=None, requests=None):
        if not logger:
            logger = current_app.logger
        if not requests:
            requests = g.requests

        request_path = "{}/{}".format(STORAGE_API, bucket)

        logger.info("Calling storage api via this URL: %s", request_path)
        response = requests.post(request_path, files=files)
        if response.status_code == 201:
            return response.json()
        raise ApplicationError("Failed to store document", "ST01")
