import unkey

# 10 requests a second
OPENNEM_RATELIMIT_ADMIN = unkey.Ratelimit(
    unkey.RatelimitType.Fast,
    limit=10,
    refill_rate=10,
    refill_interval=1000,
)

# 1 request per second
OPENNEM_RATELIMIT_PRO = unkey.Ratelimit(
    unkey.RatelimitType.Fast,
    limit=1,
    refill_rate=1,
    refill_interval=1000,
)

# 1000 requests per day
OPENNEM_RATELIMIT_ACADEMIC = unkey.Ratelimit(
    unkey.RatelimitType.Fast,
    limit=1000,
    refill_rate=1000,
    refill_interval=1000 * 60 * 60 * 24,
)

# 100 requests per day
OPENNEM_RATELIMIT_USER = unkey.Ratelimit(
    unkey.RatelimitType.Fast,
    limit=100,
    refill_rate=100,
    refill_interval=1000 * 60 * 60 * 24,
)
