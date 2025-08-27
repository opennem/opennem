"""Reads the project version from pyproject.toml metadata

Dynamically reads version information from pyproject.toml using tomllib
to ensure single source of truth for version management.
"""

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path


def _is_number(value: str | int | float) -> bool:
    """Check if a value is a number (copied from normalizers to avoid circular import)"""
    if isinstance(value, int | float):
        return True

    value = str(value).strip()
    # Simple regex to match numbers (integers or floats)
    return bool(re.match(r"^-?\d+(?:\.\d+)?$", value))


def _read_version_from_pyproject() -> str:
    """Read version from pyproject.toml file"""
    # Get path to pyproject.toml (two levels up from this file)
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

    with pyproject_path.open("rb") as f:
        pyproject_data = tomllib.load(f)

    return pyproject_data["project"]["version"]


# Read version from pyproject.toml
__version__ = _read_version_from_pyproject()


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


def get_version(dev_tag: bool = False) -> str:
    """Read the version from pyproject.toml metadata"""
    version_parts = [
        __version__,
    ]

    # Import settings here to avoid circular imports
    from opennem import settings

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
        patch=int(version_components[2]) if _is_number(version_components[2]) else version_components[2],
    )


if __name__ == "__main__":
    # Test version reading directly without using get_version to avoid circular imports
    print(f"Version from pyproject.toml: {__version__}")

    # Test version parsing
    version_components = __version__.split(".")
    version_model = Version(
        major=int(version_components[0]),
        minor=int(version_components[1]),
        patch=int(version_components[2]) if _is_number(version_components[2]) else version_components[2],
    )

    print(f"Major: {version_model.major}")
    print(f"Minor: {version_model.minor}")
    print(f"Patch: {version_model.patch}")
    print(f"Full version: {version_model}")
    print(f"Is release: {version_model.is_release}")
