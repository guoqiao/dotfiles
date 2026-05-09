#!/usr/bin/env bash

set -ueo pipefail

echo "use these env vars to config your git user:"
cat << EOF
export GIT_AUTHOR_NAME="${USER}"
export GIT_AUTHOR_EMAIL="${USER}@$(hostname)"
export GIT_COMMITTER_NAME="${USER}"
export GIT_COMMITTER_EMAIL="${USER}@$(hostname)"
EOF

