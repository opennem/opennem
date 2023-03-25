"""
Render Mako Templates
"""

from pathlib import Path
from pkgutil import get_loader

from mako.lookup import TemplateLookup

from opennem import settings


def _get_template_dir() -> str:
    _module_root = Path(get_loader("opennem").path).parent / settings.templates_dir

    return str(_module_root)


TEMPLATE_DIR = _get_template_dir()

template_lookup = TemplateLookup(directories=[TEMPLATE_DIR], module_directory="/tmp/.mako_modules")


def serve_template(template_name: str, **kwargs) -> str:
    _template = template_lookup.get_template(template_name)

    return _template.render(**kwargs)
