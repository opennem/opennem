## Overview

OpenNEM (OpenElectricity) is an Australian Energy Market Data Platform that collects, processes, and serves public energy data from Australian energy networks (NEM and WEM). The platform provides a REST API for accessing processed energy data and exports data in various formats for both the frontend website at openelectricity.org.au and the backend API at api.openelectricity.org.au.

## Development Commands

### Running the Application
- `opennem dev` - Run development server with hot reload
- `opennem api` - Run production API server (this deploys to api.openelectricity.org.au)
- `opennem worker` - Run background workers for data processing (this deploys as a worker)

### Testing and Code Quality
- `uv run pytest tests -v` - Run all tests
- `uv run pytest tests/test_specific.py -v` - Run specific test file
- `uv run pytest tests/ -k "test_name" -v` - Run specific test by name
- `uv run ruff format opennem` - Format code
- `uv run ruff check opennem` - Lint code
- `uv run pyright -v .venv opennem` - Type checking
- `make check` - Run all quality checks (format, lint, type check)

### Database Operations
- `alembic upgrade head` - Apply database migrations
- `alembic revision --autogenerate -m "description"` - Create new migration
- Database connection uses environment variables (DATABASE_HOST, DATABASE_PORT, etc.)

### Version Management
- `make version BUMP=dev` - Bump development version
- `make version BUMP=patch` - Bump patch version
- `make version BUMP=minor` - Bump minor version
- `make release` - Full release process (format, lint, version bump, tag)

## Architecture Overview

### Data Flow Architecture
1. **Crawlers** (`opennem/crawlers/`) fetch data from AEMO, BOM, and other sources
2. **Parsers** (`opennem/core/parsers/`) process various file formats (CSV, Excel, JSON)
3. **Controllers** (`opennem/controllers/`) contain business logic for data processing
4. **Aggregators** (`opennem/aggregates/`) compute statistics and summaries
5. **API** (`opennem/api/`) serves processed data via FastAPI endpoints
6. **Workers** (`opennem/workers/`) handle background processing tasks

### Key Components

**API Layer** (`opennem/api/`):
- FastAPI application with versioned endpoints (v4 is current)
- Authentication via Unkey and Clerk
- Rate limiting and Redis caching
- Main router composition in `opennem/api/app.py`

**Data Models** (`opennem/db/models/`):
- SQLAlchemy models for facilities, markets, prices, and generation data
- Pydantic schemas in `opennem/schema/` for validation and serialization
- Database migrations in `opennem/db/migrations/`

**Data Processing**:
- RecordReactor (`opennem/recordreactor/`) for event-driven updates for milestones / records
- Flow solvers (`opennem/flows/`) for interconnector calculations
- Aggregation pipelines for statistics generation

**External Clients** (`opennem/clients/`):
- AEMO client for market data
- BOM client for weather data
- Rooftop solar data clients

### Environment Configuration
The application uses environment variables for configuration. These are loaded as a pydantic settings object in `opennem/settings_schema.py`:
- Development: `.env.development`
- Key variables: DATABASE_HOST, REDIS_URL, S3_BUCKET_NAME, API keys
- Environment variables are loaded in `opennem/__init__.py`

### Testing Strategy
- Unit tests for parsers, validators, and utilities
- Integration tests for API endpoints
- Fixtures in `tests/fixtures/` for test data
- Mock external services in tests

## Important Patterns

### Error Handling
- Use structured logging with `opennem.core.logger`
- Sentry integration for error tracking in production
- Proper exception handling in crawlers to prevent data loss

### Data Validation
- Always validate incoming data with Pydantic schemas
- Use validators in `opennem/core/validators/` for domain-specific rules
- Check data quality before persisting to database

### Background Tasks
- Use ARQ (`opennem/tasks/`) for async task processing
- Tasks are defined with proper retry logic and error handling
- Monitor task execution via Logfire

### API Design
- Follow REST conventions for endpoints
- Use dependency injection for database sessions
- Implement proper pagination for large datasets
- Version API changes appropriately

### Coding Standards
- Ensure minimum complexity of functions and methods
- Lint and format all code with `uv run ruff format opennem` and `uv run ruff check opennem`
- Use strong in-built types for all parameters and return functions
- Use pydantic models for data parsing and internal schemas
- Support Python 3.10 and above - including built in types such as list, dict, set, etc.
- Use asyncio for all asynchronous code
- Use asyncpg for database operations
- Use httpx for all HTTP requests by loading it from `opennem.utils.http`
- Use sqlalchemy for database operations

### Git Workflow
- **NEVER commit or merge into the `production` branch** - always use `main` branch for development
- The `production` branch is for releases only
- Create PRs against `main`, not `production`

## Network-Specific Data Considerations

