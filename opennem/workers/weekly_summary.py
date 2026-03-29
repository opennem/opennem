"""
Weekly summary — fueltech mix, price, renewable proportion,
and milestones per network posted to Slack for approval then
published to Twitter/X, Bluesky, and LinkedIn.
"""

import io
import logging
from datetime import datetime, timedelta
from operator import attrgetter
from pathlib import Path

from opennem import settings
from opennem.api.data.schema import DataMetric
from opennem.api.queries import QueryType, get_timeseries_query
from opennem.core.fueltech_group import get_fueltech_group
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.templates import serve_template
from opennem.core.time_interval import Interval
from opennem.db import get_read_session
from opennem.db.clickhouse import execute_async, get_clickhouse_client
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM
from opennem.static.fueltech_icons import FALLBACK_ICON, FUELTECH_ICON_PATHS

logger = logging.getLogger("opennem.workers.weekly_summary")


# --- Schemas ---


class WeeklySummaryResult(BaseConfig):
    """Per-fueltech-group result for one week"""

    fueltech_group_id: str
    fueltech_label: str
    fueltech_color: str
    renewable: bool
    energy_gwh: float
    market_value: float
    demand_proportion: float = 0.0
    wow_change: float | None = None  # energy % change
    mv_wow_change: float | None = None  # market value % change


class WeeklyPriceResult(BaseConfig):
    """Per-region market summary for one week"""

    network_region: str
    demand_energy_gwh: float
    avg_price: float


class WeeklyMilestone(BaseConfig):
    """Significant milestone from the week"""

    interval: datetime
    record_id: str
    description: str | None = None
    significance: int
    value: float | None = None
    value_unit: str | None = None
    pct_change: float | None = None
    aggregate: str | None = None  # "high" or "low"
    metric: str | None = None
    period: str | None = None
    network_id: str | None = None
    network_region: str | None = None
    fueltech_id: str | None = None


class WeeklySummary(BaseConfig):
    """Complete weekly summary for a network"""

    week_start: datetime
    week_end: datetime
    week_number: int
    network: str
    chart_url: str | None = None
    results: list[WeeklySummaryResult]
    price_results: list[WeeklyPriceResult]
    milestones: list[WeeklyMilestone]

    # WoW changes for headline stats
    total_energy_wow: float | None = None
    renewable_wow: float | None = None
    avg_price_wow: float | None = None

    @property
    def renewable_proportion(self) -> float:
        return sum(r.demand_proportion for r in self.results if r.renewable)

    @property
    def total_energy_gwh(self) -> float:
        return sum(r.energy_gwh for r in self.results)

    @property
    def total_market_value(self) -> float:
        return sum(r.market_value for r in self.results)

    @property
    def records(self) -> list[WeeklySummaryResult]:
        return sorted(self.results, key=attrgetter("energy_gwh"), reverse=True)

    def records_chart(self, cutoff: float = 1.0, other_color: str = "brown") -> list[WeeklySummaryResult]:
        """Group small fueltechs into 'Other' for chart readability."""
        above = [r for r in self.records if r.demand_proportion > cutoff]
        below = [r for r in self.records if r.demand_proportion <= cutoff]

        if below:
            other = WeeklySummaryResult(
                fueltech_group_id="other",
                fueltech_label="Other",
                fueltech_color=other_color,
                renewable=False,
                energy_gwh=sum(r.energy_gwh for r in below),
                market_value=sum(r.market_value for r in below),
                demand_proportion=sum(r.demand_proportion for r in below),
            )
            above.append(other)

        return above


# --- Date helpers ---


