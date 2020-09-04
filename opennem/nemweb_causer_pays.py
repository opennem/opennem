# pylint: skip-file
import datetime
import re

import requests
from sqlalchemy import exc

import pandas as pd
from dms_daemon import CONFIG, nemweb_requests, orm


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


def table_date(date):
    table = datetime.date(date.year, date.month, 1).strftime("fcas_%Y%m")
    try:
        d = nemweb_requests.last_date(table=table, db="nemweb_causer_pays")
        return d
    except exc.ProgrammingError as E:
        auto_table(E.args[1])
        table_date(date)


def latest_table_date():
    date = datetime.date.today()
    d = table_date(date)

    if d == None:
        date -= datetime.timedelta(20)
        d = table_date(date)

    return d


def process_fcas(link):
    zipIO = nemweb_requests.get_zip(href=link)
    fcas_files = nemweb_requests.ZipFileStreamer(zipIO)
    for fcas_file in fcas_files.filelist:
        yield fcas_files.extract_stream(fcas_file)


def insert_fcas(csvs, table="fcas_201802"):
    connection = orm.engine3.connect()
    transaction = connection.begin()

    for csv in csvs:
        df = pd.read_csv(
            csv,
            parse_dates=[0],
            index_col=[0],
            header=None,
            names=[
                "SETTLEMENTDATE",
                "ELEMENT_ID",
                "VARIABLE_ID",
                "VALUE",
                "QUALITY",
            ],
        )

        if df.index.dtype.name == "object":
            df.dropna(inplace=True)
            slack_dms_webhook(
                "Issue with FCAS csv (wrong datetime)\n  (CSV file starting at {})".format(
                    df.index[0]
                )
            )

        try:
            df.to_sql(table, con=transaction.connection, if_exists="append")

        except exc.IntegrityError as E:
            transaction.rollback()
            connection.close()
            new_element_keys = check_missing_element(df)
            if new_element_keys != []:
                add_element_keys(new_element_keys)
                insert_fcas(csvs, table=table)
            else:
                raise E

    transaction.commit()
    connection.close()


def check_missing_element(df):
    # could make this into an excpetion?
    unique_elements = list(df.ELEMENT_ID.unique())
    cursor = orm.engine3.execute("SELECT id FROM elements")
    element_keys = [i[0] for i in cursor]
    new_keys = []
    for key in unique_elements:
        if key not in element_keys:
            new_keys.append(key)
    return new_keys


def causer_pays():
    d = latest_table_date()

    page = nemweb_requests.get_page(
        link="http://www.nemweb.com.au/Reports/Current/Causer_Pays/"
    )

    pattern = re.compile("/Reports/Current/Causer_Pays/FCAS_([0-9]{12}).zip")

    for match in pattern.finditer(page.text):
        dt = datetime.datetime.strptime(match.group(1), "%Y%m%d%H%M")
        if dt > d:
            table = dt.strftime("fcas_%Y%m")
            print(match.group(0), table)
            csvs = [csv for csv in process_fcas(match.group(0))]
            insert_fcas(csvs, table=table)


def create_table(table_str="fcas_201801"):
    with orm.engine3.connect() as conn:
        conn.execute("CREATE TABLE {0} like fcas_201802".format(table_str))
        conn.execute(
            "ALTER TABLE `nemweb_causer_pays`.`{0}`  "
            "ADD CONSTRAINT `fk_{0}_1` "
            "FOREIGN KEY (`ELEMENT_ID`) "
            "REFERENCES `nemweb_causer_pays`.`elements` (`ID`) "
            "ON DELETE RESTRICT "
            "ON UPDATE RESTRICT, "
            "ADD CONSTRAINT `fk_{0}_2` "
            "FOREIGN KEY (`VARIABLE_ID`) "
            "REFERENCES `nemweb_causer_pays`.`variables` (`ID`) "
            "ON DELETE RESTRICT "
            "ON UPDATE RESTRICT".format(table_str)
        )


def auto_table(error_msg):
    pattern = re.compile(
        "Table 'nemweb_causer_pays.(fcas_[0-9]{6})' doesn't exist"
    )
    match = pattern.match(error_msg)
    if len(match.groups()) == 1:
        create_table(match.group(1))
        slack_dms_webhook("Created new table: {0}".format(match.group(1)))
    else:
        raise Exception(
            "Auto_table error: wrong table name format",
            match.group(0).split("'")[1],
        )


def find_new_id(df):
    for element in df.ELEMENT_ID.unique():
        cursor = orm.engine3.execute(
            "SELECT * FROM elements where id = {0}".format(element)
        )
        print(cursor.fetchall()[0])


def read_range():
    d = datetime.datetime(2017, 2, 10, 12, 25)
    for i in range(6):
        d += datetime.timedelta(0, 1800)
        f = archive_file_reader(d)
        csvs = [z for z in process_archive_file(f)]
        insert_fcas(csvs, table="fcas_201711")
        print(d)


def archive_file_reader(d=datetime.datetime(2017, 2, 10, 15, 25)):
    filename = "/data/marble/nemweb/DATA_ARCHIVE/FCAS_Causer_Pays/{0.year}/FCAS_Causer_Pays_{1}/FCAS_{2}.zip".format(
        d, d.strftime("%Y_%m"), d.strftime("%Y%m%d%H%M")
    )
    return filename


def process_archive_file(filename):
    fcas_files = nemweb_requests.ZipFileStreamer(filename)
    for fcas_file in fcas_files.filelist:
        yield fcas_files.extract_stream(fcas_file)


class NewKeyError(KeyError):
    def __init__(self, *args, **kwargs):
        KeyError.__init__(self, *args, **kwargs)

    def __str__(self):
        return "New element id: {0}".format(*self.args)


def add_element_keys(new_element_keys):
    """Adds list of new element keys to elements table"""
    df = pd.DataFrame(new_element_keys, columns=["ID"])
    with orm.engine3.connect() as conn:
        df.to_sql("elements", con=conn, if_exists="append", index=False)
    slack_dms_webhook("Added new elements: {0}".format(new_element_keys))
