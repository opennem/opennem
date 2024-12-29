"""
OpenNEM Normalization Module

This module provides a set of utilities to normalize, clean and parse passed
in data from various sources.

"""

import logging
import re
from decimal import Decimal

logger = logging.getLogger("opennem.core.normalizers")

# Custom normalizers

__match_twitter_handle = re.compile(r"^@?[A-Za-z\_]{1,15}$")


def validate_twitter_handle(twitter_handle: str) -> re.Match | None:
    """Validate a twitter handle. Optional @, length up to 15 characters"""
    return re.match(__match_twitter_handle, twitter_handle)


# Number normalizers

__is_number = re.compile(r"^[\d\.]+$")
__is_single_number = re.compile(r"^\d$")


def is_number(value: str | int | float) -> bool:
    if isinstance(value, int):
        return True

    if isinstance(value, float):
        return True

    value = str(value).strip()

    if re.match(__is_number, value):
        return True

    return False


def is_single_number(value: str | int) -> bool:
    value = str(value).strip()

    if re.match(__is_single_number, value):
        return True
    return False


def clean_float(number: str | int | float) -> float:
    num_return = None

    if isinstance(number, str):
        number = number.strip()

        if number == "":
            return None

        num_return = float(number)
        return num_return

    if isinstance(number, int):
        return float(number)

    if isinstance(number, Decimal):
        return float(number)

    if isinstance(number, float):
        return number


# Whitespace normalizers


def strip_whitespace(subject: str) -> str:
    return str(re.sub(r"\s+", "", subject.strip()))


def normalize_whitespace(subject: str) -> str:
    return str(re.sub(r"\s{2,}", " ", subject.strip()))


def strip_double_spaces(subject: str) -> str:
    """Strips double spaces back to spaces"""
    return re.sub(" +", " ", subject)


# String normalizers

__urlsafe_match = re.compile(r"^[a-zA-Z0-9_-]*$")


def string_to_title(subject: str) -> str:
    """Title case and clean string"""
    return str(subject).strip().title()


def string_is_urlsafe(subject: str) -> bool:
    """Check if a string is URL safe"""
    return isinstance(re.match(__urlsafe_match, subject), re.Match)


# Case Styles
# convert to/from various cases


def snake_to_camel(string: str) -> str:
    """Converts snake case to camel case. ie. field_name to FieldName"""
    return "".join(word.capitalize() for word in string.split("_"))


# OpenNEM specific normalizers


def normalize_duid(duid: str | None) -> str | None:
    """Take what is supposed to be a DUID and clean it up so we always return a string, even if its blank"""
    duid = duid or ""

    if not duid:
        return None

    # strip out non-ascii characters
    duid_ascii = duid.encode("ascii", "ignore").decode("utf-8")

    # strip out non-alpha num
    # @TODO also pass to validator
    duid_ascii = re.sub(r"\W\_\-\#+", "", duid_ascii)

    # strip out control chars
    duid_ascii = re.sub(r"\_[xX][0-9A-F]{4}\_", "", duid_ascii)

    # normalize
    duid_ascii = duid_ascii.strip().upper()

    if duid_ascii == "-" or not duid_ascii:
        return ""

    return duid_ascii


def cast_float_or_none(value: float | None) -> float | None:
    """Cast a float or None"""
    if value is None:
        return None

    return round(float(value), 4)


def clean_capacity(capacity: str | int | float, round_to: int = 6) -> float | None:
    """
    Takes a capacity and cleans it up into a float

    @TODO support unit conversion
    """
    cap_clean: str | None = None

    if capacity is None or capacity == "-":
        return None

    # Type gating float, string, int, others ..
    if type(capacity) is float:
        return round(capacity, round_to)

    elif isinstance(capacity, str):
        cap_clean = strip_whitespace(capacity)

        if cap_clean.find("-") > 0:
            cap_clean_components = cap_clean.split("-")
            cap_clean = cap_clean_components.pop()
            return clean_capacity(cap_clean)

        if cap_clean.find("/") > 0:
            cap_clean_components = cap_clean.split("/")
            cap_clean = cap_clean_components.pop()
            return clean_capacity(cap_clean)

        if cap_clean == "":
            return None

        # funky values in spreadsheet
        cap_clean = cap_clean.replace(",", ".")
        return round(float(cap_clean), round_to)

    elif type(capacity) == int:
        return round(float(capacity), round_to)

    elif type(capacity) is not float:
        if capacity is None:
            return None

        raise Exception(f"Capacity clean of type {type(capacity)} not supported: {capacity}")

    if cap_clean is None:
        return None

    cap_clean = round(cap_clean, round_to)

    return cap_clean
