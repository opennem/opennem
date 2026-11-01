"""Daily milestone head audit (#786). Alert only: never writes milestones, never rebuilds.

Runs `opennem.recordreactor.head_audit.audit_heads` and, when any significance 7+ or month chain
head is BAD (no longer the record on the settled data), sends a Sentry warning and a Slack message.
Both are deduped: Sentry groups on a fixed fingerprint, and Slack only posts when the set of BAD
heads changes (or once a week while it stays the same), so a known-bad head that is waiting on a
chain rebuild does not page every day.

Stands down while a milestone rebuild holds the lock: mid-rebuild the chains are partly empty.
Maintenance mode is handled centrally by the worker guard (`opennem.tasks.maintenance`).
"""

import hashlib
import logging

import sentry_sdk

from opennem.recordreactor.head_audit import AuditStatus, HeadFinding, audit_heads

logger = logging.getLogger("opennem.monitors.milestone_head_audit")

SLACK_DEDUPE_KEY = "opennem:milestone_head_audit:bad_digest"
# re-post an unchanged BAD set after this long, so a parked fix is not forgotten
SLACK_REPOST_SECONDS = 7 * 24 * 3600
# lines in the slack message before it is cut
SLACK_MAX_LINES = 20


def bad_digest(findings: list[HeadFinding]) -> str:
    """Stable digest of the BAD set: record id + head interval, order independent."""
    keys = sorted(f"{f.record_id}@{f.interval:%Y-%m-%dT%H:%M}" for f in findings if f.status == AuditStatus.bad)
    return hashlib.sha256("\n".join(keys).encode()).hexdigest()[:16]


def format_bad_line(finding: HeadFinding) -> str:
    return f"{finding.record_id} {finding.interval:%Y-%m-%d %H:%M} (sig {finding.significance}): {finding.reason}"


async def _redis_call(action: str, digest: str | None = None) -> str | None:
    """get / set / clear the posted-digest key. Errors are logged and swallowed (dedupe fails open)."""
    try:
        from opennem.tasks.broker import get_redis_pool

        redis = await get_redis_pool()
        try:
            if action == "get":
                value = await redis.get(SLACK_DEDUPE_KEY)
                return value.decode() if isinstance(value, bytes) else (str(value) if value is not None else None)
            if action == "set" and digest:
                await redis.set(SLACK_DEDUPE_KEY, digest, ex=SLACK_REPOST_SECONDS)
            if action == "clear":
                await redis.delete(SLACK_DEDUPE_KEY)
        finally:
            await redis.close()
    except Exception as e:
        logger.warning(f"head audit slack dedupe unavailable ({action}): {e}")
    return None


async def run_milestone_head_audit_check() -> list[HeadFinding]:
    """Audit chain heads; warn on BAD ones. Returns the BAD findings."""
    from opennem import settings
    from opennem.clients.slack import slack_message
    from opennem.recordreactor.rebuild_guard import skip_if_rebuild_in_progress

    if await skip_if_rebuild_in_progress("milestone head audit"):
        return []

    findings = await audit_heads()
    bad = [f for f in findings if f.status == AuditStatus.bad]
    suspect = sum(1 for f in findings if f.status == AuditStatus.suspect)

    if not bad:
        logger.info(f"milestone head audit clean: {len(findings)} heads, {suspect} suspect")
        # a BAD set that comes back after being fixed is news again
        await _redis_call("clear")
        return bad

    lines = [format_bad_line(f) for f in bad]
    for line in lines:
        logger.warning(f"milestone head BAD: {line}")

    with sentry_sdk.new_scope() as scope:
        scope.fingerprint = ["milestone-head-audit-bad"]
        scope.set_tag("bad_heads", str(len(bad)))
        scope.set_context("milestone_head_audit", {"bad": lines[:50], "suspect": suspect, "checked": len(findings)})
        scope.capture_message(f"milestone head audit: {len(bad)} heads are no longer the record", level="warning")

    digest = bad_digest(findings)
    # fails open: with redis down the same BAD set re-posts daily (sentry still groups on the fingerprint)
    if await _redis_call("get") != digest:
        shown = "\n".join(f"• {line}" for line in lines[:SLACK_MAX_LINES])
        more = f"\n…and {len(lines) - SLACK_MAX_LINES} more" if len(lines) > SLACK_MAX_LINES else ""
        posted = await slack_message(
            webhook_url=settings.slack_hook_monitoring,
            message=(
                f"*Milestone head audit: {len(bad)} record heads are no longer the record* ({suspect} suspect)\n"
                f"The settled data contradicts these published records, usually after a data repair or "
                f"re-aggregation (#786):\n{shown}{more}\n"
                f"Details: `opennem milestones audit-heads`. Fix with a scoped rebuild of the affected chains."
            ),
            tag_users=settings.slack_admin_alert,
        )
        # only after the post: a failed post must not mute this set for a week
        if posted:
            await _redis_call("set", digest)

    return bad
