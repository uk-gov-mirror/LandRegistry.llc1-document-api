import json

from flask import current_app
from werkzeug.exceptions import HTTPException


class ApplicationError(Exception):

    """Custom error class

    This class is to be raised when the application identifies that there's been a problem
    and that the client should be informed.

    Example:
        raise ApplicationError("Title number invalid", "E102", 400)

    The handler method will then create the response body in a standard structure so clients
    will always know what to parse.
    """

    def __init__(self, message, code, http_code=500):
        Exception.__init__(self)
        self.message = message
        self.http_code = http_code
        self.code = code

    # For ApplicationErrors raised in this API we will submit a response appropriate for our API
    def response(self):
        return json.dumps(
            {
                "error_message": self.message,
                "error_code": self.code
            }
        ), self.http_code, {'Content-Type': 'application/json'}


def unhandled_exception(e):

    if isinstance(e, HTTPException):
        return e

    current_app.logger.exception('Unhandled Exception: %s', repr(e))
    return ApplicationError("Internal Server Error", 500, 500).response()


def application_error(e):
    current_app.logger.warning('Application Exception: %s', repr(e), exc_info=True)
    return e.response()


def register_exception_handlers(app):
    app.register_error_handler(ApplicationError, application_error)
    app.register_error_handler(Exception, unhandled_exception)

    app.logger.info("Exception handlers registered")
