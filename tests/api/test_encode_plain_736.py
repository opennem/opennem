"""#736: orjson plain-dict encode is JSON-equal (and byte-equal where possible) to the old stdlib path."""

import json
import math
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from enum import StrEnum

import pytest
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from opennem.api.response_cache import _encode_plain


class Mode(StrEnum):
    A = "a"


class Item(BaseModel):
    name: str
    when: datetime
    opt: str | None = None


def _old(value: object) -> bytes:
    return json.dumps(value, default=jsonable_encoder, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()


def _payload() -> dict:
    aest = timezone(timedelta(hours=10))
    return {
        "z": 1,
        "a": [None, True, False],
        "aware": datetime(2026, 1, 2, 3, 4, 5, tzinfo=aest),
        "utc": datetime(2026, 1, 2, 3, 4, 5, 123456, tzinfo=UTC),
        "naive": datetime(2026, 1, 2, 3, 4, 5),
        "micro": datetime(2026, 1, 2, 3, 4, 5, 1),
        "d": date(2026, 1, 2),
        "floats": [0.1, 1e16, 1e22, 123456789.123456789, -0.0, 3.0, 5000.0, 2**53, 0.30000000000000004],
        "ints": [0, -1, 2**63 - 1],
        "dec": [Decimal("1.50"), Decimal("3"), Decimal("1E+2")],
        "enum": Mode.A,
        "uni": 'café ☃ "q" \\ \n  ',
        "model": Item(name="n", when=datetime(2026, 1, 1, tzinfo=UTC)),
        "nested": [{"k": [[["2026-01-01T00:00:00+10:00", None], ["2026-01-01T00:05:00+10:00", 1.0]]]}],
    }


def test_json_equal_and_bytes_equal_for_realistic_payload() -> None:
    new = _encode_plain(_payload())
    old = _old(_payload())
    assert json.loads(new) == json.loads(old)
    # key order preserved
    assert list(json.loads(new)) == list(json.loads(old))
    assert new == old


def test_non_str_keys_and_big_ints_fall_back() -> None:
    p = {1: "a", "big": 2**70}
    assert _encode_plain(p) == _old(p)


def test_nan_serialises_as_null() -> None:
    assert json.loads(_encode_plain({"v": math.nan, "w": math.inf})) == {"v": None, "w": None}
    with pytest.raises(ValueError):
        _old({"v": math.nan})


def test_small_floats_json_equal_but_not_byte_equal() -> None:
    """Known byte difference: stdlib writes 1e-05 / 1.5e-07, orjson writes 0.00001 / 1.5e-7. Values identical."""
    p = {"v": [1e-05, 1.5e-7, 1e-300, 1e16, 5e-324, 0.0001]}
    assert json.loads(_encode_plain(p)) == json.loads(_old(p))
