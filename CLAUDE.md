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
