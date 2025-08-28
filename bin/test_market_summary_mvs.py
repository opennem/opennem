#!/usr/bin/env python3
"""
Test script for creating and backfilling market_summary materialized views.
"""

import logging

from opennem.db.clickhouse import get_clickhouse_client, table_exists
from opennem.db.clickhouse_materialized_views import (
    backfill_materialized_views,
    ensure_materialized_views_exist,
    get_materialized_view_stats,
)
from opennem.db.clickhouse_views import (
    MARKET_SUMMARY_DAILY_VIEW,
    MARKET_SUMMARY_MONTHLY_VIEW,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main function to test market_summary materialized views."""

    # Views to create and backfill
    market_summary_views = [
        MARKET_SUMMARY_DAILY_VIEW,
        MARKET_SUMMARY_MONTHLY_VIEW,
    ]

    logger.info("Testing market_summary materialized views")

    # 1. Check if base table exists
    client = get_clickhouse_client()
    if not table_exists(client, "market_summary"):
        logger.error("Base table 'market_summary' does not exist!")
        return

    # Get date range from market_summary
    result = client.execute("""
        SELECT
            min(interval) as min_date,
            max(interval) as max_date,
            count() as record_count
        FROM market_summary
    """)

    if not result or not result[0][0]:
        logger.error("No data found in market_summary table")
        return

    min_date, max_date, record_count = result[0]
    logger.info(f"Market summary data range: {min_date} to {max_date} ({record_count:,} records)")

    # 2. Ensure materialized views exist
    logger.info("Ensuring materialized views exist...")
    ensure_materialized_views_exist(market_summary_views)

    # 3. Check current status of views
    logger.info("\nCurrent status of materialized views:")
    stats = get_materialized_view_stats(["market_summary_daily_mv", "market_summary_monthly_mv"])
    for view_name, view_stats in stats.items():
        if view_stats.get("exists"):
            logger.info(f"  {view_name}:")
            logger.info(f"    Records: {view_stats.get('record_count', 0):,}")
            logger.info(f"    Date range: {view_stats.get('min_date')} to {view_stats.get('max_date')}")
            logger.info(f"    Size: {view_stats.get('size')}")
        else:
            logger.info(f"  {view_name}: Does not exist")

    # 4. Ask user if they want to backfill
    print("\nDo you want to backfill the materialized views? (y/n): ", end="")
    response = input().strip().lower()

    if response != "y":
        logger.info("Skipping backfill")
        return

    # 5. Ask if they want to refresh (drop and recreate)
    print("Do you want to refresh views (drop and recreate)? (y/n): ", end="")
    refresh = input().strip().lower() == "y"

    # 6. Backfill the views
    logger.info("\nBackfilling materialized views...")
    logger.info(f"Date range: {min_date} to {max_date}")
    logger.info(f"Refresh views: {refresh}")

    try:
        results = backfill_materialized_views(
            views=["market_summary_daily_mv", "market_summary_monthly_mv"],
            start_date=min_date,
            end_date=max_date,
            refresh_views=refresh,
        )

        logger.info("\nBackfill completed successfully!")
        for view_name, count in results.items():
            logger.info(f"  {view_name}: {count:,} records")

    except Exception as e:
        logger.error(f"Error during backfill: {e}")
        return

    # 7. Verify the results
    logger.info("\nVerifying results...")

    # Check daily view
    daily_result = client.execute("""
        SELECT
            count() as record_count,
            min(date) as min_date,
            max(date) as max_date
        FROM market_summary_daily_mv
    """)

    if daily_result and daily_result[0][0]:
        count, min_dt, max_dt = daily_result[0]
        logger.info(f"Daily MV: {count:,} records from {min_dt} to {max_dt}")

    # Check monthly view
    monthly_result = client.execute("""
        SELECT
            count() as record_count,
            min(month) as min_month,
            max(month) as max_month
        FROM market_summary_monthly_mv
    """)

    if monthly_result and monthly_result[0][0]:
        count, min_dt, max_dt = monthly_result[0]
        logger.info(f"Monthly MV: {count:,} records from {min_dt} to {max_dt}")

    # 8. Test a sample query
    logger.info("\nTesting sample query on daily MV...")
    sample_query = """
        SELECT
            date,
            network_id,
            network_region,
            round(price_avg, 2) as avg_price,
            round(demand_total_energy_daily, 2) as total_energy_gwh,
            round(demand_total_market_value_daily, 2) as total_market_value
        FROM market_summary_daily_mv
        WHERE date = '2024-01-01'
        ORDER BY network_id, network_region
        LIMIT 10
    """

    sample_result = client.execute(sample_query)
    if sample_result:
        logger.info("Sample results for 2024-01-01:")
        for row in sample_result:
            logger.info(f"  {row}")

    logger.info("\nMarket summary materialized views setup complete!")


if __name__ == "__main__":
    main()
