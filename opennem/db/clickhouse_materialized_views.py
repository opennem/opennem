"""
Clickhouse materialized view management utilities.

This module provides generic functions for creating, refreshing, and backfilling
materialized views in ClickHouse.
"""

import logging
from datetime import datetime, timedelta

from opennem.db.clickhouse import get_clickhouse_client, table_exists
from opennem.db.clickhouse_views import (
    CLICKHOUSE_MATERIALIZED_VIEWS,
    MaterializedView,
)

logger = logging.getLogger("opennem.db.clickhouse_materialized_views")


def ensure_materialized_views_exist(views: list[MaterializedView] | None = None) -> None:
    """
    Ensure that materialized views exist in ClickHouse.
    Creates them if they don't exist.

    Args:
        views: List of MaterializedView objects to ensure exist.
               If None, ensures all views in CLICKHOUSE_MATERIALIZED_VIEWS exist.
    """
    client = get_clickhouse_client()

    if views is None:
        views = list(CLICKHOUSE_MATERIALIZED_VIEWS.values())

    for view in views:
        if not table_exists(client, view.name):
            client.execute(view.schema)
            logger.info(f"Created materialized view: {view.name}")
        else:
            logger.debug(f"Materialized view already exists: {view.name}")


def refresh_materialized_views(views: list[MaterializedView | str] | None = None, drop_existing: bool = False) -> None:
    """
    Refresh materialized views by optionally dropping and recreating them.

    Args:
        views: List of MaterializedView objects or view names to refresh.
               If None, refreshes all views in CLICKHOUSE_MATERIALIZED_VIEWS.
        drop_existing: If True, drops existing views before recreating them.
    """
    client = get_clickhouse_client()

    # Determine which views to process
    views_to_process = []
    if views is None:
        views_to_process = list(CLICKHOUSE_MATERIALIZED_VIEWS.values())
    else:
        for view in views:
            if isinstance(view, str):
                if view in CLICKHOUSE_MATERIALIZED_VIEWS:
                    views_to_process.append(CLICKHOUSE_MATERIALIZED_VIEWS[view])
                else:
                    logger.warning(f"View {view} not found in CLICKHOUSE_MATERIALIZED_VIEWS")
            elif isinstance(view, MaterializedView):
                views_to_process.append(view)

    # Process each view
    for view in views_to_process:
        if drop_existing:
            logger.info(f"Dropping existing view: {view.name}")
            client.execute(f"DROP TABLE IF EXISTS {view.name}")

        if not table_exists(client, view.name) or drop_existing:
            client.execute(view.schema)
            logger.info(f"Created materialized view: {view.name}")


