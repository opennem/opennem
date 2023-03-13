# noqa: F408, F401
import pytest

from opennem.settings import settings
from opennem.settings.schema import OpennemSettings


def test_opennem_imports() -> None:
    try:
        import opennem

        hasattr(opennem, "core")
    except Exception:
        pytest.fail("Could not import main module")


def test_opennem_version() -> None:
    import opennem

    assert isinstance(opennem.__version__, str), "Version is a string"
    assert len(opennem.__version__) > 1, "Version is not empty"
    assert "." in opennem.__version__, "Version is somewhat versiony"
    assert len(opennem.__version__.split(".")) > 2, "Version is more versiony"


def test_opennem_path() -> None:
    import opennem

    assert hasattr(opennem, "__path__"), "Module has a path"
    assert isinstance(opennem.__path__, list), "Path is a list"  # type: ignore


def test_opennem_settings() -> None:
    import opennem

    assert hasattr(opennem, "settings"), "We have settings"

    assert isinstance(settings, OpennemSettings), "Settings is an openem settings schema"
