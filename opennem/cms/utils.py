"""CMS utility functions."""

from collections.abc import Container


def strip_synthetic_prefix(code: str) -> tuple[str, str]:
    """Strip leading '0' from synthetic DUIDs. Returns (operational_code, display_code)."""
    if code and len(code) > 1 and code[0] == "0" and code[1].isalpha():
        return code[1:], code
    return code, code


def resolve_operational_code(code: str, reserved: Container[str]) -> tuple[str, str]:
    """Strip the synthetic prefix, unless the stripped code belongs to something else.

    The '0' prefix marks a code OpenNEM invented — a derived battery unit, or a placeholder
    for a facility whose real DUID isn't known yet — and stripping it recovers the
    operational code. That only holds while the stripped result is unclaimed. `0WNSF`
    (Winton North, committed, no data) strips to `WNSF`, which is a real and entirely
    different facility (Wangaratta), and the collision meant Winton North was silently
    dropped from every sync (#481).

    When the stripped code is already claimed, the prefix is not synthetic-in-context and
    the code is kept whole, so both facilities survive the sync.

    Args:
        code: the raw code as held in the CMS
        reserved: codes claimed by other records — must not contain `code` itself
    """
    operational, display = strip_synthetic_prefix(code)

    if operational != code and operational in reserved:
        return code, code

    return operational, display
