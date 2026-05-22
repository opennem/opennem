"""Content generation helpers for social media posts.

Generates text and images for different post types (milestones, etc.).
"""

import io
import logging
from datetime import datetime
from pathlib import Path

from opennem.core.fueltech_group import get_fueltech_group
from opennem.core.templates import serve_template
from opennem.recordreactor.schema import MilestoneRecordOutputSchema
from opennem.static.fueltech_icons import FALLBACK_ICON, FUELTECH_ICON_PATHS

logger = logging.getLogger("opennem.social.content")


# ---------- Text ----------


def render_milestone_social_text(milestone: MilestoneRecordOutputSchema) -> str:
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

    return " ".join(parts)


def build_record_url(record_id: str, focus_ts_ms: int) -> str:
    """Build a deep link to the record page on openelectricity.org.au."""
    return f"https://openelectricity.org.au/records/{record_id}?focus={focus_ts_ms}&offset=10_00"


# ---------- Image card ----------

CARD_WIDTH = 1200
CARD_HEIGHT = 630
SPARKLINE_VIEW_W = 1088  # 1200 - 2*56 card padding
SPARKLINE_VIEW_H = 290  # matches rendered container aspect so circle stays round


def _icon_color(fueltech_id: str | None) -> str:
    """Solar's yellow background needs a dark icon; everything else is white."""
    return "#222" if fueltech_id and fueltech_id.startswith("solar") else "#fff"


def _fueltech_icon_svg(fueltech_id: str | None, px: int = 38) -> str:
    icon_paths = FUELTECH_ICON_PATHS.get(fueltech_id or "", FALLBACK_ICON)
    color = _icon_color(fueltech_id)
    icon_paths = icon_paths.replace("currentColor", color)
    return (
        f'<svg width="{px}" height="{px}" viewBox="0 0 17 17" '
        f'xmlns="http://www.w3.org/2000/svg" fill="none" stroke="{color}">'
        f"{icon_paths}"
        "</svg>"
    )


def _format_value(value: float, unit: str) -> tuple[str, str]:
    """Format a record value + unit for display.

    Returns (value_str, unit_str). Value is grouped with thousands separator;
    MWh ≥1000 promote to GWh.
    """
    if unit == "MWh" and value >= 1000:
        return f"{value / 1000:,.1f}", "GWh"
    if unit == "MW":
        return f"{value:,.0f}", "MW"
    if unit == "%":
        return f"{value:.1f}", "%"
    if unit == "AUD":
        return f"${value:,.0f}", ""
    if unit == "tCO2e":
        return f"{value:,.0f}", "tCO₂e"
    return f"{value:,.0f}", unit


def _format_pct_change(pct: float | None) -> tuple[str, str]:
    """Returns (css_class, display_string)."""
    if pct is None or abs(pct) < 0.1:
        return "flat", ""
    arrow = "&#9650;" if pct > 0 else "&#9660;"
    css = "up" if pct > 0 else "down"
    return css, f"{arrow} {abs(pct):.1f}% on previous record"


def _format_set_date(interval: datetime, period: str | None) -> str:
    """Format the record-set date depending on the period granularity."""
    if period in ("interval", "hour"):
        return interval.strftime("%-d %b %Y, %-I:%M%p").replace("AM", "am").replace("PM", "pm")
    if period == "day":
        return interval.strftime("%-d %b %Y")
    if period == "week":
        return f"week of {interval.strftime('%-d %b %Y')}"
    if period == "month":
        return interval.strftime("%B %Y")
    if period in ("season", "quarter"):
        return interval.strftime("%b %Y")
    if period == "year":
        return interval.strftime("%Y")
    return interval.strftime("%-d %b %Y")


def _format_history_label(history: list[tuple[datetime, float]]) -> str:
    if not history:
        return "Previous records"
    span = (history[-1][0] - history[0][0]).days
    if span > 730:
        return f"Previous records · {history[0][0].year}–{history[-1][0].year}"
    if span > 60:
        return f"Previous records · last {span // 30} months"
    if span > 0:
        return f"Previous records · last {span} days"
    return "Previous records"


