"""
OpenNEM cache utilities

"""
import logging
from collections.abc import Callable
from functools import wraps

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
        network: NetworkSchema | None = None,
        networks: list[NetworkSchema] | None = None,
        network_region: str | None = None,
        facilities: list[str] | None = None,
        energy: bool = False,
    ) -> ScadaDateRange | None:
        key_list = []

        if network:
            key_list = [network.code]

        if networks:
            key_list += [n.code for n in networks]

        if facilities:
            key_list += facilities

        key_list.append(str(energy))

        key = frozenset(key_list)
        ret: ScadaDateRange | None = None

        try:
            _val: dict = scada_cache[key]
            ret = ScadaDateRange(**_val)

            logger.debug(f"scada range HIT at key: {key}")

            return ret
        except KeyError:
            ret = func(network, networks, network_region, facilities, energy)

            logger.debug(f"scada range MISS at key: {key}")

            if ret:
                scada_cache[key] = ret.dict()
            return ret

    return _cache_scada_wrapper
