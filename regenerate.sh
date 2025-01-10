#!/bin/bash
set -eu

API_URL="http://ai-prompt-service.staging.openeduhub.net/v3/api-docs"

# check if program openapi-python-client exists
if ! command -v openapi-python-client &> /dev/null
then
    echo "openapi-python-client could not be found"
    echo "Please install openapi-python-client by running"
    echo "pipx install openapi-python-client --include-deps"
    exit
fi

rm -rf ./zapi/
if [ -f README.md ]; then
    mv README.md README.md.bak
fi
python3 cleanup-openapi.py --url "$API_URL" > api-docs.json
openapi-python-client generate --path api-docs.json --config openapi-python.yaml --output-path . --overwrite
if [ -f README.md.bak ]; then
    mv README.md.bak README.md
fi
