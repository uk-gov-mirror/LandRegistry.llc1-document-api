import json
from unittest.mock import MagicMock, patch

from flask import url_for
from flask_testing import TestCase
from llc1_document_api import main
from llc1_document_api.models import SearchItem


class TestGenerate(TestCase):

    def create_app(self):
        return main.app

    @patch('llc1_document_api.app.validate')
    @patch('llc1_document_api.views.v1_0.generate.PayloadValidator')
    def test_generate_diff_format_no_charges(self, extent_validator_mock, validate):
        extent_validator_mock.validate.return_value = True

        with main.app.app_context():
            response = self.client.post(url_for('generate.generate_llc1_async'),
                                        data=json.dumps({"source": "LLC1 Unit Test", "format": "JSON"}),
                                        content_type="application/json",
                                        headers={'Authorization': 'Fake JWT'})

            self.assert_status(response, 400)

    @patch('llc1_document_api.app.validate')
    @patch('llc1_document_api.views.v1_0.generate.PayloadValidator')
    @patch('llc1_document_api.views.v1_0.generate.db')
    def test_generate_diff_format(
        self, mock_db, extent_validator_mock, validate
    ):
        expected_response = {"search_reference": "000 000 010", "status": "created"}

        extent_validator_mock.validate.return_value = True
        mock_db.session.add = mock_add_add_id

        with main.app.app_context():
            response = self.client.post(url_for('generate.generate_llc1_async'),
                                        data=json.dumps({"source": "LLC1 Unit Test", "format": "JSON", "charges": []}),
                                        content_type="application/json",
                                        headers={'Authorization': 'Fake JWT'})

            response_json = json.loads(response.get_data(as_text=True))
            self.assert_status(response, 201)
            mock_db.session.commit.assert_called()
            self.assertEqual(response_json, expected_response)

    @patch('llc1_document_api.app.validate')
    @patch('llc1_document_api.views.v1_0.generate.PayloadValidator')
    @patch('llc1_document_api.views.v1_0.generate.db')
    def test_generate_diff_format_except(
        self, mock_db, extent_validator_mock, validate
    ):
        expected_response = {'error_code': 'LLC1-01', 'error_message': 'Error recording LLC1'}

        extent_validator_mock.validate.return_value = True
        mock_db.session.add.side_effect = Exception("Nooooo")

        with main.app.app_context():
            response = self.client.post(url_for('generate.generate_llc1_async'),
                                        data=json.dumps({"source": "LLC1 Unit Test", "format": "JSON", "charges": []}),
                                        content_type="application/json",
                                        headers={'Authorization': 'Fake JWT'})

            response_json = json.loads(response.get_data(as_text=True))
            self.assert_status(response, 500)
            mock_db.session.commit.assert_not_called()
            mock_db.session.rollback.assert_called()
            self.assertEqual(response_json, expected_response)

    @patch('llc1_document_api.app.validate')
    @patch('llc1_document_api.views.v1_0.generate.PayloadValidator')
    @patch('llc1_document_api.views.v1_0.generate.PdfGenerationService')
    def test_generate_async(
        self, mock_pdf, extent_validator_mock, validate
    ):
        expected_response = {"search_reference": "000 000 010", "status": "generating"}

        extent_validator_mock.validate.return_value = True
        mock_pdf.generate_pdf = mock_generate_pdf_add_id

        response = self.client.post(url_for('generate.generate_llc1_async'),
                                    data=json.dumps({"source": "LLC1 Unit Test"}),
                                    content_type="application/json",
                                    headers={'Authorization': 'Fake JWT'})

        response_json = json.loads(response.get_data(as_text=True))
        self.assert_status(response, 202)
        self.assertEqual(response_json, expected_response)

    @patch('llc1_document_api.app.validate')
    @patch('llc1_document_api.views.v1_0.generate.PdfGenerationService')
    @patch('llc1_document_api.views.v1_0.generate.SearchItem')
    def test_poll_llc1_not_found(self, mock_search_item, mock_pdf, validate):

        mock_search_item.query.get.return_value = None

        response = self.client.get(url_for('generate.poll_llc1', search_ref="000 000 010",
                                           return_supporting_docs=True),
                                   content_type="application/json",
                                   headers={'Authorization': 'Fake JWT'})

        response_json = json.loads(response.get_data(as_text=True))
        self.assert_status(response, 404)
        self.assertEqual(response_json, {'error_code': 'POL-01',
                                         "error_message": "Requested search reference not found"})

    @patch('llc1_document_api.app.validate')
    @patch('llc1_document_api.views.v1_0.generate.PdfGenerationService')
    @patch('llc1_document_api.views.v1_0.generate.SearchItem')
    def test_poll_llc1_not_finished(self, mock_search_item, mock_pdf, validate):

        mock_search_item.query.get.return_value = SearchItem(MagicMock(), "", "")

        mock_pdf.check_for_result.return_value = None

        response = self.client.get(url_for('generate.poll_llc1', search_ref="000 000 010",
                                           return_supporting_docs=True),
                                   content_type="application/json",
                                   headers={'Authorization': 'Fake JWT'})

        response_json = json.loads(response.get_data(as_text=True))
        self.assert_status(response, 202)
        self.assertEqual(response_json, {'status': 'generating'})

    @patch('llc1_document_api.app.validate')
    @patch('llc1_document_api.views.v1_0.generate.PdfGenerationService')
    @patch('llc1_document_api.views.v1_0.generate.SearchItem')
    def test_poll_llc1_ok(self, mock_search_item, mock_pdf, validate):

        mock_search_item.query.get.return_value = SearchItem(MagicMock(), "", "")

        mock_pdf.check_for_result.return_value = {"a": "result"}

        response = self.client.get(url_for('generate.poll_llc1', search_ref="000 000 010",
                                           return_supporting_docs=True),
                                   content_type="application/json",
                                   headers={'Authorization': 'Fake JWT'})

        response_json = json.loads(response.get_data(as_text=True))
        self.assert_status(response, 201)
        self.assertEqual(response_json, {"a": "result"})

    @patch('llc1_document_api.app.validate')
    def test_callback_llc1_invalid(self, validate):

        response = self.client.post(url_for('generate.callback_llc1', search_ref="000 000 010",),
                                    data=json.dumps({"statuf": "doesn't", "result": {"matter": "here"}}),
                                    content_type="application/json",
                                    headers={'Authorization': 'Fake JWT'})

        response_json = json.loads(response.get_data(as_text=True))
        self.assert_status(response, 400)
        self.assertEqual(response_json, {'error_code': None, 'error_message': 'The request body was invalid'})

    @patch('llc1_document_api.app.validate')
    @patch('llc1_document_api.views.v1_0.generate.SearchItem')
    def test_callback_llc1_not_found(self, mock_search_item, validate):
        with main.app.test_request_context():

            mock_search_item.query.get.return_value = None

            response = self.client.post(url_for('generate.callback_llc1', search_ref="000 000 010",),
                                        data=json.dumps({"status": "doesn't", "result": {"matter": "here"}}),
                                        content_type="application/json",
                                        headers={'Authorization': 'Fake JWT'})

            response_json = json.loads(response.get_data(as_text=True))
            self.assert_status(response, 404)
            self.assertEqual(response_json, {'error_code': 'CBAC-01',
                                             "error_message": "Requested search reference not found"})

    @patch('llc1_document_api.app.validate')
    @patch('llc1_document_api.views.v1_0.generate.PdfGenerationService')
    @patch('llc1_document_api.views.v1_0.generate.SearchItem')
    def test_callback_llc1_ok(self, mock_search_item, mock_pdf, validate):
        with main.app.test_request_context():

            mock_search_item.query.get.return_value = SearchItem(MagicMock(), "", "")

            response = self.client.post(url_for('generate.callback_llc1', search_ref="000 000 010",),
                                        data=json.dumps({"status": "doesn't", "result": {"matter": "here"}}),
                                        content_type="application/json",
                                        headers={'Authorization': 'Fake JWT'})

            mock_pdf.callback.assert_called()
            response_json = json.loads(response.get_data(as_text=True))
            self.assert_status(response, 202)
            self.assertEqual(response_json, {"status": "accepted"})

    @patch('llc1_document_api.views.v1_0.generate.PdfGenerationService')
    @patch('llc1_document_api.app.validate')
    def test_languages(self, mock_validate, mock_pdf):
        with main.app.test_request_context():

            mock_pdf.get_languages.return_value = '{"en": "English"}'

            response = self.client.get(url_for('generate.llc1_languages'),
                                       headers={'Authorization': 'Fake JWT'})

            response_json = json.loads(response.get_data(as_text=True))
            self.assert_status(response, 200)
            self.assertEqual(response_json, {"en": "English"})


def mock_add_add_id(search_item):
    search_item.id = 10


def mock_generate_pdf_add_id(request, search_item):
    search_item.id = 10
    search_item.generation_status = "generating"
