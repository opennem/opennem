import logging
from operator import attrgetter
from pathlib import Path

from opennem.db import get_database_engine
from opennem.db.views.queries import (
    get_all_views_query,
    get_query_drop_view,
    get_view_unique_index_query,
)

from .continuous_aggregates import (
    create_continuous_aggregation_query,
    remove_continuous_aggregation_query,
)
from .schema import ContinuousAggregationPolicy, ViewDefinition

logger = logging.getLogger("opennem.db.views")

VIEW_PATH = Path(__file__).parent.parent / "fixtures" / "views"


AggregationPolicy30Minutes = ContinuousAggregationPolicy(
    interval="30 minutes", start_interval="2 hours"
)

AggregationPolicy6Hours = ContinuousAggregationPolicy(
    interval="6 hours", start_interval="12 hours", end_interval="2 hours"
)

_VIEW_MAP = [
    ViewDefinition(
        priority=1,
        name="mv_facility_energy_hour",
        materialized=True,
        filepath="mv_facility_energy_hour.sql",
        aggregation_policy=AggregationPolicy30Minutes,
    ),
    ViewDefinition(
        priority=2,
        name="mv_facility_all",
        materialized=True,
        filepath="mv_facility_all.sql",
        aggregation_policy=AggregationPolicy6Hours,
        primary_key=["trading_interval", "network_id", "code"],
    ),
    ViewDefinition(
        priority=3,
        name="mv_region_emissions",
        materialized=True,
        filepath="mv_region_emissions.sql",
        aggregation_policy=AggregationPolicy6Hours,
        primary_key=["trading_interval", "network_id", "network_region"],
    ),
    ViewDefinition(
        priority=3,
        name="mv_interchange_energy_nem_region",
        materialized=True,
        filepath="mv_interchange_energy_nem_region.sql",
        aggregation_policy=AggregationPolicy30Minutes,
    ),
    ViewDefinition(
        priority=10,
        name="vw_region_flow_emissions",
        materialized=False,
        filepath="vw_region_flow_emissions.sql",
    ),
]


def get_view_content(viewdef: ViewDefinition) -> str:
    if not VIEW_PATH.is_dir():
        raise Exception("View directory: {} does not exist".format(VIEW_PATH))

    view_full_path = VIEW_PATH / Path(viewdef.filepath)

    if not view_full_path.is_file():
        raise Exception("View {} not found in view path:".format(view_full_path))

    view_content: str = ""

    with view_full_path.open() as fh:
        view_content = fh.read()

    return view_content


POSTGIS_VIEWS = ["geography_columns", "geometry_columns", "raster_columns", "raster_overviews"]


def purge_views() -> None:
    """Remove views that aren't in the view table"""

    engine = get_database_engine()

    all_views_query = get_all_views_query()
    all_views = []

    with engine.connect() as c:
        result = list(c.execute(all_views_query))

    # Dont drop postgis or mapped views
    all_views = [i[0] for i in result if i[0] not in POSTGIS_VIEWS + [i.name for i in _VIEW_MAP]]

    for view_name in all_views:

        with engine.connect() as c:
            c.execution_options(isolation_level="AUTOCOMMIT")

            query = "drop materialized view if exists {} cascade;".format(view_name)

            logger.info("Dropping view {}".format(view_name))
            logger.debug(query)

            try:
                c.execute(query)
            except Exception as e:
                logger.error("Error dropping view: {}".format(e))


def init_database_views() -> None:
    """ Initialize all the database view """

    engine = get_database_engine()

    views_sorted_by_priority = list(sorted(_VIEW_MAP, key=attrgetter("priority")))

    for view in views_sorted_by_priority:
        logger.info("Initializing view {}".format(view.name))

        with engine.connect() as c:
            c.execution_options(isolation_level="AUTOCOMMIT")

            # drop
            drop_query = get_query_drop_view(view)

            logger.debug(drop_query)

            try:
                c.execute(drop_query)
            except Exception as e:
                logger.warn("Could not drop view {}".format(view.name))

            # create
            create_query = get_view_content(view)
            logger.debug(create_query)

            c.execute(create_query)

            # index
            index_create_query = get_view_unique_index_query(view)

            if index_create_query:
                logger.debug(index_create_query)

                try:
                    c.execute(index_create_query)
                except Exception as e:
                    logger.error("Error creating index: {}".format(e))

    return None


def init_aggregation_policies() -> None:
    """ Initializes the continuous aggregation policies """

    # @TODO check what exists with query

    engine = get_database_engine()

    for view in _VIEW_MAP:
        if not view.aggregation_policy:
            continue

        with engine.connect() as c:

            drop_query = remove_continuous_aggregation_query(view)

            try:
                logger.debug(drop_query)
                c.execute(drop_query)
            except Exception as e:
                logger.warn("Could not drop continuous aggregation query: {}".format(e))
                pass

            create_query = create_continuous_aggregation_query(view)

            logger.debug(create_query)

            try:
                c.execute(create_query)
            except Exception as e:
                logger.warn("Could not create continuous aggregation query: {}".format(e))
