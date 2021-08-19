set -uo pipefail

# Links the out of project directory venv locally

VENV_PATH=".venv"

if [ -d $VENV_PATH ]
then
  echo "virtualenv exists"
  exit -1
fi

_POETRY_ENV_PATH=`poetry env info -p`

if [ ! $? -eq 0 ]
then
  echo "No poetry environments listed"
  exit -1
fi

ln -s $_POETRY_ENV_PATH .venv

echo "Created .venv"
