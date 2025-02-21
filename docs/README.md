# OpenElectricity Docs

Documentation lives at https://docs.openelectricity.org.au

### Development

```
npx mintlify dev
```

### Sync OpenAPI

Generating API reference information reads the OpenAPI spec from the `openapi.json` file in the root of the repository.

```bash
./sync-openapi.sh
```

### Publishing Changes

Changes are auto deplpoyed from the `master` branch
