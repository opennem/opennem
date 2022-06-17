""" Utilities for loading modules """

from importlib import import_module
from pkgutil import iter_modules
from typing import List

from opennem.core.crawlers.schema import CrawlerDefinition


def iter_crawler_definitions(module: str):
    """Return an iterator over all spider classes defined in the given module
    that can be instantiated (i.e. which have name)
    """

    for obj in vars(module).values():
        if isinstance(obj, CrawlerDefinition) and getattr(obj, "name", None):
            yield obj


def import_module_from_string(module_name: str) -> None:
    pass


def walk_modules(path: str):
    """Loads a module and all its submodules from the given module path and
    returns them. If *any* module throws an exception while importing, that
    exception is thrown back.
    """

    mods = []
    mod = import_module(path)
    mods.append(mod)
    if hasattr(mod, "__path__"):
        for _, subpath, ispkg in iter_modules(mod.__path__):
            fullpath = path + "." + subpath
            if ispkg:
                mods += walk_modules(fullpath)
            else:
                submod = import_module(fullpath)
                mods.append(submod)

    return mods


def load_all_crawler_definitions(path: str) -> List[CrawlerDefinition]:
    crawler_definitions = []

    try:
        for module in walk_modules(path):
            for crawler_class in iter_crawler_definitions(module):
                crawler_definitions.append(crawler_class)
    except ImportError as e:
        raise Exception("Error importing: {}".format(e))

    return crawler_definitions


if __name__ == "__main__":
    load_all_crawler_definitions("opennem.crawlers")
