"""Content generation helpers for social media posts.

Generates text and images for different post types (milestones, etc.).
"""

import logging

from opennem.recordreactor.schema import MilestoneRecordSchema

logger = logging.getLogger("opennem.social.content")


def render_milestone_social_text(milestone: MilestoneRecordSchema) -> str:
    """Generate social media text for a new milestone/record."""
    desc = milestone.description or milestone.record_id

    parts = [desc]

    if milestone.value is not None and milestone.value_unit:
        unit = milestone.value_unit
        val = float(milestone.value)
        if unit == "MWh" and val >= 1000:
            parts.append(f"({val / 1000:,.1f} GWh)")
        elif unit == "MW":
            parts.append(f"({val:,.0f} MW)")
        elif unit == "%":
            parts.append(f"({val:.1f}%)")
        else:
            parts.append(f"({val:,.0f} {unit})")

    if milestone.pct_change is not None:
        pct = float(milestone.pct_change)
        if abs(pct) > 0.1:
            direction = "up" if pct > 0 else "down"
            parts.append(f"— {direction} {abs(pct):.1f}% from previous record")

    parts.append("\nopenelectricity.org.au/records")

    return " ".join(parts)
