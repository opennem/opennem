"""
View utils

"""


def format_offset(offset: str) -> str:
    """Format an offset interval"""
    # @TODO check valid intervals?
    return "INTERVAL '{}'".format(offset)
