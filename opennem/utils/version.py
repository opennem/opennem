"""Reads the project version

@NOTE updated to dynamically update with build scripts
"""

from dataclasses import dataclass

from opennem import __version__, settings
from opennem.core.normalizers import is_number


@dataclass
class Version:
    major: int
    minor: int
    patch: int | str

    @property
    def is_release(self) -> bool:
        return not isinstance(self.patch, str)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def get_version(dev_tag: bool = True) -> str:
    """Read the version from the package __version__ variable"""
    version_parts = [
        __version__,
    ]

    if settings.env in ["local", "development"] and dev_tag:
        # append dev tag
        version_parts.append("dev")

    return ".".join(version_parts)


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
