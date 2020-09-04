# pylint: skip-file
import datetime
import os
import re
import time
from io import BytesIO, StringIO

import requests
from sqlalchemy.exc import IntegrityError

import pandas as pd
from dms_daemon import CONFIG, live, orm
from dms_daemon.market_notice_reader import check_notice
from dms_daemon.nemweb_reader import NemFile, ZipFileStreamer


def slack_dms_webhook(message):
    json_text = "{0} \n ({1})".format(
        message, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    requests.post(
        "https://hooks.slack.com/services/{0}".format(
            CONFIG["slack_hooks"]["error_message"]
        ),
        json={"text": "{0}".format(json_text)},
    )


def get_page(link="http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/"):
    return requests.get(link)


def get_zip(
    href="/Reports/CURRENT/Dispatch_SCADA/PUBLIC_DISPATCHSCADA_201708161600_0000000286435695.zip",
):
    response = requests.get("http://www.nemweb.com.au{0}".format(href))
    return BytesIO(response.content)


def last_date(
    table="DISPATCH_UNIT_SCADA", column="SETTLEMENTDATE", db="nemweb_live"
):
    cursor = orm.engine2.execute(
        "SELECT MAX({1}) FROM {0}".format(table, column)
    )
    return cursor.fetchall()[0][0]


def process_zip(link):
    zipIO = get_zip(href=link)
    scada_file = live.load_scadafile(zipIO)
    return scada_file


def insert(df, name):
    for key in orm.keys.keys():
        if key in df.columns:
            # df[key] = df[key].apply(lambda x: orm.keys[key][x])
            try:
                df[key] = df[key].apply(lambda x: orm.keys[key][x])
            except KeyError as e:
                if (key == "DUID") & (name == "DISPATCH_UNIT_SCADA"):
                    orm.engine_meta.execute(
                        "INSERT INTO DUID (DUID) VALUES ({0})".format(e)
                    )
                else:
                    raise e

    table = orm.Base.classes[name]
    columns = [col.name for col in table.__table__.columns]

    if "ROP" in columns:
        columns.remove("ROP")

    dx = df[columns[1:]]
    dx.to_sql(name, con=orm.engine2, if_exists="append", index=None)


# Instances of live inserters


def dispatch_scada():
    d = last_date()
    page = get_page()
    tables = ["DISPATCH_UNIT_SCADA"]

    pattern = re.compile(
        "/Reports/CURRENT/Dispatch_SCADA/PUBLIC_DISPATCHSCADA_([0-9]{12})_[0-9]{16}.zip"
    )

    for match in pattern.finditer(page.text):
        dt = datetime.datetime.strptime(match.group(1), "%Y%m%d%H%M")
        if dt > d:
            nemfile = process_zip(match.group(0))

            for table in tables:
                df = nemfile.__dict__[table].drop_duplicates().copy()
                insert(df, table)
                print(table, dt)


def rooftop_actual():
    d = last_date(table="ROOFTOP_ACTUAL", column="INTERVAL_DATETIME")
    page = get_page(
        link="http://www.nemweb.com.au/Reports/Current/ROOFTOP_PV/ACTUAL/"
    )
    tables = ["ROOFTOP_ACTUAL"]

    pattern = re.compile(
        "/Reports/Current/ROOFTOP_PV/ACTUAL/PUBLIC_ROOFTOP_PV_ACTUAL_MEASUREMENT_([0-9]{14})_[0-9]{16}.zip"
    )

    for match in pattern.finditer(page.text):
        dt = datetime.datetime.strptime(match.group(1), "%Y%m%d%H%M00")
        if dt > d + datetime.timedelta(0, 1800):
            # print (match.group(0))
            nemfile = process_zip(match.group(0))
            nemfile.ROOFTOP_ACTUAL = nemfile.ROOFTOP_ACTUAL[
                nemfile.ROOFTOP_ACTUAL.REGIONID.isin(
                    ["NSW1", "QLD1", "SA1", "TAS1", "VIC1"]
                )
            ]

            for table in tables:
                df = nemfile.__dict__[table].drop_duplicates().copy()
                insert(df, table)
                print(table, dt)


def dispatch_unit_solution():
    d = last_date(table="DISPATCH_UNIT_SOLUTION")
    page = get_page(
        link="http://nemweb.com.au/Reports/Current/Next_Day_Dispatch/"
    )
    tables = ["DISPATCH_UNIT_SOLUTION"]

    pattern = re.compile(
        "/Reports/Current/Next_Day_Dispatch/PUBLIC_NEXT_DAY_DISPATCH_([0-9]{8})_[0-9]{16}.zip"
    )

    for match in pattern.finditer(page.text):
        dt = datetime.datetime.strptime(match.group(1), "%Y%m%d")
        if (
            dt.date() >= d.date()
        ):  # not that same as metered gen - should probably make them consistent
            nemfile = process_zip(match.group(0))

            for table in tables:
                df = nemfile.__dict__[table].drop_duplicates().copy()
                insert(df, table)
                print(table, dt)


def dispatch_unit_duplicate(
    link="http://www.nemweb.com.au/Reports/Current/Next_Day_Dispatch/DUPLICATE/",
):
    d = datetime.datetime(2020, 4, 1)
    page = get_page(link)
    tables = ["DISPATCH_UNIT_SOLUTION"]

    pattern = re.compile(
        "/Reports/Current/Next_Day_Dispatch/DUPLICATE/PUBLIC_NEXT_DAY_DISPATCH_([0-9]{8})_[0-9]{16}.zip"
    )

    for match in pattern.finditer(page.text):
        dt = datetime.datetime.strptime(match.group(1), "%Y%m%d")
        if (
            dt.date() >= d.date()
        ):  # not that same as metered gen - should probably make them consistent
            print(dt)
            nemfile = process_zip(match.group(0))

            for table in tables:
                df = nemfile.__dict__[table].drop_duplicates().copy()
                insert(df, table)
                print(table, dt)


def metered_data_gen_duid():
    d = last_date(table="METER_DATA_GEN_DUID", column="INTERVAL_DATETIME")
    last_trading_day = datetime.datetime(
        d.year, d.month, d.day
    ) - datetime.timedelta(1)

    page = get_page(
        link="http://www.nemweb.com.au/Reports/Current/Next_Day_Actual_Gen/"
    )
    tables = ["METER_DATA_GEN_DUID"]

    pattern = re.compile(
        "/Reports/Current/Next_Day_Actual_Gen/PUBLIC_NEXT_DAY_ACTUAL_GEN_([0-9]{8})_[0-9]{16}.zip"
    )

    for match in pattern.finditer(page.text):
        dt = datetime.datetime.strptime(match.group(1), "%Y%m%d")
        if dt > last_trading_day:
            nemfile = process_zip(match.group(0))

            for table in tables:
                df = nemfile.__dict__[table].drop_duplicates().copy()
                insert(df, table)
                print(table, dt)


def rooftop_forecast(d):
    page = get_page(
        link="http://www.nemweb.com.au/Reports/Current/ROOFTOP_PV/FORECAST/"
    )
    tables = ["ROOFTOP_FORECAST"]

    pattern = re.compile(
        "/Reports/Current/ROOFTOP_PV/FORECAST/PUBLIC_ROOFTOP_PV_FORECAST_([0-9]{14})_[0-9]{16}.zip"
    )

    for match in pattern.finditer(page.text):
        dt = datetime.datetime.strptime(match.group(1), "%Y%m%d%H%M00")
        if dt > d:
            nemfile = process_zip(match.group(0))

            for table in tables:
                df = nemfile.__dict__[table].drop_duplicates().copy()
                insert(df, table)
                print(table, dt)


def rooftop_forecast_duplicate():
    d = last_date(table="ROOFTOP_FORECAST", column="VERSION_DATETIME")
    try:
        rooftop_forecast(d)
    except IntegrityError as E:
        d = datetime.datetime.strptime(E.params[0][0], "%Y/%m/%d %H:%M:%S")
        slack_dms_webhook("Duplicate forecast `{0}`\n{1}".format(d, E.args[0]))
        rooftop_forecast(d + datetime.timedelta(0, 1800))


def dispatch_is():
    d = last_date(table="DISPATCH_PRICE")
    page = get_page(
        link="http://www.nemweb.com.au/Reports/CURRENT/DispatchIS_Reports/"
    )
    tables = [
        "DISPATCH_PRICE",
        "DISPATCH_REGIONSUM",
        "DISPATCH_INTERCONNECTORRES",
    ]

    pattern = re.compile(
        "/Reports/CURRENT/DispatchIS_Reports/PUBLIC_DISPATCHIS_([0-9]{12})_[0-9]{16}.zip"
    )

    for match in pattern.finditer(page.text):
        dt = datetime.datetime.strptime(match.group(1), "%Y%m%d%H%M")
        if dt > d:
            nemfile = process_zip(match.group(0))

            for table in tables:
                df = nemfile.__dict__[table].drop_duplicates().copy()
                insert(df, table)
                print(table, dt)


def trading_is():
    d = last_date(table="TRADING_PRICE")
    page = get_page(
        link="http://www.nemweb.com.au/Reports/CURRENT/TradingIS_Reports/"
    )
    tables = [
        "TRADING_PRICE",
        "TRADING_REGIONSUM",
        "TRADING_INTERCONNECTORRES",
    ]

    pattern = re.compile(
        "/Reports/CURRENT/TradingIS_Reports/PUBLIC_TRADINGIS_([0-9]{12})_[0-9]{16}.zip"
    )

    for match in pattern.finditer(page.text):
        dt = datetime.datetime.strptime(match.group(1), "%Y%m%d%H%M")
        if dt > d:
            nemfile = process_zip(match.group(0))

            for table in tables:
                df = nemfile.__dict__[table].drop_duplicates().copy()
                if "ROP" in df.columns:
                    df = df.drop("ROP", axis=1)
                insert(df, table)
                print(table, dt)


def bidoffer_energy():
    d = last_date(table="OFFER_BIDPEROFFER")
    page = get_page(
        link="http://www.nemweb.com.au/Reports/CURRENT/Next_Day_Offer_Energy/"
    )
    tables = ["OFFER_BIDDAYOFFER", "OFFER_BIDPEROFFER"]

    pattern = re.compile(
        "/Reports/CURRENT/Next_Day_Offer_Energy/PUBLIC_NEXT_DAY_OFFER_ENERGY_([0-9]{8})_[0-9]{16}.zip"
    )

    for match in pattern.finditer(page.text):
        dt = datetime.datetime.strptime(match.group(1), "%Y%m%d")
        if dt > d:
            nemfile = process_zip(match.group(0))

            for table in tables:
                df = nemfile.__dict__[table].drop_duplicates().copy()
                insert(df, table)
                print(table, dt)


def bidoffer_fcas():
    d = datetime.datetime(2017, 7, 31)
    page = get_page(
        link="http://www.nemweb.com.au/Reports/CURRENT/Next_Day_Offer_FCAS/"
    )
    tables = ["OFFER_BIDDAYOFFER", "OFFER_BIDPEROFFER"]

    pattern = re.compile(
        "/Reports/CURRENT/Next_Day_Offer_FCAS/PUBLIC_NEXT_DAY_OFFER_FCAS_([0-9]{8})_[0-9]{16}.zip"
    )

    for match in pattern.finditer(page.text):
        dt = datetime.datetime.strptime(match.group(1), "%Y%m%d")
        if dt > d:
            nemfile = process_zip(match.group(0))

            for table in tables:
                df = nemfile.__dict__[table].drop_duplicates().copy()
                insert(df, table)
                print(table, dt)


def seqno_to_dt(x):
    x = str(x)
    year = int(x[:4])
    month = int(x[4:6])
    day = int(x[6:8])
    ti = int(x[-2:])
    return datetime.datetime(year, month, day, 4) + ti * datetime.timedelta(
        0, 1800
    )


def predispatch():
    d = last_date(
        table="PREDISPATCH_REGION_SOLUTION", column="PREDISPATCHSEQNO"
    )
    # d = datetime.datetime(2020,1,30)
    d = seqno_to_dt(d)
    page = get_page(
        link="http://www.nemweb.com.au/Reports/CURRENT/PredispatchIS_Reports/"
    )
    tables = ["PREDISPATCH_REGION_SOLUTION", "PREDISPATCH_REGION_PRICES"]

    pattern = re.compile(
        "/Reports/CURRENT/PredispatchIS_Reports/PUBLIC_PREDISPATCHIS_([0-9]{12})_[0-9]{14}.zip"
    )

    for match in pattern.finditer(page.text):
        dt = datetime.datetime.strptime(match.group(1), "%Y%m%d%H%M")
        if dt > d:
            nemfile = process_zip(match.group(0))

            for table in tables:
                df = nemfile.__dict__[table].drop_duplicates().copy()
                insert(df, table)
                print(table, dt)


def market_notices():
    page = get_page(
        link="http://www.nemweb.com.au/Reports/Current/Market_Notice/"
    )

    pattern = re.compile(
        "/Reports/Current/Market_Notice/NEMITWEB1_MKTNOTICE_([0-9]{8}).R([0-9]{5})"
    )

    for match in pattern.finditer(page.text):
        dt = datetime.datetime.strptime(match.group(1), "%Y%m%d")
        notice_dir = "/data/marble/nemweb/MARKET_NOTICES/{0}/".format(
            datetime.date(dt.year, dt.month, dt.day)
        )

        if os.path.isdir(notice_dir) == False:
            os.mkdir(notice_dir)

        filename = "{0}{1}.txt".format(notice_dir, match.group(2))

        if os.path.exists(filename):
            continue

        else:
            print(filename)
            response = requests.get(
                "http://www.nemweb.com.au{0}".format(match.group(0))
            )
            with open(filename, "wb") as f:
                f.write(response.content)
            check_notice(filename)


if __name__ == "__main__":
    for func in [
        trading_is,
        dispatch_is,
        dispatch_scada,
        market_notices,
        rooftop_actual,
        rooftop_forecast_duplicate,
    ]:
        try:
            func()
        except Exception as E:
            print(func)
            slack_dms_webhook(
                "`{0}` failed from file `{1}`\n{2}\n{3}".format(
                    func.__name__, __file__, E, E.args
                )
            )
