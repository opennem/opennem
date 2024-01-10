"""
OpenNEM Normalization Module

This module provides a set of utilities to normalize, clean and parse passed
in data from various sources.

"""
import itertools
import logging
import re
from decimal import Decimal
from re import Pattern

logger = logging.getLogger("opennem.core.normalizers")

# Words that are stripped out of station names
STRIP_WORDS = [
    "stage 1",
    "stage 2",
    "stage 3",
    "stage 4",
    "stage 5",
    "phase 1",
    "phase 2",
    "phase 3",
    "phase 4",
    "phase 5",
    "energy facility",
    "coal mine",
    "nett off",
    "renewable energy facility",
    "waste disposal facility",
    "network support station",
    "combined cycle",
    "green power hub units",
    "unit 1",
    "wind and solar",
    "streams station",
    "utilisation facility",
    "gas turbines",
    "stockland development",
    "backup generation",
    "gas turbine",
    "mini hydro",
    "power hub",
    "wastewater treatment",
    "water treatment",
    "wind farm",
    "solar park",
    "solar farm",
    "solar system",
    "power station",
    "bio reactor",
    "biogas",
    "generation station",
    "sydney",
    "cogeneration",
    "kograh",
    "technologies",
    "biomass",
    "site",
    "project",
    "landfill",
    "wwt",
    "waste",
    "ltd",
    "agl",
    "pty",
    "units",
    "unit",
    "gas",
    "filtration",
    "hydro",
    "diesel",
    "turbine",
    "system",
    "plant",
    "battery",
    "g1",
    "farm",
    "1",
    "sv",
    "sf",
    "pe",
    "pf",
    "pv",
    "ps",
    "solar",
    "storage",
    "wind",
    "ccgt",
    "renewable",
    "water",
    "lfg",
    "nsw",
    "vic",
    "qld",
    "sa",
    "dhl6",
    "run of river",
    "and",
    "bess",
    "bess1",
    "h2e",
    "gen",
    "gt",
    "bioreactor",
    "bordertown",
    "winery",
]

# Words that are acronyms and should be uppercased
ACRONYMS = [
    "cec",
    "bhp",
    "rsl",
    "csu",
    "dhp",
    "stp",
    "wtp",
    "hvdc",
    "scs",
    "sips",
    "jv",
    "gt",
    "lmcc",
    "sa",
    "vpp",
    "fpc",
    "cd",
    "ab",
    "stp",
    "krc",
    "h2e",
    "jl",
    "uom",
    "agl",
    "nawma",
]

# replacemnt words for stations
STATION_WORD_REPLACEMENTS = {"University Of Melbourne": "UoM"}

# skip station cleaning for any station matching
STATION_SKIP_CLEANING_MATCHES = ["Hallett"]

# Dictionary map of accented chars to their A-Z equivelants
_ACCENT_REPLACE_MAP = dict(
    zip(
        "ÂÃÄÀÁÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖŐØŒÙÚÛÜŰÝÞßàáâãäåæçèéêëìíîïðñòóôõöőøœùúûüűýþÿ",
        itertools.chain(
            "AAAAAA",
            ["AE"],
            "CEEEEIIIIDNOOOOOOO",
            ["OE"],
            "UUUUUY",
            ["TH", "ss"],
            "aaaaaa",
            ["ae"],
            "ceeeeiiiionooooooo",
            ["oe"],
            "uuuuuy",
            ["th"],
            "y",
        ),
        strict=False,
    )
)

# Stores translation table for accent chars
_ACCENT_TRANSLATION = str.maketrans(_ACCENT_REPLACE_MAP)

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


def clean_float(number: str | int | float) -> float | None:
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

    return None


# Whitespace normalizers


def strip_whitespace(subject: str) -> str:
    return str(re.sub(r"\s+", "", subject.strip()))


def strip_most_punctuation(subject: str) -> str:
    """Removes most puncuation from a string"""
    return re.sub(r"[\(\)#\$!_\?\s\@]+", "", subject)


def strip_special_chars(subject: str) -> str:
    """Strip out most special chars

    @TODO this requires unit tests
    """
    return str(re.sub(r"[\s]+", "", subject.strip()))


def normalize_whitespace(subject: str) -> str:
    return str(re.sub(r"\s{2,}", " ", subject.strip()))


def strip_double_spaces(subject: str) -> str:
    """Strips double spaces back to spaces"""
    return re.sub(" +", " ", subject)


def string_to_upper(subject: str = "") -> str:
    """Strips and uppercases strings. Used for ID's"""
    subject_clean = subject.strip().upper()

    return subject_clean


# String normalizers

__urlsafe_match = re.compile(r"^[a-zA-Z0-9_-]*$")


def is_lowercase(subject: str) -> bool:
    return subject.lower() == subject


def is_uppercase(subject: str) -> bool:
    return subject.upper() == subject


def strip_and_lower_string(subject: str) -> str:
    return subject.strip().lower()


def string_to_title(subject: str) -> str:
    """Title case and clean string"""
    return str(subject).strip().title()


def normalize_string(subject: str) -> str:
    """Deprecated function alias"""
    logger.warning("normalize_string is deprecated")
    return string_to_title(subject)


