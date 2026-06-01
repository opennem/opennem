import uuid
from datetime import datetime

from opennem.recordreactor.schema import (
    MilestoneAggregate,
    MilestonePeriod,
    MilestoneRecordOutputSchema,
    MilestoneRecordSchema,
    MilestoneType,
    MilestoneUnitSchema,
)
from opennem.recordreactor.utils import check_milestone_is_new
from opennem.schema.network import NetworkNEM


# Helper function to create a test unit schema
def create_test_unit(unit_value: str = "MW") -> MilestoneUnitSchema:
    """Create a test unit schema"""
    return MilestoneUnitSchema(name="power_mega", label="Megawatts", unit=unit_value, output_format="{value} {unit}")


# Helper function to create a milestone record
def create_milestone_record(
    value: float,
    interval: datetime = None,
    aggregate: MilestoneAggregate = MilestoneAggregate.high,
    metric: MilestoneType = MilestoneType.demand,
) -> MilestoneRecordSchema:
    """Create a test milestone record"""
    if interval is None:
        interval = datetime(2023, 6, 15, 12, 30)

    return MilestoneRecordSchema(
        interval=interval,
        aggregate=aggregate,
        metric=metric,
        period=MilestonePeriod.day,
        network=NetworkNEM,
        unit=create_test_unit(),
        network_region="NSW1",
        fueltech=None,
        value=value,
    )


# Helper function to create a milestone output record
def create_milestone_output_record(
    value: float,
    interval: datetime = None,
    aggregate: str = "high",
    metric: str = "demand",
) -> MilestoneRecordOutputSchema:
    """Create a test milestone output record"""
    if interval is None:
        interval = datetime(2023, 6, 14, 12, 30)  # Previous day

    return MilestoneRecordOutputSchema(
        record_id="au.nem.nsw1.demand.day.high",
        interval=interval,
        instance_id=uuid.uuid4(),
        aggregate=aggregate,
        metric=metric,
        period="day",
        significance=1,
        value=value,
        value_unit="MW",
        network_id="NEM",
        network_region="NSW1",
        description="Test milestone",
    )


