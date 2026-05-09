#!/usr/bin/env bash

set -xueo pipefail

curl -fsSL ${OPENAI_BASE_URL}/models \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" | jq

