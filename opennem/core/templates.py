"""
Render Mako Templates
"""

from pathlib import Path

from mako.lookup import TemplateLookup


def _get_template_dir() -> str:
    _module_root = Path(__file__).parent.parent / "templates"

    if not _module_root.exists():
        raise FileNotFoundError(f"Template directory {_module_root} does not exist")

    return str(_module_root)


template_lookup = TemplateLookup(directories=[_get_template_dir()], module_directory="/tmp/.mako_modules")


def serve_template(template_name: str, **kwargs) -> str:
    """
    Render a template from the templates directory
    """
    _template = template_lookup.get_template(template_name)

    rendered = _template.render(**kwargs)

    if isinstance(rendered, bytes):
        return rendered.decode("utf-8")

    elif isinstance(rendered, bytearray | memoryview):
        return str(rendered)

    return str(rendered)
