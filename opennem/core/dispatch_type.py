import enum


class DispatchType(enum.Enum):
    GENERATOR = 1
    LOAD = 2


def parse_dispatch_type(dispatch_string: str):
    """
        Converts dispatch type string into an enum constant

    """
    if not dispatch_string:
        return None

    dispatch_string = dispatch_string.lower().strip()

    if dispatch_string == "load":
        return DispatchType.LOAD

    if dispatch_string == "generating":
        return DispatchType.GENERATOR

    if dispatch_string == "generator":
        return DispatchType.GENERATOR

    raise Exception("Unknown dispatch type: {}".format(dispatch_string))
