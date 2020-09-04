# pylint: skip-file
import datetime
import re
import time
from io import BytesIO, StringIO

import requests
import sentry_sdk

import pytz
from datadog import statsd
from dms_daemon import orm
from dms_daemon.nemweb_reader import NemFile, ZipFileStreamer

sentry_sdk.init(
    "https://7bdb0e977ab94a1c83db9b927b6dfd29@o402615.ingest.sentry.io/5264004"
)


meta_cols = "DUID, STATION_NAME, PARTICIPANT, REGIONID, FUEL_TECH"
sql = "SELECT {0} FROM nemweb_meta.FULL_REGISTER".format(meta_cols)
cursor = orm.engine_meta.execute(sql)
meta_data = {i[0]: i[1:] for i in cursor.fetchall()}

tz = pytz.timezone("Australia/Melbourne")


class SCADA_File(NemFile):
    # similar to nemfile obj., with additional meta_data funtcionality
    def __init__(
        self,
        fileobject="/data/marble/nemweb/ARCHIVE/DispatchIS_Reports/PUBLIC_DISPATCHIS_20170208.zip",
    ):
        self.meta = fileobject.readline()
        NemFile.__init__(self, fileobject)

    def timestamp(self):
        timestring = ",".join(self.meta.columns[5:7])
        return datetime.datetime.strptime(timestring, "%Y/%m/%d,%H:%M:%S")


def load_scadafile(f="PUBLIC_DISPATCHIS_201309150010_0000000246668929.zip"):
    with ZipFileStreamer(f) as zf:
        if zf.member_count == 1:
            filename = zf.namelist()[0]
            zfs = zf.extract_stream(filename)
            return SCADA_File(zfs)
        else:
            raise Exception("More than one file in zipfile")


def get_page(url="http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/"):
    response = requests.get(url)
    return response


def get_zip(
    href="/Reports/CURRENT/Dispatch_SCADA/PUBLIC_DISPATCHSCADA_201708161600_0000000286435695.zip",
    log=True,
):
    response = requests.get("http://www.nemweb.com.au{0}".format(href))
    if log:
        web_log(response)
    return BytesIO(response.content)


def web_log(response):
    webtimestamp = response.headers["Last-Modified"]
    timestamp = datetime.datetime.strptime(
        webtimestamp, "%a, %d %b %Y %H:%M:%S GMT"
    ) + datetime.timedelta(0, 10 * 3600)

    Previous_DI = datetime.datetime.now().replace(second=0, microsecond=0)

    # web delay logging
    web_delay = timestamp - Previous_DI
    statsd.gauge("unit.error.web_delay", web_delay.seconds)


def main():
    localtime = datetime.datetime.now(tz).replace(second=0, microsecond=0)
    Previous_DI = localtime - localtime.dst()

    capacity()
    Current_DI = Previous_DI + datetime.timedelta(0, 300)
    DI_timestring = Current_DI.strftime("%Y%m%d%H%M")

    time.sleep(60)
    request_time = datetime.datetime.now()
    page = get_page(
        url="http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/"
    )
    page2 = get_page(
        url="http://www.nemweb.com.au/Reports/CURRENT/DispatchIS_Reports/"
    )

    pattern = re.compile(
        "/Reports/CURRENT/Dispatch_SCADA/PUBLIC_DISPATCHSCADA_{0}_[0-9]{{16}}.zip".format(
            DI_timestring
        )
    )
    links = re.findall(pattern, page.text)
    links2 = link_getter(page2, DI_timestring)

    if len(links) == 1:
        zipIO = get_zip(href=links[0])
        scada_file = load_scadafile(zipIO)

        zipIO2 = get_zip(href=links2[0])
        dispatch_file = load_scadafile(zipIO2)

        # timedelay logging
        nemde_delay = tz.localize(scada_file.timestamp()) - Previous_DI
        statsd.gauge("unit.error.nemde_delay", nemde_delay.seconds)

        # data processing
        dispatch_scada_proc(scada_file, dispatch_file)
        dispatch_file_proc(dispatch_file)

    elif len(links) == 0:
        statsd.gauge("unit.error.skipped_di", 1)


