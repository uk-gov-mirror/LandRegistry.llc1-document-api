from flask_testing import TestCase
from llc1_document_api import main
from llc1_document_api.exceptions import ApplicationError


class TestExceptions(TestCase):

    def create_app(self):
        return main.app

    def test_application_error_init_default_http_code(self):
        with main.app.app_context():
            error = ApplicationError("test message", "abc")

            self.assertEqual(error.message, "test message")
            self.assertEqual(error.code, "abc")
            self.assertEqual(error.http_code, 500)

    def test_application_error_init_set_http_code(self):
        with main.app.app_context():
            error = ApplicationError("test message", "abc", 400)

            self.assertEqual(error.message, "test message")
            self.assertEqual(error.code, "abc")
            self.assertEqual(error.http_code, 400)
