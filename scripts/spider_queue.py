#!/usr/bin/env python
"""
Srapyd control script

"""


from opennem.utils.scrapyd import job_schedule_all

if __name__ == "__main__":
    job_schedule_all("latest")
