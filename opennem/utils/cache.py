"""
OpenNEM cache utilities

"""

import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from cachetools import TTLCache

from opennem.api.stats.schema import ScadaDateRange
from opennem.schema.network import NetworkSchema

logger = logging.getLogger(__name__)

CACHE_AGE = 60 * 2

scada_cache: TTLCache = TTLCache(maxsize=100, ttl=CACHE_AGE)


def cache_scada_result(func: Callable[..., Awaitable[ScadaDateRange]]) -> Callable[..., Awaitable[ScadaDateRange]]:
    """
    Caches the scada_range results in memory since they're called so often
    by wrapping the function.
    """

    @wraps(func)
    async def _cache_scada_wrapper(
        network: NetworkSchema | None = None,
        networks: list[NetworkSchema] | None = None,
        network_region: str | None = None,
        facilities: list[str] | None = None,
        energy: bool = False,
    ) -> ScadaDateRange:
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
            _val: dict[str, Any] = scada_cache[key]
            ret = ScadaDateRange(**_val)

            logger.debug(f"scada range HIT at key: {key}")

            return ret
        except KeyError:
            ret = await func(network, networks, network_region, facilities, energy)
        except Exception as e:
            logger.error(f"Error in cache_scada_result: {e}")

        logger.debug(f"scada range MISS at key: {key}")

        if ret:
            scada_cache[key] = ret.dict()

        if not isinstance(ret, ScadaDateRange):
            raise Exception(f"Invalid return type for scada range: {ret}")

        return ret

    return _cache_scada_wrapper
