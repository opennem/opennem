"""
View utils

"""

from typing import List, Optional

_INDEX_PREFIX = "idx"


def format_offset(offset: str) -> str:
    """Format an offset interval"""
    # @TODO check valid intervals?
    return "INTERVAL '{}'".format(offset)


def get_index_name(table_name: str, keys: Optional[List[str]] = None, unique: bool = False) -> str:
    keys_list = "_".join(keys) if keys else None

    name_components = [
        _INDEX_PREFIX,
        table_name,
        keys_list,
        "unique" if unique else "",
    ]

    index_name = "_".join([i for i in name_components if i])

    return index_name
