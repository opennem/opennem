import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

BASE_ENV_FILE_NAME = ".env"


def replace_database_in_url(db_url, db_name):
    """
        replaces the database portion of a database connection URL with db_name

        @param db_name database name to replace with
    """

    db_url_parsed = urlparse(db_url)
    db_url_parsed = db_url_parsed._replace(path=f"/{db_name}")

    return db_url_parsed.geturl()


def load_env_file(environment: str) -> Optional[Path]:
    environment_suffix = environment.strip().lower()

    environment_env_file = "{}.{}".format(
        BASE_ENV_FILE_NAME, environment_suffix
    )

    env_path = Path(os.getcwd()) / Path(environment_env_file)

    if env_path.is_file():
        return env_path

    return None
