from datetime import datetime

import pytest

from opennem.core.parsers.aemo.filenames import AEMOMMSFilename, parse_aemo_filename, parse_aemo_filename_datetimes


@pytest.mark.parametrize(
    ["dtstring", "expected"],
    [
        ("20220415", datetime.fromisoformat("2022-04-15T00:00:00")),
        ("202206130025", datetime.fromisoformat("2022-06-13T00:25:00")),
        ("202204210025", datetime.fromisoformat("2022-04-21T00:25:00")),
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
                "date": datetime.fromisoformat("2022-06-13T00:25:00"),
                "interval": "0000000365048508",
            },
        ),
        (
            "PUBLIC_NEXT_DAY_ACTUAL_GEN_20220415_0000000361359411.zip",
            {
                "filename": "PUBLIC_NEXT_DAY_ACTUAL_GEN",
                "date": datetime.fromisoformat("2022-04-15T00:00:00"),
                "interval": "0000000361359411",
            },
        ),
        (
            "PUBLIC_PRICE_REVISION_DISPATCH_20220417153013_0000000361443655.zip",
            {
                "filename": "PUBLIC_PRICE_REVISION_DISPATCH",
                "date": datetime.fromisoformat("2022-04-17T15:30:13"),
                "interval": "0000000361443655",
            },
        ),
        (
            "FCAS_202204210025.zip",
            {"filename": "FCAS", "date": datetime.fromisoformat("2022-04-21T00:25:00"), "interval": None},
        ),
        (
            "PUBLIC_VWAFCASPRICES_202204220000_20220423040501.zip",
            {
                "filename": "PUBLIC_VWAFCASPRICES",
                "date": datetime.fromisoformat("2022-04-22T00:00:00"),
                "interval": "20220423040501",
            },
        ),
        (
            "PUBLIC_TRADINGIS_20210926_20211002.zip",
            {
                "filename": "PUBLIC_TRADINGIS",
                "date": datetime.fromisoformat("2021-09-26T00:00:00"),
                "interval": "20211002",
            },
        ),
        # new aemo archive scheme (2024-08+): PUBLIC_ARCHIVE#<TABLE>#FILE01#<date>.zip
        (
            "PUBLIC_ARCHIVE#DISPATCHREGIONSUM#FILE01#202408010000.zip",
            {
                "filename": "PUBLIC_ARCHIVE#DISPATCHREGIONSUM#FILE01",
                "date": datetime.fromisoformat("2024-08-01T00:00:00"),
                "interval": None,
            },
        ),
        # same scheme with the '#' url-encoded as %23
        (
            "PUBLIC_ARCHIVE%23DISPATCHPRICE%23FILE01%23202408010000.zip",
            {
                "filename": "PUBLIC_ARCHIVE%23DISPATCHPRICE%23FILE01",
                "date": datetime.fromisoformat("2024-08-01T00:00:00"),
                "interval": None,
            },
        ),
    ],
)
def test_parse_aemo_filename(filename: str, components: AEMOMMSFilename) -> None:
    comp_result = parse_aemo_filename(filename)
    components_model = AEMOMMSFilename(**components)  # type: ignore
    assert comp_result == components_model, "Components match"


@pytest.mark.parametrize(
    ["filename", "matches"],
    [
        ("PUBLIC_DVD_DISPATCHREGIONSUM_202408010000.zip", True),
        ("PUBLIC_ARCHIVE#DISPATCHREGIONSUM#FILE01#202408010000.zip", True),
        ("PUBLIC_ARCHIVE%23DISPATCHREGIONSUM%23FILE01%23202408010000.zip", True),
        ("PUBLIC_DVD_TRADINGREGIONSUM_202408010000.zip", False),
        ("PUBLIC_ARCHIVE#TRADINGREGIONSUM#FILE01#202408010000.zip", False),
    ],
)
def test_mms_filename_filter(filename: str, matches: bool) -> None:
    """the mms filename filter matches a table across both aemo archive naming schemes"""
    import re

    from opennem.crawlers.mms import mms_filename_filter

    pattern = mms_filename_filter("DISPATCHREGIONSUM")
    assert bool(re.match(pattern, filename)) is matches
