import re
from decimal import Decimal
from typing import Optional, Union

from opennem.core.station_names import station_map_name

__id_unit_regex = re.compile(r"^(Y|C)[0-9]{1,3}")

__id_duid_regex = re.compile(r"[A-Z0-9]{1,6}")


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
    "power",
    "farm",
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
    "h2e",
    "bess1",
    "gen",
    "gt",
    "bioreactor",
    "bordertown",
]

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


__is_number = re.compile(r"^[\d\.]+$")
__is_single_number = re.compile(r"^\d$")

# @TODO put all these helpers in utils/


def strip_whitespace(subject: str) -> str:
    return str(re.sub(r"\s+", "", subject.strip()))


def normalize_whitespace(subject: str) -> str:
    return str(re.sub(r"\s{2,}", " ", subject.strip()))


def is_number(value: Union[str, int]) -> bool:
    if type(value) is int:
        return True

    value = str(value).strip()

    if re.match(__is_number, value):
        return True

    return False


def is_single_number(value: Union[str, int]) -> bool:
    if re.match(__is_single_number, value):
        return True
    return False


# @TODO not yet implemented
def id_unit(facility_name: str) -> str:
    __n = facility_name

    return __n


# @TODO not yet implement
def id_duid(facility_name: str) -> str:
    __n = facility_name

    return __n


def normalize_aemo_region(region_code: str = "") -> str:
    region_code = region_code.strip().upper()

    return region_code


def normalize_duid(duid: str) -> str:
    duid = duid or ""

    # @TODO replace with regexp that removes junk
    duid = duid.strip()

    if duid == "-":
        return ""

    return duid


def normalize_string(csv_string: str) -> str:
    if not type(csv_string) is str:
        csv_string = str(csv_string)

    csv_string = csv_string.strip().title()

    return csv_string


def name_normalizer(name: str) -> str:
    name_normalized = ""

    if name and type(name) is str:
        name_normalized = name.strip()

    name_normalized = re.sub(r"\-", "", name_normalized)

    return str(name_normalized)


def stem(word: str) -> str:
    """Get the stem of a word"""
    return word.lower().rstrip(",.!:;'-\"").lstrip("'\"")


def clean_sentence(sentence: str) -> str:
    """Method to clean up a sentence into word stems"""
    sentence_parts = sentence.strip().split()

    sentence_parts_stemmed = map(stem, sentence_parts)

    sentence_reformed = "".join(sentence_parts_stemmed)

    return sentence_reformed


def is_lowercase(subject: str) -> bool:
    return subject.lower() == subject


def is_uppercase(subject: str) -> bool:
    return subject.upper() == subject


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


def clean_numbers(part: Union[str, int]) -> Union[str, int, None]:
    """
    Clean the number part of a station name

    """
    if not is_number(part):
        return part

    part_parsed = int(part)

    if part_parsed < 6:
        return part_parsed

    return None


def station_name_cleaner(facility_name: str) -> str:
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
        comp_clean = clean_numbers(comp)

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

    elif type(capacity) == str:
        cap_clean = strip_whitespace(capacity)

        if "-" in cap_clean:
            cap_clean_components = cap_clean.split("-")
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
