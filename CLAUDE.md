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
