from datetime import datetime

import pytest

from opennem.core.parsers.aemo.filenames import AEMOMMSFilename, parse_aemo_filename, parse_aemo_filename_datetimes


@pytest.mark.parametrize(
    ["dtstring", "expected"],
    [
        ("20220415", datetime.fromisoformat("2022-04-15T00:00:00")),
        ("202206130025", datetime.fromisoformat("2022-06-13T00:25:00")),
    ],
)
def test_parse_aemo_filename_datetimes(dtstring: str, expected: datetime) -> None:
    """test datetime parser"""
    parse_result = parse_aemo_filename_datetimes(dtstring)
    assert parse_result == expected, "Got correct datetime"


@pytest.mark.parametrize(
    ["filename", "components"],
    [
        (
            "PUBLIC_DISPATCHSCADA_202206130025_0000000365048508.zip",
            {
                "filename": "PUBLIC_DISPATCHSCADA",
                "date": "202206130025",
                "interval": "0000000365048508",
            },
        ),
        (
            "PUBLIC_NEXT_DAY_ACTUAL_GEN_20220415_0000000361359411.zip",
            {
                "filename": "PUBLIC_NEXT_DAY_ACTUAL_GEN",
                "date": "20220415",
                "interval": "0000000361359411",
            },
        ),
        (
            "PUBLIC_PRICE_REVISION_DISPATCH_20220417153013_0000000361443655.zip",
            {"filename": "PUBLIC_PRICE_REVISION_DISPATCH", "date": "20220417153013", "interval": "0000000361443655"},
        ),
    ],
)
def test_parse_aemo_filename(filename: str, components: AEMOMMSFilename) -> None:
    comp_result = parse_aemo_filename(filename)
    components_model = AEMOMMSFilename(**components)  # type: ignore
    assert comp_result == components_model, "Components match"
