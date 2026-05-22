#!/bin/bash

# Check if flag $1 is in ${@:2}
_lrc_tools_flag_used() {
    local flag="$1"
    shift

    local f
    for f in "$@"; do
      if [[ "$f" == "$flag" ]]; then
        return 0
      fi
    done

    return 1
}

# Walk $words up to $cword, collecting flags into $used_flags and counting
# positional args into $pos_count. $1 = start index, ${@:2} = value-taking flags.
#
# Typical usage:
#   local used_flags pos_count
#   _lrc_tools_collect_args 2 --other --flags -f
_lrc_tools_collect_args() {
  local start_idx=$1
  shift
  local value_flags=("$@")

  used_flags=()
  pos_count=0

  local idx=$start_idx
  while [[ $idx -lt $cword ]]; do
    local w="${words[$idx]}"
    local is_value=false

    for vf in "${value_flags[@]}"; do
      if [[ "$w" == "$vf" ]]; then
        used_flags+=("$w")
        ((idx+=2))
        is_value=true
        break
      fi
    done
    $is_value && continue

    if [[ "$w" == --* || "$w" == -* ]]; then
      used_flags+=("$w")
      ((idx++))
      continue
    fi

    # Non-flag word, could be a value for a preceding flag
    local prev_is_value=false
    if [[ $idx -gt $start_idx ]]; then
      local prev_w="${words[$((idx-1))]}"
      local pvf
      for pvf in "${value_flags[@]}"; do
        if [[ "$prev_w" == "$pvf" ]]; then
          prev_is_value=true
          break
        fi
      done
    fi

    if ! $prev_is_value; then
      ((pos_count++))
    fi
    ((idx++))
  done
}

# Set $prev_is_flag_arg / $prev_flag_name if $prev is a value-taking flag
_lrc_tools_check_prev_flag() {
  prev_is_flag_arg=false
  prev_flag_name=""

  if [[ $cword -ge 3 ]]; then
    local prev_word="${words[$((cword-1))]}"
    case "$prev_word" in
      --lang) prev_is_flag_arg=true; prev_flag_name="lang" ;;
      --output|-o) prev_is_flag_arg=true; prev_flag_name="output" ;;
    esac
  fi
}

# === Subcommand completers ===

_lrc_tools_read()
{
  local cur prev words cword
  _init_completion || return

  if [[ "$cur" == --* ]] || [[ "$cur" == -* ]]; then
    mapfile -t COMPREPLY < <(compgen -W "--include-lang" -- "$cur")
    return
  fi

  local num_args=$((cword - 2))
  if [[ $num_args -eq 0 ]]; then
    _filedir
  elif [[ $num_args -eq 1 ]]; then
    mapfile -t COMPREPLY < <(compgen -W "timed plain" -- "$cur")
  fi
}

_lrc_tools_embed()
{
  local cur prev words cword
  _init_completion || return

  local used_flags pos_count
  _lrc_tools_collect_args 2 "--lang" "--output" "-o"
  _lrc_tools_check_prev_flag

  if $prev_is_flag_arg; then
    case "$prev_flag_name" in
      lang) return 0 ;;
      output) _filedir ;;
    esac
    return
  fi

  if [[ "$cur" == --* ]] || [[ "$cur" == -* ]]; then
    local result=""
    local flag
    if [[ "$cur" == --* ]]; then
      local candidates=(--no-timed --no-plain --in-place --dry-run --lang --output)
    else
      local candidates=(-n -o --no-timed --no-plain --in-place --dry-run --lang --output)
    fi

    for flag in "${candidates[@]}"; do
      if ! _lrc_tools_flag_used "$flag" "${used_flags[@]}"; then
        result="$result $flag"
      fi
    done

    mapfile -t COMPREPLY < <(compgen -W "$result" -- "$cur")
    return
  fi

  if [[ $pos_count -eq 0 ]]; then
    _filedir "mp3"
  elif [[ $pos_count -eq 1 ]]; then
    _filedir "lrc"
  fi
}

_lrc_tools_extract()
{
  local cur prev words cword
  _init_completion || return

  local used_flags pos_count
  _lrc_tools_collect_args 2 "--output" "-o"
  _lrc_tools_check_prev_flag

  if $prev_is_flag_arg; then
    case "$prev_flag_name" in
      output) _filedir ;;
    esac
    return
  fi

  if [[ "$cur" == --* ]] || [[ "$cur" == -* ]]; then
    local result=""
    local flag
    if [[ "$cur" == --* ]]; then
      local candidates=(--output --dry-run)
    else
      local candidates=(-o -n --output --dry-run)
    fi

    for flag in "${candidates[@]}"; do
      if ! _lrc_tools_flag_used "$flag" "${used_flags[@]}"; then
        result="$result $flag"
      fi
    done

    mapfile -t COMPREPLY < <(compgen -W "$result" -- "$cur")
    return
  fi

  if [[ $pos_count -eq 0 ]]; then
    _filedir "mp3"
  elif [[ $pos_count -eq 1 ]]; then
    mapfile -t COMPREPLY < <(compgen -W "timed plain" -- "$cur")
  fi
}

_lrc_tools_clean()
{
  local cur prev words cword
  _init_completion || return

  local used_flags pos_count
  _lrc_tools_collect_args 2

  if [[ "$cur" == --* ]] || [[ "$cur" == -* ]]; then
    local result=""
    local flag
    if [[ "$cur" == --* ]]; then
      local candidates=(--timed-only --plain-only --yes --dry-run)
    else
      local candidates=(-y -n --timed-only --plain-only --yes --dry-run)
    fi

    for flag in "${candidates[@]}"; do
      if ! _lrc_tools_flag_used "$flag" "${used_flags[@]}"; then
        result="$result $flag"
      fi
    done

    mapfile -t COMPREPLY < <(compgen -W "$result" -- "$cur")
    return
  fi

  _filedir "mp3"
}

_lrc_tools_inspect()
{
  local cur prev words cword
  _init_completion || return

  _filedir
}

# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------

_lrc_tools()
{
  local cur prev words cword
  _init_completion || return

  if [[ $cword -eq 1 ]]; then
    mapfile -t COMPREPLY < <(compgen -W "read embed extract clean inspect" -- "$cur")
    return
  fi

  local subcmd="${words[1]}"
  case "$subcmd" in
    read) _lrc_tools_read ;;
    embed) _lrc_tools_embed ;;
    extract) _lrc_tools_extract ;;
    clean) _lrc_tools_clean ;;
    inspect) _lrc_tools_inspect ;;
    *) _filedir ;;
  esac
}

# Register the completion function for lrc_tools
complete -F _lrc_tools lrc_tools
