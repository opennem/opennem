from functools import wraps
from typing import Dict, List, Optional

from expiringdict import ExpiringDict

from opennem.api.stats.schema import ScadaDateRange
from opennem.schema.network import NetworkSchema

CACHE_AGE = 60 * 15

scada_cache = ExpiringDict(max_len=100, max_age_seconds=CACHE_AGE)


def cache_scada_result(func):
    @wraps(func)
    def _cache_scada_wrapper(
        network: Optional[NetworkSchema] = None,
        networks: Optional[List[NetworkSchema]] = None,
        network_region: Optional[str] = None,
    ):
        key_list = [network.code]

        # if network_region:
        #     if hasattr(network_region, "code"):
        #         key_list.append(network_region.code)
        #     else:
        #         key_list.append(network_region)

        if networks:
            key_list += [n.code for n in networks]

        key = frozenset(key_list)

        try:
            _val: Dict = scada_cache[key]
            ret: ScadaDateRange = ScadaDateRange(**_val)
            return ret
        except KeyError:
            ret: ScadaDateRange = func(network, networks, network_region)
            scada_cache[key] = ret.dict()
            return ret

    return _cache_scada_wrapper
