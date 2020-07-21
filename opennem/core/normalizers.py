import re

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
]


__is_number = re.compile("^\d+$")
__is_single_number = re.compile("^\d$")


def is_number(value):
    if type(value) is not str:
        value = str(value)

    if re.match(__is_number, value):
        return True

    return False


def is_single_number(value):
    if re.match(__is_single_number, value):
        return True
    return False


def id_unit(facility_name):
    __n = facility_name

    return __n


def id_duid(facility_name):
    __n = facility_name

    return __n


def normalize_duid(duid):
    duid = duid or ""

    duid = duid.strip()

    if duid == "-":
        return None

    return duid


def name_normalizer(name):
    name_normalized = None

    if name and type(name) is str:
        name_normalized = name.strip()

    name_normalized = re.sub(r"\-", "", name_normalized)

    return str(name_normalized)


def clean_numbers(part):
    if not is_number(part):
        return part

    part_parsed = int(part)

    if part_parsed < 6 and part_parsed != 1:
        return part_parsed

    return None


def station_name_cleaner(facility_name):
    name_clean = facility_name or ""

    if type(facility_name) is str:
        name_clean = facility_name.strip()
    else:
        name_clean = str(facility_name)

    # @todo check has duid / unit other

    name_clean = name_clean.lower()

    name_clean = name_clean.replace("\u00a0", " ")

    if name_clean.startswith("hornsdale power reserve"):
        return "Hornsdale Power Reserve"

    if name_clean.startswith("swan hill solar farm"):
        return "Swan Hill Solar Farm"

    if name_clean.startswith("redmud green energy"):
        return "Redmud Green Energy"

    # strip units from name
    name_clean = re.sub(r"\d+\ ?(mw|kw|MW|KW)", "", name_clean)

    # strip other chars
    name_clean = re.sub(r",|-|\(|\)|\–", "", name_clean)
    # name_clean = re.sub(r"(\W|\ )+", "", name_clean)

    name_clean = re.sub(" +", " ", name_clean)

    if name_clean == "Darling Downs Solar Farm, Units 144":
        name_clean = "darling downs solar farm"

    if not name_clean in ["barcaldine solar farm", "Darling Downs Solar Farm"]:
        for w in STRIP_WORDS:
            if name_clean.startswith("todae solar") and w in ["solar"]:
                continue

            if " " in w:
                name_clean = name_clean.replace(w, "")

    if name_clean.startswith("government virtual power"):
        name_clean = name_clean.replace("government virtual power", "SA VPP")

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

    name_clean = " ".join(
        [str(i) for i in name_components_parsed if i is not None]
    )

    name_clean = re.sub(" +", " ", name_clean)

    name_clean = name_clean.strip()

    if name_clean.startswith("Bogong / Mackay"):
        name_clean = "Bogong/Mackay"

    if name_clean.startswith("Churchill Abattoir"):
        return "Churchill Abattoir"

    if name_clean.startswith("LMCC Works Depot"):
        return "Lake Macquarie Community"

    return name_clean


def participant_name_filter(participant_name):
    _p = (
        participant_name.strip()
        .replace("Pty Ltd", "")
        .replace("Ltd", "")
        .replace("/", " / ")
    )

    _p = re.sub(" +", " ", _p).strip()

    return _p.strip()


def clean_capacity(capacity):
    cap_clean = capacity

    if type(capacity) is str:
        cap_clean = capacity.replace("-", "")

        if cap_clean == "":
            return None

        # funky values in spreadsheet
        cap_clean = cap_clean.replace(",", ".")

        cap_clean = float(cap_clean)

    return cap_clean
