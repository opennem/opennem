# OpenNEM Command Line Interface

The OpenNEM CLI provides various commands for managing the OpenNEM platform. The CLI can be run using either:

<pre>
# Using UV (recommended)
uv run opennem

# Using Python directly
python -m opennem.cli
</pre>

## Command Groups

### Database Commands (db)

Commands for managing the OpenNEM database.

<pre>
# Initialize database schema and tables
opennem db init

# Load initial data fixtures
opennem db fixtures
</pre>

### Import Commands (import)

Commands for importing data into OpenNEM.

<pre>
# Import facility data
opennem import facilities

# Import fuel technology data
opennem import fueltechs

# Import BOM weather station data
opennem import bom
</pre>

### Crawler Commands (crawl)

Commands for managing data crawlers.

<pre>
# List all available crawlers and their status
opennem crawl list

# Run a specific crawler
opennem crawl run <name>

# Run options:
#   --all        Run all available data for the crawler (default: False)
#   --limit N    Limit to N most recent records
#   --reverse    Reverse the order of the crawlers

# Examples:
opennem crawl run aemo
opennem crawl run wem --all --limit 100
opennem crawl run nem --reverse

# Flush crawler metadata
opennem crawl flush
opennem crawl flush --days 7 --crawler "my-crawler"
</pre>

### Inspect Command

Inspect OpenNEM JSON data from a URL.

<pre>
opennem inspect <url>
</pre>

### Export Commands (export)

Commands for exporting data from OpenNEM.

<pre>
# Currently no export commands implemented
</pre>

### Task Commands (task)

Commands for managing background tasks.

<pre>
# Currently no task commands implemented
</pre>

## Error Handling

All commands include proper error handling and will:

1. Display meaningful error messages in red
2. Log errors appropriately
3. Exit with status code 1 on failure
4. Show debug information if DEBUG=true is set

## Environment Variables

The CLI respects the following environment variables:

- DEBUG: Enable debug output (default: false)
- Other OpenNEM settings as defined in opennem/settings_schema.py

## Development

When developing new CLI commands:

1. Use Typer for command implementation
2. Include proper type hints
3. Add comprehensive help text
4. Handle errors appropriately
5. Add new commands to the appropriate command group
6. Document new commands in this file

## Exit Codes

- 0: Success
- 1: General error
- 130: User interrupted (Ctrl+C)

## Logging

The CLI uses the standard Python logging framework with:

- Log level controlled by environment variables
- Errors logged to stderr
- Info and debug messages to stdout
- Rich formatting for better readability

## Dependencies

The CLI requires the following key dependencies:

- typer[all]: Modern CLI framework
- rich: Terminal formatting
- asyncio: Async support
- Other OpenNEM dependencies as specified in pyproject.toml

## Best Practices

When using the CLI:

1. Use uv run opennem for better performance
2. Set appropriate environment variables before running commands
3. Check command help with --help flag
4. Use debug mode when troubleshooting
5. Monitor logs for detailed operation information

## Command Help

Every command supports the --help flag for detailed usage information:

<pre>
# Show main help
opennem --help

# Show help for a command group
opennem db --help
opennem import --help
opennem crawl --help

# Show help for a specific command
opennem crawl run --help
opennem db init --help
</pre>

## Common Workflows

### Initial Setup

<pre>
# Initialize the database
opennem db init

# Load required fixtures
opennem db fixtures

# Import initial facility data
opennem import facilities
opennem import fueltechs
</pre>

### Data Collection

<pre>
# List available crawlers
opennem crawl list

# Run specific crawlers
opennem crawl run aemo
opennem crawl run wem

# Run with specific options
opennem crawl run nem --all --limit 1000
</pre>

## Troubleshooting

If you encounter issues:

1. Enable debug mode:
   <pre>
   export DEBUG=true
   opennem <command>
   </pre>

2. Check logs:
   <pre>
   tail -f logs/opennem.log
   </pre>

3. Verify database connection:
   <pre>
   opennem db init
   </pre>

## Support

For issues with the CLI:

1. Check the logs using appropriate log level
2. Verify environment variables
3. Ensure database connectivity
4. Check the [GitHub issues](https://github.com/opennem/opennem/issues)
5. Join the OpenNEM community on [Discord](https://discord.gg/opennem)

## Contributing

When adding new CLI commands:

1. Follow the existing command structure
2. Add comprehensive help text
3. Include error handling
4. Update this documentation
5. Add tests for new functionality

## Future Enhancements

Planned improvements to the CLI include:

1. Additional export commands
2. Task management features
3. Enhanced crawler controls
4. Better progress reporting
5. Configuration management commands
</pre>