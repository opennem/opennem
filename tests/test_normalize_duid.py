import pytest

from opennem.core.normalizers import normalize_duid


@pytest.mark.parametrize(
    ["duid", "duid_expected"],
    [
        ("TARONG#1", "TARONG#1"),
        ("V-S-MNSP1", "V-S-MNSP1"),
        (
            " LIMOSF11\
 ",
            "LIMOSF11",
        ),
    ],
)
def test_duid_cleaner(duid: str, duid_expected: str) -> None:
    duid_return = normalize_duid(duid)
    assert duid_return == duid_expected, "Matched duid"


def _legacy_normalize_duid(duid: str | None) -> str | None:
    """normalize_duid before the fast path and cache, kept as the reference"""
    import re

    duid = duid or ""
    if not duid:
        return None
    duid_ascii = duid.encode("ascii", "ignore").decode("utf-8")
    duid_ascii = re.sub(r"\W\_\-\#+", "", duid_ascii)
    duid_ascii = re.sub(r"\_[xX][0-9A-F]{4}\_", "", duid_ascii)
    duid_ascii = duid_ascii.strip().upper()
    if duid_ascii == "-" or not duid_ascii:
        return ""
    return duid_ascii


_EDGE_CASES = [
    None,
    "",
    "-",
    " - ",
    " ",
    "\t\n",
    "_x000D_",
    "AB_x000D_CD",
    "ab_X00AF_cd",
    "AB_x000d_CD",
    "_x000D__x000A_",
    "__x000D__",
    "UNIT_-#",
    "UNIT._-###1",
    "UNIT a_-#b",
    "_-#",
    "._-#",
    "é_-#",
    "BBATTERY1",
    "bbattery1",
    "  lves1  ",
    "COLLIE_ESR1",
    "0SUPERNODE",
    "TARONG#1",
    "V-S-MNSP1",
    "ÉNERGIE1",
    "unité",
    "ß",
    "ﬁ",
    " UNIT ",
    "UNIT ",
    "日本",
    "A\x00B",
    "\x0bUNIT\x0c",
    "-_x0041_-",
]

_ALPHABET = "abcXYZ019 _-#.xX\t\n\r\x0b  éß日ﬁ0AF" + "_x000D_"


@pytest.mark.parametrize("duid", _EDGE_CASES)
def test_normalize_duid_matches_legacy_edge_cases(duid: str | None) -> None:
    assert normalize_duid(duid) == _legacy_normalize_duid(duid)
    # second call is served from the cache
    assert normalize_duid(duid) == _legacy_normalize_duid(duid)


def test_normalize_duid_matches_legacy_fuzz() -> None:
    import random

    rng = random.Random(773)
    pieces = list(_ALPHABET) + ["_x000D_", "_X00FF_", "_-#", "_-##", "_x00", "000D_"]
    for _ in range(50_000):
        duid = "".join(rng.choices(pieces, k=rng.randint(0, 12)))
        assert normalize_duid(duid) == _legacy_normalize_duid(duid), repr(duid)


def test_normalize_duid_str_subclass_returns_plain_str() -> None:
    class Code(str):
        pass

    result = normalize_duid(Code(" lves1 "))
    assert result == "LVES1"
    assert type(result) is str
