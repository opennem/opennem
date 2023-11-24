#!/usr/bin/env bash
# Sets up a temporary venv for notebook requirements and exports to a requirements file
set -uo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

source $SCRIPT_DIR/_functions.sh

unset _NOTEBOOK_VENV
unset _NOTEBOOK_REQUIREMENTS

_NOTEBOOK_VENV=".venv_notebook"
_NOTEBOOK_REQUIREMENTS="requirements_notebooks.txt"

# _PACKAGES="jupyter seaborn ipywidgets pyoptimus ipython pandas=='1.3.2'"
_PACKAGES="jupyter seaborn"

_checkrequirements() {
  _require_command python
  _require_command pip
}

_promptcontinue() {
  read -p "$1: Are you sure? (N/y) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]
  then
      exit 1
  fi
}

_rmvenv() {
  if [ -d ${_NOTEBOOK_VENV} ]; then
    _promptcontinue "Virtual env exists at ${_NOTEBOOK_VENV}, will delete"
    rm -rf ${_NOTEBOOK_VENV}
    _log "Deleted ${_NOTEBOOK_VENV}"
  else
    _log "${_NOTEBOOK_VENV} doesnt exist. Will create it."
  fi
}

_initvenv() {
  _log "Initializing venv"
  python -m venv ${_NOTEBOOK_VENV}
}

_sourcevenv() {
  if [ ! -z ${VIRTUAL_ENV+x} ]; then
    _log "Running in ${VIRTUAL_ENV}"
    return
  fi

  if [ ! -d ${_NOTEBOOK_VENV} ]; then
    _logerror "Virtualenv not initialized"
    return
  fi

  source ${_NOTEBOOK_VENV}/bin/activate
  _log "Now running in $VIRTUAL_ENV"
}

_installpackages() {
  # fixes for openblas
  export SYSTEM_VERSION_COMPAT=1 \
  LDFLAGS="-L/$(brew --prefix openblas)/lib" \
  CPPFLAGS="-I$(brew --prefix openblas)/include" \
  OPENBLAS="$(brew --prefix openblas)"

  pip install ${_PACKAGES}
}

_export_requirements() {
  pip3 freeze -l > ${_NOTEBOOK_REQUIREMENTS}
  _log "Wrote requirements to ${_NOTEBOOK_REQUIREMENTS}"
}

init_notebook_venv() {
  _log "Initializing notebook venv and exporting"

  _checkrequirements
  _rmvenv

  _initvenv
  _sourcevenv
  _installpackages
  _export_requirements

  _log "Done"
}

init_notebook_venv
