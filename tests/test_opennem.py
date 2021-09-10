# noqa: F408, F401
import pytest


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

    assert isinstance(opennem.__path__, list), "Path is a list"
