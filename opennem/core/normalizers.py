"""
OpenNEM Normalization Module

This module provides a set of utilities to normalize, clean and parse passed
in data from various sources.

"""
import itertools
import logging
import re
from decimal import Decimal
from typing import Dict, List, Optional, Union

from opennem.core.station_names import station_map_name

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
    )
)

# Stores translation table for accent chars
_ACCENT_TRANSLATION = str.maketrans(_ACCENT_REPLACE_MAP)

# Custom normalizers

__match_twitter_handle = re.compile(r"^@?[A-Za-z\_]{1,15}$")


def validate_twitter_handle(twitter_handle: str) -> Optional[re.Match]:
    """Validate a twitter handle. Optional @, length up to 15 characters"""
    return re.match(__match_twitter_handle, twitter_handle)


# Number normalizers

__is_number = re.compile(r"^[\d\.]+$")
__is_single_number = re.compile(r"^\d$")


def is_number(value: Union[str, int]) -> bool:
    if type(value) is int:
        return True

    value = str(value).strip()

    if re.match(__is_number, value):
        return True

    return False


def is_single_number(value: Union[str, int]) -> bool:
    value = str(value).strip()

    if re.match(__is_single_number, value):
        return True
    return False


def clean_float(number: Union[str, int, float]) -> Optional[float]:
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
    logger.warn("normalize_string is deprecated")
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


# OpenNEM specific normalizers


def normalize_aemo_region(region_code: str = "") -> str:
    """Alias for string to upper"""
    logger.warn("normalize_aemo_region is going to be deprecated")
    return string_to_upper(region_code)


def string_is_equal_case_insensitive(subject: str, value: str) -> bool:
    """Case insensitive string is equal"""
    return subject.strip().lower() == value.strip().lower()


def normalize_duid(duid: Optional[str]) -> str:
    """Take what is supposed to be a DUID and clean it up so we always return a string, even if its blank"""
    duid = duid or ""

    # @TODO replace with regexp that removes junk
    duid = duid.strip()

    if duid == "-":
        return ""

    return duid


def name_normalizer(name: str) -> str:
    name_normalized = ""

    if name and type(name) is str:
        name_normalized = name.strip()

    name_normalized = re.sub(r"\-", "", name_normalized)

    return str(name_normalized)


# Station name cleaner


def clean_station_numbers_to_string(part: Union[str, int]) -> str:
    """
    Clean the number part of a station name and remove it completely if its a large number
    """
    if not is_number(part):
        return str(part)

    part_parsed = int(part)

    if part_parsed < 6:
        return str(part_parsed)

    return ""


def strip_words_from_sentence(subject: str, strip_words: List[str] = STRIP_WORDS) -> str:
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


def station_name_run_replacements(
    subject: str, replacement_map: Dict[str, str] = STATION_WORD_REPLACEMENTS
) -> str:
    """Run a string replacement map over a string - note that it's case sensitive"""
    for subject_string, replacement_string in replacement_map.items():
        if subject_string in subject:
            subject = subject.replace(subject_string, replacement_string)

    return subject


def skip_clean_for_matching(
    subject: str, skip_matches: List[str] = STATION_SKIP_CLEANING_MATCHES
) -> bool:
    """Skip station cleaning for those matching"""
    for skip_match in skip_matches:
        if skip_match.lower() in subject.lower():
            return True

    return False


def station_name_cleaner(station_name: str) -> str:
    """Refactred version of the station name cleaner. Cleans up station names prior to applying
    any manual mappings"""

    # Clean it up all in lower case
    station_clean_name = station_name

    # Exit early if we already map
    if station_map_name(station_clean_name) != station_clean_name:
        return station_map_name(station_clean_name)

    if skip_clean_for_matching(station_clean_name):
        return station_clean_name

    # List of cleaning methods to pass the string through
    for clean_func in [
        str.strip,
        str.lower,
        strip_double_spaces,
        strip_encoded_non_breaking_spaces,
        strip_capacity_from_string,
        strip_non_alpha_characters_from_string,
        strip_words_from_sentence,
        strip_double_spaces,
        str.strip,
    ]:
        station_clean_name = clean_func(station_clean_name)  # type: ignore

    # Exit early if we already map
    if station_map_name(station_clean_name) != station_clean_name:
        return station_map_name(station_clean_name)

    # Split the name up into parts and go through each one
    name_components = [str(i) for i in station_clean_name.strip().split(" ")]
    name_components_parsed: List[str] = []

    for _comp in name_components:
        comp: Optional[str] = str(_comp)

        if not comp:
            continue

        if not isinstance(comp, str):
            comp = ""

        if comp in STRIP_WORDS:
            comp = ""

        if comp in ACRONYMS:
            comp = comp.upper()
        elif isinstance(comp, str) and comp.startswith("mc"):
            comp = "Mc" + comp[2:].capitalize()
        elif isinstance(comp, str) and comp != "":
            comp = comp.capitalize()

        # strip numbers greater than 5
        if comp:
            comp = clean_station_numbers_to_string(comp)

        name_components_parsed.append(comp)

    # Join the name back up
    station_clean_name = " ".join(name_components_parsed)

    # List of cleaning methods to pass the string through
    for clean_func in [
        str.strip,
        str.lower,
        strip_double_spaces,
        string_to_title,
        clean_and_format_slashed_station_names,
        station_name_run_replacements,
    ]:
        station_clean_name = clean_func(station_clean_name)  # type: ignore

    # Exit if we map
    if station_map_name(station_clean_name) != station_clean_name:
        return station_map_name(station_clean_name)

    return station_clean_name


