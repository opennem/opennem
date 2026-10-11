"""Admin routes never appear in any openapi doc the app serves, and are all include_in_schema=False."""

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from opennem.api.app import app

DOC_URLS = ["/openapi.json", "/v4/openapi.json", "/v3/openapi.json", "/v2/openapi.json", "/v1/openapi.json"]


def _walk(routes: list) -> list:
    """every route, recursing into mounts and sub-apps"""
    found = []
    for route in routes:
        found.append(route)
        for sub in (getattr(route, "app", None), getattr(route, "original_router", None)):
            if sub is not None and hasattr(sub, "routes") and sub is not app:
                found.extend(_walk(sub.routes))
    return found


def _doc_urls() -> list[str]:
    served = {getattr(r, "path", "") for r in _walk(app.routes)}
    return sorted({*DOC_URLS, *(p for p in served if p.endswith("openapi.json"))})


def test_no_openapi_doc_exposes_admin_paths() -> None:
    client = TestClient(app)
    docs: dict[str, dict] = {}
    for url in _doc_urls():
        r = client.get(url)
        if r.status_code == 200:
            docs[url] = r.json()

    assert "/openapi.json" in docs and "/v4/openapi.json" in docs
    for url, doc in docs.items():
        leaked = [p for p in doc["paths"] if "/admin" in p]
        assert not leaked, f"{url} exposes {leaked}"

    # not vacuous: public routes are present in the same docs
    assert any(p.endswith("/me") for p in docs["/v4/openapi.json"]["paths"])
    assert any(p.endswith("/me") for p in docs["/openapi.json"]["paths"])


def test_app_get_openapi_has_no_admin_paths() -> None:
    assert not [p for p in app.openapi()["paths"] if "/admin" in p]


def test_admin_routes_exist_and_are_excluded_from_schema() -> None:
    admin = [r for r in _walk(app.routes) if "/admin/" in getattr(r, "path", "") + "/" and isinstance(r, APIRoute)]
    assert any(r.path.startswith("/v4/admin/social") for r in admin), "admin routes not registered"
    assert all(r.include_in_schema is False for r in admin), [r.path for r in admin if r.include_in_schema]
