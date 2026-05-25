"""
Custom OpenAPI generator — wraps FastAPI's default to inject SDK code samples.

`x-codeSamples` is a widely-supported OpenAPI extension (Tangly, Mintlify,
ReDoc, Stoplight) that surfaces per-language SDK snippets next to the curl
on each endpoint. We load the canonical snippets from
`opennem.api.code_samples` and walk the spec's path map once, caching the
result on `app.openapi_schema` so generation cost is paid only on first
request.
"""

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from opennem.api.code_samples import lookup

_HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")


def custom_openapi(app: FastAPI) -> Any:
    """Return the FastAPI OpenAPI schema with `x-codeSamples` injected.

    Caches the result on `app.openapi_schema` per FastAPI's standard
    pattern. Wire by assigning `app.openapi = partial(custom_openapi, app)`.
    """
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        terms_of_service=app.terms_of_service,
        contact=app.contact,
        license_info=app.license_info,
        routes=app.routes,
        tags=app.openapi_tags,
        servers=app.servers,
    )

    for path, methods in schema.get("paths", {}).items():
        for method in _HTTP_METHODS:
            op = methods.get(method)
            if not isinstance(op, dict):
                continue
            samples = lookup(path, method)
            if samples:
                op["x-codeSamples"] = samples

    app.openapi_schema = schema
    return schema
