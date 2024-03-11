from flask import current_app, g
from llc1_document_api.config import SEARCH_LOCAL_LAND_CHARGE_API_URL
from llc1_document_api.exceptions import ApplicationError


class SearchLocalLandChargeService(object):
    """Service class for making requests to /local_land_charges endpoint."""

    @staticmethod
    def get_user_information(user_id, logger=None, requests=None):
        if not logger:
            logger = current_app.logger
        if not requests:
            requests = g.requests
        logger.info("Retrieving userid '{}' information".format(user_id))

        response = requests.get("{}/users/{}".format(SEARCH_LOCAL_LAND_CHARGE_API_URL, user_id))

        if response.status_code == 404:
            logger.warning("Failed to find user information for id '{}'".format(user_id))
            return None
        elif response.status_code != 200:
            logger.error("Failed to retrieve user information for id '{}'".format(user_id))
            raise ApplicationError("Failed to retrieve user information", "SLLC01", 500)

        return response.json()
