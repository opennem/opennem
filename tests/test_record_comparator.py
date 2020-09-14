from opennem.db.models.opennem import Facility, FacilityStatus, FuelTech
from opennem.importer.comparator import compare_record_differs
from opennem.schema.opennem import (
    FacilitySchema,
    FacilityStatusSchema,
    FueltechSchema,
)


class TestRecordComparator(object):
    models = {}
    schemas = {}

    @classmethod
    def setup_class(cls):
        """
            Load the stations fixture for this test suite
        """
        fueltech_record_dict = {
            "code": "coal_black",
            "label": "Black Coal",
            "renewable": True,
        }

        status_record_dict = {"code": "operating", "label": "Operating"}

        facility_record_dict = {
            "code": "TEST",
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

        cls.models["facility_plain"] = db_facility
        cls.schemas["facility_plain"] = schema_facility

    def test_none(self):
        subject = {
            "field": True,
        }

        target = {"field": None}

        assert (
            compare_record_differs(subject, target, "field") is True
        ), "No field means it changed"
        assert (
            compare_record_differs(subject, {}, "field") is True
        ), "Empty means it changed"

    def test_boolean(self):
        subject = {
            "field": True,
        }

        target = {"field": True}

        target_false = {"field": False}

        assert (
            compare_record_differs(subject, target, "field") is False
        ), "Fields are both true"
        assert (
            compare_record_differs(subject, target_false, "field") is True
        ), "Fields True and False so differ"

    def test_fueltech(self):
        subject_schema = self.schemas.get("facility_plain")
        target_model = self.models.get("facility_plain")

        assert (
            compare_record_differs(subject_schema, target_model, "fueltech")
            is False
        ), "Fueltechs are identical"
