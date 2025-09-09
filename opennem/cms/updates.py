"""
Module that sends a slack report of CMS updates based on updatedAt metadata
in the database.

"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from opennem import settings
from opennem.clients.slack import slack_message
from opennem.db import get_read_session
from opennem.db.models.opennem import Facility, Unit
from opennem.utils.dates import format_sydney_time

logger = logging.getLogger("opennem.cms.updates")


async def get_cms_updates_report(hours: int = 24) -> str:
    """
    Get a report of facilities and units that have been updated in CMS in the last N hours.

    Args:
        hours: Number of hours to look back (default 24)

    Returns:
        Formatted report string
    """
    cutoff_time = datetime.now(UTC) - timedelta(hours=hours)

    async with get_read_session() as session:
        # Get updated facilities with their units
        facilities_query = select(Facility).where(Facility.cms_updated_at >= cutoff_time).options(selectinload(Facility.units))

        result = await session.execute(facilities_query)
        updated_facilities = result.scalars().all()

        # Get ALL updated units with their facilities (not just standalone)
        units_query = select(Unit).where(Unit.cms_updated_at >= cutoff_time).options(selectinload(Unit.facility))

        result = await session.execute(units_query)
        all_updated_units = result.scalars().all()

    # Build the report
    report_lines = []
    report_lines.append("*CMS Updates Report*")
    report_lines.append(f"_Report generated: {format_sydney_time(datetime.now(UTC))} Sydney_")
    report_lines.append("")

    # Process facilities
    if updated_facilities:
        report_lines.append(f"*Facility Updates ({len(updated_facilities)}):*")
        for facility in updated_facilities:
            num_units = len(facility.units)
            total_capacity = sum(u.capacity_registered or 0 for u in facility.units)
            report_lines.append(
                f"• {facility.name} ({facility.code}) - {facility.network_region} - "
                f"{num_units} units, {total_capacity:.1f}MW - {format_sydney_time(facility.cms_updated_at)}"
            )
        report_lines.append("")

    # Process all units with better formatting - limit to top 20 to avoid character limit
    if all_updated_units:
        # Sort by update time (most recent first)
        sorted_units = sorted(all_updated_units, key=lambda u: u.cms_updated_at or datetime.min.replace(tzinfo=UTC), reverse=True)

        # Limit to avoid Slack's character limit
        display_units = sorted_units[:20] if len(sorted_units) > 20 else sorted_units
        units_text = (
            f"*Unit Updates (showing {len(display_units)} of {len(all_updated_units)}):*"
            if len(sorted_units) > 20
            else f"*Unit Updates ({len(all_updated_units)}):*"
        )
        report_lines.append(units_text)

        for unit in display_units:
            facility_name = unit.facility.name if unit.facility else "Unknown"
            facility_code = unit.facility.code if unit.facility else "N/A"
            region = unit.facility.network_region if unit.facility else "N/A"
            capacity = f"{unit.capacity_registered:.1f}MW" if unit.capacity_registered else "N/A"
            fueltech = unit.fueltech_id or "N/A"

            report_lines.append(
                f"• {unit.code} - {facility_name} ({facility_code}) - {region} - "
                f"{fueltech} - {capacity} - {format_sydney_time(unit.cms_updated_at)}"
            )
        report_lines.append("")

    if not updated_facilities and not all_updated_units:
        report_lines.append("No CMS updates found in the last 24 hours.")

    # Get unique stations that had unit updates
    unique_stations = {(u.facility.code, u.facility.name) for u in all_updated_units if u.facility}
    report_lines.append(f"• Stations with unit changes: {len(unique_stations)}")

    return "\n".join(report_lines)


async def send_cms_updates_slack_report() -> None:
    """
    Send a slack report of CMS updates based on updatedAt metadata in the database.
    """
    report = await get_cms_updates_report(hours=24)

    if settings.slack_hook_new_facilities:
        await slack_message(webhook_url=settings.slack_hook_new_facilities, message=report)
