# LLC1 Document API

This is the repository for the LLC1 API used to collate the information required to generate an LLC1 document. This application is built to run on our common development environment (common dev-env), which you can read more about here: https://github.com/LandRegistry/common-dev-env


### Documentation

The API has been documented using swagger YAML files. 

The swagger files can be found under the [documentation](llc1_document_api/documentation) directory.

At present the documentation is not hooked into any viewer within the dev environment. To edit or view the 
documentation open the YAML file in swagger.io <http://editor.swagger.io>

## Linting

Linting is performed with [Flake8](http://flake8.pycqa.org/en/latest/). To run linting:
```
docker-compose exec llc1-document-api make lint
```