def _build_sparkline_svg(
    history: list[tuple[datetime, float]],
    current_value: float,
    color: str,
) -> str:
    """Render a sparkline SVG path from history values, with the current value
    pinned to the right edge as a focus dot.

    history: list of (interval, value) ordered oldest → newest. May be empty.
    current_value: the new record value (becomes the rightmost point).
    """
    points: list[tuple[datetime, float]] = list(history)
    # Append the current record as the final point if not already there
    if not points or points[-1][1] != current_value:
        # Use a synthetic timestamp slightly after the last history point
        last_ts = points[-1][0] if points else datetime.now()
        points.append((last_ts, current_value))

    if len(points) < 2:
        return (
            f'<svg class="sparkline-svg" viewBox="0 0 {SPARKLINE_VIEW_W} {SPARKLINE_VIEW_H}" '
            f'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">'
            f'<text x="{SPARKLINE_VIEW_W // 2}" y="{SPARKLINE_VIEW_H // 2 + 6}" '
            f'text-anchor="middle" fill="#999" font-family="DM Mono, monospace" font-size="14">'
            f"first record of its kind"
            f"</text></svg>"
        )

    values = [v for _, v in points]
    vmin = 0.0
    vmax = max(values)
    if vmax <= 0:
        vmax = 1.0
    # Padding inside the viewBox so the focus dot (r=8 + stroke 3) doesn't clip
    pad_y = 16
    pad_x_left = 6
    pad_x_right = 28
    h = SPARKLINE_VIEW_H - 2 * pad_y
    w = SPARKLINE_VIEW_W - pad_x_left - pad_x_right

    # Place points evenly across X (we don't have to honor exact dates — visual trend matters)
    n = len(points)
    coords = []
    for i, (_, v) in enumerate(points):
        x = pad_x_left + (i / (n - 1)) * w
        y = pad_y + h - ((v - vmin) / (vmax - vmin)) * h
        coords.append((x, y))

    # Smooth-ish polyline with line-to commands (good enough at this size)
    d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
    # Area fill underneath (extend to padded baseline, not viewBox edge)
    baseline_y = SPARKLINE_VIEW_H - pad_y
    area_d = d + f" L {coords[-1][0]:.1f},{baseline_y} L {coords[0][0]:.1f},{baseline_y} Z"

    fx, fy = coords[-1]

    return (
        f'<svg class="sparkline-svg" viewBox="0 0 {SPARKLINE_VIEW_W} {SPARKLINE_VIEW_H}" '
        f'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">'
        f'<path d="{area_d}" fill="{color}" fill-opacity="0.12" stroke="none"/>'
        f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.5" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="6" fill="white" stroke="black" stroke-width="2.5"/>'
        f"</svg>"
    )


def render_milestone_card(
    record_id: str,
    interval: datetime,
    description: str | None,
    value: float,
    value_unit: str,
    pct_change: float | None,
    period: str | None,
    network_region: str | None,
    fueltech_id: str | None,
    history: list[tuple[datetime, float]] | None = None,
) -> bytes:
    """Render a 1200x630 PNG milestone card.

    `history` is an ordered list of (interval, value) tuples for previous records
    of the same record_id, oldest first. The current record is plotted as the
    rightmost focus point.
    """
    from html2image import Html2Image

    # Fueltech color + icon
    ft_color = "#888888"
    if fueltech_id:
        try:
            fg = get_fueltech_group(fueltech_id)
            ft_color = fg.color or "#888888"
        except Exception:
            pass

    icon_svg = _fueltech_icon_svg(fueltech_id, px=38)
    icon_color = _icon_color(fueltech_id)

    # Strip "for NEM/WEM in X" suffix from description for compactness
    title = description or record_id
    for strip in [" for NEM", " for WEM"]:
        if strip in title:
            title = title[: title.index(strip)]

    # Region label (strip trailing 1 from NEM regions)
    region = network_region.rstrip("1") if network_region else ""

    value_str, unit_str = _format_value(float(value), value_unit)
    change_class, change_str = _format_pct_change(pct_change)
    set_date = _format_set_date(interval, period)

    history = history or []
    sparkline_svg = _build_sparkline_svg(history, float(value), ft_color)
    history_label = _format_history_label(history)
    period_label = (period or "").upper()

    html = serve_template(
        "record_card.html",
        title=title,
        description=description or record_id,
        region=region,
        ft_color=ft_color,
        icon_color=icon_color,
        icon_svg=icon_svg,
        value_str=value_str,
        unit_str=unit_str,
        change_class=change_class,
        change_str=change_str,
        set_date=set_date,
        sparkline_svg=sparkline_svg,
        history_label=history_label,
        period_label=period_label,
    )

    output_dir = "/tmp"
    output_file = f"record_card_{record_id.replace('.', '_')}.png"
    hti = Html2Image(
        output_path=output_dir,
        size=(CARD_WIDTH, CARD_HEIGHT),
        custom_flags=["--force-device-scale-factor=2"],
    )
    hti.screenshot(html_str=html, save_as=output_file)

    output_path = Path(output_dir) / output_file
    data = output_path.read_bytes()
    output_path.unlink(missing_ok=True)

    buf = io.BytesIO(data)
    buf.seek(0)
    return buf.getvalue()