def backfill_materialized_view(
    view: MaterializedView, start_date: datetime | None = None, end_date: datetime | None = None, chunk_size_days: int = 30
) -> int:
    """
    Backfill a single materialized view for a given date range.

    Args:
        view: MaterializedView definition
        start_date: Start date for backfill. If None, uses min date from source table.
        end_date: End date for backfill. If None, uses max date from source table.
        chunk_size_days: Number of days to process at once for chunked backfills.

    Returns:
        int: Total number of records processed
    """
    client = get_clickhouse_client(timeout=300)

    # Normalize dates to capture full days (start at 00:00:00, end at 23:59:59)
    # This prevents partial day captures when the job runs mid-day
    if start_date is not None:
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    if end_date is not None:
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=0)

    # Determine source table from the view schema
    source_table = _get_source_table_from_view(view)

    # Get date range if not provided
    if start_date is None or end_date is None:
        try:
            result = client.execute(f"""
                SELECT
                    min({view.timestamp_column}) as min_date,
                    max({view.timestamp_column}) as max_date
                FROM {source_table}
            """)

            if result and result[0][0] is not None:
                if start_date is None:
                    start_date = result[0][0]
                if end_date is None:
                    end_date = result[0][1]
            else:
                logger.warning(f"No data found in source table {source_table}")
                return 0
        except Exception as e:
            logger.error(f"Failed to get date range for {view.name} from {source_table}: {e}")
            logger.error(f"Attempted to use timestamp column '{view.timestamp_column}' which may not exist in {source_table}")
            # Try to provide helpful debugging information
            try:
                # Get the actual columns from the source table
                result = client.execute(f"DESCRIBE TABLE {source_table}")
                columns = [row[0] for row in result]
                logger.info(f"Available columns in {source_table}: {columns}")
            except Exception:
                pass
            return 0

    total_records = 0

    # Check if the backfill query has parameters
    if "%(start)s" in view.backfill_query and "%(end)s" in view.backfill_query:
        # Process in chunks
        current_date = start_date
        while current_date <= end_date:
            chunk_end = min(current_date + timedelta(days=chunk_size_days), end_date)

            logger.info(f"Backfilling {view.name} from {current_date} to {chunk_end}")

            try:
                # DELETE existing data for this date range to prevent double-counting
                # This is required for SummingMergeTree which adds values during merges
                delete_query = f"""
                    ALTER TABLE {view.name} DELETE
                    WHERE {view.timestamp_column} >= %(start)s
                    AND {view.timestamp_column} <= %(end)s
                """
                client.execute(delete_query, {"start": current_date.date(), "end": chunk_end.date()})
                logger.debug(f"Deleted existing data from {view.name} for {current_date.date()} to {chunk_end.date()}")

                # INSERT new data
                client.execute(
                    view.backfill_query,
                    {"start": current_date, "end": chunk_end},
                )

                # Verify data was inserted — silent failures here cause data gaps
                verify = client.execute(
                    (
                        f"SELECT count() FROM {view.name} WHERE {view.timestamp_column} >= %(start)s "
                        f"AND {view.timestamp_column} <= %(end)s"
                    ),
                    {"start": current_date.date(), "end": chunk_end.date()},
                )
                row_count = verify[0][0] if verify else 0
                if row_count == 0:
                    logger.error(
                        f"CRITICAL: Backfill {view.name} inserted 0 rows "
                        f"for {current_date.date()} to {chunk_end.date()} — data gap!"
                    )
                else:
                    logger.info(f"Backfill {view.name}: {row_count} rows for {current_date.date()} to {chunk_end.date()}")
            except Exception as e:
                logger.error(f"Failed to backfill {view.name} for period {current_date} to {chunk_end}: {e}")
                # Continue with next chunk instead of failing completely
                logger.warning("Skipping chunk and continuing with next period")

            current_date = chunk_end + timedelta(seconds=1)
    else:
        # Execute backfill query without parameters
        logger.info(f"Backfilling {view.name} (full table)")
        try:
            client.execute(view.backfill_query)
        except Exception as e:
            logger.error(f"Failed to backfill {view.name} (full table): {e}")
            return 0

    # Return count of records in the view
    result = client.execute(f"SELECT count() FROM {view.name}")
    total_records = result[0][0] if result else 0

    logger.info(f"Backfill complete for {view.name}. Total records: {total_records}")
    return total_records


def backfill_materialized_views(
    views: list[MaterializedView | str] | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    refresh_views: bool = False,
) -> dict[str, int]:
    """
    Backfill multiple materialized views from their source tables.

    Args:
        views: List of MaterializedView objects or view names to backfill.
               If None, backfills all views in CLICKHOUSE_MATERIALIZED_VIEWS.
        start_date: Start date for backfill. If None, uses min date from source.
        end_date: End date for backfill. If None, uses max date from source.
        refresh_views: If True, drops and recreates views before backfilling.

    Returns:
        dict: Mapping of view names to record counts
    """
    # Determine which views to process
    views_to_process = []
    if views is None:
        views_to_process = list(CLICKHOUSE_MATERIALIZED_VIEWS.values())
    else:
        for view in views:
            if isinstance(view, str):
                if view in CLICKHOUSE_MATERIALIZED_VIEWS:
                    views_to_process.append(CLICKHOUSE_MATERIALIZED_VIEWS[view])
                else:
                    raise ValueError(f"View {view} not found in CLICKHOUSE_MATERIALIZED_VIEWS")
            elif isinstance(view, MaterializedView):
                views_to_process.append(view)

    # Refresh views if requested
    if refresh_views:
        refresh_materialized_views(views_to_process, drop_existing=True)
    else:
        ensure_materialized_views_exist(views_to_process)

    # Backfill each view
    results = {}
    for view in views_to_process:
        try:
            record_count = backfill_materialized_view(view=view, start_date=start_date, end_date=end_date)
            results[view.name] = record_count
        except Exception as e:
            logger.error(f"Failed to backfill view {view.name}: {e}")
            results[view.name] = 0
            # Continue processing other views instead of failing completely

    return results


