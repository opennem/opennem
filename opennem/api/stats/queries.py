"""
Queries for network data

@TODO use sqlalchemy text() compiled queries
"""

from sqlalchemy import text
from sqlalchemy.sql.elements import TextClause

from opennem.controllers.output.schema import OpennemExportSeries


def power_facility_query(
    time_series: OpennemExportSeries,
    facility_code: str,
) -> TextClause:
    __query = """
        SELECT
            time_bucket_gapfill('{trunc}', fs.interval) as interval_bucket,
            fs.facility_code,
            fs.unit_code,
            round(sum(fs.generated)::numeric, 2) as generated
        FROM at_facility_intervals fs
        WHERE
            fs.facility_code = '{facility_code}' and
            fs.interval >= '{date_min}' and fs.interval <= '{date_max}'
        GROUP BY 1, 2, 3
        ORDER BY interval_bucket DESC, 2, 3;

    """

    date_range = time_series.get_range()

    query = __query.format(
        facility_code=facility_code,
        trunc=time_series.interval.interval_sql,
        date_max=date_range.end,
        date_min=date_range.start,
    )

    return text(query)