def dispatch_scada_proc(sf, df):
    for i, row in sf.DISPATCH_UNIT_SCADA.iterrows():
        try:
            meta = meta_data[row.DUID]
            region = meta[-2]
            price = df.DISPATCH_PRICE.RRP[
                df.DISPATCH_PRICE.REGIONID == region
            ].values[0]
            scadavalue = row.SCADAVALUE
            meta_pairs = [
                "{0}:{1}".format(i, j)
                for i, j in zip(meta_cols.lower().split(","), meta)
            ]
            statsd.gauge("unit.power", scadavalue, tags=meta_pairs)
            statsd.gauge(
                "unit.marketvalue", scadavalue * price / 12.0, tags=meta_pairs
            )
        except:
            print("missing")
            pass


def dispatch_file_proc(df):
    dp = df.DISPATCH_PRICE[["REGIONID", "RRP"]]
    dr = df.DISPATCH_REGIONSUM[["REGIONID", "TOTALDEMAND", "NETINTERCHANGE"]]
    dc = dp.merge(dr, on="REGIONID")
    dc["VALUE"] = dc.RRP * dc.TOTALDEMAND / 12.0
    for i, row in dc.iterrows():
        statsd.gauge(
            "dispatch.totaldemand",
            row.TOTALDEMAND,
            tags=["regionid:{0}".format(row.REGIONID)],
        )
        statsd.gauge(
            "dispatch.netinterchange",
            row.NETINTERCHANGE,
            tags=["regionid:{0}".format(row.REGIONID)],
        )
        statsd.gauge(
            "dispatch.price",
            row.RRP,
            tags=["regionid:{0}".format(row.REGIONID)],
        )
        statsd.gauge(
            "dispatch.marketvalue",
            row.VALUE,
            tags=["regionid:{0}".format(row.REGIONID)],
        )


def link_getter(page, DI_timestring):
    pattern = re.compile(
        "/Reports/CURRENT/DispatchIS_Reports/PUBLIC_DISPATCHIS_{0}_[0-9]{{16}}.zip".format(
            DI_timestring
        )
    )
    links = re.findall(pattern, page.text)
    return links


def capacity():
    cap_sql = sql.format("REG_CAP")
    cursor = orm.engine_meta.execute(cap_sql)
    cap_data = {i[0]: i[1:] for i in cursor.fetchall()}

    for duid in cap_data:
        value = cap_data[duid][0]
        meta = meta_data[duid]
        meta_pairs = [
            "{0}:{1}".format(i, j)
            for i, j in zip(meta_cols.lower().split(","), meta)
        ]
        statsd.gauge("unit.capacity", value, meta_pairs)


def main_test():
    Previous_DI = datetime.datetime.now().replace(second=0, microsecond=0)
    capacity()
    Current_DI = Previous_DI + datetime.timedelta(0, 300)
    DI_timestring = Current_DI.strftime("%Y%m%d%H%M")

    time.sleep(60)
    request_time = datetime.datetime.now()

    page = get_page(
        url="http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/"
    )
    page2 = get_page(
        url="http://www.nemweb.com.au/Reports/CURRENT/DispatchIS_Reports/"
    )

    pattern = re.compile(
        "/Reports/CURRENT/Dispatch_SCADA/PUBLIC_DISPATCHSCADA_{0}_[0-9]{{16}}.zip".format(
            DI_timestring
        )
    )
    links = re.findall(pattern, page.text)
    links2 = link_getter(page2, DI_timestring)

    zipIO = get_zip(href=links[0])
    zipIO2 = get_zip(href=links2[0])

    return load_scadafile(zipIO), load_scadafile(zipIO2)


if __name__ == "__main__":
    main()
