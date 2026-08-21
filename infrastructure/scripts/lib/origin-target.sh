#!/usr/bin/env bash

# Select the origin-side target profile without consuming the caller's arguments.
# Public callers default to the test server; production always requires the
# explicit --production flag.
rbf_origin_select_target() {
  local root_dir="$1"; shift
  local target_environment="test" target_flag_seen="" config_file="" config_explicit=false
  local requested_target index
  local args=("$@")

  for ((index=0; index<${#args[@]}; index++)); do
    case "${args[$index]}" in
      --production|--test)
        requested_target="${args[$index]#--}"
        if [[ -n "$target_flag_seen" && "$target_flag_seen" != "$requested_target" ]]; then
          echo '[origin] --test and --production cannot be combined.' >&2
          return 2
        fi
        target_environment="$requested_target"
        target_flag_seen="$requested_target"
        ;;
      --config)
        if ((index + 1 >= ${#args[@]})); then
          echo '[origin] --config requires a file.' >&2
          return 2
        fi
        config_file="${args[$((index + 1))]}"
        config_explicit=true
        ((index+=1))
        ;;
    esac
  done

  if [[ "$config_explicit" == false ]]; then
    config_file="${RBF_ORIGIN_CONFIG:-$root_dir/.env.origin.$target_environment}"
  fi

  RBF_ORIGIN_TARGET="$target_environment"
  RBF_ORIGIN_CONFIG_FILE="$config_file"
  RBF_ORIGIN_CONFIG_EXPLICIT="$config_explicit"
  export RBF_ORIGIN_TARGET RBF_ORIGIN_CONFIG_FILE RBF_ORIGIN_CONFIG_EXPLICIT
}

# Resolve an operator-entered identity name without ever using the current
# working directory. Bare names and relative paths live below the user's
# private SSH directory; configured absolute paths remain supported.
rbf_origin_resolve_identity_path() {
  local requested="$1"
  [[ -n "$requested" ]] || return 0
  [[ "$requested" != *$'\n'* && "$requested" != *$'\r'* ]] || {
    echo '[origin] SSH identity path must be a single line.' >&2
    return 2
  }
  case "$requested" in
    /*) ;;
    "~/"*)
      [[ -n "${HOME:-}" ]] || { echo '[origin] HOME is required to resolve the SSH identity.' >&2; return 2; }
      requested="$HOME/${requested#~/}"
      ;;
    *)
      [[ -n "${HOME:-}" ]] || { echo '[origin] HOME is required to resolve the SSH identity.' >&2; return 2; }
      requested="$HOME/.ssh/$requested"
      ;;
  esac
  realpath -m -- "$requested"
}

# SSH identities are runtime credentials and must never live anywhere below
# the repository, even when an ignored filename would keep Git from staging it.
rbf_origin_require_external_identity() {
  local root_dir="$1" identity_path="$2" label="${3:-SSH identity}"
  [[ -n "$identity_path" ]] || return 0
  [[ "$identity_path" == /* ]] || {
    echo "[origin] $label must resolve to an absolute path outside the repository." >&2
    return 2
  }
  local normalized_root normalized_identity
  normalized_root="$(realpath -m -- "$root_dir")"
  normalized_identity="$(realpath -m -- "$identity_path")"
  case "$normalized_identity" in
    "$normalized_root"|"$normalized_root"/*)
      echo "[origin] $label must not be stored in the repository: $normalized_identity" >&2
      return 2
      ;;
  esac
}

rbf_origin_default_identity_path() {
  local target_environment="$1" username="$2"
  [[ -n "${HOME:-}" ]] || return 0
  printf '%s/.ssh/rbf-deploy-%s-%s\n' "$HOME" "$target_environment" "$username"
}

# Interactive reconfiguration must recover from profiles created before the
# repository-external identity invariant. Keep valid external identities, but
# replace a legacy repository-local suggestion with the safe target default.
rbf_origin_configure_identity_suggestion() {
  local root_dir="$1" configured_path="$2" target_environment="$3" username="$4"
  local resolved=""
  if [[ -n "$configured_path" ]]; then
    if resolved="$(rbf_origin_resolve_identity_path "$configured_path")" \
        && rbf_origin_require_external_identity "$root_dir" "$resolved" >/dev/null 2>&1; then
      printf '%s\n' "$resolved"
      return 0
    fi
    echo '[origin] Ignoring the legacy repository-local SSH identity during reconfiguration.' >&2
  fi
  rbf_origin_default_identity_path "$target_environment" "$username"
}
