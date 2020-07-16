import re

__id_unit_regex = re.compile(r"^(Y|C)[0-9]{1,3}")

__id_duid_regex = re.compile(r"[A-Z0-9]{1,6}")


STRIP_WORDS = [
    "wind farm",
    "solar farm",
    "farm",
    "power station",
    "ltd",
    "pty",
    "unit",
    "gas",
    "turbine",
]


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

    return name_normalized


def station_name_cleaner(facility_name):
    __n = facility_name or ""

    if type(facility_name) is str:
        __n = facility_name.strip()
    else:
        __n = str(facility_name)

    # @todo check has duid / unit other

    __n = __n.lower()

    for strip_word in STRIP_WORDS:
        __n = __n.replace(" {}".format(strip_word), "")

    __n = __n.title()

    return __n


def participant_name_filter(participant_name):
    _p = participant_name.strip().replace("Pty Ltd", "").replace("Ltd", "")

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