def _get_week_boundaries(week_start: datetime | None = None) -> tuple[datetime, datetime]:
    """Get Monday 00:00 to Sunday 23:59 for a week.

    If week_start is None, returns the most recent *complete* week
    (the week that ended last Sunday). If week_start is provided,
    returns that week (week_start must be a Monday).
    """
    if week_start is not None:
        # Use the explicit week_start (must be a Monday)
        ws = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        we = ws + timedelta(days=7) - timedelta(seconds=1)
        return ws, we

    # Default: most recent complete week (ended last Sunday)
    now = datetime.now()
    days_since_monday = now.weekday()
    this_monday = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)

    week_end = this_monday - timedelta(seconds=1)  # Sunday 23:59:59
    week_start_dt = this_monday - timedelta(days=7)  # Previous Monday 00:00

    return week_start_dt, week_end


# --- Data fetching ---


async def _fetch_fueltech_energy(
    network: NetworkSchema,
    week_start: datetime,
    week_end: datetime,
) -> list[tuple]:
    """Fetch energy + market_value by fueltech_group for a date range from ClickHouse."""
    query, params, _columns = get_timeseries_query(
        query_type=QueryType.DATA,
        network=network,
        metrics=[DataMetric.ENERGY, DataMetric.MARKET_VALUE],
        interval=Interval.WEEK,
        date_start=week_start,
        date_end=week_end,
        secondary_groupings=[SecondaryGrouping.FUELTECH_GROUP],
    )

    client = get_clickhouse_client()
    return await execute_async(client, query, params)


async def _fetch_price_by_region(
    network: NetworkSchema,
    week_start: datetime,
    week_end: datetime,
) -> list[tuple]:
    """Fetch demand energy + avg price per region from ClickHouse."""
    query, params, _columns = get_timeseries_query(
        query_type=QueryType.MARKET,
        network=network,
        metrics=[Metric.DEMAND_ENERGY, Metric.PRICE],
        interval=Interval.WEEK,
        date_start=week_start,
        date_end=week_end,
        primary_grouping=PrimaryGrouping.NETWORK_REGION,
    )

    client = get_clickhouse_client()
    return await execute_async(client, query, params)


async def _fetch_milestones(
    network: NetworkSchema,
    week_start: datetime,
    week_end: datetime,
) -> list[WeeklyMilestone]:
    """Fetch significant milestones from PG for the week."""
    from opennem.api.milestones.queries import get_milestone_records

    # Step down significance until we find at least 4 milestones
    records: list[dict] = []
    async with get_read_session() as session:
        for min_sig in (9, 8, 7):
            records, _total = await get_milestone_records(
                session=session,
                date_start=week_start,
                date_end=week_end,
                significance_min=min_sig,
                record_filter=[network.code],
                limit=20,
            )
            if len(records) >= 4:
                break

    return [
        WeeklyMilestone(
            interval=r["interval"],
            record_id=r.get("record_id", ""),
            description=r.get("description"),
            significance=r.get("significance", 0),
            value=r.get("value"),
            value_unit=r.get("value_unit"),
            pct_change=r.get("pct_change"),
            aggregate=r.get("aggregate"),
            metric=r.get("metric"),
            period=r.get("period"),
            network_id=r.get("network_id"),
            network_region=r.get("network_region"),
            fueltech_id=r.get("fueltech_id"),
        )
        for r in records
    ]


# Fueltech groups to exclude from the generation mix
# battery = net storage (negative), battery_charging = demand-side
EXCLUDED_FUELTECH_GROUPS = {"battery", "battery_charging", "pumps"}


