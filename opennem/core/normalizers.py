import re
from typing import Union

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
    "renewable energy facility",
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
    "ltd",
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
    "gen",
    "e",
    "jv",
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
]


__is_number = re.compile(r"^\d+$")
__is_single_number = re.compile(r"^\d$")

# @TODO put all these helpers in utils/

strip_whitespace = lambda v: str(re.sub(r"\s+", "", v.strip()))


def is_number(value: Union[str, int]) -> bool:
    if type(value) is not str:
        value = str(value)

    if re.match(__is_number, value):
        return True

    return False


def is_single_number(value: Union[str, int]) -> bool:
    if re.match(__is_single_number, value):
        return True
    return False


# @TODO not yet implemented
def id_unit(facility_name):
    __n = facility_name

    return __n


# @TODO not yet implement
def id_duid(facility_name):
    __n = facility_name

    return __n


def normalize_duid(duid: str) -> str:
    duid = duid or ""

    # @TODO replace with regexp that removes junk
    duid = duid.strip().replace("-", "")

    if duid == "":
        return None

    return duid


def normalize_string(csv_string) -> str:
    if not type(csv_string) is str:
        csv_string = str(csv_string)

    csv_string = csv_string.strip().title()

    return csv_string


def name_normalizer(name: str) -> str:
    name_normalized = None

    if name and type(name) is str:
        name_normalized = name.strip()

    name_normalized = re.sub(r"\-", "", name_normalized)

    return str(name_normalized)


def clean_numbers(part) -> int:
    if not is_number(part):
        return part

    part_parsed = int(part)

    if part_parsed < 6:
        return part_parsed

    return None


def station_name_cleaner(facility_name: str) -> str:
    """"
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
    if not name_clean in ["barcaldine solar farm", "Darling Downs Solar Farm"]:
        for w in STRIP_WORDS:
            if name_clean.startswith("todae solar") and w in ["solar"]:
                continue

            if " " in w:
                name_clean = name_clean.replace(w, "")

    name_components = [str(i) for i in name_clean.strip().split(" ")]
    name_components_parsed = []

    for comp in name_components:
        comp = str(comp)
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
        comp = clean_numbers(comp)

        name_components_parsed.append(comp)

    if name_components_parsed[0] == "UOM":
        name_components_parsed = name_components_parsed[:-1]

    name_clean = " ".join(
        [str(i) for i in name_components_parsed if i is not None]
    )

    name_clean = re.sub(" +", " ", name_clean)

    name_clean = name_clean.strip()

    if "/" in name_clean:
        name_clean = " / ".join(
            [i.strip().capitalize() for i in name_clean.split("/")]
        )

    if station_map_name(name_clean) != name_clean:
        return station_map_name(name_clean)

    return name_clean


def participant_name_filter(participant_name: str) -> str:
    participant_name = strip_whitespace(participant_name)

    _p = (
        participant_name.strip()
        .replace("Pty Ltd", "")
        .replace("Ltd", "")
        .replace("/", " / ")
    )

    _p = re.sub(" +", " ", _p).strip()

    return _p.strip()


def clean_capacity(capacity: Union[str, int, float]) -> float:
    cap_clean = capacity

    if type(capacity) is str:
        cap_clean = strip_whitespace(capacity)

        cap_clean = capacity.replace("-", "")

        if cap_clean == "":
            return None

        # funky values in spreadsheet
        cap_clean = cap_clean.replace(",", ".")
        cap_clean = float(cap_clean)

    elif type(capacity) is int:
        cap_clean = float(cap_clean)

    elif type(capacity) is not float:
        raise Exception(
            "Capacity clean of type {} not supported: {}".format(
                type(capacity), capacity
            )
        )

    cap_clean = round(cap_clean, 6)

    return cap_clean
