"""Reads the project version

@NOTE updated to dynamically update with build scripts
"""

from dataclasses import dataclass

from opennem import __version__ as version
from opennem.core.normalizers import is_number


@dataclass
class Version:
    major: int
    minor: int
    patch: int | str

    @property
    def is_release(self) -> bool:
        return not isinstance(self.patch, str)

    __str__ = lambda self: f"{self.major}.{self.minor}.{self.patch}"  # noqa: E731


def get_version() -> str:
    """@TODO remove this and use poetry versioning"""
    return version


def get_version_model() -> Version:
    """Gets the version components"""
    version = get_version()

    version_components = version.split(".")

    return Version(
        major=int(version_components[0]),
        minor=int(version_components[1]),
        patch=int(version_components[2]) if is_number(version_components[2]) else version_components[2],
    )


if __name__ == "__main__":
    r = get_version_model()
    print(r.major)
    print(r.minor)
    print(r.patch)
    print(r)
