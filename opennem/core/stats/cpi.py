"""
Import and parse CPI stats
"""

from opennem.core.parsers.cpi import stat_au_cpi
from opennem.core.stats.store import store_stats_database

if __name__ == "__main__":
    r = stat_au_cpi()
    store_stats_database(r)
