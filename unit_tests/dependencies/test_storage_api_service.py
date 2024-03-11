from unittest import TestCase
from unittest.mock import MagicMock

from flask import current_app, g
from llc1_document_api import main
from llc1_document_api.dependencies.storage_api_service import \
    StorageAPIService
from llc1_document_api.exceptions import ApplicationError


class TestStorageApiService(TestCase):

    def test_get_external_url_successful(self):
        with main.app.test_request_context():
            g.trace_id = "test_id"
            g.requests = MagicMock()
            current_app.config['STORAGE_API'] = "http://test.com"

            g.requests.get.return_value.status_code = 200
            g.requests.get.return_value.json.return_value = {'external_reference': 'test-reference'}

            result = StorageAPIService.get_external_url('file', 'bucket')

            self.assertIsNotNone(result)
            self.assertEqual('test-reference', result)

    def test_get_external_url_successful_subdirs(self):
        with main.app.test_request_context():
            g.trace_id = "test_id"
            g.requests = MagicMock()
            current_app.config['STORAGE_API'] = "http://test.com"

            g.requests.get.return_value.status_code = 200
            g.requests.get.return_value.json.return_value = {'external_reference': 'test-reference'}

            result = StorageAPIService.get_external_url('file', 'bucket', 'dir')

            self.assertIsNotNone(result)
            self.assertEqual('test-reference', result)

    def test_get_external_url_404(self):
        with main.app.test_request_context():
            g.trace_id = "test_id"
            g.requests = MagicMock()
            current_app.config['STORAGE_API'] = "http://test.com"

            g.requests.get.return_value.status_code = 404

            result = StorageAPIService.get_external_url('file', 'bucket')

            self.assertIsNone(result)

    def test_get_external_url_500(self):
        with main.app.test_request_context():
            g.trace_id = "test_id"
            g.requests = MagicMock()
            current_app.config['STORAGE_API'] = "http://test.com"

            g.requests.get.return_value.status_code = 500

            self.assertRaises(ApplicationError, StorageAPIService.get_external_url, 'file', 'bucket')

    def test_save_files_ok(self):
        with main.app.test_request_context():
            g.trace_id = "test_id"
            g.requests = MagicMock()
            mock_response = MagicMock()
            g.requests.post.return_value = mock_response
            mock_response.status_code = 201
            mock_response.json.return_value = {"some": "json"}
            result = StorageAPIService.save_files('files', 'bucket')
            self.assertEqual(result, {"some": "json"})
            g.requests.post.assert_called()

    def test_save_files_bad(self):
        with main.app.test_request_context():
            g.trace_id = "test_id"
            g.requests = MagicMock()
            mock_response = MagicMock()
            g.requests.post.return_value = mock_response
            mock_response.status_code = 202
            mock_response.json.return_value = {"some": "json"}
            with self.assertRaises(ApplicationError):
                result = StorageAPIService.save_files('files', 'bucket')
                self.assertEqual(result, {"some": "json"})
                g.requests.post.assert_called()
