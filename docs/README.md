# OpenElectricity Documentation

Documentation lives at https://docs.openelectricity.org.au

This folder contains the documentation for OpenElectricity, built with [Mintlify](https://mintlify.com).

## Prerequisites

- Node.js v19+ installed

## Installation

Install dependencies from within the `docs/` folder:

```bash
cd docs/
npm install
```

Or using bun:

```bash
cd docs/
bun install
```

## Development

Run the documentation locally from within the `docs/` folder:

```bash
npm run dev
```

Or using bun:

```bash
bun run dev
```

The documentation will be available at http://localhost:3000

### Custom Port

To use a different port:

```bash
npm run dev -- --port 3333
```

## Build

Build the documentation:

```bash
npm run build
```

## Update Mintlify CLI

To update to the latest version of Mintlify:

```bash
npm run update
```

## Sync OpenAPI

Generating API reference information reads the OpenAPI spec from the `openapi.json` file in the root of the repository.

```bash
./sync-openapi.sh
```

## Configuration

The documentation is configured in `mint.json`. See the [Mintlify documentation](https://mintlify.com/docs) for configuration options.

## Publishing Changes

Changes are auto deployed from the `master` branch via GitHub integration.