def replace_accented(subject: str) -> str:
    """Replaces accented characters in a string to their A-Z equiv. ex ñ => n"""
    return subject.translate(_ACCENT_TRANSLATION)


def strip_encoded_non_breaking_spaces(subject: str) -> str:
    return subject.replace("\u00a0", "")


def strip_capacity_from_string(subject: str) -> str:
    return re.sub(r"\d+\ ?(mw|kw|MW|KW)", "", subject)


def strip_non_alpha_characters_from_string(subject: str) -> str:
    """Strips punctuation, brackets, etc."""
    return re.sub(r",|-|\(|\)|\–|\"|\'", "", subject)


def string_is_urlsafe(subject: str) -> bool:
    """Check if a string is URL safe"""
    return isinstance(re.match(__urlsafe_match, subject), re.Match)


def stem(word: str) -> str:
    """Get the stem of a word"""
    return word.lower().rstrip(",.!:;'-\"").lstrip("'\"")


def clean_sentence(sentence: str) -> str:
    """Method to clean up a sentence into word stems"""
    sentence_parts = sentence.strip().split()

    sentence_parts_stemmed = map(stem, sentence_parts)

    sentence_reformed = "".join(sentence_parts_stemmed)

    return sentence_reformed


# Case Styles
# convert to/from various cases


def snake_to_camel(string: str) -> str:
    """Converts snake case to camel case. ie. field_name to FieldName"""
    return "".join(word.capitalize() for word in string.split("_"))


def _build_split_re(split_words: list[str]) -> Pattern[str]:
    _regexp_format = ("({})").format("|".join(_SPLIT_WORDS))
    _split_regexp = re.compile(_regexp_format)

    return _split_regexp


_SPLIT_WORDS = ["settlement", "total", "net", "type", "id", "scheduled", "semi", "date"]

_split_words_regexp = _build_split_re(_SPLIT_WORDS)


def capitalized_block_to_words(string: str) -> list[str]:
    """Converts capitalized block words into a list so it can be rejoined"""
    subject: str = string

    for clean_func in [str.strip, str.lower, strip_whitespace, strip_most_punctuation]:
        subject = clean_func(subject)  # type: ignore

    _split_result = re.split(_split_words_regexp, subject)
    rejoined_word = [i for i in _split_result if i]

    return rejoined_word


def blockwords_to_snake_case(subject: str) -> str:
    _wordlist = capitalized_block_to_words(subject)

    return "_".join(_wordlist)


# OpenNEM specific normalizers


def normalize_aemo_region(region_code: str = "") -> str:
    """Alias for string to upper"""
    logger.warning("normalize_aemo_region is going to be deprecated")
    return string_to_upper(region_code)


def string_is_equal_case_insensitive(subject: str, value: str) -> bool:
    """Case insensitive string is equal"""
    return subject.strip().lower() == value.strip().lower()


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


def name_normalizer(name: str) -> str:
    name_normalized = ""

    if name and type(name) is str:
        name_normalized = name.strip()

    name_normalized = re.sub(r"\-", "", name_normalized)

    return str(name_normalized)


# Station name cleaner


def clean_station_numbers_to_string(part: str | int) -> str:
    """
    Clean the number part of a station name and remove it completely if its a large number
    """
    if not is_number(part):
        return str(part)

    if isinstance(part, float) or part.find(".") > 0:
        return str(part)

    part_parsed = int(part)

    if part_parsed < 6:
        return str(part_parsed)

    return ""


def strip_words_from_sentence(subject: str, strip_words: list[str] = STRIP_WORDS) -> str:
    for w in strip_words:
        if f" {w}" in subject:
            subject = subject.replace(f" {w}", " ")

        if " " in w:
            subject = subject.replace(w, " ")

    return subject


def clean_and_format_slashed_station_names(subject: str) -> str:
    """Cleans up slashed station names like Name / Name"""
    if "/" in subject:
        subject = " / ".join([i.strip().title() for i in subject.split("/")])

    return subject


def station_name_run_replacements(subject: str, replacement_map: dict[str, str] = STATION_WORD_REPLACEMENTS) -> str:
    """Run a string replacement map over a string - note that it's case sensitive"""
    for subject_string, replacement_string in replacement_map.items():
        if subject_string in subject:
            subject = subject.replace(subject_string, replacement_string)

    return subject


def strip_station_name_numbering(sub: str) -> str:
    """Strips end of names like 'Sydney No 3' to just 'Sydney'.

    @NOTE Not all manipulation is done in lower case."""
    return re.sub(r" No ?\d?$", "", sub)


def station_name_hyphenate(sub: str) -> str:
    """Hyphenates names like 'Dapto to Wollongong' as 'Dapto-Wollongong'."""
    return re.sub(r"\ To\ ", "-", sub, re.IGNORECASE)


def skip_clean_for_matching(subject: str, skip_matches: list[str] = STATION_SKIP_CLEANING_MATCHES) -> bool:
    """Skip station cleaning for those matching"""
    for skip_match in skip_matches:
        if skip_match.lower() in subject.lower():
            return True

    return False


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
