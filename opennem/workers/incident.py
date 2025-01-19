"""
OpenNEM Data Gap Incident Tracker

This module provides functionality to track data gap incidents in Redis.
It stores information about when data gaps are detected and their resolution status.
"""

from datetime import datetime
from typing import NamedTuple

from opennem.tasks.broker import get_redis_pool


class DataGapIncident(NamedTuple):
    """Data structure for tracking data gap incidents"""

    start_time: datetime
    last_seen: datetime
    resolved: bool
    resolution_time: datetime | None = None


REDIS_KEY_PREFIX = "opennem:datagap:"


async def get_active_incident() -> DataGapIncident | None:
    """
    Get the currently active data gap incident if one exists.

    Returns:
        DataGapIncident | None: The active incident or None if no active incident
    """
    redis = await get_redis_pool()
    incident_data = await redis.hgetall(f"{REDIS_KEY_PREFIX}active")

    if not incident_data:
        return None

    return DataGapIncident(
        start_time=datetime.fromisoformat(incident_data[b"start_time"].decode()),
        last_seen=datetime.fromisoformat(incident_data[b"last_seen"].decode()),
        resolved=incident_data[b"resolved"].decode() == "true",
        resolution_time=datetime.fromisoformat(incident_data[b"resolution_time"].decode())
        if incident_data.get(b"resolution_time")
        else None,
    )


async def create_incident(start_time: datetime, last_seen: datetime) -> None:
    """
    Create a new data gap incident in Redis.

    Args:
        start_time: When the incident was first detected
        last_seen: The last time data was seen before the gap
    """
    redis = await get_redis_pool()

    # Store the incident data
    await redis.hmset(
        f"{REDIS_KEY_PREFIX}active",
        {
            "start_time": start_time.isoformat(),
            "last_seen": last_seen.isoformat(),
            "resolved": "false",
        },
    )


async def resolve_incident(resolution_time: datetime) -> None:
    """
    Mark the current incident as resolved.

    Args:
        resolution_time: When the incident was resolved
    """
    redis = await get_redis_pool()

    # Update the incident with resolution info
    await redis.hmset(
        f"{REDIS_KEY_PREFIX}active",
        {
            "resolved": "true",
            "resolution_time": resolution_time.isoformat(),
        },
    )

    # Archive the incident
    incident_data = await redis.hgetall(f"{REDIS_KEY_PREFIX}active")
    if incident_data:
        start_time = datetime.fromisoformat(incident_data[b"start_time"].decode())
        archive_key = f"{REDIS_KEY_PREFIX}archive:{start_time.isoformat()}"
        await redis.hmset(archive_key, incident_data)

        # Delete the active incident
        await redis.delete(f"{REDIS_KEY_PREFIX}active")


async def has_active_incident() -> bool:
    """
    Check if there is currently an active data gap incident.

    Returns:
        bool: True if there is an active incident, False otherwise
    """
    incident = await get_active_incident()
    return incident is not None and not incident.resolved
