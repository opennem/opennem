from datetime import datetime


def map_date_start_to_season(dt: datetime) -> str:
    """Map a date to a season

    Args:
        dt (datetime): The date to map

    Returns:
        str: The season
    """
    seasons = {
        "jan": "summer",
        "feb": "summer",
        "mar": "autumn",
        "apr": "autumn",
        "may": "autumn",
        "jun": "winter",
        "jul": "winter",
        "aug": "winter",
        "sep": "spring",
        "oct": "spring",
        "nov": "spring",
        "dec": "summer",
    }

    return seasons[dt.strftime("%b").lower()]
