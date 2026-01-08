from unkey.py import models

# Admin: 10 requests/second
OPENNEM_RATELIMIT_ADMIN = models.RatelimitRequest(
    name="admin_ratelimit",
    limit=10,
    duration=1000,  # milliseconds
    cost=1,
    auto_apply=True,
)

# Pro: 1 request/second
OPENNEM_RATELIMIT_PRO = models.RatelimitRequest(name="pro_ratelimit", limit=1, duration=1000, cost=1, auto_apply=True)

# Academic: 1000 requests/day
OPENNEM_RATELIMIT_ACADEMIC = models.RatelimitRequest(
    name="academic_ratelimit",
    limit=1000,
    duration=86_400_000,  # 24 hours
    cost=1,
    auto_apply=True,
)

# User: 100 requests/day
OPENNEM_RATELIMIT_USER = models.RatelimitRequest(name="user_ratelimit", limit=100, duration=86_400_000, cost=1, auto_apply=True)
