import logging
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from textwrap import dedent
from typing import Any

from datetime_truncate import truncate as date_trunc
from sqlalchemy import text as sql

from opennem import settings
from opennem.api.time import human_to_interval
from opennem.core.feature_flags import get_list_of_enabled_features
from opennem.core.normalizers import cast_float_or_none
from opennem.db import db_connect
from opennem.queries.utils import duid_to_case
from opennem.schema.network import NetworkAEMORooftop, NetworkAEMORooftopBackfill, NetworkAPVI, NetworkSchema
from opennem.schema.time import TimeInterval
from opennem.schema.units import UnitDefinition
from opennem.utils.cache import cache_scada_result
from opennem.utils.dates import (
    chop_timezone,
    get_last_completed_interval_for_network,
    get_today_for_network,
)
from opennem.utils.numbers import cast_trailing_nulls
from opennem.utils.timezone import is_aware, make_aware
from opennem.utils.version import get_version

from .schema import DataQueryResult, OpennemData, OpennemDataHistory, OpennemDataSet, ScadaDateRange

logger = logging.getLogger(__name__)


def stats_factory(
    stats: list[DataQueryResult],
    units: UnitDefinition,
    interval: TimeInterval,
    network: NetworkSchema | None = None,
    timezone: timezone | str | None = None,
    code: str | None = None,
    region: str | None = None,
    include_group_code: bool = False,
    fueltech_group: bool | None = False,
    fueltech_code: str | None = None,
    group_field: str | None = None,
    data_id: str | None = None,
    localize: bool | None = True,
    cast_nulls: bool | None = True,
    include_code: bool = True,
    exclude_nulls: bool = True,
) -> OpennemDataSet:
    """
    Takes a list of data query results and returns OpennemDataSets

    @TODO optional groupby field
    @TODO multiple groupings / slight refactor

    """

    if network:
        timezone = network.get_timezone()

    group_codes = list({i.group_by for i in stats if i.group_by})

    stats_grouped = []

    for group_code in group_codes:
        data_grouped: dict[datetime, Any] = {}

        for stat in stats:
            if stat.group_by != group_code:
                continue

            if stat.interval not in data_grouped:
                data_grouped[stat.interval] = None

            # if stat.result:
            data_grouped[stat.interval] = stat.result

        data_sorted = OrderedDict(sorted(data_grouped.items()))

        data_value = list(data_sorted.values())

        # Skip null series
        if exclude_nulls and not [i for i in data_value if i]:
            continue

        # @TODO possible bring this back
        # Skip zero series
        # if sum([i for i in data_value if i]) == 0:
        # continue

        # Cast trailing nulls
        if (not units.name.startswith("temperature") or (units.cast_nulls is True)) and (cast_nulls is True):
            data_value = cast_trailing_nulls(data_value)

        data_trimmed = dict(zip(data_sorted.keys(), data_value, strict=True))

        # data_trimmed = trim_nulls(data_trimmed)

        # Find start/end dates
        dates = list(data_trimmed.keys())

        if not dates:
            return None

        start = min(dates)
        end = max(dates)

        # should probably make sure these are the same TZ
        if localize:
            if timezone and not is_aware(start):
                start = make_aware(start, timezone)

            if timezone and not is_aware(end):
                end = make_aware(end, timezone)

        if timezone and localize and network and network.offset:
            if tz := network.get_timezone():
                start = start.astimezone(tz)
                end = end.astimezone(tz)

        # Everything needs a timezone even flat dates
        if network and timezone and not is_aware(start):
            start = start.replace(tzinfo=network.get_fixed_offset())

        if network and timezone and not is_aware(end):
            end = end.replace(tzinfo=network.get_fixed_offset())

        # @TODO compose this and make it generic - some intervals
        # get truncated.
        # trunc the date for days and months
        if interval == human_to_interval("1d"):
            start = date_trunc(start, truncate_to="day")
            end = date_trunc(end, truncate_to="day")

        if interval == human_to_interval("1M"):
            start = date_trunc(start, truncate_to="month")
            end = date_trunc(end, truncate_to="month")

        # free
        dates = []

        history = OpennemDataHistory(
            start=start,
            last=end,
            interval=interval.interval_human,
            data=[cast_float_or_none(i) for i in data_trimmed.values()],
        )

        data = OpennemData(
            data_type=units.unit_type,
            units=units.unit,
            # interval=interval,
            # period=period,
            history=history,
        )

        if include_code:
            data.code = group_code

        if network:
            data.network = network.code.lower()

        # *sigh* - not the most flexible model
        # @TODO fix this schema and make it more flexible
        if fueltech_group:
            data.fuel_tech = group_code

            data_comps = [
                # @NOTE disable for now since FE doesn't
                # support it
                network.country if network else None,
                network.code.lower() if network else None,
                region.lower() if region and region.lower() != network.code.lower() else None,
                "fuel_tech",
                group_code,
                units.unit_type,
            ]

            data.id = ".".join(i for i in data_comps if i)
            # @TODO make this an alias
            data.type = units.unit_type

        # override fueltech code
        if fueltech_code:
            data.fuel_tech = fueltech_code

        if group_field:
            group_fields = []

            # setattr(data, group_field, group_code)

            if network:
                group_fields.extend((network.country.lower(), network.code.lower()))
            if region and region.lower() != network.code.lower():
                group_fields.append(region.lower())

            if units.name_alias:
                group_fields.append(units.name_alias)
            elif units.unit_type:
                group_fields.append(units.unit_type)

            if group_code and include_group_code:
                group_fields.extend((group_code, group_field))
            data.id = ".".join([f for f in group_fields if f])
            data.type = units.unit_type

        if data_id:
            data.id = data_id

        if not data.id:
            _id_list = []

            # @NOTE disable for now since FE doesn't
            # support it
            # network.country if network else None,

            if network:
                _id_list.extend((network.country.lower(), network.code.lower()))
            if region and (region.lower() != network.code.lower()):
                _id_list.append(region.lower())

            if group_code and include_group_code:
                _id_list.append(group_code.lower())

            if units:
                if units.name_alias:
                    _id_list.append(units.name_alias)
                elif units.name:
                    _id_list.append(units.name)

            data.id = ".".join([f for f in _id_list if f])
            data.type = units.unit_type

        if region:
            data.region = region

        stats_grouped.append(data)

    dt_now = datetime.now()

    if network:
        dt_now = dt_now.astimezone(network.get_timezone())

    # @NOTE this should probably be
    # country.network.region
    if not code:
        if network:
            code = network.code

        if region:
            code = region

    stat_set = OpennemDataSet(
        type=units.unit_type,
        data=stats_grouped,
        created_at=dt_now,
        feature_flags=get_list_of_enabled_features(),
        version=get_version(),
        messages=settings.api_messages,
    )

    if include_code:
        stat_set.code = code

    if network:
        stat_set.network = network.code

    if region:
        stat_set.region = region

    return stat_set


