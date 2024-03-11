from unittest import TestCase
from unittest.mock import Mock, patch

from llc1_document_api import blueprints


class TestBlueprints(TestCase):

    @patch('llc1_document_api.blueprints.general')
    @patch('llc1_document_api.blueprints.generate')
    def test_register_blueprints(self, generate_mock, general_mock):
        """Should register the expected blueprints."""
        app_mock = Mock()
        app_mock.register_blueprint = Mock()

        blueprints.register_blueprints(app_mock)

        app_mock.register_blueprint.assert_any_call(generate_mock)
        app_mock.register_blueprint.assert_any_call(general_mock)
