import json
from datetime import datetime
from unittest.mock import MagicMock, patch

from flask import url_for
from flask_testing import TestCase
from llc1_document_api import main
from llc1_document_api.exceptions import ApplicationError
from llc1_document_api.views.v1_0.search import get_email, search_query
from unit_tests.test_models import POLYGON_FC, POLYGON_FC_GC


class TestSearch(TestCase):

    def create_app(self):
        return main.app

    def test_get_email_none(self):
        result = get_email(None, {}, MagicMock(), MagicMock())
        self.assertEqual(result, "N/A")

    def test_get_email_cached(self):
        result = get_email("custard", {"custard": {"email": "an@email.com"}}, MagicMock(), MagicMock())
        self.assertEqual(result, "an@email.com")

    @patch('llc1_document_api.views.v1_0.search.SearchLocalLandChargeService')
    def test_get_email_not_cached(self, mock_sllc):
        mock_sllc.get_user_information.return_value = {"email": "another@email.com"}
        result = get_email("custard", {}, MagicMock(), MagicMock())
        self.assertEqual(result, "another@email.com")

    @patch('llc1_document_api.views.v1_0.search.SearchLocalLandChargeService')
    def test_get_email_not_found(self, mock_sllc):
        mock_sllc.get_user_information.return_value = None
        result = get_email("custard", {}, MagicMock(), MagicMock())
        self.assertEqual(result, None)

    @patch('llc1_document_api.app.validate')
    @patch('llc1_document_api.views.v1_0.search.SearchQuery')
    def test_get_paid_search_query_not_found(self, mock_search_query, extent_validator_mock):
        extent_validator_mock.validate.return_value = True

        mock_search_query.query.filter.return_value.one_or_none.return_value = None

        response = self.client.get(url_for('search.get_paid_search_query', query_id=1),
                                   content_type="application/json",
                                   headers={'Authorization': 'Fake JWT'})
        mock_search_query.query.filter.return_value.one_or_none.assert_called()
        self.assert_status(response, 404)

    @patch('llc1_document_api.app.validate')
    @patch('llc1_document_api.views.v1_0.search.SearchQuery')
    def test_get_paid_search_query_ok(self, mock_search_query, extent_validator_mock):
        extent_validator_mock.validate.return_value = True

        mock_search_query.query.filter.return_value.one_or_none.return_value.to_dict.return_value = {"Rhubarb": "pie"}

        response = self.client.get(url_for('search.get_paid_search_query', query_id=1),
                                   content_type="application/json",
                                   headers={'Authorization': 'Fake JWT'})
        mock_search_query.query.filter.return_value.one_or_none.assert_called()
        self.assert_status(response, 200)
        self.assertEqual(response.json, {"Rhubarb": "pie"})

    @patch('llc1_document_api.app.validate')
    def test_post_paid_search_query_invalid_none_json(self, extent_validator_mock):
        extent_validator_mock.validate.return_value = True

        response = self.client.post(url_for('search.post_paid_search_query'),
                                    data=json.dumps({}),
                                    content_type="application/json",
                                    headers={'Authorization': 'Fake JWT'})

        self.assert_status(response, 400)

    @patch('llc1_document_api.app.validate')
    def test_post_paid_search_query_invalid_json(self, extent_validator_mock):
        extent_validator_mock.validate.return_value = True

        response = self.client.post(url_for('search.post_paid_search_query'),
                                    data=json.dumps({"rhubarb": "custard"}),
                                    content_type="application/json",
                                    headers={'Authorization': 'Fake JWT'})

        self.assert_status(response, 400)

    @patch('llc1_document_api.views.v1_0.search.db')
    @patch('llc1_document_api.views.v1_0.search.SearchQuery')
    @patch('llc1_document_api.views.v1_0.search.Thread')
    @patch('llc1_document_api.app.validate')
    def test_post_paid_search_query_valid_json_gc(self, extent_validator_mock, mock_thread, mock_search_query,
                                                  mock_db):
        extent_validator_mock.validate.return_value = True
        mock_search_query_obj = MagicMock()
        mock_search_query.return_value = mock_search_query_obj
        mock_search_query_obj.to_dict.return_value = {"some": "json"}
        response = self.client.post(url_for('search.post_paid_search_query'),
                                    data=json.dumps({"start_timestamp": "2019-01-01T00:00:00.000",
                                                     "end_timestamp": "2019-01-02T00:00:00.000",
                                                     "extent": POLYGON_FC_GC}),
                                    content_type="application/json",
                                    headers={'Authorization': 'Fake JWT'})

        self.assert_status(response, 202)
        mock_thread.assert_called()
        mock_db.session.add.assert_called_with(mock_search_query_obj)
        mock_db.session.commit.assert_called()
        mock_thread.return_value.start.assert_called()
        response_json = json.loads(response.get_data(as_text=True))
        self.assertEqual(response_json, {'some': 'json'})

    @patch('llc1_document_api.views.v1_0.search.StorageAPIService')
    @patch('llc1_document_api.views.v1_0.search.SearchLocalLandChargeService')
    def test_search_query_ok(self, mock_search_llc, mock_storage):
        mock_session = MagicMock()
        mock_logger = MagicMock()
        mock_requests = MagicMock()
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"source": "SEARCH", "contact_id": "anid"}
        mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.\
            return_value.filter.return_value.order_by.return_value.all.return_value = [
                mock_result
            ]
        mock_storage.save_files.return_value = {"file": [{
            "reference": "filereference",
            "external_reference": "externalfilereference"
        }]}
        mock_search_llc.get_user_information.return_value = {"email": "anemail@someplace.com"}
        mock_search_query = MagicMock()
        mock_session.query.return_value.filter.return_value.one_or_none.return_value = mock_search_query
        search_query(123, datetime.now(), datetime.now(), POLYGON_FC_GC, "anid", mock_session, 1, "abucket",
                     mock_logger, mock_requests)
        mock_session.commit.assert_called()
        mock_storage.save_files.assert_called()
        self.assertEqual(mock_search_query.status, "COMPLETED")
        mock_result.to_dict.assert_called()

    @patch('llc1_document_api.views.v1_0.search.StorageAPIService')
    @patch('llc1_document_api.views.v1_0.search.SearchLocalLandChargeService')
    def test_search_query_ok_fc(self, mock_search_llc, mock_storage):
        mock_session = MagicMock()
        mock_logger = MagicMock()
        mock_requests = MagicMock()
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"source": "SEARCH", "contact_id": "anid"}
        mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.\
            return_value.filter.return_value.order_by.return_value.all.return_value = [
                mock_result
            ]
        mock_storage.save_files.return_value = {"file": [{
            "reference": "filereference",
            "external_reference": "externalfilereference"
        }]}
        mock_search_llc.get_user_information.return_value = {"email": "anemail@someplace.com"}
        mock_search_query = MagicMock()
        mock_session.query.return_value.filter.return_value.one_or_none.return_value = mock_search_query
        search_query(123, datetime.now(), datetime.now(), POLYGON_FC, "anid", mock_session, 1, "abucket",
                     mock_logger, mock_requests)
        mock_session.commit.assert_called()
        mock_storage.save_files.assert_called()
        self.assertEqual(mock_search_query.status, "COMPLETED")
        mock_result.to_dict.assert_called()

    @patch('llc1_document_api.views.v1_0.search.StorageAPIService')
    @patch('llc1_document_api.views.v1_0.search.SearchLocalLandChargeService')
    def test_search_query_ok_geom(self, mock_search_llc, mock_storage):
        mock_session = MagicMock()
        mock_logger = MagicMock()
        mock_requests = MagicMock()
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"source": "SEARCH", "contact_id": "anid"}
        mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.\
            return_value.filter.return_value.order_by.return_value.all.return_value = [
                mock_result
            ]
        mock_storage.save_files.return_value = {"file": [{
            "reference": "filereference",
            "external_reference": "externalfilereference"
        }]}
        mock_search_llc.get_user_information.return_value = {"email": "anemail@someplace.com"}
        mock_search_query = MagicMock()
        mock_session.query.return_value.filter.return_value.one_or_none.return_value = mock_search_query
        search_query(123, datetime.now(), datetime.now(), POLYGON_FC['features'][0]['geometry'], "anid", mock_session,
                     1, "abucket", mock_logger, mock_requests)
        mock_session.commit.assert_called()
        mock_storage.save_files.assert_called()
        self.assertEqual(mock_search_query.status, "COMPLETED")
        mock_result.to_dict.assert_called()

    @patch('llc1_document_api.views.v1_0.search.StorageAPIService')
    @patch('llc1_document_api.views.v1_0.search.SearchLocalLandChargeService')
    def test_search_query_ok_fc_no_contact(self, mock_search_llc, mock_storage):
        mock_session = MagicMock()
        mock_logger = MagicMock()
        mock_requests = MagicMock()
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"source": "SEARCH", "contact_id": "anid"}
        mock_session.query.return_value.filter.return_value.filter.return_value.filter.\
            return_value.filter.return_value.order_by.return_value.all.return_value = [
                mock_result
            ]
        mock_storage.save_files.return_value = {"file": [{
            "reference": "filereference",
            "external_reference": "externalfilereference"
        }]}
        mock_search_llc.get_user_information.return_value = {"email": "anemail@someplace.com"}
        mock_search_query = MagicMock()
        mock_session.query.return_value.filter.return_value.one_or_none.return_value = mock_search_query
        search_query(123, datetime.now(), datetime.now(), POLYGON_FC, None, mock_session, 1, "abucket",
                     mock_logger, mock_requests)
        mock_session.commit.assert_called()
        mock_storage.save_files.assert_called()
        self.assertEqual(mock_search_query.status, "COMPLETED")
        mock_result.to_dict.assert_called()

    @patch('llc1_document_api.views.v1_0.search.StorageAPIService')
    @patch('llc1_document_api.views.v1_0.search.SearchLocalLandChargeService')
    def test_search_query_ok_fc_no_extent(self, mock_search_llc, mock_storage):
        mock_session = MagicMock()
        mock_logger = MagicMock()
        mock_requests = MagicMock()
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"source": "SEARCH", "contact_id": "anid"}
        mock_session.query.return_value.filter.return_value.filter.return_value.filter.\
            return_value.filter.return_value.order_by.return_value.all.return_value = [
                mock_result
            ]
        mock_storage.save_files.return_value = {"file": [{
            "reference": "filereference",
            "external_reference": "externalfilereference"
        }]}
        mock_search_llc.get_user_information.return_value = {"email": "anemail@someplace.com"}
        mock_search_query = MagicMock()
        mock_session.query.return_value.filter.return_value.one_or_none.return_value = mock_search_query
        search_query(123, datetime.now(), datetime.now(), None, "anid", mock_session, 1, "abucket",
                     mock_logger, mock_requests)
        mock_session.commit.assert_called()
        mock_storage.save_files.assert_called()
        self.assertEqual(mock_search_query.status, "COMPLETED")
        mock_result.to_dict.assert_called()

    @patch('llc1_document_api.views.v1_0.search.StorageAPIService')
    @patch('llc1_document_api.views.v1_0.search.SearchLocalLandChargeService')
    def test_search_query_ok_fc_no_extent_no_contact(self, mock_search_llc, mock_storage):
        mock_session = MagicMock()
        mock_logger = MagicMock()
        mock_requests = MagicMock()
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"source": "SEARCH", "contact_id": "anid"}
        mock_session.query.return_value.filter.return_value.filter.\
            return_value.filter.return_value.order_by.return_value.all.return_value = [
                mock_result
            ]
        mock_storage.save_files.return_value = {"file": [{
            "reference": "filereference",
            "external_reference": "externalfilereference"
        }]}
        mock_search_llc.get_user_information.return_value = {"email": "anemail@someplace.com"}
        mock_search_query = MagicMock()
        mock_session.query.return_value.filter.return_value.one_or_none.return_value = mock_search_query
        search_query(123, datetime.now(), datetime.now(), None, None, mock_session, 1, "abucket",
                     mock_logger, mock_requests)
        mock_session.commit.assert_called()
        mock_storage.save_files.assert_called()
        self.assertEqual(mock_search_query.status, "COMPLETED")
        mock_result.to_dict.assert_called()

    @patch('llc1_document_api.views.v1_0.search.StorageAPIService')
    @patch('llc1_document_api.views.v1_0.search.SearchLocalLandChargeService')
    def test_search_query_ok_fc_not_found(self, mock_search_llc, mock_storage):
        mock_session = MagicMock()
        mock_logger = MagicMock()
        mock_requests = MagicMock()
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"source": "SEARCH", "contact_id": "anid"}
        mock_session.query.return_value.filter.return_value.filter.\
            return_value.filter.return_value.order_by.return_value.all.return_value = [
                mock_result
            ]
        mock_storage.save_files.return_value = {"file": [{
            "reference": "filereference",
            "external_reference": "externalfilereference"
        }]}
        mock_search_llc.get_user_information.return_value = {"email": "anemail@someplace.com"}
        mock_search_query = MagicMock()
        mock_session.query.return_value.filter.return_value.one_or_none.return_value = None
        with self.assertRaises(ApplicationError):
            search_query(123, datetime.now(), datetime.now(), None, None, mock_session, 1, "abucket",
                         mock_logger, mock_requests)
        mock_session.commit.assert_not_called()
        mock_storage.save_files.assert_called()
        self.assertNotEqual(mock_search_query.status, "COMPLETED")
        mock_result.to_dict.assert_called()

    @patch('llc1_document_api.views.v1_0.search.StorageAPIService')
    @patch('llc1_document_api.views.v1_0.search.SearchLocalLandChargeService')
    def test_search_query_ok_f(self, mock_search_llc, mock_storage):
        mock_session = MagicMock()
        mock_logger = MagicMock()
        mock_requests = MagicMock()
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"source": "SEARCH", "contact_id": "anid"}
        mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.\
            return_value.filter.return_value.order_by.return_value.all.return_value = [
                mock_result
            ]
        mock_storage.save_files.return_value = {"file": [{
            "reference": "filereference",
            "external_reference": "externalfilereference"
        }]}
        mock_search_llc.get_user_information.return_value = {"email": "anemail@someplace.com"}
        mock_search_query = MagicMock()
        mock_session.query.return_value.filter.return_value.one_or_none.return_value = mock_search_query
        search_query(123, datetime.now(), datetime.now(), POLYGON_FC['features'][0], "anid", mock_session, 1,
                     "abucket", mock_logger, mock_requests)
        mock_session.commit.assert_called()
        mock_storage.save_files.assert_called()
        self.assertEqual(mock_search_query.status, "COMPLETED")
        mock_result.to_dict.assert_called()

    @patch('llc1_document_api.views.v1_0.search.StorageAPIService')
    @patch('llc1_document_api.views.v1_0.search.SearchLocalLandChargeService')
    def test_search_query_exception(self, mock_search_llc, mock_storage):
        mock_session = MagicMock()
        mock_logger = MagicMock()
        mock_requests = MagicMock()
        mock_result = MagicMock()
        mock_result.to_dict.side_effect = Exception("Badness")
        mock_session.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.\
            return_value.filter.return_value.order_by.return_value.all.return_value = [
                mock_result
            ]
        mock_storage.save_files.return_value = {"file": [{
            "reference": "filereference",
            "external_reference": "externalfilereference"
        }]}
        mock_search_llc.get_user_information.return_value = {"email": "anemail@someplace.com"}
        mock_search_query = MagicMock()
        mock_session.query.return_value.filter.return_value.one_or_none.return_value = mock_search_query
        search_query(123, datetime.now(), datetime.now(), POLYGON_FC['features'][0], "anid", mock_session, 1,
                     "abucket", mock_logger, mock_requests)
        mock_session.commit.assert_called()
        mock_storage.save_files.assert_not_called()
        self.assertEqual(mock_search_query.status, "FAILED")
        mock_result.to_dict.assert_called()
