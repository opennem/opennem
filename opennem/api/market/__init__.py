"""
Market data module for OpenNEM API.

This module handles market-specific metrics like price and demand.
These metrics are queried and returned separately from facility data
as they don't support the same grouping capabilities.
"""

from opennem.api.market.router import router
from opennem.api.market.schema import MarketMetric, MarketTimeSeries

__all__ = ["router", "MarketMetric", "MarketTimeSeries"]