def networks_to_in(networks: list[NetworkSchema]) -> str:
    codes = [f"'{n.code}'" for n in networks]

    return ", ".join(codes)


def get_scada_range_optimized(network: NetworkSchema) -> ScadaDateRange:
    """Optimized version of get_scada_range"""
    if not network.data_first_seen:
        raise Exception(f"No data start for {network.code}. Required for optimized scada range")

    data_start = chop_timezone(network.data_first_seen)
    data_end = get_last_completed_interval_for_network(network, tz_aware=False).replace(tzinfo=None)

    # find an earlier subnetwork data start
    if network.subnetworks:
        for subnetwork in network.subnetworks:
            if subnetwork.data_first_seen and chop_timezone(subnetwork.data_first_seen) < data_start:
                data_start = subnetwork.data_first_seen

    if not data_start:
        raise Exception(f"No data start for {network.code}")

    return ScadaDateRange(start=data_start, end=data_end, network=network)


@cache_scada_result
async def get_scada_range(
    network: NetworkSchema,
    networks: list[NetworkSchema] | None = None,
    network_region: str | None = None,
    facilities: list[str] | None = None,
    energy: bool = False,
) -> ScadaDateRange:
    """Get the start and end dates for a network query. This is more efficient
    than providing or querying the range at query time
    """
    engine = db_connect()

    __query = """
    select
        min(u.data_first_seen),
        max(fs.interval)
    from facility_scada fs
    join units u on fs.facility_code = u.code
    join facilities f on f.id = u.station_id
    where
        fs.interval >= '{date_min}' and
        fs.is_forecast is FALSE and
        {facility_query}
        {network_query}
        {network_region_query}
        u.fueltech_id not in ({excluded_fueltechs})
        and u.interconnector is FALSE
        and fs.{field} is not null;
    """

    network_query = ""
    field_name = "generated"

    # List of fueltechs to exclude from query
    excluded_fueltechs: list[str] = ["imports", "exports"]

    # If we don't have a rooftop network we exclude solar_rooftop from the query
    # @TODO define the rooftop networks in the schema
    exclude_rooftop = True

    if network in [NetworkAPVI, NetworkAEMORooftop, NetworkAEMORooftopBackfill]:
        exclude_rooftop = False

    # Iterate through the list of networks provided
    for net_exclude in [NetworkAPVI, NetworkAEMORooftop, NetworkAEMORooftopBackfill]:
        if networks and net_exclude in networks:
            exclude_rooftop = False

    if exclude_rooftop:
        excluded_fueltechs.append("solar_rooftop")

    # Only check energy values
    if energy is True:
        field_name = "energy"

    # Only look back 7 days because the query is more optimized
    date_min = get_today_for_network(network=network) - timedelta(days=7)

    if network:
        network_query = f"f.network_id = '{network.code}' and"

    if networks:
        net_case = networks_to_in(networks)
        network_query = f"f.network_id IN ({net_case}) and "

    network_region_query = ""

    if network_region:
        network_region_query = f"f.network_region = '{network_region}' and"

    facility_query = ""

    if facilities:
        fac_case = duid_to_case(facilities)
        facility_query = f"u.code IN ({fac_case}) and "

    scada_range_query = dedent(
        __query.format(
            field=field_name,
            date_min=date_min,
            facility_query=facility_query,
            network_query=network_query,
            network_region_query=network_region_query,
            excluded_fueltechs=", ".join([f"'{i}'" for i in list(excluded_fueltechs)]),
        )
    )

    async with engine.begin() as conn:
        logger.debug(scada_range_query)
        res = await conn.execute(sql(scada_range_query))
        scada_range_result = res.fetchone()

        if not scada_range_result:
            raise Exception(f"No scada range results for {network.code}")

        scada_min = scada_range_result[0]
        scada_max = scada_range_result[1]

    if not scada_min or not scada_max:
        raise Exception(f"No scada range results (min or max dates) for {network.code}")

    # set network timezone since that is what we're querying
    if network and network.get_fixed_offset():
        scada_min = scada_min.replace(tzinfo=network.get_fixed_offset())
        scada_max = scada_max.replace(tzinfo=network.get_fixed_offset())

    scada_range = ScadaDateRange(start=scada_min, end=scada_max, network=network)

    return scada_range


if __name__ == "__main__":
    import asyncio

    from opennem.schema.network import NetworkNEM

    res = asyncio.run(get_scada_range(network=NetworkNEM))
    print(res)
