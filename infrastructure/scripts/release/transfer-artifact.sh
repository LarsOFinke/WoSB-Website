#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  echo "Usage: $0 ARTIFACT USER@HOST TARGET_DIRECTORY [PORT]" >&2
  exit 2
}
[[ $# -ge 3 && $# -le 4 ]] || usage

artifact="$1"
target="$2"
directory="$3"
port="${4:-22}"
[[ -f "$artifact" ]] || { echo "Artefakt nicht gefunden: $artifact" >&2; exit 1; }
[[ "$directory" == /* && "$directory" != *$'\n'* && "$directory" != *' '* ]] || { echo "Zielverzeichnis muss ein absoluter, einzeiliger Pfad ohne Leerzeichen sein." >&2; exit 2; }

name="$(basename "$artifact")"
ssh_args=(-p "$port" -o BatchMode=yes -o StrictHostKeyChecking=yes)
scp_args=(-P "$port" -o BatchMode=yes -o StrictHostKeyChecking=yes)
ssh "${ssh_args[@]}" "$target" "install -d -m 0750 -- $(printf '%q' "$directory")"
scp "${scp_args[@]}" "$artifact" "$target:$directory/$name"
echo "Übertragen: $target:$directory/$name"
