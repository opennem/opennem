"""Tests for the CMS query retry predicate (transient sanity errors must be retried)."""

from sanity.exceptions import (
    SanityAuthError,
    SanityConnectionError,
    SanityNotFoundError,
    SanityRateLimitError,
    SanityServerError,
    SanityTimeoutError,
    SanityValidationError,
)

from opennem.cms.queries import _CMS_RETRYABLE_ERRORS


def test_transient_sanity_errors_are_retryable() -> None:
    # these are the network/cdn blips that previously aborted the whole cms sync (BACKEND-5C0)
    for exc in (SanityTimeoutError, SanityConnectionError, SanityServerError, SanityRateLimitError):
        assert issubclass(exc, _CMS_RETRYABLE_ERRORS), f"{exc.__name__} should be retryable"


def test_non_transient_sanity_errors_are_not_retryable() -> None:
    # auth / not-found / bad-query are not transient — fail fast instead of hammering the cms
    for exc in (SanityAuthError, SanityNotFoundError, SanityValidationError):
        assert not issubclass(exc, _CMS_RETRYABLE_ERRORS), f"{exc.__name__} should not be retryable"