### NEM vs WEM
- **NEM** (National Electricity Market): Covers eastern Australia (NSW, QLD, SA, TAS, VIC)
- **WEM** (Wholesale Electricity Market): Covers Western Australia, isolated grid with no interconnectors

### WEM Data Limitations
- WEM public data sources (`referenceTradingPrices`) only provide **price data, not demand**
- The `balancing_summary` table for WEM only has `price` populated; `demand` and `generation_total` are NULL
- **Solution**: Since WEM is isolated (no interconnectors), demand ≈ total generation. Calculate WEM demand from `facility_scada` generation totals
- This is implemented in `opennem/aggregates/market_summary.py` via the `wem_generation` CTE

### Market Summary Aggregation
- `opennem/aggregates/market_summary.py` aggregates data from PostgreSQL to ClickHouse
- Feature flag `DEMAND_FROM_MARKET_SUMMARY` controls whether API uses ClickHouse (True) or PostgreSQL (False)
- Dev environment uses ClickHouse; Prod currently uses PostgreSQL
- Materialized views: `market_summary_daily_mv`, `market_summary_monthly_mv`

### Backfill Commands
```python
# Backfill last N days
from opennem.aggregates.market_summary import run_market_summary_aggregate_for_last_days
asyncio.run(run_market_summary_aggregate_for_last_days(days=400))

# Full historical backfill (takes several hours)
from opennem.aggregates.market_summary import reset_market_summary
asyncio.run(reset_market_summary(start_date=datetime(1999, 1, 1), skip_schema_refresh=True))

# Backfill materialized views
from opennem.aggregates.market_summary import backfill_market_summary_views
backfill_market_summary_views(refresh_views=True)
```

### Known Data Quality Issues
- Pre-existing bad data with `network_id='NEM', network_region='WEM'` exists in `market_summary` table (WEM should not be a NEM region)
- WEM `facility_scada` data may lag behind `balancing_summary` by several hours

## ClickHouse

### Environment Access
- **ch-dev**: Default local connection via `.env.local`
- **ch-prod**: Use `ENV=production` prefix (e.g., `ENV=production uv run python script.py`)
- ch-dev has data from 2020; ch-prod has full history from 1999

### unit_intervals Table
- **Network IDs**: `NEM`, `WEM`, `AEMO_ROOFTOP`, `APVI` (not `AEMO_NEM`)
- **Coverage**: 1999-01-01 to present, ~749M records, continuous daily coverage
- **All timestamps in UTC** - no DST transitions
- Aggregation code: `opennem/aggregates/unit_intervals.py`

### Network Data Intervals & Lag
| Network | Interval | Expected Lag |
|---------|----------|--------------|
| NEM | 5 min | Near real-time |
| AEMO_ROOFTOP | 30 min | ~30 minutes max |
| WEM | 5 min | ~24 hours (publishes daily) |
| APVI | 5 min | Follows AEMO_ROOFTOP |

### unit_intervals Aggregation
```python
# Catch up all networks to current time
from opennem.aggregates.unit_intervals import run_unit_intervals_aggregate_to_now
asyncio.run(run_unit_intervals_aggregate_to_now())

# Backfill from specific date
from opennem.aggregates.unit_intervals import run_unit_intervals_backlog
asyncio.run(run_unit_intervals_backlog(start_date=datetime(2025, 1, 1)))
```

### ClickHouse Materialized Views

All MVs are defined in `opennem/db/clickhouse_views.py` and managed via `opennem/db/clickhouse_materialized_views.py`.

| View | Source | Timestamp Col | Purpose |
|------|--------|---------------|---------|
| `unit_intervals_daily_mv` | `unit_intervals` | `date` | Daily aggregation per unit |
| `fueltech_intervals_mv` | `unit_intervals` | `interval` | 5-min intervals by fueltech |
| `fueltech_intervals_daily_mv` | `unit_intervals` | `date` | Daily by fueltech |
| `renewable_intervals_mv` | `unit_intervals` | `interval` | 5-min by renewable flag |
| `renewable_intervals_daily_mv` | `unit_intervals` | `date` | Daily by renewable flag |
| `market_summary_daily_mv` | `market_summary` | `date` | Daily market summary |
| `market_summary_monthly_mv` | `market_summary` | `month` | Monthly market summary |

**RecordReactor dependency**: The milestone/records system (`opennem/recordreactor/`) queries `fueltech_intervals_mv` and `renewable_intervals_mv` for power/energy/emissions metrics. If these MVs are missing historical data, milestones will only show recent records.

