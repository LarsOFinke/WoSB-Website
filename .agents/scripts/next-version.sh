#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
classification="${1:-}"

case "$classification" in
  patch|minor|major) ;;
  *) echo "Usage: bash .agents/scripts/next-version.sh patch|minor|major" >&2; exit 2 ;;
esac

version="$(tr -d '[:space:]' < "$ROOT_DIR/VERSION")"
[[ "$version" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]] || {
  echo "Invalid repository version: $version" >&2
  exit 1
}
major="${BASH_REMATCH[1]}"
minor="${BASH_REMATCH[2]}"
patch="${BASH_REMATCH[3]}"

case "$classification" in
  patch) patch=$((patch + 1)) ;;
  minor) minor=$((minor + 1)); patch=0 ;;
  major) major=$((major + 1)); minor=0; patch=0 ;;
esac

printf '%s.%s.%s\n' "$major" "$minor" "$patch"
