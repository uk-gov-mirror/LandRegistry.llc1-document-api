from datetime import datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch

from flask import g
from llc1_document_api import main
from llc1_document_api.dependencies.pdf_generation_service import \
    PdfGenerationService
from llc1_document_api.exceptions import ApplicationError
from llc1_document_api.models import SearchItem

mock_lon = {
    "display-id": "LLC-0",
    "item": {
        "charge-type": "Light obstruction notice",
        "documents-filed": {
            "form-a": [
                {
                    "bucket": "lon",
                    "subdirectory": "123"
                }
            ]
        }
    }
}


class TestPdfGenerationService(TestCase):

    @patch('llc1_document_api.dependencies.pdf_generation_service.db')
    @patch('llc1_document_api.dependencies.pdf_generation_service.PDF_GENERATION_API')
    def test_generate_pdf_successful_response(self, mock_config, mock_db):
        with main.app.test_request_context():
            g.trace_id = "test_id"
            g.requests = MagicMock()
            mock_config.return_value = "abc"
            g.requests.post.return_value.status_code = 202
            g.requests.post.return_value.json.return_value = {"status": "generating"}

            mock_reference_item = SearchItem(MagicMock(), "", "")
            mock_reference_item.id = 12
            PdfGenerationService.generate_pdf({"things": "ABC"}, mock_reference_item)
            mock_db.session.add.assert_called_with(mock_reference_item)
            mock_db.session.commit.assert_called()
            self.assertEqual(mock_reference_item.generation_status, "generating")

    @patch('llc1_document_api.dependencies.pdf_generation_service.db')
    @patch('llc1_document_api.dependencies.pdf_generation_service.PDF_GENERATION_API')
    def test_generate_pdf_non_202(self, mock_config, mock_db):
        with main.app.test_request_context():
            g.trace_id = "test_id"
            g.requests = MagicMock()
            mock_config.return_value = "abc"
            g.requests.post.return_value.status_code = 500

            mock_reference_item = SearchItem(MagicMock(), "", "")
            mock_reference_item.id = 12
            PdfGenerationService.generate_pdf({"things": "ABC"}, mock_reference_item)
            mock_db.session.add.assert_called_with(mock_reference_item)
            mock_db.session.commit.assert_called()
            self.assertEqual(mock_reference_item.generation_status, "failed")

    @patch('llc1_document_api.dependencies.pdf_generation_service.db')
    @patch('llc1_document_api.dependencies.pdf_generation_service.PDF_GENERATION_API')
    def test_generate_pdf_exception(self, mock_config, mock_db):
        with main.app.test_request_context():
            g.trace_id = "test_id"
            g.requests = MagicMock()
            mock_config.return_value = "abc"
            g.requests.post.side_effect = ApplicationError("blah", "blah1", 500)

            mock_reference_item = SearchItem(MagicMock(), "", "")
            mock_reference_item.id = 12

            PdfGenerationService.generate_pdf({"things": "ABC"}, mock_reference_item)
            mock_db.session.add.assert_called_with(mock_reference_item)
            mock_db.session.commit.assert_called()
            self.assertEqual(mock_reference_item.generation_status, "failed")

    @patch('llc1_document_api.dependencies.pdf_generation_service.StorageAPIService')
    @patch('llc1_document_api.dependencies.pdf_generation_service.db')
    def test_check_for_results_success_including_lons(self, mock_db, mock_storage_api):
        with main.app.test_request_context():
            g.trace_id = "test_id"
            g.requests = MagicMock()
            mock_storage_api.get_external_url.return_value = 'lons-external-url'
            mock_reference_item = SearchItem(datetime.now(), "Blah", document="abc123",
                                             generation_status="success", external_url="external123",
                                             charges=[mock_lon])
            mock_reference_item.id = 12

            result = PdfGenerationService.check_for_result(mock_reference_item, 60,
                                                           return_supporting_docs=True)

            expected_result = {
                'reference_number': '000 000 012',
                'document_url': 'abc123',
                'supporting_documents': {
                    'LLC-0': 'lons-external-url'
                },
                "external_url": "external123",
                'number_of_charges': 1
            }
            self.assertEqual(result, expected_result)

    @patch('llc1_document_api.dependencies.pdf_generation_service.StorageAPIService')
    @patch('llc1_document_api.dependencies.pdf_generation_service.db')
    def test_check_for_results_failed(self, mock_db, mock_storage_api):
        with main.app.test_request_context():
            g.trace_id = "test_id"
            g.requests = MagicMock()
            mock_reference_item = SearchItem(datetime.now(), "Blah", document="abc123",
                                             generation_status="failed", external_url="external123",
                                             charges=[{}])
            mock_reference_item.id = 12

            with self.assertRaises(ApplicationError):
                PdfGenerationService.check_for_result(mock_reference_item, 5,
                                                      return_supporting_docs=False)

    @patch('llc1_document_api.dependencies.pdf_generation_service.StorageAPIService')
    @patch('llc1_document_api.dependencies.pdf_generation_service.db')
    def test_check_for_results_inprogress(self, mock_db, mock_storage_api):
        with main.app.test_request_context():
            g.trace_id = "test_id"
            g.requests = MagicMock()
            mock_reference_item = SearchItem(datetime.now(), "Blah", document="abc123",
                                             generation_status="generating", external_url="external123",
                                             charges=[{}])
            mock_reference_item.id = 12

            result = PdfGenerationService.check_for_result(mock_reference_item, 5,
                                                           return_supporting_docs=False)
            self.assertIsNone(result)

    @patch('llc1_document_api.dependencies.pdf_generation_service.db')
    def test_callback_success(self, mock_db):
        with main.app.test_request_context():
            g.trace_id = "test_id"
            g.requests = MagicMock()
            mock_reference_item = SearchItem(datetime.now(), "Blah", document="abc123",
                                             generation_status="generating", external_url="external123",
                                             charges=[{}])
            mock_reference_item.id = 12
            PdfGenerationService.callback(mock_reference_item, {"status": "success",
                                                                "result": {
                                                                    "document_url": "doc_url",
                                                                    "included_charges": [{}],
                                                                    "external_url": "ext_url"
                                                                }})

            self.assertEqual(mock_reference_item.charges, [{}])
            self.assertEqual(mock_reference_item.document, "doc_url")
            self.assertEqual(mock_reference_item.external_url, "ext_url")
            self.assertEqual(mock_reference_item.generation_status, "success")

    @patch('llc1_document_api.dependencies.pdf_generation_service.db')
    def test_callback_fail(self, mock_db):
        with main.app.test_request_context():
            g.trace_id = "test_id"
            g.requests = MagicMock()
            mock_reference_item = SearchItem(datetime.now(), "Blah", document="abc123",
                                             generation_status="generating", external_url="external123",
                                             charges=[{}])
            mock_reference_item.id = 12

            with self.assertRaises(ApplicationError):
                PdfGenerationService.callback(mock_reference_item, {"status": "failed"})

            self.assertEqual(mock_reference_item.generation_status, "failed")

    @patch('llc1_document_api.dependencies.pdf_generation_service.db')
    @patch('llc1_document_api.dependencies.pdf_generation_service.PDF_GENERATION_API')
    def test_languages_non_200(self, mock_config, mock_db):
        with main.app.test_request_context():
            g.trace_id = "test_id"
            g.requests = MagicMock()
            mock_config.return_value = "abc"
            g.requests.get.return_value.status_code = 500

            with self.assertRaises(ApplicationError):
                PdfGenerationService.get_languages()

    @patch('llc1_document_api.dependencies.pdf_generation_service.db')
    @patch('llc1_document_api.dependencies.pdf_generation_service.PDF_GENERATION_API')
    def test_languages_ok(self, mock_config, mock_db):
        with main.app.test_request_context():
            g.trace_id = "test_id"
            g.requests = MagicMock()
            mock_config.return_value = "abc"
            g.requests.get.return_value.status_code = 200
            g.requests.get.return_value.text = "languages"

            result = PdfGenerationService.get_languages()
            self.assertEqual("languages", result)
