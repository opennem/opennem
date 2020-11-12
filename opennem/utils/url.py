import urllib
from urllib.parse import urljoin, urlparse

# Support S3 URI's in urllib
urllib.parse.uses_netloc.append("s3")
urllib.parse.uses_relative.append("s3")


def bucket_to_website(bucket_path: str, to_scheme: str = "https") -> str:
    """
    Converts a bucket path to a website path
    """
    bucket_path = urlparse(bucket_path)
    bucket_path = bucket_path._replace(scheme=to_scheme)
    return bucket_path.geturl()
