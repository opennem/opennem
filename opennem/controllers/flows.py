import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Sequence, Tuple, Union

from dateutil.relativedelta import relativedelta

from opennem.api.export.map import StatType
from opennem.api.stats.controllers import stats_factory
from opennem.api.stats.schema import DataQueryResult, OpennemDataSet, RegionFlowEmissionsResult
from opennem.api.time import human_to_interval, human_to_period
from opennem.core.compat.loader import get_dataset
from opennem.core.compat.schema import OpennemDataSetV2
from opennem.core.flows import net_flows_emissions
from opennem.core.units import get_unit
from opennem.db import get_database_engine
from opennem.schema.dates import TimeSeries
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.schema.stats import StatTypes
from opennem.schema.time import TimePeriod

logger = logging.getLogger("opennem.controllers.flows")
logger.setLevel(logging.DEBUG)


class FlowType(Enum):
    imports = "imports"
    exports = "exports"


td_month = relativedelta(months=1)
td_day = relativedelta(days=1)


def parse_ds_to_generated(
    ds: OpennemDataSetV2, flow_type: FlowType, stat_type: StatType
) -> Sequence[Tuple[datetime, Union[float, int]]]:
    generated_list = []

    search_id_match = "{}.{}".format(flow_type.value, stat_type.value)

    dsid = ds.search_id(search_id_match)

    if not dsid:
        logger.error("No return for ds for {}".format(search_id_match))
        return []

    dt_current = dsid.history.start
    dt_delta = td_month

    if dsid.history.interval == "1d":
        dt_delta = td_day

    for v in dsid.history.data:
        generated_list.append((dt_current, v))
        dt_current += dt_delta

        if dt_current == dsid.history.last:
            generated_list.append((dt_current, v))
            break

    return generated_list


def interconnector_region_daily(
    time_series: TimeSeries,
    network_region_code: str,
) -> OpennemDataSet:
    bucket_size = "monthly"

    if time_series.year:
        bucket_size = "daily"

    ds = get_dataset(StatType.energy, network_region_code, bucket_size, time_series.year)

    return_ds = OpennemDataSet()

    for ft in [FlowType.imports, FlowType.exports]:
        for st in [StatType.energy, StatType.marketvalue, StatType.emissions]:
            row = parse_ds_to_generated(ds, flow_type=ft, stat_type=st)

            if len(row) < 1 or not row:
                logger.error("No flow parse return for {} {}".format(ft, st))
                continue

            data_query_results = [
                DataQueryResult(interval=i[0], group_by=ft.value, result=i[1]) for i in row
            ]

            units = None

            if st == StatType.energy:
                units = get_unit("energy_giga")
            elif st == StatType.marketvalue:
                units = get_unit("market_value")
            elif st == StatType.emissions:
                units = get_unit("emissions")

            if not units:
                raise Exception("Invalid units")

            result = stats_factory(
                data_query_results,
                network=time_series.network,
                period=time_series.period,
                interval=time_series.interval,
                units=units,
                region=network_region_code,
                fueltech_group=True,
                # localize=False,
            )

            if not result:
                logger.error("No interconnector energy result")
                # return result
                continue

            logger.info(
                "Adding {} {} with {} values".format(units.name, result.ids, len(result.data))
            )
            return_ds.append_set(result)

    return return_ds
