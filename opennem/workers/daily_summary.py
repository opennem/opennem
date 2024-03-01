"""
Daily summary - fueltechs as proportion of demand
and other stats per network
"""
import io
import logging
from datetime import datetime, timedelta
from operator import attrgetter

import matplotlib.pyplot as plt

from opennem import settings
from opennem.clients.cfimage import save_image_to_cloudflare
from opennem.clients.slack import slack_message
from opennem.core.templates import serve_template
from opennem.db import get_database_engine
from opennem.queries.summary import get_daily_fueltech_summary_query
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.utils.dates import get_last_complete_day_for_network  # noqa: F401

logger = logging.getLogger("opennem.controllers.summary.daily")


class DailySummaryResult(BaseConfig):
    trading_day: datetime
    network: str
    fueltech_id: str
    fueltech_label: str
    fueltech_color: str
    renewable: bool
    energy: float
    generated_total: float
    demand_total: float
    demand_proportion: float


class DailySummary(BaseConfig):
    trading_day: datetime
    network: str
    chart_url: str | None = None
    environment: str | None = None

    results: list[DailySummaryResult]

    @property
    def renewable_proportion(self) -> float:
        return sum(i.demand_proportion for i in filter(lambda x: x.renewable is True, self.results))

    @property
    def total_energy(self) -> float:
        return sum(i.energy for i in self.results)

    @property
    def records(self) -> list[DailySummaryResult]:
        return sorted(self.results, key=attrgetter("energy"), reverse=True)

    def records_chart(self, cutoff: float = 1.0, other_color: str = "brown") -> list[DailySummaryResult]:
        records = self.records

        records_unfiltered = list(filter(lambda x: x.demand_proportion > cutoff, records))
        records_filtered = list(filter(lambda x: x.demand_proportion <= cutoff, records))

        other = records[0].copy()
        other.fueltech_label = "Other"
        other.energy = 0.0
        other.demand_proportion = 0.0
        other.fueltech_color = other_color

        for r in records_filtered:
            other.energy = r.energy
            other.demand_proportion += r.demand_proportion

        records_unfiltered.append(other)

        return records_unfiltered


def get_daily_fueltech_summary(network: NetworkSchema) -> DailySummary:
    engine = get_database_engine()
    _result = []
    day = get_last_complete_day_for_network(network) - timedelta(days=1)

    query = get_daily_fueltech_summary_query(day=day, network=network)

    with engine.connect() as c:
        logger.debug(query)
        _result = list(c.execute(query))

    records = [
        DailySummaryResult(
            trading_day=i[0],
            network=network.code,
            fueltech_id=i[1],
            fueltech_label=i[2],
            fueltech_color=i[3],
            renewable=i[4],
            energy=i[5],
            generated_total=i[6],
            demand_total=i[7],
            demand_proportion=i[8],
        )
        for i in _result
    ]

    ds = DailySummary(trading_day=records[0].trading_day, network=records[0].network, results=records)

    return ds


def plot_daily_fueltech_summary(daily_summary: DailySummary) -> io.BytesIO:
    """Returns a chart of the daily fueltech summary"""
    chart_records = daily_summary.records_chart()

    # font and format settings
    font = {
        "family": '"IBM Plex Serif",Georgia,"Times New Roman",Times,serif',
        "weight": "400",
        "color": "black",
        "size": 14,
    }
    data = [i.demand_proportion for i in chart_records]
    labels = [i.fueltech_label for i in chart_records]
    colors = [i.fueltech_color for i in chart_records]

    # create pie chart
    _, ax = plt.subplots()

    ax.pie(data, labels=labels, colors=colors, autopct="%.0f%%", textprops={**font, **{"size": 8}})

    day_formatted = daily_summary.trading_day.strftime("%a %-d %b %Y")
    env_string = " (DEV)" if not settings.is_prod else ""

    ax.set_title(f"OpenNEM Daily Summary for {daily_summary.network.upper()} for {day_formatted} {env_string}", fontdict=font)
    # ax.legend()

    # save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)

    return buf


def render_daily_fueltech_summary_tweet_text(daily_summary: DailySummary) -> str:
    """Renders daily fueltech summary text"""
    _render = serve_template("tweet_daily_summary.md", ds=daily_summary)

    logging.debug(_render)

    return _render


def run_daily_fueltech_summary(network: NetworkSchema) -> None:
    """Produces daily fueltech summary slack message"""

    if not settings.send_daily_fueltech_summary:
        return None

    ds = get_daily_fueltech_summary(network=network)

    summary_plot = plot_daily_fueltech_summary(daily_summary=ds)

    summary_text = render_daily_fueltech_summary_tweet_text(daily_summary=ds)

    cfimage = save_image_to_cloudflare(summary_plot)

    if settings.dry_run:
        return None

    if slack_message(message=summary_text, image_url=cfimage.url, image_alt="Daily Summary"):
        logger.info("Sent slack message")

    else:
        logger.error("Could not send slack message for daily fueltech summary")


if __name__ == "__main__":
    run_daily_fueltech_summary(network=NetworkNEM)
    # plot_daily_fueltech_summary(network=NetworkNEM)