def _build_fueltech_results(
    current_rows: list[tuple],
    prev_rows: list[tuple] | None = None,
) -> list[WeeklySummaryResult]:
    """Build WeeklySummaryResult list from CH query rows.

    CH columns: interval, network, fueltech_group, energy (MWh), market_value ($)
    Energy is converted from MWh to GWh (÷1000).
    """
    # Filter out excluded fueltechs and convert MWh → GWh
    filtered_rows = [
        (r[0], r[1], r[2], (r[3] or 0) / 1000, r[4] or 0) for r in current_rows if r[2] not in EXCLUDED_FUELTECH_GROUPS
    ]

    # Sum total energy for proportion calculation
    total_energy = sum(row[3] for row in filtered_rows)

    # Build lookups for previous week (also convert MWh → GWh)
    prev_energy: dict[str, float] = {}
    prev_mv: dict[str, float] = {}
    if prev_rows:
        for row in prev_rows:
            fg_id = row[2]
            if fg_id in EXCLUDED_FUELTECH_GROUPS:
                continue
            prev_energy[fg_id] = (row[3] or 0) / 1000
            prev_mv[fg_id] = row[4] or 0

    results = []
    for row in filtered_rows:
        fg_id = row[2]
        energy_gwh = row[3]
        market_value = row[4]

        try:
            fg = get_fueltech_group(fg_id)
        except Exception:
            logger.warning(f"Unknown fueltech group: {fg_id}")
            continue

        proportion = (energy_gwh / total_energy * 100) if total_energy > 0 else 0

        # WoW changes
        wow = None
        if fg_id in prev_energy and prev_energy[fg_id] > 0:
            wow = ((energy_gwh - prev_energy[fg_id]) / prev_energy[fg_id]) * 100

        mv_wow = None
        if fg_id in prev_mv and prev_mv[fg_id] > 0:
            mv_wow = ((market_value - prev_mv[fg_id]) / prev_mv[fg_id]) * 100

        results.append(
            WeeklySummaryResult(
                fueltech_group_id=fg_id,
                fueltech_label=fg.label,
                fueltech_color=fg.color or "grey",
                renewable=fg.renewable,
                energy_gwh=round(energy_gwh, 2),
                market_value=round(market_value, 2),
                demand_proportion=round(proportion, 2),
                wow_change=round(wow, 1) if wow is not None else None,
                mv_wow_change=round(mv_wow, 1) if mv_wow is not None else None,
            )
        )

    return results


def _build_price_results(rows: list[tuple], network: NetworkSchema) -> list[WeeklyPriceResult]:
    """Build WeeklyPriceResult list from CH query rows.

    CH columns: interval, network, network_region, demand_energy (MWh), price ($/MWh)
    Filters out regions that don't belong to the queried network.
    """
    # NEM regions: NSW1, QLD1, SA1, TAS1, VIC1. WEM region: WEM.
    nem_regions = {"NSW1", "QLD1", "SA1", "TAS1", "VIC1"}
    wem_regions = {"WEM"}
    valid_regions = nem_regions if network.code == "NEM" else wem_regions

    results = []
    for row in rows:
        region = row[2]
        if region not in valid_regions:
            continue
        results.append(
            WeeklyPriceResult(
                network_region=region,
                demand_energy_gwh=round(row[3] or 0, 2),
                avg_price=round(row[4] or 0, 2),
            )
        )

    return results


# --- Chart (HTML → headless Chrome screenshot) ---

# Social media portrait: 1080x1350 (4:5 ratio — Instagram, Twitter, LinkedIn)
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1350


def _get_logo_url() -> str:
    """Get logo as a file:// URL or data URI for HTML rendering."""
    logo_path = Path(__file__).parent.parent.parent.parent / "platform" / "public" / "logo" / "open-electricity.png"
    if logo_path.exists():
        return logo_path.as_uri()
    return ""


def _generate_pie_svg(records: list[WeeklySummaryResult], size: int = 380) -> str:
    """Generate an SVG pie chart from fueltech records."""
    cx, cy, r = size // 2, size // 2, size // 2 - 10
    total = sum(rec.demand_proportion for rec in records)
    if total <= 0:
        return ""

    paths = []
    angle = -90  # start at top

    for rec in records:
        pct = rec.demand_proportion / total
        sweep = pct * 360
        large_arc = 1 if sweep > 180 else 0

        import math

        x1 = cx + r * math.cos(math.radians(angle))
        y1 = cy + r * math.sin(math.radians(angle))
        x2 = cx + r * math.cos(math.radians(angle + sweep))
        y2 = cy + r * math.sin(math.radians(angle + sweep))

        if pct >= 0.999:
            # Full circle
            paths.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{rec.fueltech_color}" />')
        else:
            path = f"M {cx},{cy} L {x1:.2f},{y1:.2f} A {r},{r} 0 {large_arc},1 {x2:.2f},{y2:.2f} Z"
            paths.append(f'<path d="{path}" fill="{rec.fueltech_color}" />')

        # Percentage label for slices > 5%
        if pct > 0.05:
            label_angle = angle + sweep / 2
            label_r = r * 0.65
            lx = cx + label_r * math.cos(math.radians(label_angle))
            ly = cy + label_r * math.sin(math.radians(label_angle))
            paths.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="central" '
                f'fill="white" font-family="DM Sans, sans-serif" font-size="18" font-weight="600">'
                f"{rec.demand_proportion:.0f}%</text>"
            )

        angle += sweep

    return f'<svg viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">{"".join(paths)}</svg>'


