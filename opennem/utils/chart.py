""" Utility to generate simple charts """

import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

import matplotlib.pyplot as plt

ValidNumber = float | int | Decimal


logger = logging.getLogger("opennem.utils.chart")


@dataclass
class PlotValues:
    interval: datetime
    value: ValidNumber


@dataclass
class PlotIntegerValues:
    interval: int
    value: ValidNumber


@dataclass
class PlotSeries:
    values: list[PlotValues | PlotIntegerValues]
    label: str | None
    color: str = field(default="blue")

    def x(self) -> list[datetime]:
        return [i.interval for i in self.values]

    def y(self) -> list[ValidNumber]:
        return [i.value for i in self.values]


@dataclass
class Plot:
    series: list[PlotSeries]
    destination_file: str | None = field(default=None)
    title: str | None = field(default=None)
    legend: bool = field(default=True)


def chart_line(plot: Plot, show: bool = False, destination_file: str | None = None) -> None:
    """Creates a line chart from the series and returns"""
    _, ax = plt.subplots()

    if plot.title:
        ax.set_title(plot.title)

    for s in plot.series:
        ax.plot(s.x(), s.y(), s.color, label=s.label)

        ax.axhline(0, color="grey", linewidth=0.8)
        ax.set_ylabel("value")

    if plot.legend:
        ax.legend()

    if show:
        plt.show()

    if plot.destination_file:
        plt.savefig(plot.destination_file)
        logger.info(f"Saved figure to {plot.destination_file}")

    if destination_file:
        plt.savefig(destination_file)
        logger.info(f"Saved figure to {destination_file}")

    return plot


if __name__ == "__main__":
    p = Plot(
        series=[
            PlotSeries(values=[PlotValues(interval=datetime.now(), value=1)], label="test"),
            PlotSeries(values=[PlotValues(interval=datetime.now(), value=3)], label="test 2"),
        ],
        title="test",
        legend=True,
    )
    chart_line(p, show=True)
