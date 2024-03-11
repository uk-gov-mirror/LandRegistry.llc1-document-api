# Set the base image to the s2i image
FROM docker-registry/stp/stp-s2i-python-extended:3.9

# Development environment values
# These values are not the same as our production environment
ENV APP_NAME=llc1-document-api \
    LOG_LEVEL="DEBUG" \
    PDF_GENERATION_API="http://pdf-generation-api:8080/v1.0/llc1" \
    PDF_GENERATION_API_ROOT="http://pdf-generation-api:8080" \
    STORAGE_API="http://storage-api:8080/v1.0/storage" \
    SQL_HOST="postgres-13" \
    SQL_DATABASE="llc_document_db" \
    SQL_PASSWORD="llc_document_password" \
    APP_SQL_USERNAME="llc_document_user" \
    SQL_USE_ALEMBIC_USER="false" \
    ALEMBIC_SQL_USERNAME="root" \
    _DEPLOY_SQL_PASSWORD="superroot" \
    MAX_HEALTH_CASCADE=6 \
    AUTHENTICATION_API_URL="http://dev-search-authentication-api:8080/v2.0" \
    AUTHENTICATION_API_ROOT="http://dev-search-authentication-api:8080" \
    STORAGE_API_ROOT="http://storage-api:8080" \
    REPORT_API_SQL_USERNAME="llc_document_report_user" \
    REPORT_API_SQL_PASSWORD="llc_document_report_password" \
    SQLALCHEMY_POOL_RECYCLE="3300" \
    ASYNC_PDF_TIMEOUT="300" \
    CALLBACK_PREFIX="http://llc1-document-api:8080" \
    APP_MODULE='llc1_document_api.main:app' \
    FLASK_APP='llc1_document_api.main' \
    GUNICORN_ARGS='--reload' \
    WEB_CONCURRENCY='2' \
    SEARCH_LOCAL_LAND_CHARGE_API_URL="http://search-local-land-charge-api:8080" \
    SEARCH_QUERY_BUCKET="paid-search-query" \
    SEARCH_QUERY_TIMEOUT="900" \
    DEFAULT_TIMEOUT="30" \
    PYTHONPATH=/src
# Switch from s2i's non-root user back to root for the following commmands
USER root

# Create a user that matches dev-env runner's host user
# And ensure they have access to the jar folder at runtime
ARG OUTSIDE_UID
ARG OUTSIDE_GID
RUN groupadd --force --gid $OUTSIDE_GID containergroup && \
 useradd --uid $OUTSIDE_UID --gid $OUTSIDE_GID containeruser

ADD requirements_test.txt requirements_test.txt
ADD requirements.txt requirements.txt
RUN pip3 install -r requirements.txt && \
    pip3 install -r requirements_test.txt

# Set the user back to a non-root user like the s2i run script expects
# When creating files inside the docker container, this will also prevent the files being owned
# by the root user, which would cause issues if running on a Linux host machine
USER containeruser

CMD ["/usr/libexec/s2i/run"]
