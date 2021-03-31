"""
OpenNEM cache utilities

"""
import logging
from functools import wraps
from typing import Callable, Dict, List, Optional

from cachetools import TTLCache

from opennem.api.stats.schema import ScadaDateRange
from opennem.schema.network import NetworkSchema
from opennem.settings import settings

logger = logging.getLogger(__name__)

CACHE_AGE = settings.cache_scada_values_ttl_sec

scada_cache: TTLCache = TTLCache(maxsize=100, ttl=CACHE_AGE)


def cache_scada_result(func: Callable) -> Callable:
    """
    Caches the scada_range results in memory since they're called so often
    by wrapping the function.
    """

    @wraps(func)
    def _cache_scada_wrapper(
        network: Optional[NetworkSchema] = None,
        networks: Optional[List[NetworkSchema]] = None,
        network_region: Optional[str] = None,
        facilities: Optional[List[str]] = None,
    ) -> Optional[ScadaDateRange]:
        key_list = []

        if network:
            key_list = [network.code]

        if networks:
            key_list += [n.code for n in networks]

        if facilities:
            key_list += facilities

        key = frozenset(key_list)
        ret: Optional[ScadaDateRange] = None

        try:
            _val: Dict = scada_cache[key]
            ret = ScadaDateRange(**_val)

            logger.debug("scada range HIT at key: {}".format(key))

            return ret
        except KeyError:
            ret = func(network, networks, network_region, facilities)

            logger.debug("scada range MISS at key: {}".format(key))

            if ret:
                scada_cache[key] = ret.dict()
            return ret

    return _cache_scada_wrapper
