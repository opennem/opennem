"""Every milestones route requires an api key.

`@api_protected()` sat above `@milestones_router.get`, so it wrapped a function FastAPI never calls
and every milestones route served anonymous requests. Auth is now a router dependency; these pin it
on the real versioned app, including the unversioned and legacy aliases.
"""

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from opennem.api.app import app
from opennem.api.milestones.router import milestones_router
from opennem.api.security import get_current_user


def _milestone_paths() -> list[str]:
    """Concrete request paths for every milestones route the app serves"""
    examples = {
        "{record_id}": "au.nem.wind.power.interval.high",
        "{instance_id}": "01a0cbb6-e2cc-7852-8960-38e78197e4ca",
    }
    paths = set()
    for route in app.routes:
        path = getattr(route, "path", "")
        if "/milestones/" not in path:
            continue
        for placeholder, value in examples.items():
            path = path.replace(placeholder, value)
        paths.add(path)
    return sorted(paths)


MILESTONE_PATHS = _milestone_paths()


def test_every_router_route_depends_on_auth() -> None:
    for route in milestones_router.routes:
        assert isinstance(route, APIRoute)
        assert any(d.call is get_current_user for d in route.dependant.dependencies), route.path


def test_app_serves_the_v4_routes() -> None:
    v4 = [p for p in MILESTONE_PATHS if p.startswith("/v4/milestones/")]
    assert len(v4) == 5, MILESTONE_PATHS


@pytest.mark.parametrize("path", MILESTONE_PATHS)
def test_anonymous_request_is_rejected(path: str) -> None:
    assert TestClient(app).get(path).status_code == 401


@pytest.mark.parametrize("path", MILESTONE_PATHS)
def test_short_key_is_rejected(path: str) -> None:
    # under 10 chars is refused before unkey is called, so this needs no network
    assert TestClient(app).get(path, headers={"Authorization": "Bearer short"}).status_code == 401
