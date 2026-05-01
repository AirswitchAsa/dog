# Install

DOG ships in three forms: an agent skill, a CLI (prebuilt binary or PyPI package), and source.

## Agent skill

The skill teaches coding agents (Claude Code, Cursor, Codex, etc.) how to navigate `.dog.md` specs as a source of truth. It is the recommended starting point if your goal is agent integration.

```bash
npx skills add https://github.com/AirswitchAsa/dog/tree/main/skills/dog
```

The skill ([`skills/dog`](../../skills/dog/)) auto-bootstraps the CLI: it prefers an installed `dog` binary, falling back to `uvx --from dog-cli dog` if no binary is on the PATH.

## CLI: prebuilt binary

For macOS (Apple Silicon) and Linux (glibc 2.35+):

```bash
curl -fsSL https://raw.githubusercontent.com/AirswitchAsa/dog/main/scripts/install.sh | sh
```

The installer drops `dog` into `~/.local/bin`. Override the location with `DOG_INSTALL_DIR`. Pin a specific version with `DOG_INSTALL_VERSION=v2026.4.30`.

**Windows:** download `dog-windows-x64.exe` from [Releases](https://github.com/AirswitchAsa/dog/releases/latest) and place it on your PATH.

**Intel macOS:** prebuilt binaries are not published — install via PyPI instead.

> **macOS note:** binaries are unsigned. The `curl | sh` installer above clears Gatekeeper for you. If you download via browser, run `xattr -d com.apple.quarantine ~/.local/bin/dog` once, or install via `pip` / `uv`.

## CLI: PyPI

```bash
pip install dog-cli
# or:
uv tool install dog-cli
# or, ephemeral:
uvx --from dog-cli dog --help
```

Use `uvx --from dog-cli dog` (not `uvx dog-cli`) for ephemeral execution — the package name and the executable name differ.

## Build from source

```bash
uv sync --group dev
scripts/build-binary.sh                          # standalone (dist-bin/dog_cli.dist/dog)
DOG_NUITKA_MODE=onefile scripts/build-binary.sh  # single file (dist-bin/dog)
```

Release binaries are produced by the [Release Binaries](../../.github/workflows/release.yml) workflow on tag push (`v*`) or manual dispatch — matrix-builds onefile binaries for macOS arm64, Linux x64/arm64 (glibc 2.35+), and Windows x64.

## Verify the install

```bash
dog --version
dog lint docs   # if you already have a docset
```
