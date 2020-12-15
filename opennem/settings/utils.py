import os
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

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


def _is_env_file(env_file_path: str) -> bool:
    """
    Checks if env file exists in current working directory
    """
    return (_cwd / Path(env_file_path)).is_file()


def load_env_file(environment: Optional[str]) -> List[str]:
    """
    Returns a list of env files to load
    """
    env_files = [BASE_ENV_FILE_NAME]

    if environment:
        environment_suffix = environment.strip().lower()

        env_files.append(
            "{}.{}".format(BASE_ENV_FILE_NAME, environment_suffix)
        )

    env_files_exist = [str(i) for i in env_files if _is_env_file(i)]

    return env_files_exist
