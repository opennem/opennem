"""Removing an osm_way_id in the CMS must clear it, and its boundary, in Postgres (#481).

Every other field in the importer syncs behind a truthy guard, which silently makes a value
un-removable. For osm_way_id that meant a wrong match was permanent: TESLA_PICTON (Picton,
WA) kept pointing at Pindari Power Station in NSW and kept serving that boundary long after
the id was removed from Sanity.

The boundary is derived from the link by bin/osm-import-boundaries.py, which only fills rows
where boundary IS NULL and so never retracts a stale polygon on its own.
"""

import inspect

import pytest

from opennem.cms import importer
from opennem.cms.importer import normalise_osm_way_id

_SOURCE = inspect.getsource(importer)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("366249341", "366249341"),
        ("  366249341  ", "366249341"),
        ("-10059368", "-10059368"),  # negative ids encode a relation rather than a way
        (None, None),
        ("", None),
        ("   ", None),
    ],
)
def test_normalise_osm_way_id(value, expected):
    assert normalise_osm_way_id(value) == expected


def test_blank_normalises_to_none_not_empty_string():
    """An empty string is truthy enough to keep a stale boundary alive, so it must be None."""
    assert normalise_osm_way_id("") is None
    assert normalise_osm_way_id("  ") is None


def test_osm_way_id_is_not_behind_a_truthy_guard():
    """The exact shape of the original bug — guard the guard."""
    assert 'if hasattr(facility, "osm_way_id") and facility.osm_way_id:' not in _SOURCE
    assert "osm_way_id = normalise_osm_way_id(facility.osm_way_id)" in _SOURCE


def test_clearing_the_link_also_clears_the_boundary():
    """A dropped link must drop the derived geometry, or the wrong shape outlives it."""
    assert "facility_db.boundary = None" in _SOURCE
