from opennem.utils.version import get_version


# @TODO mock this because obviouuuuusly...
def test_version() -> None:
    version = get_version()

    assert version.startswith("3") is True
