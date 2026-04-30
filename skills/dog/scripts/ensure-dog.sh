#!/usr/bin/env sh
set -eu

if command -v dog >/dev/null 2>&1 && dog --help >/dev/null 2>&1; then
  if [ "$#" -eq 0 ]; then
    printf '%s\n' "dog"
    exit 0
  fi
  exec dog "$@"
fi

if command -v uvx >/dev/null 2>&1; then
  if uvx --from dog-cli dog --help >/dev/null 2>&1; then
    if [ "$#" -eq 0 ]; then
      printf '%s\n' "uvx --from dog-cli dog"
      exit 0
    fi
    exec uvx --from dog-cli dog "$@"
  fi
fi

cat >&2 <<'EOF'
DOG CLI is not available.

Install it with one of:
  curl -fsSL https://raw.githubusercontent.com/AirswitchAsa/dog/main/scripts/install.sh | sh
  uv tool install dog-cli
  pip install dog-cli

Or run it ephemerally when uvx is available:
  uvx --from dog-cli dog <command>
EOF
exit 1