def _old_station_name_cleaner(facility_name: str) -> str:
    """ "
    This cleans station names from their messy as hell AEMO names to something
    we can plug into name_clean and humans can actually read

    It's a bit of a mess and could use a refactor


    """
    name_clean = facility_name or ""

    if type(facility_name) is str:
        name_clean = facility_name.strip()
    else:
        name_clean = str(facility_name).strip()

    # @todo check has duid / unit other

    name_clean = name_clean.lower()

    # @TODO replace with the re character stripped - this is unicode junk
    name_clean = name_clean.replace("\u00a0", " ")

    if station_map_name(name_clean) != name_clean:
        return station_map_name(name_clean)

    # strip units from name
    name_clean = re.sub(r"\d+\ ?(mw|kw|MW|KW)", "", name_clean)

    # strip other chars
    name_clean = re.sub(r",|-|\(|\)|\–|\"|\'", "", name_clean)
    # name_clean = re.sub(r"(\W|\ )+", "", name_clean)

    name_clean = re.sub(" +", " ", name_clean)

    name_clean = name_clean.replace("yalumba winery", "yalumba")
    name_clean = name_clean.replace("university of melbourne", "uom")

    # @TODO remove these hard codes
    if name_clean not in ["barcaldine solar farm", "Darling Downs Solar Farm"]:
        for w in STRIP_WORDS:
            if name_clean.startswith("todae solar") and w in ["solar"]:
                continue

            if " " in w:
                name_clean = name_clean.replace(w, "")

    name_components = [str(i) for i in name_clean.strip().split(" ")]
    name_components_parsed = []

    for _comp in name_components:
        comp: Optional[str] = str(_comp)

        if not comp:
            continue

        comp = comp.strip()
        comp = re.sub(r",|-|\(|\)|\–", "", comp)

        if type(comp) is not str:
            comp = None

        if comp == "":
            comp = None

        if comp in STRIP_WORDS:
            comp = None

        if comp in ACRONYMS:
            comp = comp.upper()
        elif type(comp) is str and comp.startswith("mc"):
            comp = "Mc" + comp[2:].capitalize()
        elif type(comp) is str and comp != "":
            comp = comp.capitalize()

        # strip numbers greater than 5
        comp_clean = clean_station_numbers_to_string(comp)

        if comp_clean:
            comp = comp_clean

        name_components_parsed.append(comp)

    if name_components_parsed[0] == "uom":
        name_components_parsed = name_components_parsed[:-1]

    name_clean = " ".join([str(i) for i in name_components_parsed if i is not None])

    name_clean = re.sub(" +", " ", name_clean)

    name_clean = name_clean.strip()

    if "/" in name_clean:
        name_clean = " / ".join([i.strip().title() for i in name_clean.split("/")])

    if station_map_name(name_clean) != name_clean:
        return station_map_name(name_clean)

    # uom special case
    name_clean = name_clean.replace("UOM ", "UoM ")

    # todae special case
    todae_match = re.match(r"^(Todae)\ (.*)", name_clean)
    if todae_match:
        todae_name, todae_rest = todae_match.groups()

        name_clean = "{} ({})".format(todae_rest, todae_name)

    return name_clean


def participant_name_filter(participant_name: str) -> Optional[str]:
    participant_name = strip_whitespace(participant_name)

    _p = participant_name.strip().replace("Pty Ltd", "").replace("Ltd", "").replace("/", " / ")

    _p = re.sub(" +", " ", _p).strip()

    _p = _p.strip()

    if _p == "":
        return None

    return _p


def clean_capacity(capacity: Union[str, int, float], round_to: int = 6) -> Optional[float]:
    """
    Takes a capacity and cleans it up into a float

    @TODO support unit conversion
    """
    cap_clean = None

    if capacity is None:
        return None

    # Type gating float, string, int, others ..
    if type(capacity) is float:
        cap_clean = capacity

    elif isinstance(capacity, str):
        cap_clean = strip_whitespace(capacity)

        if "-" in cap_clean:
            cap_clean_components = cap_clean.split("-")
            cap_clean = cap_clean_components.pop()
            return clean_capacity(cap_clean)

        if "/" in cap_clean:
            cap_clean_components = cap_clean.split("/")
            cap_clean = cap_clean_components.pop()
            return clean_capacity(cap_clean)

        if cap_clean == "":
            return None

        # funky values in spreadsheet
        cap_clean = cap_clean.replace(",", ".")
        cap_clean = float(cap_clean)

    elif type(capacity) == int:
        cap_clean = float(capacity)

    elif type(capacity) is not float:
        if capacity is None:
            return None

        raise Exception(
            "Capacity clean of type {} not supported: {}".format(type(capacity), capacity)
        )

    if cap_clean is None:
        return None

    cap_clean = round(cap_clean, round_to)

    return cap_clean
