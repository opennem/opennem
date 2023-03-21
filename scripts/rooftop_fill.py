#!/usr/bin/env python
"""
Fill AEMO_ROOFTOP_BACKFILL network data with APVI derived data from v2

Monthly calculated data

requires aemo_rooftop_backfill.csv file
"""

import csv
import logging
from datetime import date, datetime
from pathlib import Path

from pydantic import validator

from opennem.core.normalizers import clean_float
from opennem.db import SessionLocal
from opennem.db.models.opennem import AggregateFacilityDaily
from opennem.schema.core import BaseConfig
from opennem.settings import settings  # noqa: F401

logger = logging.getLogger("opennem.scripts.rooftop_fill")

NEM_MIN_ROOFTOP_DATE = datetime.fromisoformat("2018-03-01T00:00:00+00")


def _get_aemo_backfill_facility_id(network_region: str) -> str:
    return f"ROOFTOP_AEMO_ROOFTOP_BACKFILL_{network_region[:-1]}".upper()


class BackfillRecord(BaseConfig):
    trading_day: date
    network_id: str = "AEMO_ROOFTOP_BACKFILL"
    fueltech_id: str = "solar_rooftop"
    network_region: str
    market_value: float | None
    energy_v2: float | None
    energy_v3: float | None = None

    _validate_energyv3 = validator("energy_v3", pre=True)(clean_float)

    @property
    def energy(self) -> float:
        _value = 0.0

        if self.energy_v2:
            _value = self.energy_v2

        if self.energy_v3:
            _value -= self.energy_v3

            logger.debug(f"Settings energy to delta: {self.energy_v2} {self.energy_v3} : {_value}")

        return round(_value * 1000, 0)

    @property
    def facility_code(self) -> str:
        return _get_aemo_backfill_facility_id(self.network_region)


def import_rooftop_aemo_backfills() -> None:
    csvrecords = []
    backfill_file = Path(__file__).parent / "notebooks" / "aemo_rooftop_backfill.csv"

    with backfill_file.open() as fh:
        fieldnames = fh.readline().strip().split(",")
        csvreader = csv.DictReader(fh, fieldnames=fieldnames)
        csvrecords = [BackfillRecord(**i) for i in csvreader]

    logger.debug(f"Loaded {len(csvrecords)} records")

    export_records = [i.dict(exclude={"energy_v2", "energy_v3", "network_region"}) for i in csvrecords]

    session = SessionLocal()

    records_added = 0
    records_updated = 0

    for rec in export_records:
        model = (
            session.query(AggregateFacilityDaily)
            .filter_by(network_id="AEMO_ROOFTOP_BACKFILL")
            .filter_by(trading_day=rec["trading_day"])
            .filter_by(facility_code=rec["facility_code"])
        ).first()

        if not model:
            model = AggregateFacilityDaily(**rec)
            records_added += 1
        else:
            records_updated += 1

        model.energy = rec["energy"]
        model.market_value = rec["market_value"]

        session.add(model)

    session.commit()
    logger.debug(f"Added {records_added} records and updated {records_updated}")


if __name__ == "__main__":
    import_rooftop_aemo_backfills()
