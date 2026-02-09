"""CMS utility functions."""


def strip_synthetic_prefix(code: str) -> tuple[str, str]:
    """Strip leading '0' from synthetic DUIDs. Returns (operational_code, display_code)."""
    if code and len(code) > 1 and code[0] == "0" and code[1].isalpha():
        return code[1:], code
    return code, code
