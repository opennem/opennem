""" Defined AEMO data source structures """
import enum
import logging
from datetime import date
from pathlib import Path

from pydantic import validator

from opennem.core.normalizers import normalize_duid
from opennem.parsers.aemo.normalisers import aemo_gi_capacity_cleaner, clean_closure_year_expected
from opennem.schema.core import BaseConfig

logger = logging.getLogger("opennem.parsers.aemo.schema")

# Data classes and definitions


class AEMODataSource(enum.Enum):
    rel = "rel"  # @NOTE registration and exemption list
    gi = "gi"  # @NOTE general information table
    closures = "closures"


class AEMOGIRecord(BaseConfig):
    """Defines an AEMO source records (ie. one row in either REL or GI or closures )"""

    name: str
    name_network: str | None = None
    network_region: str
    fueltech_id: str | None = None
    status_id: str | None = None
    duid: str | None = None
    units_no: int | None = None
    capacity_registered: float | None = None
    closure_year_expected: int | None = None
    unique_id: str | None = None

    _clean_duid = validator("duid", pre=True, allow_reuse=True)(normalize_duid)
    _clean_capacity = validator("capacity_registered", pre=True, allow_reuse=True)(aemo_gi_capacity_cleaner)
    _clean_closure_year_expected = validator("closure_year_expected", pre=True, allow_reuse=True)(clean_closure_year_expected)


class AEMOSourceSet(BaseConfig):
    aemo_source: AEMODataSource
    source_date: date
    source_url: str | None = None
    local_path: Path | None = None
    records: list[AEMOGIRecord] = []
