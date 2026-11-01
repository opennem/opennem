"""Maintenance mode (#782): shared state, response contract and status hook.

Turned on by env on the api and worker apps (read once at boot, so flip the env and restart):

    MAINTENANCE_MODE=true
    MAINTENANCE_MESSAGE="..."                      # optional, a default is used
    MAINTENANCE_ETA=2026-11-02T14:00:00+10:00      # optional, ISO 8601 with offset

Everything here is pure: no DB, ClickHouse or Redis calls. The API gate lives in opennem/api/maintenance.py,
the worker guard in opennem/tasks/maintenance.py.

Frontend contract (both shapes are stable):

    GET /v4/maintenance  -> 200 {"maintenance": bool, "message": str | null, "eta": str | null}
    any gated route      -> 503 {"success": false, "error": str, "maintenance": true, "message": str, "eta": str | null}
                            headers: Retry-After (seconds), Cache-Control: no-store

Status hook: when STATUS_WEBHOOK_URL is set, maintenance start/end POSTs
{"event": "maintenance.start" | "maintenance.end", "maintenance": bool, "message", "eta", "env", "source", "timestamp"}
with an optional `Authorization: Bearer STATUS_WEBHOOK_TOKEN`. The worker detects start/end itself on boot
(Redis marker), or post by hand with `opennem maintenance notify start|end`.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any, Literal

from opennem import settings

logger = logging.getLogger("opennem.maintenance")

DEFAULT_MESSAGE = "OpenElectricity is undergoing scheduled maintenance. Data will be back shortly."
DEFAULT_RETRY_AFTER_SECONDS = 300
MIN_RETRY_AFTER_SECONDS = 60
MAX_RETRY_AFTER_SECONDS = 3600

# never cache a maintenance answer at the edge (Cloudflare) or in a browser; the flag can flip at any restart
NO_STORE_HEADERS: dict[str, str] = {
    "Cache-Control": "no-store, max-age=0",
    "CDN-Cache-Control": "no-store",
    "Cloudflare-CDN-Cache-Control": "no-store",
}

# Redis key the worker keeps while maintenance is on, so a restart can tell start from end
MARKER_KEY = "opennem:maintenance:active"

MaintenanceEvent = Literal["maintenance.start", "maintenance.end"]


def is_maintenance_mode() -> bool:
    return bool(settings.maintenance_mode)


def maintenance_message() -> str:
    return (settings.maintenance_message or "").strip() or DEFAULT_MESSAGE


def maintenance_eta() -> str | None:
    return (settings.maintenance_eta or "").strip() or None


def maintenance_state() -> dict[str, Any]:
    """Public state for GET /v4/maintenance. Message/eta only while on."""
    if not is_maintenance_mode():
        return {"maintenance": False, "message": None, "eta": None}
    return {"maintenance": True, "message": maintenance_message(), "eta": maintenance_eta()}


def maintenance_error_body() -> dict[str, Any]:
    """503 body for gated routes. Keeps `success`/`error` so existing API clients still read it as an error."""
    message = maintenance_message()
    return {"success": False, "error": message, "maintenance": True, "message": message, "eta": maintenance_eta()}


def retry_after_seconds(now: datetime | None = None) -> int:
    """Seconds until the ETA, clamped to [60, 3600]; the default when the ETA is unset, unparseable, naive or past."""
    eta = maintenance_eta()
    if not eta:
        return DEFAULT_RETRY_AFTER_SECONDS
    try:
        eta_dt = datetime.fromisoformat(eta)
    except ValueError:
        return DEFAULT_RETRY_AFTER_SECONDS
    if eta_dt.tzinfo is None:
        return DEFAULT_RETRY_AFTER_SECONDS
    remaining = int((eta_dt - (now or datetime.now(UTC))).total_seconds())
    if remaining <= 0:
        return DEFAULT_RETRY_AFTER_SECONDS
    return max(MIN_RETRY_AFTER_SECONDS, min(MAX_RETRY_AFTER_SECONDS, remaining))


# status hook


def status_event_payload(event: MaintenanceEvent, source: str) -> dict[str, Any]:
    on = event == "maintenance.start"
    return {
        "event": event,
        "maintenance": on,
        "message": maintenance_message() if on else None,
        "eta": maintenance_eta() if on else None,
        "env": settings.env,
        "source": source,
        "timestamp": datetime.now(UTC).isoformat(),
    }


async def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> int:
    from opennem.utils.http import http_factory

    client = http_factory(mimic_browser=False, proxy=False, retry_403=False)
    resp = await asyncio.wait_for(client.post(url, json=payload, headers=headers), timeout=10)
    return resp.status_code


async def notify_status(event: MaintenanceEvent, source: str = "worker") -> bool:
    """Post a maintenance start/end to the status hook and the Slack monitoring channel. Never raises.

    Returns True when the status webhook accepted it (False when unset or failed).
    """
    payload = status_event_payload(event, source)
    sent = False

    url = settings.status_webhook_url
    if url:
        headers = {"Content-Type": "application/json"}
        if settings.status_webhook_token and settings.status_webhook_token.get_secret_value():
            headers["Authorization"] = f"Bearer {settings.status_webhook_token.get_secret_value()}"
        try:
            status_code = await _post_json(url, payload, headers)
            sent = 200 <= status_code < 300
            if not sent:
                logger.warning(f"status webhook returned {status_code} for {event}")
        except Exception as e:
            logger.warning(f"status webhook failed for {event}: {e}")
    else:
        logger.info(f"no STATUS_WEBHOOK_URL set, {event} not posted to a status page")

    if settings.slack_hook_monitoring:
        try:
            from opennem.clients.slack import slack_message

            if event == "maintenance.start":
                eta = f" (eta {payload['eta']})" if payload["eta"] else ""
                text = f"[{settings.env}] maintenance started: {payload['message']}{eta}"
            else:
                text = f"[{settings.env}] maintenance ended"
            await asyncio.wait_for(slack_message(webhook_url=settings.slack_hook_monitoring, message=text), timeout=10)
        except Exception as e:
            logger.warning(f"slack maintenance notice failed for {event}: {e}")

    return sent


async def detect_transition(redis: Any) -> MaintenanceEvent | None:
    """Compare the flag with the Redis marker: start when on and unmarked, end when off and marked. Never raises.

    Call before the startup flush (it would delete the marker); call `set_marker` after it.
    """
    try:
        was_on = bool(await redis.exists(MARKER_KEY))
    except Exception as e:
        logger.warning(f"could not read maintenance marker: {e}")
        return None
    on = is_maintenance_mode()
    if on and not was_on:
        return "maintenance.start"
    if not on and was_on:
        try:
            await redis.delete(MARKER_KEY)
        except Exception as e:
            logger.warning(f"could not clear maintenance marker: {e}")
        return "maintenance.end"
    return None


async def set_marker(redis: Any) -> None:
    """Keep the marker while on (survives a restart, cleared on the first boot with the flag off). Never raises."""
    if not is_maintenance_mode():
        return
    try:
        await redis.set(MARKER_KEY, datetime.now(UTC).isoformat())
    except Exception as e:
        logger.warning(f"could not set maintenance marker: {e}")