def _get_source_table_from_view(view: MaterializedView) -> str:
    """
    Extract the source table name from a MaterializedView's schema.

    Args:
        view: MaterializedView object

    Returns:
        str: Name of the source table
    """
    # Simple extraction - looks for FROM clause in the schema
    # This assumes the source table is the first FROM in the SELECT statement
    schema_lower = view.schema.lower()
    from_index = schema_lower.find(" from ")
    if from_index == -1:
        raise ValueError(f"Could not find FROM clause in view schema for {view.name}")

    # Extract table name after FROM
    after_from = view.schema[from_index + 6 :].strip()

    # Handle FINAL modifier
    if after_from.lower().startswith("("):
        # Subquery, not a simple table
        raise ValueError(f"Complex FROM clause not supported for {view.name}")

    # Get the table name (until space, newline, or FINAL)
    table_parts = after_from.split()
    if not table_parts:
        raise ValueError(f"Could not extract table name from view schema for {view.name}")

    table_name = table_parts[0]

    # Remove FINAL if present
    if table_parts[0].upper() != "FINAL" and len(table_parts) > 1 and table_parts[1].upper() == "FINAL":
        # Table name is the first part
        pass

    return table_name


def get_materialized_view_stats(view_names: list[str] | None = None) -> dict:
    """
    Get statistics for materialized views.

    Args:
        view_names: List of view names to get stats for.
                   If None, gets stats for all views.

    Returns:
        dict: Statistics for each view
    """
    client = get_clickhouse_client()

    if view_names is None:
        view_names = list(CLICKHOUSE_MATERIALIZED_VIEWS.keys())

    stats = {}
    for view_name in view_names:
        if view_name not in CLICKHOUSE_MATERIALIZED_VIEWS:
            logger.warning(f"View {view_name} not found")
            continue

        view = CLICKHOUSE_MATERIALIZED_VIEWS[view_name]

        if not table_exists(client, view_name):
            stats[view_name] = {"exists": False}
            continue

        # Get table size from system.parts
        size_result = client.execute(f"""
            SELECT formatReadableSize(sum(bytes)) as size
            FROM system.parts
            WHERE table = '{view_name}'
        """)

        # Get actual data stats from the view itself
        stats_result = client.execute(f"""
            SELECT
                count() as record_count,
                min({view.timestamp_column}) as min_date,
                max({view.timestamp_column}) as max_date
            FROM {view_name}
        """)

        if stats_result and stats_result[0]:
            stats[view_name] = {
                "exists": True,
                "record_count": stats_result[0][0] if stats_result[0][0] else 0,
                "min_date": stats_result[0][1],
                "max_date": stats_result[0][2],
                "size": size_result[0][0] if size_result and size_result[0] else "0B",
            }
        else:
            stats[view_name] = {
                "exists": True,
                "record_count": 0,
                "min_date": None,
                "max_date": None,
                "size": "0B",
            }

    return stats


