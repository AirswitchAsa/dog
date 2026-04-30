#!/usr/bin/env sh
set -eu

REPO="${DOG_INSTALL_REPO:-AirswitchAsa/dog}"
VERSION="${DOG_INSTALL_VERSION:-latest}"
INSTALL_DIR="${DOG_INSTALL_DIR:-$HOME/.local/bin}"

err() { printf 'error: %s\n' "$*" >&2; exit 1; }
info() { printf '%s\n' "$*" >&2; }

uname_s="$(uname -s)"
uname_m="$(uname -m)"

case "$uname_s" in
  Darwin) os="darwin" ;;
  Linux)  os="linux" ;;
  *)      err "unsupported OS: $uname_s (Windows: download manually from https://github.com/$REPO/releases)" ;;
esac

case "$uname_m" in
  arm64|aarch64) arch="arm64" ;;
  x86_64|amd64)  arch="x64" ;;
  *)             err "unsupported arch: $uname_m" ;;
esac

if [ "$os" = "darwin" ] && [ "$arch" = "x64" ]; then
  err "Intel macOS binaries are not published. Install via: uv tool install dog-cli  (or: pip install dog-cli)"
fi

asset="dog-${os}-${arch}"

if [ "$VERSION" = "latest" ]; then
  url="https://github.com/${REPO}/releases/latest/download/${asset}"
else
  url="https://github.com/${REPO}/releases/download/${VERSION}/${asset}"
fi

command -v curl >/dev/null 2>&1 || err "curl is required"
mkdir -p "$INSTALL_DIR"

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

info "downloading $asset from $url"
if ! curl -fsSL --retry 3 -o "$tmp" "$url"; then
  err "download failed (asset may not exist for this platform: $asset)"
fi

target="$INSTALL_DIR/dog"
mv "$tmp" "$target"
chmod +x "$target"
trap - EXIT

info "installed: $target"

case ":$PATH:" in
  *":$INSTALL_DIR:"*) ;;
  *) info "warning: $INSTALL_DIR is not on PATH. Add it, e.g.: export PATH=\"$INSTALL_DIR:\$PATH\"" ;;
esac

"$target" --help >/dev/null 2>&1 || err "installed binary failed self-check"
info "ok: run 'dog --help' to verify"
