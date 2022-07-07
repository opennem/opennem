#!/usr/bin/env/python
from opennem.utils.http import attach_proxy, http


def run_req() -> None:
    """ """
    req = attach_proxy(http)
    url = "http://lumtest.com/myip.json"

    resp = req.get(url)

    print(resp.json())


if __name__ == "__main__":
    run_req()