def refresh_all_materialized_views(
    days: int = 30,
    optimize: bool = True,
    views: list[str] | None = None,
) -> dict[str, int]:
    """
    Refresh all ClickHouse materialized views by re-backfilling recent data.

    This is useful when:
    - MVs have stale/corrupt data from incomplete backfills
    - Source data was updated and MVs need to reflect changes
    - ReplacingMergeTree tables have duplicate versions

    Args:
        days: Number of days to backfill (default 30)
        optimize: Run OPTIMIZE TABLE FINAL after backfill (default True)
        views: Specific view names to refresh. If None, refreshes all views.

    Returns:
        dict: Mapping of view names to record counts

    Usage:
        # From CLI:
        uv run python -m opennem.db.clickhouse_materialized_views --days 30

        # From Python:
        from opennem.db.clickhouse_materialized_views import refresh_all_materialized_views
        refresh_all_materialized_views(days=30)
    """
    from datetime import datetime, timedelta

    client = get_clickhouse_client()

    # Use start-of-day for start_date and end-of-day for end_date
    # to ensure we capture full days, not partial days based on when the job runs
    now = datetime.now()
    end_date = now.replace(hour=23, minute=59, second=59, microsecond=0)
    start_date = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)

    logger.info(f"Refreshing materialized views from {start_date.date()} to {end_date.date()}")

    # Print current stats
    print("\n=== Current MV Stats ===")
    stats = get_materialized_view_stats(views)
    for name, s in stats.items():
        if s.get("exists"):
            print(f"  {name}: {s['record_count']:,} records, {s['min_date']} to {s['max_date']}")
        else:
            print(f"  {name}: does not exist")

    # Backfill
    print(f"\n=== Backfilling {days} days ===")
    results = backfill_materialized_views(
        views=views,
        start_date=start_date,
        end_date=end_date,
        refresh_views=False,
    )

    for name, count in results.items():
        print(f"  {name}: {count:,} records")

    # Optimize tables to merge duplicates
    if optimize:
        print("\n=== Optimizing tables ===")
        view_names = views or list(CLICKHOUSE_MATERIALIZED_VIEWS.keys())
        for name in view_names:
            try:
                print(f"  Optimizing {name}...")
                client.execute(f"OPTIMIZE TABLE {name} FINAL")
            except Exception as e:
                logger.error(f"Failed to optimize {name}: {e}")

    # Print final stats
    print("\n=== Final MV Stats ===")
    stats = get_materialized_view_stats(views)
    for name, s in stats.items():
        if s.get("exists"):
            print(f"  {name}: {s['record_count']:,} records, {s['min_date']} to {s['max_date']}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Manage ClickHouse materialized views",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show stats for all MVs
  uv run python -m opennem.db.clickhouse_materialized_views --stats

  # Refresh all MVs for last 30 days
  uv run python -m opennem.db.clickhouse_materialized_views --days 30

  # Refresh specific MV
  uv run python -m opennem.db.clickhouse_materialized_views --days 30 --view fueltech_intervals_daily_mv

  # Refresh without optimize (faster but may leave duplicates)
  uv run python -m opennem.db.clickhouse_materialized_views --days 30 --no-optimize
        """,
    )
    parser.add_argument("--stats", action="store_true", help="Show stats for all materialized views")
    parser.add_argument("--days", type=int, default=30, help="Number of days to backfill (default: 30)")
    parser.add_argument("--view", type=str, action="append", help="Specific view(s) to refresh (can be repeated)")
    parser.add_argument("--no-optimize", action="store_true", help="Skip OPTIMIZE TABLE FINAL after backfill")

    args = parser.parse_args()

    if args.stats:
        print("=== Materialized View Stats ===")
        stats = get_materialized_view_stats()
        for name, s in stats.items():
            if s.get("exists"):
                print(f"  {name}: {s['record_count']:,} records, {s['min_date']} to {s['max_date']}, size={s['size']}")
            else:
                print(f"  {name}: does not exist")
    else:
        refresh_all_materialized_views(
            days=args.days,
            optimize=not args.no_optimize,
            views=args.view,
        )
