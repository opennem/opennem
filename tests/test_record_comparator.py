from opennem.db.models.opennem import Facility, FacilityStatus, FuelTech
from opennem.importer.comparator import compare_record
from opennem.schema.opennem import (
    FacilitySchema,
    FacilityStatusSchema,
    FueltechSchema,
)


class TestRecordComparator(object):
    def test_fueltech(self):
        fueltech_record_dict = {
            "code": "coal_black",
            "label": "Black Coal",
            "renewable": True,
        }

        status_record_dict = {"code": "operating", "label": "Operating"}

        facility_record_dict = {
            "code": "TEST",
            # "network_region": {"code": "NEM", "country": "au", "label": "NEM"},
        }

        db_fueltech = FuelTech(**fueltech_record_dict)
        schema_fueltech = FueltechSchema(**fueltech_record_dict)

        db_facility = Facility(**facility_record_dict)
        db_facility.fueltech = db_fueltech

        schema_status = FacilityStatusSchema(**status_record_dict)

        schema_facility = FacilitySchema(
            **facility_record_dict,
            fueltech=schema_fueltech,
            status=schema_status,
        )
        schema_facility.fueltech = schema_fueltech

        assert (
            compare_record(schema_facility, db_facility, "fueltech") is True
        ), "Fueltechs are identical"