def _get_fueltech_icon_svg(fueltech_id: str | None, color: str) -> str:
    """Get inline SVG for a fueltech icon in a colored circle, matching openelectricity style."""
    icon_paths = FUELTECH_ICON_PATHS.get(fueltech_id or "", FALLBACK_ICON)
    # Solar uses black icon on yellow bg, everything else uses white
    icon_color = "#222" if fueltech_id == "solar" else "#fff"

    return (
        f'<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">'
        f'<circle cx="16" cy="16" r="16" fill="{color}"/>'
        f'<g transform="translate(7.5, 7.5)" stroke="{icon_color}" fill="none">'
        f"{icon_paths}"
        f"</g></svg>"
    )


def _format_wow(change: float | None) -> tuple[str, str]:
    """Format a WoW change value into (css_class, display_string)."""
    if change is not None and abs(change) > 1:
        arrow = "&#9650;" if change > 0 else "&#9660;"
        css = "wow-up" if change > 0 else "wow-down"
        return css, f"{arrow} {abs(change):.0f}%"
    if change is not None:
        return "wow-flat", "–"
    return "wow-flat", ""


def _prepare_record_display(r: WeeklySummaryResult) -> dict:
    """Prepare a record for HTML template display."""
    wow_class, wow_str = _format_wow(r.wow_change)

    return {
        "fueltech_label": r.fueltech_label,
        "fueltech_color": r.fueltech_color,
        "energy_str": f"{r.energy_gwh:,.0f}",
        "pct_str": f"{r.demand_proportion:.1f}",
        "wow_class": wow_class,
        "wow_str": wow_str,
    }


def _prepare_milestone_display(m: WeeklyMilestone) -> dict:
    """Prepare a milestone for HTML template display."""
    # Format value and unit separately for template
    value_str = ""
    unit_str = ""
    if m.value is not None:
        v = float(m.value)
        unit = m.value_unit or ""
        if unit == "MW":
            value_str = f"{v:,.0f}"
            unit_str = "MW"
        elif unit == "MWh":
            if v >= 1000:
                value_str = f"{v / 1000:,.1f}"
                unit_str = "GWh"
            else:
                value_str = f"{v:,.0f}"
                unit_str = "MWh"
        elif unit == "AUD":
            value_str = f"${v:,.0f}"
        elif unit == "tCO2e":
            value_str = f"{v:,.0f}"
            unit_str = "tCO2e"
        elif unit == "%":
            value_str = f"{v:.1f}"
            unit_str = "%"
        else:
            value_str = f"{v:,.0f}"
            unit_str = unit

    # Format pct_change
    change_str = ""
    change_class = "wow-flat"
    if m.pct_change is not None:
        pct = float(m.pct_change)
        if abs(pct) > 0.1:
            arrow = "&#9650;" if pct > 0 else "&#9660;"
            change_class = "wow-up" if pct > 0 else "wow-down"
            change_str = f"{arrow} {abs(pct):.1f}%"

    # Fueltech color
    ft_color = "#888"
    if m.fueltech_id:
        try:
            fg = get_fueltech_group(m.fueltech_id)
            ft_color = fg.color or "#888"
        except Exception:
            pass

    # Build icon SVG
    icon_svg = _get_fueltech_icon_svg(m.fueltech_id, ft_color)

    # Region label (strip trailing "1" from NEM regions like NSW1 → NSW)
    region = ""
    if m.network_region:
        region = m.network_region.rstrip("1")

    # Short description — strip "for NEM in ..." suffix for compactness
    desc = m.description or m.record_id
    for strip in [" for NEM", " for WEM"]:
        if strip in desc:
            desc = desc[: desc.index(strip)]

    return {
        "date_str": m.interval.strftime("%-d %b"),
        "description": desc,
        "value_str": value_str,
        "unit_str": unit_str,
        "change_str": change_str,
        "change_class": change_class,
        "ft_color": ft_color,
        "icon_svg": icon_svg,
        "region": region,
        "period": (m.period or "").capitalize(),
    }


