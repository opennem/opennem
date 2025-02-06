"""
Core grouping definitions for OpenNEM.

This module defines how time series data can be grouped in queries and responses.
It separates groupings into primary (network-based) and secondary (data-based) types.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum


class PrimaryGrouping(str, Enum):
    """
    Primary grouping types for time series data.

    These groupings are network-based and determine the base level of aggregation.

    Attributes:
        NETWORK: Group by network only (default)
        NETWORK_REGION: Group by network regions (e.g., QLD1, NSW1)
    """

    NETWORK = "network"
    NETWORK_REGION = "network_region"


class SecondaryGrouping(str, Enum):
    """
    Secondary grouping types for time series data.

    These groupings can be applied on top of the primary grouping to provide
    additional dimensionality to the data.

    Attributes:
        FUELTECH: Group by individual fuel technologies
        FUELTECH_GROUP: Group by fuel technology groups (e.g., coal, gas, solar)
        STATUS: Group by facility status (e.g., operating, retired)
        RENEWABLE: Group by renewable vs non-renewable
    """

    FUELTECH = "fueltech"
    FUELTECH_GROUP = "fueltech_group"
    STATUS = "status"
    RENEWABLE = "renewable"


@dataclass
class GroupingMetadata:
    """
    Metadata about a grouping type.

    This class contains information about how a grouping should be handled
    in queries and responses.

    Attributes:
        column_name: The database column name for this grouping
        description: Human-readable description of the grouping
    """

    column_name: str
    description: str


# Metadata for primary groupings
PRIMARY_GROUPING_METADATA = {
    PrimaryGrouping.NETWORK: GroupingMetadata(
        column_name="network_id",
        description="Group by network only",
    ),
    PrimaryGrouping.NETWORK_REGION: GroupingMetadata(
        column_name="network_region",
        description="Group by network regions",
    ),
}

# Metadata for secondary groupings
SECONDARY_GROUPING_METADATA = {
    SecondaryGrouping.FUELTECH: GroupingMetadata(
        column_name="fueltech_id",
        description="Group by individual fuel technologies",
    ),
    SecondaryGrouping.FUELTECH_GROUP: GroupingMetadata(
        column_name="fueltech_group_id",
        description="Group by fuel technology groups",
    ),
    SecondaryGrouping.STATUS: GroupingMetadata(
        column_name="status_id",
        description="Group by facility status",
    ),
    SecondaryGrouping.RENEWABLE: GroupingMetadata(
        column_name="renewable",
        description="Group by renewable vs non-renewable",
    ),
}


def get_primary_grouping_metadata(grouping: PrimaryGrouping) -> GroupingMetadata:
    """
    Get metadata for a primary grouping.

    Args:
        grouping: The grouping to get metadata for

    Returns:
        GroupingMetadata: The metadata for the grouping

    Raises:
        ValueError: If the grouping is not found
    """
    if grouping not in PRIMARY_GROUPING_METADATA:
        raise ValueError(f"Unknown primary grouping: {grouping}")
    return PRIMARY_GROUPING_METADATA[grouping]


def get_secondary_grouping_metadata(grouping: SecondaryGrouping) -> GroupingMetadata:
    """
    Get metadata for a secondary grouping.

    Args:
        grouping: The grouping to get metadata for

    Returns:
        GroupingMetadata: The metadata for the grouping

    Raises:
        ValueError: If the grouping is not found
    """
    if grouping not in SECONDARY_GROUPING_METADATA:
        raise ValueError(f"Unknown secondary grouping: {grouping}")
    return SECONDARY_GROUPING_METADATA[grouping]


def validate_groupings(
    primary: PrimaryGrouping,
    secondary: Sequence[SecondaryGrouping] | None = None,
) -> None:
    """
    Validate a combination of primary and secondary groupings.

    Args:
        primary: The primary grouping to validate
        secondary: Optional sequence of secondary groupings to validate

    Raises:
        ValueError: If the grouping combination is invalid
    """
    if not secondary:
        return

    primary_meta = get_primary_grouping_metadata(primary)
    if not primary_meta.allow_secondary and secondary:
        raise ValueError(f"Primary grouping {primary} cannot be combined with secondary groupings")
