from opennem.core.crawlers.schema import CrawlerDefinition
from opennem.core.parsers.aemo.filenames import AEMODataBucketSize
from opennem.core.time import get_interval, get_interval_by_size
from opennem.schema.time import TimeInterval


class NemwebCrawlerException(Exception):
    """_summary_

    Args:
        Exception (_type_): _description_
    """

    pass


def get_time_interval_for_crawler(crawler: CrawlerDefinition) -> TimeInterval:
    """For a crawler get its interval size"""
    time_interval: TimeInterval | None = None

    if not crawler.network:
        raise NemwebCrawlerException("Require a crawler that defines a network")

    if crawler.bucket_size:
        if crawler.bucket_size == AEMODataBucketSize.interval:
            if not crawler.network.interval_size:
                raise NemwebCrawlerException("Require an interval size for network for this crawler")
            time_interval = get_interval_by_size(crawler.network.interval_size)
        elif crawler.bucket_size == AEMODataBucketSize.day:
            time_interval = get_interval("1d")
        elif crawler.bucket_size == AEMODataBucketSize.week:
            time_interval = get_interval("1w")
        elif crawler.bucket_size == AEMODataBucketSize.fortnight:
            time_interval = get_interval("1f")
        elif crawler.bucket_size == AEMODataBucketSize.month:
            time_interval = get_interval("1M")
        elif crawler.bucket_size == AEMODataBucketSize.year:
            time_interval = get_interval("1Y")

    elif crawler.network and crawler.network.interval_size:
        time_interval = get_interval_by_size(crawler.network.interval_size)

    if not time_interval:
        raise Exception(f"Could not get a time interval for crawler: {crawler.network.code} {crawler.bucket_size}")

    return time_interval
