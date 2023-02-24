import logging
import re

from pydantic import BaseModel

from opennem.core.unit_single import facility_unit_numbers_are_single

logger = logging.getLogger(__name__)

__is_number = re.compile(r"^\d+$")

__is_single_number = re.compile(r"^\d$")

__is_unit_alias = re.compile(r"([A-Z|a-z]{1,6})")

__is_unit_alias_forced = re.compile(r"([A-Z|a-z]{1,6}\d{1,2})")

__unit_range_parse = re.compile(r"(\d+)\-(\d+)")


class UnitSchema(BaseModel):
    # The unit id
    id: int = 1

    # The unit alias
    alias: str | None = None

    # The number of units
    number: int = 1

    capacity: int | None


def is_number(v: str) -> bool:
    return bool(re.match(__is_number, v))


def is_single_number(v: str) -> bool:
    return bool(re.match(__is_single_number, v))


# Has a unit alias like A or GT
def unit_has_alias(v: str) -> bool:
    return bool(re.search(__is_unit_alias, v))


def unit_has_alias_forced(v: str) -> bool:
    return bool(re.search(__is_unit_alias_forced, v))


def strip_whitespace(v: str) -> str:
    return str(re.sub(r"\s+", "", v.strip()))


def parse_unit_duid(unit_input: str, unit_duid: str) -> UnitSchema:
    return parse_unit_number(unit_input, facility_unit_numbers_are_single(unit_duid))


def parse_unit_number(unit_input: str, force_single: bool = False) -> UnitSchema:
    """
    Parses unit number string into a UnitSchema model

    force_single is a hack for units like Hallett where "GT 2-4" means
    unit alias GT2-4 rather than alias GT with id 2 and 2 units

    AEMO put a unit no in sometimes when they mean a unit ID (ie. 8) and
    sometimes it means the number of units (ie. 40)
    """
    unit_id = 1
    unit_no = 0
    unit_alias = None

    has_alias = False

    if unit_input is None:
        unit_input = ""

    # Normalize to string
    if type(unit_input) is not str:
        unit_input = str(unit_input)

    # Strip whitespace and capitalize
    unit_input = strip_whitespace(unit_input)
    unit_input = unit_input.upper()

    if unit_input == "":
        unit_input = "1"

    # @TODO handle the silly multi unit lines
    if "," in unit_input:
        uc = unit_input.split(",")

        # This is a bit of a hack - we use the first unit and
        # count the additionals as extra unit numbers. It works
        # for now
        unit_input = uc[0]
        uc = uc[1:]
        unit_no += len(uc)

        for unit_component in uc:
            if "&" in unit_component:
                unit_no += 1

    if "&" in unit_input:
        unit_no += len(unit_input.split("&"))

    if force_single and unit_has_alias_forced(unit_input):
        has_alias = True

        # extract the unit alias
        unit_alias_search = re.search(__is_unit_alias_forced, unit_input)

        if unit_alias_search and unit_alias_search.lastindex == 1:
            unit_alias = unit_alias_search.group(1)

        if not unit_alias or type(unit_alias) is not str:
            raise Exception(f"Error extracting alias from {unit_input}: Got {unit_alias}")

        # remove the unit alias
        unit_input = re.sub(r"[A-Za-z]{1,6}\d{1,2}\-", "", unit_input)

    if not has_alias and unit_has_alias(unit_input):
        has_alias = True

        # extract the unit alias
        unit_alias_search = re.search(__is_unit_alias, unit_input)

        if unit_alias_search and unit_alias_search.lastindex == 1:
            unit_alias = unit_alias_search.group(1)

        if not unit_alias or type(unit_alias) is not str:
            raise Exception(f"Error extracting alias from {unit_input}: Got {unit_alias}")

        # remove the unit alias
        unit_input = re.sub(r"[A-Za-z\ ]", "", unit_input)

    # Simple single number matches
    if is_number(unit_input):
        unit_id = int(unit_input)
        unit_no += 1

        # This is the crazy hack for when AEMO mix unit_no and unit_id
        # in the same field
        if unit_id > 8:
            unit_id = 1
            unit_no = unit_id

    # Range matches (ex. 1-50)
    unit_range_match = re.search(__unit_range_parse, unit_input)

    if unit_range_match and unit_range_match.lastindex == 2:
        unit_id = int(unit_range_match.group(1))
        unit_max = int(unit_range_match.group(2))

        if unit_max < unit_id:
            raise Exception(f"Invalid max unit number {unit_max} on id {unit_id} for range {unit_input}")

        unit_no += unit_max - unit_id + 1

    unit = UnitSchema(
        id=unit_id,
        number=unit_no,
        alias=unit_alias,
    )

    return unit
