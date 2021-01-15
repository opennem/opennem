#!/usr/bin/env python
"""
Srapyd control script

"""
import sys

from opennem.utils.scrapyd import job_schedule_all

if __name__ == "__main__":
    job_schedule_all(sys.argv[1])
