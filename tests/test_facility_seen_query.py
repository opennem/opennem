"""Tests for the facility seen-range update query (BACKEND-51M/51N).

The facility_codes filter previously referenced an alias "f" that was never joined in the
query, so postgres raised `missing FROM-clause entry for table "f"` whenever the sanity
webhook created a new facility (see opennem/workers/facility_data_seen.py).
"""

from opennem.workers.facility_data_seen import get_update_seen_query


def test_facility_codes_filter_uses_facility_scada_alias() -> None:
    query = str(get_update_seen_query(include_first_seen=True, facility_codes=["SMFBESS2"]))

    assert "f.code in" not in query
    assert "fs.facility_code in ('SMFBESS2')" in query


def test_no_facility_codes_filter_when_not_provided() -> None:
    query = str(get_update_seen_query(include_first_seen=True))

    assert "facility_code in" not in query
