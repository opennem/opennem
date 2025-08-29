from datetime import datetime
import uuid

import pytest

from opennem.core.units import get_unit_by_value
from opennem.recordreactor.schema import (
    MilestoneAggregate,
    MilestoneRecordOutputSchema,
    MilestoneRecordSchema,
    MilestoneType,
    MilestonePeriod,
    MilestoneUnitSchema,
)
from opennem.recordreactor.utils import check_milestone_is_new
from opennem.schema.network import NetworkNEM


# Helper function to create a test unit schema
def create_test_unit(unit_value: str = "MW") -> MilestoneUnitSchema:
    """Create a test unit schema"""
    return MilestoneUnitSchema(
        name="power_mega",
        label="Megawatts", 
        unit=unit_value,
        output_format="{value} {unit}"
    )


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
        description="Test milestone"
    )


class TestCheckMilestoneIsNew:
    """Test the check_milestone_is_new function"""

    def test_identical_rounded_values_return_false(self):
        """Test that milestones with different raw but identical rounded values return False"""
        # Test case from the original issue: 708.1 vs 708.9 should both round to 708
        milestone = create_milestone_record(value=708.1)
        previous = create_milestone_output_record(value=708.9)
        
        assert check_milestone_is_new(milestone, previous) == False

    def test_identical_rounded_values_different_decimals(self):
        """Test various fractional differences that round to the same integer"""
        test_cases = [
            (708.1, 708.9),  # Original issue case
            (500.2, 500.8),  # Different hundreds
            (1000.4, 1000.6),  # Different thousands 
            (50.1, 50.49),   # Edge case near rounding boundary
            (99.51, 99.99),  # Edge case near rounding boundary
        ]
        
        for current_val, previous_val in test_cases:
            milestone = create_milestone_record(value=current_val)
            previous = create_milestone_output_record(value=previous_val)
            
            assert check_milestone_is_new(milestone, previous) == False, \
                f"Expected False for {current_val} vs {previous_val} (both round to {round(current_val, 0)})"

    def test_different_rounded_values_high_aggregate(self):
        """Test that milestones with different rounded values work correctly for high aggregate"""
        milestone = create_milestone_record(value=709.0, aggregate=MilestoneAggregate.high)
        previous = create_milestone_output_record(value=708.0, aggregate="high")
        
        # For high aggregate, 709 > 708 should return True
        assert check_milestone_is_new(milestone, previous) == True

    def test_different_rounded_values_low_aggregate(self):
        """Test that milestones with different rounded values work correctly for low aggregate"""
        milestone = create_milestone_record(value=707.0, aggregate=MilestoneAggregate.low)
        previous = create_milestone_output_record(value=708.0, aggregate="low")
        
        # For low aggregate, 707 < 708 should return True
        assert check_milestone_is_new(milestone, previous) == True

    def test_proportion_metric_uses_different_rounding(self):
        """Test that proportion metrics use round_to=2 instead of round_to=0"""
        milestone = create_milestone_record(value=0.751, metric=MilestoneType.proportion)
        previous = create_milestone_output_record(value=0.749, metric="proportion")
        
        # With round_to=2: 0.751 rounds to 0.75, 0.749 rounds to 0.75 - should be False
        assert check_milestone_is_new(milestone, previous) == False

    def test_proportion_metric_different_rounded_values(self):
        """Test that proportion metrics work when rounded values are actually different"""
        milestone = create_milestone_record(value=0.76, aggregate=MilestoneAggregate.high, metric=MilestoneType.proportion)
        previous = create_milestone_output_record(value=0.74, aggregate="high", metric="proportion")
        
        # With round_to=2: 0.76 > 0.74, should be True for high aggregate
        assert check_milestone_is_new(milestone, previous) == True

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
            assert check_milestone_is_new(milestone, previous) == True, \
                f"Expected True for metric {metric.value} with values 708.7 vs 708.3"

    def test_interval_check_prevents_old_intervals(self):
        """Test that milestones with intervals <= previous interval return False"""
        current_time = datetime(2023, 6, 15, 12, 30)
        same_time = datetime(2023, 6, 15, 12, 30)
        earlier_time = datetime(2023, 6, 14, 12, 30)
        
        # Test same interval
        milestone = create_milestone_record(value=710.0, interval=current_time)
        previous = create_milestone_output_record(value=700.0, interval=same_time)
        assert check_milestone_is_new(milestone, previous) == False
        
        # Test earlier interval
        milestone = create_milestone_record(value=710.0, interval=earlier_time)
        previous = create_milestone_output_record(value=700.0, interval=current_time)
        assert check_milestone_is_new(milestone, previous) == False

    def test_null_value_returns_false(self):
        """Test that milestones with null values return False"""
        milestone = create_milestone_record(value=None)
        previous = create_milestone_output_record(value=708.0)
        
        assert check_milestone_is_new(milestone, previous) == False

    def test_edge_cases_around_rounding_boundary(self):
        """Test edge cases around the 0.5 rounding boundary"""
        # Test values that round up vs down
        test_cases = [
            (708.5, 708.49),  # 709 vs 708 - different after rounding
            (708.4, 708.6),   # 708 vs 709 - different after rounding  
            (708.499, 708.501), # 708 vs 709 - different after rounding
        ]
        
        for current_val, previous_val in test_cases:
            milestone = create_milestone_record(value=current_val, aggregate=MilestoneAggregate.high)
            previous = create_milestone_output_record(value=previous_val, aggregate="high")
            
            current_rounded = round(current_val, 0)
            previous_rounded = round(previous_val, 0)
            
            if current_rounded == previous_rounded:
                assert check_milestone_is_new(milestone, previous) == False, \
                    f"Expected False for {current_val} vs {previous_val} (both round to {current_rounded})"
            elif current_rounded > previous_rounded:
                assert check_milestone_is_new(milestone, previous) == True, \
                    f"Expected True for {current_val} vs {previous_val} ({current_rounded} > {previous_rounded})"

    def test_high_vs_low_aggregate_logic(self):
        """Test that high and low aggregates use correct comparison operators"""
        # High aggregate: new value must be greater than previous
        milestone_high = create_milestone_record(value=710.0, aggregate=MilestoneAggregate.high)
        previous_high = create_milestone_output_record(value=700.0, aggregate="high")
        assert check_milestone_is_new(milestone_high, previous_high) == True
        
        # High aggregate: new value less than previous should be False
        milestone_high_lower = create_milestone_record(value=690.0, aggregate=MilestoneAggregate.high)
        assert check_milestone_is_new(milestone_high_lower, previous_high) == False
        
        # Low aggregate: new value must be less than previous
        milestone_low = create_milestone_record(value=690.0, aggregate=MilestoneAggregate.low)
        previous_low = create_milestone_output_record(value=700.0, aggregate="low")
        assert check_milestone_is_new(milestone_low, previous_low) == True
        
        # Low aggregate: new value greater than previous should be False
        milestone_low_higher = create_milestone_record(value=710.0, aggregate=MilestoneAggregate.low)
        assert check_milestone_is_new(milestone_low_higher, previous_low) == False