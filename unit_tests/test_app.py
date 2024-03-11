from unittest import TestCase
from unittest.mock import Mock, patch

from flask import g
from llc1_document_api import app, main
from llc1_document_api.exceptions import ApplicationError


class TestApp(TestCase):

    TRACE_ID = 'some trace id'
    X_API_Version = '1.0.0'

    @patch('llc1_document_api.app.validate')
    @patch('llc1_document_api.app.uuid')
    @patch('llc1_document_api.app.RequestsSessionTimeout')
    def test_before_request(self, requests_mock, uuid_mock, validate):
        """Should set a uuid trace id, update the trace id on global, and assign the session to the global object."""

        with main.app.app_context():
            with main.app.test_request_context(headers={
                "X-Trace-ID": self.TRACE_ID,
                "Authorization": "Fake JWT"
            }):

                session_mock = Mock()
                requests_mock.return_value = session_mock

                app.before_request()

                self.assertEqual(g.trace_id, self.TRACE_ID)
                self.assertEqual(g.requests, session_mock)

                g.requests.headers.update.assert_any_call({'Authorization': "Fake JWT"})
                g.requests.headers.update.assert_any_call({'X-Trace-ID': self.TRACE_ID})

    def test_after_request(self):
        """Should set the X-API-Version to the expected value."""
        response_mock = Mock()
        response_mock.headers = {
            "X-API-Version": None
        }
        result = app.after_request(response_mock)

        self.assertEqual(result.headers["X-API-Version"], self.X_API_Version)

    @patch('llc1_document_api.app.validate')
    @patch('llc1_document_api.app.uuid')
    @patch('llc1_document_api.app.RequestsSessionTimeout')
    def test_before_request_no_auth(self, requests_mock, uuid_mock, validate):
        """Should set a uuid trace id, update the trace id on global, and assign the session to the global object."""
        with main.app.app_context():
            with main.app.test_request_context(headers={
                "X-Trace-ID": self.TRACE_ID,
            }):

                session_mock = Mock()
                requests_mock.return_value = session_mock

                with self.assertRaises(ApplicationError):
                    app.before_request()
