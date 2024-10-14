"""
Maps CMS field names to database field names

"""

_CMS_FIELD_MAP = {
    "website": "website_url",
    "wikipedia": "wikipedia_link",
}


def cms_field_to_database_field(cms_field: str) -> str:
    """Map a CMS field to a database field
    If it's not in the map, return the original field name
    """
    if cms_field in _CMS_FIELD_MAP:
        return _CMS_FIELD_MAP[cms_field]
    return cms_field
