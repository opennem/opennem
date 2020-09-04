from functools import reduce
from typing import List, Optional

from opennem.core.normalizers import is_single_number


def getcommonletters(strlist):
    return "".join(
        [
            x[0]
            for x in zip(*strlist)
            if reduce(lambda a, b: (a == b) and a or None, x)
        ]
    )


def findcommonstart(strlist):
    strlist = strlist[:]
    prev = None
    while True:
        common = getcommonletters(strlist)
        if common == prev:
            break
        strlist.append(common)
        prev = common

    return getcommonletters(strlist)


def station_code_from_duids(duids: List[str]) -> Optional[str]:
    """
        Derives a station code from a list of duids

        ex.

        BARRON1,BARRON2 => BARRON
        OSBAG,OSBAG => OSBAG

    """
    if type(duids) is not list:
        return None

    if not duids:
        return None

    if len(duids) == 0:
        return None

    duids_uniq = list(set(duids))

    common = findcommonstart(duids_uniq)

    if not common:
        return None

    # strip last character if we have one
    if is_single_number(common[-1]):
        common = common[:-1]

    if common.endswith("_"):
        common = common[:-1]

    if len(common) > 2:
        return common

    return None
