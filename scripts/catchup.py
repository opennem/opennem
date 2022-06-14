#!/usr/bin/env python
"""
catchup manual script
"""
from opennem.api.export.tasks import export_energy
from opennem.controllers.nem import store_aemo_tableset
from opennem.core.parsers.aemo.mms import parse_aemo_urls
from opennem.workers.aggregates import run_aggregates_all
from opennem.workers.energy import run_energy_update_days
from opennem.workers.gap_fill.energy import run_energy_gapfill


def run_catchup() -> None:
    urls = [
        # "http://www.nemweb.com.au/Reports/CURRENT/Next_Day_Actual_Gen/PUBLIC_NEXT_DAY_ACTUAL_GEN_20220526_0000000363995082.zip",
        # "http://www.nemweb.com.au/Reports/CURRENT/Next_Day_Actual_Gen/PUBLIC_NEXT_DAY_ACTUAL_GEN_20220527_0000000364099030.zip",
        # "http://nemweb.com.au/Reports/Current/Next_Day_Dispatch/PUBLIC_NEXT_DAY_DISPATCH_20220526_0000000363995086.zip",
        # "http://nemweb.com.au/Reports/Current/Next_Day_Dispatch/PUBLIC_NEXT_DAY_DISPATCH_20220527_0000000364099034.zip",
        "https://www.nemweb.com.au/Reports/ARCHIVE/Dispatch_SCADA/PUBLIC_DISPATCHSCADA_20220524.zip",
        "https://www.nemweb.com.au/Reports/ARCHIVE/Dispatch_SCADA/PUBLIC_DISPATCHSCADA_20220525.zip",
        "https://www.nemweb.com.au/Reports/ARCHIVE/Dispatch_SCADA/PUBLIC_DISPATCHSCADA_20220526.zip",
        "https://www.nemweb.com.au/Reports/ARCHIVE/Dispatch_SCADA/PUBLIC_DISPATCHSCADA_20220527.zip",
        "https://www.nemweb.com.au/Reports/ARCHIVE/Dispatch_SCADA/PUBLIC_DISPATCHSCADA_20220528.zip",
    ]
    # ts = parse_aemo_urls(urls)
    # store_aemo_tableset(ts)
    # run_energy_gapfill(days=30)
    run_energy_gapfill(days=7)
    run_energy_update_days(days=7)
    export_energy(latest=False)


if __name__ == "__main__":
    run_catchup()
