"""Inline SVG icon paths for fueltech groups.

SVG files in `opennem/static/fueltech_icons/` are extracted from
openelectricity/src/lib/icons/fuel-techs/*Sm.svelte. They use
currentColor for stroke/fill so they inherit from the parent `color`
attribute (set by `_get_fueltech_icon_svg` in weekly_summary.py).
"""

import re
from pathlib import Path

_ICON_DIR = Path(__file__).parent / "fueltech_icons"


def _load_inner_svg(svg_path: Path) -> str:
    """Read an SVG file and return just the contents between <svg>...</svg>."""
    content = svg_path.read_text()
    match = re.search(r"<svg[^>]*>(.*)</svg>", content, re.DOTALL)
    return match.group(1).strip() if match else content


FUELTECH_ICON_PATHS: dict[str, str] = {svg_path.stem: _load_inner_svg(svg_path) for svg_path in sorted(_ICON_DIR.glob("*.svg"))}

FALLBACK_ICON = '<circle cx="8.5" cy="8.5" r="4" fill="currentColor" stroke="none"/>'
