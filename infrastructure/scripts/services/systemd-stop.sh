#!/usr/bin/env bash
set -Eeuo pipefail

# Keep stopped containers and their logs available after a failed oneshot
# startup. The operator-facing stop.sh intentionally removes the stack, but
# systemd must not destroy diagnostics while handling ExecStop after a failed
# ExecStart.
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/docker.sh"
bw_compose_with_profiles stop "$@"
