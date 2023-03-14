"""
OpenNEM Nasty Hacks

@TODO Eventually factor all of this out
"""
import logging

from opennem.api.stats.schema import OpennemDataSet

logger = logging.getLogger("opennem.hacks")


def pad_stat_set(stat_set: OpennemDataSet) -> OpennemDataSet:
    """Frontend requires padded outputs in export sets so we need to find the
    date range and pad out each output to match on both ends"""

    if len(stat_set.data) < 1:
        return stat_set

    start_dates = [i.history.start for i in stat_set.data if i.id.endswith("energy")]
    end_dates = [i.history.last for i in stat_set.data if i.id.endswith("energy")]

    if len(start_dates) < 1:
        return stat_set

    min_date = min(start_dates)
    max_date = max(end_dates)

    length_should_be = None
    perfect_data_set = None

    # Find required length
    perfect_data_sets = list(
        filter(
            lambda x: x.id.endswith("energy") and x.history.start == min_date and x.history.last == max_date,  # type: ignore
            stat_set.data,
        )
    )

    if len(perfect_data_sets) < 1:
        logger.error("No perfect data set!")
        return stat_set

    perfect_data_set = perfect_data_sets.pop()
    length_should_be = len(perfect_data_set.history.data)

    for data_set in stat_set.data:
        # prepad the min-date
        if data_set.history.start != min_date:
            required_padding = length_should_be - len(data_set.history.data)

            if required_padding > 0:
                data_set.history.data = [None] * required_padding + data_set.history.data

            if required_padding < 0:
                required_padding_pos = abs(required_padding)
                data_set.history.data = data_set.history.data[required_padding_pos:]

            data_set.history.start = min_date

    return stat_set
