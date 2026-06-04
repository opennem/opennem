# Open Electricity Documentation

Documentation lives at https://docs.openelectricity.org.au

This folder contains the documentation for Open Electricity, built with [Tangly](https://tangly.dev) (renders the Mintlify-style `docs.json` unmodified).

## Prerequisites

- Node.js v19+ and [bun](https://bun.sh)

## Installation

Install dependencies from within the `docs/` folder:

```bash
cd docs/
bun install
```

## Development

```bash
bun run dev
```

The documentation will be available at http://localhost:9411 (override with `PORT`).

## Build

```bash
bun run build      # static build -> ./dist
bun run preview    # serve ./dist locally
```

## Validate

```bash
bun run check      # tangly check --strict (config, nav, links, frontmatter)
```

## Configuration

The documentation is configured in `docs.json`. See the [Tangly documentation](https://tangly.dev) for configuration options.

## OpenAPI

API reference pages read the OpenAPI spec from the URL in `docs.json` (`api.openapi`). The `TANGLY_OPENAPI_URL` env var overrides it at build time (dev builds use `https://api.oedev.org/openapi.json`).

## Publishing

Deployed to Cloudflare Pages via GitHub Actions:

- **Pull requests** — `.github/workflows/docs-preview.yml` builds a preview and comments the URL.
- **`main`** — `.github/workflows/docs-deploy.yml` deploys to **docs.oedev.org** (dev OpenAPI).
- **`production`** — same workflow deploys to **docs.openelectricity.org.au** (prod OpenAPI), gated by the `docs-production` environment.

Only changes under `docs/**` trigger these workflows.
