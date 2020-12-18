#!/usr/bin/env python
from opennem.scheduler import huey

if __name__ == "__main__":
    huey.flush()
    print("Flushed all tasks")
