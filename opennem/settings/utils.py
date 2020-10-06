from urllib.parse import urlparse


def replace_database_in_url(db_url, db_name):
    """
        replaces the database portion of a database connection URL with db_name

        @param db_name database name to replace with
    """

    db_url_parsed = urlparse(db_url)
    db_url_parsed = db_url_parsed._replace(path=f"/{db_name}")

    return db_url_parsed.geturl()
