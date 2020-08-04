import enum


class DispatchType(enum.Enum):
    GENERATING = 1
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
        return DispatchType.GENERATING

    raise Exception("Unknown dispatch type: {}".format(dispatch_string))
