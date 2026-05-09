#!/usr/bin/env bash

set -ueo pipefail

if [[ -t 0 ]]; then
  # no stdin → use arg
  PROMPT="$1"
else
  # stdin provided
  PROMPT="$(cat)"
fi

# if ENVRC_FILE exists, source it
ENVRC_FILE="${ENVRC_FILE:-.envrc}"
[[ -n "${ENVRC_FILE}" && -e "${ENVRC_FILE}" ]] && source ${ENVRC_FILE} || true

JSON=$(jq -n \
  --arg model "$OPENAI_MODEL" \
  --arg content "$PROMPT" \
  '{
    model: $model,
    messages: [
      {
        role: "user",
        content: $content
      }
    ]
  }')

echo ${JSON} | jq | tee request.json

/usr/bin/time -p curl -fsSL ${OPENAI_BASE_URL}/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -d "${JSON}" | jq | tee response.json

echo '<think>'
jq -r '.choices[0].message.reasoning_content' response.json
echo '</think>'

jq -r '.choices[0].message.content' response.json

