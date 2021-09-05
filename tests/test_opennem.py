import opennem


def test_opennem_imports() -> None:
    pass


def test_opennem_version() -> None:
    assert isinstance(opennem.__version__, str), "Version is a string"
