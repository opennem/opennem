from opennem.utils.version import VersionPart, get_version


# @TODO mock this because obviouuuuusly...
def test_version():
    version = get_version(VersionPart.MAJOR)

    assert version == 3
