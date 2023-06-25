import os
from pathlib import Path
from urllib.parse import urlparse

from opennem.utils.project_path import get_project_path

BASE_ENV_FILE_NAME = ".env"


def replace_database_in_url(db_url: str, db_name: str) -> str:
    """
    replaces the database portion of a database connection URL with db_name

    @param db_name database name to replace with
    """

    db_url_parsed = urlparse(db_url)
    db_url_parsed = db_url_parsed._replace(path=f"/{db_name}")

    return db_url_parsed.geturl()


# cache cwd
_cwd = Path(os.getcwd())
_project_path = get_project_path()


def _is_env_file(env_file_path: str) -> bool:
    """
    Checks if env file exists in current working directory
    """
    return (_project_path / Path(env_file_path)).is_file()


def load_env_file(environment: str | None = None) -> list[str]:
    """
    Returns a list of env files to load
    """
    env_files = [BASE_ENV_FILE_NAME]

    if environment:
        environment_suffix = environment.strip().lower()

        env_files.append(f"{BASE_ENV_FILE_NAME}.{environment_suffix}")

    env_files_exist = [str(i) for i in env_files if _is_env_file(i)]

    return env_files_exist
