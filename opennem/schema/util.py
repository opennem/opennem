import re


def first_or_none(values=None):
    if values and type(values) is list and len(values) > 0:
        return values[0]
    return None


def cast_bool(f=None):
    return True if f.lower() in ["true", "1", "yes"] else False


def strip_supressed(f=None):
    return None if f.lower() in ["suppressed"] else f


def strip_schema(f=None):
    return f


def strip_spaces(f=None):
    return f.replace(" ", "")


def capitalize(f=None):
    return f.capitalize()