def plot_weekly_fueltech_summary(ws: WeeklySummary) -> io.BytesIO:
    """Render branded HTML summary and screenshot to PNG via headless Chrome."""
    from html2image import Html2Image

    display_records = [_prepare_record_display(r) for r in ws.records[:8]]
    top_milestones = sorted(ws.milestones, key=lambda m: m.significance, reverse=True)[:5]
    display_milestones = [_prepare_milestone_display(m) for m in top_milestones]

    week_range = f"{ws.week_start.strftime('%-d %b')} – {ws.week_end.strftime('%-d %b %Y')}"
    avg_price = sum(pr.avg_price for pr in ws.price_results) / len(ws.price_results) if ws.price_results else 0

    # Simple namespace for Mako template
    class _Rec:
        def __init__(self, d):
            self.__dict__.update(d)

    template_records = [_Rec(d) for d in display_records]
    template_milestones = [_Rec(d) for d in display_milestones]

    # Format WoW for stat cards
    te_wow_class, te_wow_str = _format_wow(ws.total_energy_wow)
    ap_wow_class, ap_wow_str = _format_wow(ws.avg_price_wow)

    # Renewable WoW is percentage points, show as +/- pp
    rp_wow_class, rp_wow_str = "wow-flat", ""
    if ws.renewable_wow is not None and abs(ws.renewable_wow) > 0.1:
        arrow = "&#9650;" if ws.renewable_wow > 0 else "&#9660;"
        rp_wow_class = "wow-up" if ws.renewable_wow > 0 else "wow-down"
        rp_wow_str = f"{arrow} {abs(ws.renewable_wow):.1f}pp"

    html = serve_template(
        "weekly_summary_image.html",
        logo_url=_get_logo_url(),
        week_number=ws.week_number,
        year=ws.week_start.strftime("%Y"),
        network=ws.network,
        week_range=week_range,
        records=template_records,
        milestones=template_milestones,
        total_energy=f"{ws.total_energy_gwh:,.0f}",
        renewable_pct=f"{ws.renewable_proportion:.1f}",
        avg_price=f"{avg_price:,.0f}",
        te_wow_class=te_wow_class,
        te_wow_str=te_wow_str,
        rp_wow_class=rp_wow_class,
        rp_wow_str=rp_wow_str,
        ap_wow_class=ap_wow_class,
        ap_wow_str=ap_wow_str,
    )

    # Screenshot with headless Chrome
    output_dir = "/tmp"
    output_file = f"weekly_summary_{ws.network}_{ws.week_number}.png"

    hti = Html2Image(output_path=output_dir, size=(IMAGE_WIDTH, IMAGE_HEIGHT))
    hti.screenshot(html_str=html, save_as=output_file)

    output_path = Path(output_dir) / output_file
    buf = io.BytesIO(output_path.read_bytes())
    output_path.unlink(missing_ok=True)

    return buf


# --- Main orchestrators ---


