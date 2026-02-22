from unkey.py import models

# Admin: 10 requests/second — override regardless of plan
OPENNEM_RATELIMIT_ADMIN = models.RatelimitRequest(
    name="admin_ratelimit",
    limit=10,
    duration=1000,  # milliseconds
    cost=1,
    auto_apply=True,
)
