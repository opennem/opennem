#!/usr/bin/env python
"""
Script to run the CMS updates report
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import opennem modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from opennem.cms.updates import send_cms_updates_slack_report


async def main():
    """Run the CMS updates report"""
    await send_cms_updates_slack_report()


if __name__ == "__main__":
    asyncio.run(main())