### MV Backfill Commands
```python
from datetime import datetime
from opennem.db.clickhouse_materialized_views import (
    backfill_materialized_views,
    get_materialized_view_stats,
)

# Check MV status (records, date range)
stats = get_materialized_view_stats()
for name, s in stats.items():
    print(f"{name}: {s['record_count']:,} records, {s['min_date']} to {s['max_date']}")

# Backfill specific views
backfill_materialized_views(
    views=['fueltech_intervals_mv', 'renewable_intervals_mv'],
    start_date=datetime(1999, 1, 1),
    end_date=datetime(2025, 12, 31),
    refresh_views=False,  # Don't drop existing data
)

# Backfill all views
backfill_materialized_views(
    start_date=datetime(1999, 1, 1),
    end_date=datetime(2025, 12, 31),
)
```

### ClickHouse MergeTree Engine Types

Understanding when to use each engine type is critical for correct aggregation:

| Engine | Behavior | Use Case |
|--------|----------|----------|
| **ReplacingMergeTree(version)** | Keeps row with highest version per key | Deduplication, upserts |
| **SummingMergeTree** | SUMS numeric columns during merge | Simple aggregation (sum, count) |
| **AggregatingMergeTree** | Merges aggregate states | Complex aggregation (avg, uniq) |

**Key insight**: ReplacingMergeTree is for **deduplication**, not aggregation. If you need to aggregate incremental data, use SummingMergeTree or AggregatingMergeTree.

### MV Auto-Population Trap (Jan 2026 Incident)

**Problem**: Daily MVs that auto-populate from source tables can produce incorrect data.

**How auto-populating MVs work**:
```sql
CREATE MATERIALIZED VIEW daily_mv
ENGINE = ReplacingMergeTree(version)
AS SELECT toDate(interval) as date, sum(energy) as energy, max(version) as version
FROM unit_intervals
GROUP BY date
```

When new data arrives in `unit_intervals`:
1. MV auto-inserts a **partial** daily aggregate (e.g., 10 intervals)
2. Later, more data arrives for same day
3. MV inserts **another** partial aggregate
4. ReplacingMergeTree keeps row with **highest version** (newest = partial!)
5. **Result**: Daily MV shows partial data, not full day

**Evidence**:
```
Date         daily_mv   unit_intervals   pct
2026-01-30      88.3            216.3   40.8%  ← partial data wins!
```

**Solution: Completeness-Based Version**

Use `interval_count * 1B + max(version)` as the version:

```sql
CREATE MATERIALIZED VIEW fueltech_intervals_daily_mv
ENGINE = ReplacingMergeTree(version)
ORDER BY (date, network_id, network_region, fueltech_id, fueltech_group_id)
AS SELECT
    toDate(interval) as date,
    network_id,
    network_region,
    fueltech_id,
    fueltech_group_id,
    sum(energy) as energy,
    count() as unit_count,
    count(distinct interval) as interval_count,
    -- Completeness-based version: more intervals = higher version
    toUInt64(count(distinct interval)) * 1000000000 + max(version) as version
FROM unit_intervals
GROUP BY date, network_id, network_region, fueltech_id, fueltech_group_id
```

**How it works**:
- Backfill with 288 intervals → version = 288,000,000,XXX
- Auto-pop with 10 intervals → version = 10,000,000,XXX
- ReplacingMergeTree keeps **highest version** = backfill wins!

**Key files**:
- MV definitions: `opennem/db/clickhouse_views.py`
- MV management: `opennem/db/clickhouse_materialized_views.py`

### Daily MV Sync Verification

**Diagnose daily MV vs source divergence**:
```python
from opennem.db.clickhouse import get_clickhouse_client
client = get_clickhouse_client()
result = client.execute("""
    WITH daily AS (
        SELECT date, sum(energy)/1000 as gwh, max(version) as ver
        FROM fueltech_intervals_daily_mv FINAL
        WHERE date >= '2026-01-26' AND network_id = 'NEM'
        GROUP BY date
    ),
    source AS (
        SELECT toDate(interval) as date, sum(energy)/1000 as gwh
        FROM unit_intervals FINAL
        WHERE interval >= '2026-01-26' AND network_id = 'NEM'
        GROUP BY date
    )
    SELECT s.date,
           round(d.gwh, 1) as daily_gwh,
           round(s.gwh, 1) as source_gwh,
           round(d.gwh/s.gwh*100, 1) as pct,
           d.ver / 1000000000 as intervals
    FROM source s LEFT JOIN daily d ON s.date = d.date
    ORDER BY s.date
""")
for r in result:
    status = '✓' if r[3] and abs(r[3] - 100) < 1 else '✗'
    print(f"{status} {r[0]}: {r[3]}% (~{r[4]:.0f} intervals)")
```

**Expected output**: All days should show ~100% and ~288 intervals (for NEM 5-min data).

### MV Backfill with DELETE-before-INSERT

For daily MVs, the backfill process includes DELETE before INSERT to prevent double-counting:

