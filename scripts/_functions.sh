# Misc functions for the various shell scripts in the repo

unset RED
unset GREEN
unset RESET
unset BOLD

RED=`tput setaf 1`
GREEN=`tput setaf 2`
RESET=`tput sgr0`
BOLD=$(tput bold)


fmt_underline() {
  printf '\033[4m%s\033[24m\n' "$*"
}

fmt_code() {
  # shellcheck disable=SC2016 # backtic in single-quote
  printf '`\033[38;5;247m%s%s`\n' "$*" "$RESET"
}

_logerror() {
  printf '%s[ERROR]: %s%s\n' "$BOLD$RED" "$*" "$RESET" >&2
}

_loggreen() {
  printf '%s[ERROR]: %s%s\n' "$BOLD$GREEN" "$*" "$RESET" >&2
}

_log() {
    printf "%s[INFO ]: %s%s\n" "$BOLD$GREEN" "$*" "$RESET" >&1
}

_command_exists() {
	command -v "$@" >/dev/null 2>&1
}

_require_command() {
  if ! command -v $1 &> /dev/null
  then
      echo "$1 could not be found and is required"
      exit
  fi
}
