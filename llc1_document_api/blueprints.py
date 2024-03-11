from llc1_document_api.views.general import general
from llc1_document_api.views.v1_0.generate import generate
from llc1_document_api.views.v1_0.search import search


def register_blueprints(app):
    """Adds all blueprint objects into the app."""

    app.register_blueprint(general)
    app.register_blueprint(generate)
    app.register_blueprint(search)

    app.logger.info("Blueprints registered")
