from textwrap import dedent
from typing import Optional

from .schema import ViewDefinition


def create_continuous_aggregation_query(viewdef: ViewDefinition) -> Optional[str]:
    """Get an update query for a continuous aggregation policy"""

    if not viewdef.aggregation_policy:
        return None

    __query = """
    SELECT add_continuous_aggregate_policy(
        '{view_name}',
        start_offset => {start_offset},
        end_offset => {end_offset},
        schedule_interval => {schedule_interval}
    );

    """

    query = __query.format(
        view_name=viewdef.name,
        start_offset=viewdef.aggregation_policy.start_offset,
        end_offset=viewdef.aggregation_policy.end_offset,
        schedule_interval=viewdef.aggregation_policy.schedule_interval,
    )

    return dedent(query)


def remove_continuous_aggregation_query(viewdef: ViewDefinition) -> Optional[str]:
    """ Remove a continuous aggregation policy """

    if not viewdef.aggregation_policy:
        return None

    __query = "SELECT remove_continuous_aggregate_policy('{view_name}');"

    query = __query.format(view_name=viewdef.name)

    return dedent(query)
