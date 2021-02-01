#!/usr/bin/env python
"""
Refresh database script

"""

from opennem.db.tasks import refresh_material_views, refresh_timescale_views

refresh_timescale_views(all=True)
refresh_material_views()
