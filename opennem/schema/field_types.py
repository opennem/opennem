"""
Field types for OpenNEM pydantic schemas used in this module
"""

from typing import Annotated

from pydantic import BeforeValidator, StringConstraints


def round_float_2(v: float) -> float:
    if isinstance(v, float):
        return round(v, 2)
    return v


def round_float_4(v: float) -> float:
    if isinstance(v, float):
        return round(v, 4)
    return v


def round_float_8(v: float) -> float:
    if isinstance(v, float):
        return round(v, 8)
    return v


# Rounded float types
RoundedFloat2 = Annotated[float, BeforeValidator(round_float_2)]
RoundedFloat4 = Annotated[float, BeforeValidator(round_float_4)]
RoundedFloat8 = Annotated[float, BeforeValidator(round_float_8)]  # used for lat, lng and polygons

# valid DUID
DUIDType = Annotated[str, StringConstraints(pattern=r"^[A-Z0-9_.\-#]{3,32}$")]
