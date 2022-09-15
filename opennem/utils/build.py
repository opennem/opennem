"""OpenNEM build utils. Called in user scripts with common commands"""
import logging
from os.path import commonprefix
from pathlib import Path
from typing import Callable, List

from gitignore_parser import parse_gitignore

from opennem import PROJECT_PATH
from opennem.settings import settings  # noqa: F401

logger = logging.getLogger("opennem.utils.build")

# These are the file matches that we're cleaning
_CLEAN_GLOBS = ["__pycache__", "*.py[co]", "*.egg-info"]

_IGNORE_PATHS = [".venv", ".tox", ".git"]

IGNORE_PATHS_FULL = None

TEST = None


def read_gitignore() -> Callable:
    """Reads the gitignore file and returns a method that can check if a path
    matches the globs"""
    _gitignore_path = PROJECT_PATH / ".gitignore"

    if not _gitignore_path.is_file():
        logger.warning("Could not find an ignore file at: {}".format(_gitignore_path))
        return lambda x: False

    gitignores = parse_gitignore(_gitignore_path)

    return gitignores


def _build_ignore_matcher() -> List[Path]:
    _d = []

    for ignore_path in _IGNORE_PATHS:
        ignore_full_path = PROJECT_PATH / ignore_path

        if not ignore_full_path.is_dir():
            logger.warn(f"Ignore path {ignore_path} does not exist")
            continue

        _d.append(ignore_full_path)

    return _d


def _check_file_in_ignore_path(file_path: Path) -> bool:

    ignore_paths = _build_ignore_matcher()

    for p in ignore_paths:
        r = commonprefix([p, file_path])

        logger.debug(f"{str(file_path): <100} {str(p): <100} - {str(r)}")

        if Path(r) == PROJECT_PATH:
            return False

    return True


def cmd_clean_project() -> None:
    """Cleans the project folders of files matching _CLEAN_GLOBS"""
    count_total = 0
    count_cleaned = 0
    count_ignored = 0
    limit = 0

    logger.info("Running from project root: {}".format(PROJECT_PATH))

    for _glob in _CLEAN_GLOBS:
        _glob_matches = Path(PROJECT_PATH).rglob(_glob)

        for _m in _glob_matches:
            count_total += 1

            skip = False

            if _check_file_in_ignore_path(_m):
                skip = True

            logger.debug(f"{count_total: >5} of {limit: >5} {str(_m): <150} and {skip}")

            if limit and limit > 0 and (count_total >= limit):
                logger.info(f"Breaking because reached limit of {limit}")
                break

            if skip:
                count_ignored += 1

                if _m.is_file():
                    pass
            else:
                count_cleaned += 1

    logger.info(f"Completed. Scanned {count_total} files and deleted {count_cleaned} ignoring {count_ignored}")


if __name__ == "__main__":
    cmd_clean_project()
