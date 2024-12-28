# OpenNEM Field Types

## URL Field Types

OpenNEM provides two specialized URL field types for use in Pydantic models:

### URLNoPath

A URL type that ensures the URL has no path component and doesn't end with a slash.

Valid examples:
- https://example.com
- http://api.example.com

Invalid examples:
- https://example.com/
- https://example.com/api
- example.com

### URLCleanPath

A URL type that ensures the URL has exactly one path segment and is properly normalized.

Valid examples:
- https://example.com/api
- https://api.example.com/v1

Invalid examples:
- https://example.com
- https://example.com/api/v1
- https://example.com/api/
- example.com/api

## Usage
