#!/usr/bin/env python
from time import time

from opennem.controllers.nem import store_aemo_tableset
from opennem.core.parsers.aemo.mms import parse_aemo_mms_csv, parse_aemo_urls

if __name__ == "__main__":
    # @TODO parse into MMS schema
    url = "http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/PUBLIC_DISPATCHSCADA_202204081455_0000000360913773.zip"

    r = parse_aemo_urls([url])
    assert r.has_table("unit_scada"), "has table"

    print("has table and done")

    controller_returns = store_aemo_tableset(r)
