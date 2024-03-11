from unittest import TestCase
from unittest.mock import MagicMock

from flask import g
from llc1_document_api import main
from llc1_document_api.dependencies.search_local_land_charge_service import \
    SearchLocalLandChargeService
from llc1_document_api.exceptions import ApplicationError


class TestSearchLocalLandChargeService(TestCase):

    def test_get_user_information_ok(self):
        with main.app.test_request_context():
            mock_requests = MagicMock()
            g.requests = mock_requests
            g.trace_id = "atraceid"
            mock_response = MagicMock()
            mock_requests.get.return_value = mock_response
            mock_response.status_code = 200
            mock_response.json.return_value = {"some": "json"}
            result = SearchLocalLandChargeService.get_user_information("anid")
            self.assertEqual(result, {"some": "json"})
            mock_requests.get.assert_called()

    def test_get_user_information_not_found(self):
        with main.app.test_request_context():
            mock_requests = MagicMock()
            g.requests = mock_requests
            g.trace_id = "atraceid"
            mock_response = MagicMock()
            mock_requests.get.return_value = mock_response
            mock_response.status_code = 404
            mock_response.json.return_value = {"some": "json"}
            result = SearchLocalLandChargeService.get_user_information("anid")
            self.assertEqual(result, None)
            mock_requests.get.assert_called()

    def test_get_user_information_error(self):
        with main.app.test_request_context():
            mock_requests = MagicMock()
            g.requests = mock_requests
            g.trace_id = "atraceid"
            mock_response = MagicMock()
            mock_requests.get.return_value = mock_response
            mock_response.status_code = 500
            mock_response.json.return_value = {"some": "json"}
            with self.assertRaises(ApplicationError):
                SearchLocalLandChargeService.get_user_information("anid")
            mock_requests.get.assert_called()