async def get_weekly_summary(network: NetworkSchema, week_start: datetime | None = None) -> WeeklySummary:
    """Build a complete WeeklySummary for a week.

    Args:
        network: Network to summarize (NEM or WEM)
        week_start: Monday of the week to summarize. None = most recent complete week.
    """
    week_start, week_end = _get_week_boundaries(week_start)
    prev_start = week_start - timedelta(days=7)
    prev_end = week_start - timedelta(seconds=1)

    # Fetch current and previous week fueltech data + price data + milestones
    current_ft = await _fetch_fueltech_energy(network, week_start, week_end)
    prev_ft = await _fetch_fueltech_energy(network, prev_start, prev_end)
    price_rows = await _fetch_price_by_region(network, week_start, week_end)
    milestones = await _fetch_milestones(network, week_start, week_end)

    ft_results = _build_fueltech_results(current_ft, prev_ft)
    price_results = _build_price_results(price_rows, network)

    # Compute previous week price for WoW on headline stats
    prev_price_rows = await _fetch_price_by_region(network, prev_start, prev_end)
    prev_price_results = _build_price_results(prev_price_rows, network)

    ws = WeeklySummary(
        week_start=week_start,
        week_end=week_end,
        week_number=week_start.isocalendar()[1],
        network=network.code,
        results=ft_results,
        price_results=price_results,
        milestones=milestones,
    )

    # Build previous week summary for headline WoW
    prev_ft_results = _build_fueltech_results(prev_ft)
    prev_total = sum(r.energy_gwh for r in prev_ft_results)
    prev_renew = sum(r.demand_proportion for r in prev_ft_results if r.renewable)
    prev_avg_price = sum(pr.avg_price for pr in prev_price_results) / len(prev_price_results) if prev_price_results else 0

    if prev_total > 0:
        ws.total_energy_wow = round(((ws.total_energy_gwh - prev_total) / prev_total) * 100, 1)
    if prev_renew > 0:
        ws.renewable_wow = round(ws.renewable_proportion - prev_renew, 1)  # absolute pp change
    curr_avg_price = sum(pr.avg_price for pr in price_results) / len(price_results) if price_results else 0
    if prev_avg_price > 0:
        ws.avg_price_wow = round(((curr_avg_price - prev_avg_price) / prev_avg_price) * 100, 1)

    return ws


async def run_weekly_summary(network: NetworkSchema, week_start: datetime | None = None) -> WeeklySummary:
    """Generate weekly summary, render image, and submit to social pipeline for approval."""
    from opennem.social.pipeline import create_social_post
    from opennem.social.schema import CreateSocialPostRequest, SocialPostType

    ws = await get_weekly_summary(network, week_start)

    # Generate chart image
    chart_buf = plot_weekly_fueltech_summary(ws)
    chart_buf.seek(0)
    chart_bytes = chart_buf.read()

    # Render social text
    social_text = serve_template("weekly_summary_social.md", ws=ws)

    if settings.dry_run:
        logger.info(f"[DRY RUN] Weekly summary for {network.code}:\n{social_text}")
        return ws

    # Submit to social pipeline — handles Slack approval + publishing
    await create_social_post(
        CreateSocialPostRequest(
            post_type=SocialPostType.WEEKLY_SUMMARY,
            text_content=social_text,
            source_type="weekly_summary",
            source_id=f"{network.code}_week_{ws.week_number}",
            network_id=network.code,
            metadata={"week_number": ws.week_number, "week_start": ws.week_start.isoformat()},
        ),
        image=chart_bytes,
    )

    logger.info(f"Submitted weekly summary for {network.code} to social pipeline")
    return ws


# --- CLI ---


if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="Weekly summary report")
    parser.add_argument("--auto-approve", action="store_true", help="Skip Slack approval, publish directly")
    parser.add_argument("--network", default="NEM", choices=["NEM", "WEM"], help="Network to summarize")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually post anywhere")
    args = parser.parse_args()

    network = NetworkNEM if args.network == "NEM" else NetworkWEM

    if args.dry_run:
        settings.dry_run = True

    asyncio.run(run_weekly_summary(network=network))
