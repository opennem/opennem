from scrapy.http.response import Response

from opennem.spiders.dirlisting import DirlistingSpider


class TestDirListingSpider(DirlistingSpider):
    pass


def test_nemweb_dirlisting_spider_return(aemo_nemweb_dirlisting: Response) -> None:
    """Checks the return types for a spider"""
    assert isinstance(aemo_nemweb_dirlisting, Response), "Returns a scrapy response"
    assert isinstance(aemo_nemweb_dirlisting.body, bytes), "Response body is bytes"


def test_nemweb_dirlisting_spider_parser(aemo_nemweb_dirlisting: Response) -> None:
    """Check the response has the correct header value"""
    _decoded_body = aemo_nemweb_dirlisting.body.decode("utf-8")

    assert aemo_nemweb_dirlisting.status == 200, "Correct response code"

    assert "Dispatch_SCADA" in _decoded_body, "Contains string with directory name"


def test_nemweb_dirlisting_live(aemo_nemweb_dirlisting_live: Response) -> None:
    """Checks the return types for a spider with a live test"""
    assert isinstance(aemo_nemweb_dirlisting_live, Response), "Returns a scrapy response"
    assert isinstance(aemo_nemweb_dirlisting_live.body, bytes), "Response body is bytes"
