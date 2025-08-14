"""
Unit history tracking utilities

This module provides functions for tracking and querying historical changes
to unit fields (capacity_registered, emissions_factor_co2, emission_factor_source).
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from opennem.db.models.opennem import Unit, UnitHistory

logger = logging.getLogger(__name__)


async def track_unit_changes(
    session: AsyncSession, unit: Unit, changed_by: str | None = None, change_reason: str | None = None, **kwargs: Any
) -> UnitHistory | None:
    """
    Track changes to unit fields in the history table.

    Args:
        session: Database session
        unit: Unit instance to track changes for
        changed_by: Username or system identifier making the change
        change_reason: Optional reason for the change
        **kwargs: Field values to update (capacity_registered, emissions_factor_co2, emission_factor_source)

    Returns:
        UnitHistory instance if changes were made, None otherwise
    """
    tracked_fields = {"capacity_registered", "emissions_factor_co2", "emission_factor_source"}

    # Check what actually changed
    changes = {}
    for field in tracked_fields:
        if field in kwargs:
            old_value = getattr(unit, field)
            new_value = kwargs[field]
            # Handle None comparisons and numeric precision
            if old_value != new_value:
                changes[field] = new_value

    # Only create history if something changed
    if changes:
        history_entry = UnitHistory(unit_id=unit.id, changed_by=changed_by, change_reason=change_reason, **changes)
        session.add(history_entry)

        # Update the unit with new values
        for field, value in changes.items():
            setattr(unit, field, value)

        logger.info(f"Tracked changes for unit {unit.code}: {list(changes.keys())}")
        return history_entry

    return None


async def get_unit_value_at_date(session: AsyncSession, unit_id: int, field: str, at_date: datetime) -> Any:
    """
    Get the value of a unit field at a specific date.

    Args:
        session: Database session
        unit_id: Unit ID
        field: Field name to query (capacity_registered, emissions_factor_co2, emission_factor_source)
        at_date: Date to get the value at

    Returns:
        Field value at the specified date, or None if no history exists
    """
    # Query history for the most recent change before the date
    stmt = (
        select(UnitHistory)
        .where(UnitHistory.unit_id == unit_id, UnitHistory.changed_at <= at_date, getattr(UnitHistory, field).isnot(None))
        .order_by(UnitHistory.changed_at.desc())
        .limit(1)
    )

    result = await session.execute(stmt)
    record = result.scalar_one_or_none()

    if record:
        return getattr(record, field)

    return None


async def get_unit_history(
    session: AsyncSession, unit_id: int, field: str | None = None, limit: int | None = None
) -> list[UnitHistory]:
    """
    Get the change history for a unit.

    Args:
        session: Database session
        unit_id: Unit ID
        field: Optional field name to filter history
        limit: Optional limit on number of records

    Returns:
        List of UnitHistory records
    """
    stmt = select(UnitHistory).where(UnitHistory.unit_id == unit_id).order_by(UnitHistory.changed_at.desc())

    # Filter by field if specified
    if field:
        stmt = stmt.where(getattr(UnitHistory, field).isnot(None))

    if limit:
        stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_current_unit_values(session: AsyncSession, unit_id: int) -> dict[str, Any]:
    """
    Get the current (latest) values for all tracked fields from history.

    Args:
        session: Database session
        unit_id: Unit ID

    Returns:
        Dictionary mapping field names to their current values
    """
    current_values = {}
    tracked_fields = ["capacity_registered", "emissions_factor_co2", "emission_factor_source"]

    for field in tracked_fields:
        stmt = (
            select(UnitHistory)
            .where(UnitHistory.unit_id == unit_id, getattr(UnitHistory, field).isnot(None))
            .order_by(UnitHistory.changed_at.desc())
            .limit(1)
        )

        result = await session.execute(stmt)
        record = result.scalar_one_or_none()

        if record:
            current_values[field] = getattr(record, field)
        else:
            current_values[field] = None

    return current_values


def track_unit_changes_sync(
    session: Session, unit: Unit, changed_by: str | None = None, change_reason: str | None = None, **kwargs: Any
) -> UnitHistory | None:
    """
    Synchronous version of track_unit_changes for non-async contexts.

    See track_unit_changes for documentation.
    """
    tracked_fields = {"capacity_registered", "emissions_factor_co2", "emission_factor_source"}

    # Check what actually changed
    changes = {}
    for field in tracked_fields:
        if field in kwargs:
            old_value = getattr(unit, field)
            new_value = kwargs[field]
            if old_value != new_value:
                changes[field] = new_value

    # Only create history if something changed
    if changes:
        history_entry = UnitHistory(unit_id=unit.id, changed_by=changed_by, change_reason=change_reason, **changes)
        session.add(history_entry)

        # Update the unit with new values
        for field, value in changes.items():
            setattr(unit, field, value)

        logger.info(f"Tracked changes for unit {unit.code}: {list(changes.keys())}")
        return history_entry

    return None
