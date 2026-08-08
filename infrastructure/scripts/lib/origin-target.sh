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