class TestCheckMilestoneIsNew:
    """Test the check_milestone_is_new function"""

    def test_identical_rounded_values_return_false(self):
        """Test that milestones with different raw but identical rounded values return False"""
        # Test case from the original issue: 708.1 vs 708.9 should both round to 708
        milestone = create_milestone_record(value=708.1)
        previous = create_milestone_output_record(value=708.9)

        assert not check_milestone_is_new(milestone, previous)

    def test_identical_rounded_values_different_decimals(self):
        """Test various fractional differences that round to the same integer"""
        test_cases = [
            (708.1, 708.9),  # Original issue case
            (500.2, 500.8),  # Different hundreds
            (1000.4, 1000.6),  # Different thousands
            (50.1, 50.49),  # Edge case near rounding boundary
            (99.51, 99.99),  # Edge case near rounding boundary
        ]

        for current_val, previous_val in test_cases:
            milestone = create_milestone_record(value=current_val)
            previous = create_milestone_output_record(value=previous_val)

            assert not check_milestone_is_new(milestone, previous), (
                f"Expected False for {current_val} vs {previous_val} (both round to {round(current_val, 0)})"
            )

    def test_different_rounded_values_high_aggregate(self):
        """Test that milestones with different rounded values work correctly for high aggregate"""
        milestone = create_milestone_record(value=709.0, aggregate=MilestoneAggregate.high)
        previous = create_milestone_output_record(value=708.0, aggregate="high")

        # For high aggregate, 709 > 708 should return True
        assert check_milestone_is_new(milestone, previous)

    def test_different_rounded_values_low_aggregate(self):
        """Test that milestones with different rounded values work correctly for low aggregate"""
        milestone = create_milestone_record(value=707.0, aggregate=MilestoneAggregate.low)
        previous = create_milestone_output_record(value=708.0, aggregate="low")

        # For low aggregate, 707 < 708 should return True
        assert check_milestone_is_new(milestone, previous)

    def test_proportion_metric_uses_different_rounding(self):
        """Test that proportion metrics use round_to=2 instead of round_to=0"""
        milestone = create_milestone_record(value=0.751, metric=MilestoneType.proportion)
        previous = create_milestone_output_record(value=0.749, metric="proportion")

        # With round_to=2: 0.751 rounds to 0.75, 0.749 rounds to 0.75 - should be False
        assert not check_milestone_is_new(milestone, previous)

    def test_proportion_metric_different_rounded_values(self):
        """Test that proportion metrics work when rounded values are actually different"""
        milestone = create_milestone_record(value=0.76, aggregate=MilestoneAggregate.high, metric=MilestoneType.proportion)
        previous = create_milestone_output_record(value=0.74, aggregate="high", metric="proportion")

        # With round_to=2: 0.76 > 0.74, should be True for high aggregate
        assert check_milestone_is_new(milestone, previous)

    def test_non_proportion_metric_rounding(self):
        """Test that non-proportion metrics use round_to=0"""
        test_metrics = [MilestoneType.demand, MilestoneType.power, MilestoneType.energy]

        for metric in test_metrics:
            milestone = create_milestone_record(value=708.7, metric=metric)
            previous = create_milestone_output_record(value=708.3, metric=metric.value)

            # Both should round to 709 and 708 respectively, but be equal at 709 and 708
            # Wait, let me recalculate: 708.7 rounds to 709, 708.3 rounds to 708
            # So 709 > 708 should be True for high aggregate
            milestone.aggregate = MilestoneAggregate.high
            assert check_milestone_is_new(milestone, previous), (
                f"Expected True for metric {metric.value} with values 708.7 vs 708.3"
            )

    def test_interval_check_prevents_old_intervals(self):
        """Test that milestones with intervals <= previous interval return False"""
        current_time = datetime(2023, 6, 15, 12, 30)
        same_time = datetime(2023, 6, 15, 12, 30)
        earlier_time = datetime(2023, 6, 14, 12, 30)

        # Test same interval
        milestone = create_milestone_record(value=710.0, interval=current_time)
        previous = create_milestone_output_record(value=700.0, interval=same_time)
        assert not check_milestone_is_new(milestone, previous)

        # Test earlier interval
        milestone = create_milestone_record(value=710.0, interval=earlier_time)
        previous = create_milestone_output_record(value=700.0, interval=current_time)
        assert not check_milestone_is_new(milestone, previous)

    def test_null_value_returns_false(self):
        """Test that milestones with null values return False"""
        milestone = create_milestone_record(value=None)
        previous = create_milestone_output_record(value=708.0)

        assert not check_milestone_is_new(milestone, previous)

    def test_edge_cases_around_rounding_boundary(self):
        """Test edge cases around the 0.5 rounding boundary"""
        # Test values that round up vs down
        test_cases = [
            (708.5, 708.49),  # 709 vs 708 - different after rounding
            (708.4, 708.6),  # 708 vs 709 - different after rounding
            (708.499, 708.501),  # 708 vs 709 - different after rounding
        ]

        for current_val, previous_val in test_cases:
            milestone = create_milestone_record(value=current_val, aggregate=MilestoneAggregate.high)
            previous = create_milestone_output_record(value=previous_val, aggregate="high")

            current_rounded = round(current_val, 0)
            previous_rounded = round(previous_val, 0)

            if current_rounded == previous_rounded:
                assert not check_milestone_is_new(milestone, previous), (
                    f"Expected False for {current_val} vs {previous_val} (both round to {current_rounded})"
                )
            elif current_rounded > previous_rounded:
                assert check_milestone_is_new(milestone, previous), (
                    f"Expected True for {current_val} vs {previous_val} ({current_rounded} > {previous_rounded})"
                )

    def test_high_vs_low_aggregate_logic(self):
        """Test that high and low aggregates use correct comparison operators"""
        # High aggregate: new value must be greater than previous
        milestone_high = create_milestone_record(value=710.0, aggregate=MilestoneAggregate.high)
        previous_high = create_milestone_output_record(value=700.0, aggregate="high")
        assert check_milestone_is_new(milestone_high, previous_high)

        # High aggregate: new value less than previous should be False
        milestone_high_lower = create_milestone_record(value=690.0, aggregate=MilestoneAggregate.high)
        assert not check_milestone_is_new(milestone_high_lower, previous_high)

        # Low aggregate: new value must be less than previous
        milestone_low = create_milestone_record(value=690.0, aggregate=MilestoneAggregate.low)
        previous_low = create_milestone_output_record(value=700.0, aggregate="low")
        assert check_milestone_is_new(milestone_low, previous_low)

        # Low aggregate: new value greater than previous should be False
        milestone_low_higher = create_milestone_record(value=710.0, aggregate=MilestoneAggregate.low)
        assert not check_milestone_is_new(milestone_low_higher, previous_low)


