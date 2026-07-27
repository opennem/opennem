"""Tests for the WEM facility-scada archive parser.

Covers the two eras the archive spans (see #598):

  * before 2013-12-17 AEMO published only "Energy Generated (MWh)" and left the
    "EOI Quantity (MW)" column empty
  * from 2013-12-17 both columns are published
"""

from datetime import datetime, timedelta

from opennem.clients.wem import (
    WEM_LEGACY_INTERVAL_SIZE_MINUTES,
    WEMBalancingSummaryInterval,
    WEMGenerationInterval,
    _detect_interval_size_minutes,
    parse_wem_facility_intervals,
)

HEADER = (
    "Trading Date,Interval Number,Trading Interval,Participant Code,Facility Code,"
    "Energy Generated (MWh),EOI Quantity (MW),Extracted At"
)

# Pre-2013-12-17: EOI Quantity column is empty on every row
CSV_ENERGY_ONLY = "\n".join(
    [
        HEADER,
        '"2010-01-01",1,2010-01-01 08:00:00,"WPGENER","COLLIE_G1",84.503,,',
        '"2010-01-01",2,2010-01-01 08:30:00,"WPGENER","COLLIE_G1",106.382,,',
        '"2010-01-01",1,2010-01-01 08:00:00,"WPGENER","KWINANA_G1",0,,',
    ]
)

# Post-cutover: both columns published
CSV_WITH_EOI = "\n".join(
    [
        HEADER,
        '"2014-06-01",20,2014-06-01 17:30:00,"WPGENER","COLLIE_G1",144.541,303.174,',
        '"2014-06-01",21,2014-06-01 18:00:00,"WPGENER","COLLIE_G1",156.223,315.773,',
    ]
)


class TestWemEnergyOnlyEra:
    """Before 2013-12-17 power has to be derived from the published energy"""

    def test_records_are_not_dropped(self):
        models = parse_wem_facility_intervals(CSV_ENERGY_ONLY)

        # an empty EOI column used to fail float validation and silently drop every row
        assert len(models) == 3

    def test_energy_is_the_published_value(self):
        models = parse_wem_facility_intervals(CSV_ENERGY_ONLY)

        assert models[0].energy == 84.503

    def test_generated_is_derived_from_energy(self):
        models = parse_wem_facility_intervals(CSV_ENERGY_ONLY)

        # 30 minute interval, so MWh -> MW is x2
        assert models[0].generated == 84.503 * 2
        assert models[1].generated == 106.382 * 2

    def test_published_zero_is_preserved(self):
        models = parse_wem_facility_intervals(CSV_ENERGY_ONLY)

        zero_record = [i for i in models if i.facility_code == "KWINANA_G1"][0]

        # a unit running at zero is real data, distinct from a missing value
        assert zero_record.energy == 0.0
        assert zero_record.generated == 0.0

    def test_interval_is_awst_wall_time(self):
        models = parse_wem_facility_intervals(CSV_ENERGY_ONLY)

        # facility_scada stores WEM intervals as AWST-naive, matching the published value
        assert models[0].trading_interval.replace(tzinfo=None).isoformat() == "2010-01-01T08:00:00"


class TestWemEoiEra:
    """From 2013-12-17 the published MW column wins"""

    def test_generated_uses_published_power(self):
        models = parse_wem_facility_intervals(CSV_WITH_EOI)

        assert models[0].generated == 303.174

    def test_energy_is_the_published_value(self):
        models = parse_wem_facility_intervals(CSV_WITH_EOI)

        assert models[0].energy == 144.541


class TestIntervalSizeDetection:
    def test_detects_thirty_minute_intervals(self):
        models = parse_wem_facility_intervals(CSV_ENERGY_ONLY)

        assert models[0].interval_size_minutes == 30

    def test_override_is_respected(self):
        models = parse_wem_facility_intervals(CSV_ENERGY_ONLY, interval_size_minutes=5)

        assert models[0].interval_size_minutes == 5
        # 5 minute interval, so MWh -> MW is x12
        assert models[0].generated == 84.503 * 12

    def test_falls_back_when_only_one_interval(self):
        assert _detect_interval_size_minutes([]) == WEM_LEGACY_INTERVAL_SIZE_MINUTES

    def test_outlier_gap_does_not_win(self):
        # one stray timestamp 1 minute off must not make the whole file look 1-minute,
        # which would apply a 60x factor to every record
        base = datetime(2010, 1, 1, 8, 0)
        intervals = [base + timedelta(minutes=30 * i) for i in range(20)]
        intervals.append(base + timedelta(minutes=1))

        assert _detect_interval_size_minutes(intervals) == 30

    def test_unknown_cadence_falls_back(self):
        base = datetime(2010, 1, 1, 8, 0)
        hourly = [base + timedelta(minutes=60 * i) for i in range(10)]

        # 60 minutes is not a cadence WEM has published
        assert _detect_interval_size_minutes(hourly) == WEM_LEGACY_INTERVAL_SIZE_MINUTES

    def test_detects_five_minute_cadence(self):
        base = datetime(2024, 6, 1, 8, 0)
        five_min = [base + timedelta(minutes=5 * i) for i in range(20)]

        assert _detect_interval_size_minutes(five_min) == 5


class TestZeroHandling:
    """Zeros are preserved by FloatField, so consumers must test `is None`"""

    def test_zero_power_is_not_treated_as_missing(self):
        record = WEMGenerationInterval(
            trading_interval="2014-06-01 08:00:00",
            facility_code="COLLIE_G1",
            power=0.0,
        )

        assert record.generated == 0.0

    def test_zero_actual_generation_is_not_a_forecast(self):
        record = WEMBalancingSummaryInterval(
            TRADING_DAY_INTERVAL="2014-06-01 08:00:00",
            ACTUAL_TOTAL_GENERATION=0.0,
        )

        assert record.is_forecast is False

    def test_missing_actuals_is_a_forecast(self):
        record = WEMBalancingSummaryInterval(TRADING_DAY_INTERVAL="2014-06-01 08:00:00")

        assert record.is_forecast is True

    def test_five_minute_wemde_cadence(self):
        record = WEMGenerationInterval(
            trading_interval="2024-06-01 08:00:00",
            facility_code="COLLIE_G1",
            eoi_quantity=10.0,
            interval_size_minutes=5,
        )

        assert record.generated == 120.0
        assert record.energy == 10.0