```python
# In opennem/db/clickhouse_materialized_views.py
def backfill_materialized_view(view, start_date, end_date, chunk_size_days=30):
    # DELETE existing data for date range first
    delete_query = f"""
        ALTER TABLE {view.name} DELETE
        WHERE {view.timestamp_column} >= %(start)s
        AND {view.timestamp_column} <= %(end)s
    """
    client.execute(delete_query, {"start": current_date.date(), "end": chunk_end.date()})

    # Then INSERT fresh aggregation
    client.execute(view.backfill_query, {"start": current_date, "end": chunk_end})
```

### MV Backfill Troubleshooting

**Symptom**: Backfill fails with "Cannot reserve X MiB, not enough space"
- This is usually **disk space**, not RAM
- Check ch-prod disk: `ssh ch-prod "df -h /mnt/volume_ch_prod"`
- ClickHouse needs disk space for temp files during GROUP BY operations
- Solution: Free up or expand `/mnt/volume_ch_prod` disk

**Symptom**: Milestones only showing recent records (e.g., from start of year)
- Check MV date ranges: `get_materialized_view_stats(['fueltech_intervals_mv', 'renewable_intervals_mv'])`
- If min_date is recent, MVs need backfilling from 1999

**Symptom**: Energy export shows incorrect values (e.g., every 3rd day has ~10% of expected energy)
- **Root cause**: Daily MVs (`fueltech_intervals_daily_mv`, `renewable_intervals_daily_mv`) have stale data
- Daily MVs use ReplacingMergeTree - if backfilled when source was incomplete, they retain old aggregations
- The energy export (`energy_fueltech_daily_v4`) queries `fueltech_intervals_daily_mv` for daily intervals
- **Diagnosis**: Compare daily MV vs 5-min MV totals:
```python
# Check for divergence between daily MV and 5-min MV
from opennem.db.clickhouse import get_clickhouse_client
client = get_clickhouse_client()
result = client.execute("""
    WITH daily AS (
        SELECT date, sum(energy)/1000 as gwh FROM fueltech_intervals_daily_mv FINAL
        WHERE date >= '2026-01-01' AND network_id = 'NEM' GROUP BY date
    ),
    fivemin AS (
        SELECT toDate(interval) as date, sum(energy)/1000 as gwh FROM fueltech_intervals_mv FINAL
        WHERE interval >= '2026-01-01' AND network_id = 'NEM' GROUP BY date
    )
    SELECT f.date, round(d.gwh, 1) as daily, round(f.gwh, 1) as fivemin,
           round(d.gwh/f.gwh*100, 1) as pct
    FROM fivemin f LEFT JOIN daily d ON f.date = d.date ORDER BY f.date
""")
for r in result: print(f"{r[0]}: {r[3]}%")  # Should be ~100% for all days
```
- **Fix**: Re-backfill the daily MVs and run OPTIMIZE FINAL:
```python
from datetime import datetime
from opennem.db.clickhouse_materialized_views import backfill_materialized_views
from opennem.db.clickhouse import get_clickhouse_client

backfill_materialized_views(
    views=['fueltech_intervals_daily_mv', 'renewable_intervals_daily_mv'],
    start_date=datetime(2025, 1, 1),
    end_date=datetime.now(),
    refresh_views=False,
)
client = get_clickhouse_client()
client.execute("OPTIMIZE TABLE fueltech_intervals_daily_mv FINAL")
client.execute("OPTIMIZE TABLE renewable_intervals_daily_mv FINAL")
```

**Symptom**: Daily MVs have partial data (~100-200 intervals instead of 288)
- **Root cause**: Scheduled backfill job used `datetime.now()` which includes hour/minute
- When job ran at 15:30, query was: `WHERE interval >= '2026-01-24 15:30:00'`
- This captured only intervals from 15:30 onwards (~103 intervals)
- **Fix**: Already fixed in code - dates are now normalized to 00:00:00 and 23:59:59
- **Diagnosis**: Check interval count encoded in version:
```python
result = client.execute("""
    SELECT date, max(version) / 1000000000 as intervals
    FROM fueltech_intervals_daily_mv FINAL
    WHERE network_id = 'NEM' GROUP BY date ORDER BY date DESC LIMIT 10
""")
for r in result: print(f"{r[0]}: ~{int(r[1])} intervals")  # Should be 288-289
```

**ch-prod server specs** (as of Jan 2026):
- RAM: 31GB (plenty for queries)
- Data disk: `/mnt/volume_ch_prod` - needs ~100GB free for backfills
- No swap configured
- Config: `/etc/clickhouse-server/config.d/`

### Milestone Analysis Backfill
```python
import asyncio
from opennem.recordreactor.backlog import run_milestone_analysis_backlog

# Full refresh of milestones table (deletes existing, re-analyzes all)
asyncio.run(run_milestone_analysis_backlog(refresh=True))

# Update milestones from last recorded to now
from opennem.recordreactor.backlog import run_update_milestone_analysis_to_now
asyncio.run(run_update_milestone_analysis_to_now())
```
