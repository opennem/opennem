"""Test utilities including paths and helper functions
"""
from pathlib import Path

# from opennem import __path__

PATH_TESTS_ROOT = Path(__file__).parent / "tests"
PATH_TESTS_FIXTURES = PATH_TESTS_ROOT / "fixtures"

if not PATH_TESTS_FIXTURES.is_dir():
    raise Exception("Test fixtures path not found: {}".format(PATH_TESTS_FIXTURES))
