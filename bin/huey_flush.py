#!/usr/bin/env python
""" Flush all tasks from huey """
from opennem.workers.scheduler import huey

huey.flush()
huey.revoke_all(huey.task, revoke_once=True)
