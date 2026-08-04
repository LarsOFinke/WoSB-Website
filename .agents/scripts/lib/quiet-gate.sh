#!/usr/bin/env bash

agent_run_quiet() (
  local label="$1"
  shift

  if [[ "${AGENT_GATE_VERBOSE:-0}" == 1 ]]; then
    printf '[agent-gate] Start: %s\n' "$label"
    "$@"
    return
  fi

  local output exit_code
  output="$(mktemp /tmp/rbf-agent-gate.XXXXXX)"
  trap 'rm -f "$output"' EXIT
  if "$@" >"$output" 2>&1; then
    printf '[agent-gate] OK: %s\n' "$label"
    return 0
  else
    exit_code=$?
  fi

  printf '[agent-gate] FEHLER: %s (Exit %d)\n' "$label" "$exit_code" >&2
  printf '[agent-gate] Letzte %s Logzeilen:\n' "${AGENT_GATE_FAILURE_LINES:-200}" >&2
  tail -n "${AGENT_GATE_FAILURE_LINES:-200}" "$output" >&2
  return "$exit_code"
)
