"""
Test utilities including paths and helper functions
"""
from pathlib import Path

PATH_TESTS_ROOT = Path(__file__).parent
PATH_TESTS_FIXTURES = PATH_TESTS_ROOT / "fixtures"

if not PATH_TESTS_FIXTURES.is_dir():
    raise Exception("Tets fixtures path not found: {}".format(PATH_TESTS_FIXTURES))