# Helpers for interval-period debounce tests (NEM interval_size = 5 minutes)
def create_interval_record(
    value: float,
    interval: datetime,
    aggregate: MilestoneAggregate = MilestoneAggregate.high,
) -> MilestoneRecordSchema:
    """Create an interval-period milestone record"""
    return MilestoneRecordSchema(
        interval=interval,
        aggregate=aggregate,
        metric=MilestoneType.power,
        period=MilestonePeriod.interval,
        network=NetworkNEM,
        unit=create_test_unit(),
        network_region="NSW1",
        fueltech=None,
        value=value,
    )


def create_interval_output_record(
    value: float,
    interval: datetime,
    aggregate: str = "high",
) -> MilestoneRecordOutputSchema:
    """Create an interval-period milestone output (previous) record"""
    return MilestoneRecordOutputSchema(
        record_id="au.nem.nsw1.power.interval.high",
        interval=interval,
        instance_id=uuid.uuid4(),
        aggregate=aggregate,
        metric="power",
        period="interval",
        significance=10,
        value=value,
        value_unit="MW",
        network_id="NEM",
        network_region="NSW1",
        description="Test interval milestone",
    )


class TestCheckMilestoneIsNewDebounce:
    """Test the interval-period debounce in check_milestone_is_new"""

    def test_default_no_debounce_keeps_consecutive_records(self):
        """Without the debounce arg, a record one interval later is still new (legacy behaviour)"""
        previous = create_interval_output_record(value=100.0, interval=datetime(2026, 5, 31, 12, 0))
        milestone = create_interval_record(value=120.0, interval=datetime(2026, 5, 31, 12, 5))

        assert check_milestone_is_new(milestone, previous) is True

    def test_debounce_suppresses_record_within_window(self):
        """An increasing interval record one interval later is suppressed within the window"""
        previous = create_interval_output_record(value=100.0, interval=datetime(2026, 5, 31, 12, 0))
        milestone = create_interval_record(value=120.0, interval=datetime(2026, 5, 31, 12, 5))

        # 5 minutes = 1 interval, well within a 10-interval window
        assert check_milestone_is_new(milestone, previous, debounce_intervals=10) is False

    def test_debounce_suppresses_just_below_window(self):
        """9 intervals (45m) is still within a 10-interval window -> suppressed"""
        previous = create_interval_output_record(value=100.0, interval=datetime(2026, 5, 31, 12, 0))
        milestone = create_interval_record(value=200.0, interval=datetime(2026, 5, 31, 12, 45))

        assert check_milestone_is_new(milestone, previous, debounce_intervals=10) is False

    def test_debounce_keeps_at_window_boundary(self):
        """Exactly the window (10 intervals = 50m) is far enough apart -> kept"""
        previous = create_interval_output_record(value=100.0, interval=datetime(2026, 5, 31, 12, 0))
        milestone = create_interval_record(value=200.0, interval=datetime(2026, 5, 31, 12, 50))

        assert check_milestone_is_new(milestone, previous, debounce_intervals=10) is True

    def test_debounce_keeps_after_window(self):
        """Well beyond the window -> kept"""
        previous = create_interval_output_record(value=100.0, interval=datetime(2026, 5, 31, 12, 0))
        milestone = create_interval_record(value=200.0, interval=datetime(2026, 5, 31, 13, 0))

        assert check_milestone_is_new(milestone, previous, debounce_intervals=10) is True

    def test_debounce_disabled_with_zero(self):
        """debounce_intervals=0 disables debouncing"""
        previous = create_interval_output_record(value=100.0, interval=datetime(2026, 5, 31, 12, 0))
        milestone = create_interval_record(value=120.0, interval=datetime(2026, 5, 31, 12, 5))

        assert check_milestone_is_new(milestone, previous, debounce_intervals=0) is True

    def test_debounce_only_applies_to_interval_period(self):
        """Day+ period records are never debounced even with a huge window"""
        # day records are ~288 intervals apart; a 1000-interval window would suppress them
        # if the period guard were missing
        previous = create_milestone_output_record(value=700.0, interval=datetime(2026, 5, 30, 12, 30))
        milestone = create_milestone_record(value=710.0, interval=datetime(2026, 5, 31, 12, 30))

        assert check_milestone_is_new(milestone, previous, debounce_intervals=1000) is True

    def test_debounce_does_not_override_value_check(self):
        """A record that fails the value comparison is still not new regardless of debounce"""
        previous = create_interval_output_record(value=200.0, interval=datetime(2026, 5, 31, 12, 0))
        # lower value, high aggregate -> not a new high
        milestone = create_interval_record(value=150.0, interval=datetime(2026, 5, 31, 13, 0))

        assert check_milestone_is_new(milestone, previous, debounce_intervals=10) is False
