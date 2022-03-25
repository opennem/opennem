"""AEMO MMS Client

 * Can download a particular table for any time range
 * Understands the MMS schema and parses records
"""

MMS_DOWNLOAD_URL_TEMPLATE = "http://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/{year}/MMSDM_{year}_{month}/MMSDM_Historical_Data_SQLLoader/DATA/PUBLIC_DVD_{table}_{year}{month}010000.zip"


from opennem.utils.http import http


def run_aemo_download() -> None:
    pass


def run_test() -> None:
    pass


if __name__ == "__main__":
    run_aemo_download()
