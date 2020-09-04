# pylint: skip-file
import datetime
import glob
from time import time
from zipfile import BadZipFile

from sqlalchemy import create_engine, update
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, sessionmaker

from dms_daemon import CONFIG, nemweb_reader
from dms_daemon.settings import get_mysql_host

# Initialises connections to databases
engine = create_engine(get_mysql_host("nemweb"))
engine2 = create_engine(get_mysql_host("nemweb_live"))
engine3 = create_engine(get_mysql_host("nemweb_causer_pays"))
engine_meta = create_engine(get_mysql_host("nemweb_meta"))
engine_derived = create_engine(get_mysql_host("nemweb_derived"))

print("meta host", get_mysql_host(db_name="nemweb_meta"))

Session = sessionmaker(bind=engine)

Base = automap_base()
Base.prepare(engine, reflect=False)


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def load_keys(key):
    q = engine.execute("SELECT {0},ID FROM {0}".format(key))
    return AttrDict(q.fetchall())


keys = AttrDict(
    {i: load_keys(i) for i in ["REGIONID", "INTERCONNECTORID", "BIDTYPE", "RUNTYPE"]}
)
keys["DUID"] = AttrDict(
    engine_meta.execute("SELECT {0},ID FROM {0}".format("DUID")).fetchall()
)

region_dict = keys["REGIONID"]
duid_dict = keys["DUID"]
interconnector_dict = keys["INTERCONNECTORID"]

q = engine_meta.execute("SELECT ID,STATION_NAME FROM STATION_NAMES")
station_dict = dict(q.fetchall())

########################################################################################################


class Archive:
    def __init__(self, archive_name):
        self.name = archive_name
        self.filelist = sorted(
            glob.glob("/data/marble/nemweb/ARCHIVE/{}/*".format(archive_name))
        )
        self.__load_table_data()
        self.skip_files = []

    def unzip_archive(self, archive_file):
        for zf_name, zipfile in nemweb_reader.zip_streams(archive_file):
            yield zf_name, zipfile

    def unzip_zipfile(self, fileobject):
        return nemweb_reader.load_nemfile(f=fileobject)

    def __load_table_data(self):
        _, sample_file = next(self.unzip_archive(self.filelist[0]))
        nemfile = self.unzip_zipfile(sample_file)
        self.tables = {table: nemfile.__dict__[table].columns for table in nemfile}


########################################################################################################

"""Posibly have an archive file object??"""

########################################################################################################


class ArchiveInserter(Archive):
    """Archive subclass, with methods to insert tables from the archive"""

    def __init__(self, archive_name="Next_Day_Dispatch"):
        super.__init__(self, archive_name)
        self.csv_table = "DISPATCH_UNIT_SOLUTION"
        self.cols = Base.classes["DISPATCH_UNIT_SOLUTION"].__table__.columns.keys()
        self.cols.remove("ID")

    def insert_table(self):
        for archive_file in self.filelist:
            print(archive_file)
            self.insert_archive_file(archive_file)

    def insert_archive_file(self, archive_file):
        for zf_name, zipfile in self.unzip_archive(archive_file):
            nemfile = self.unzip_zipfile(zipfile)

            df = nemfile.__dict__[self.csv_table].copy()
            self.insert_dataframe(df)

    def insert_dataframe(self, df, map_from="DUID", map_dict=duid_dict):
        # maps duid names to duid ids
        df[map_from] = df[map_from].apply(lambda x: map_dict[x])

        df[self.cols].to_sql(
            name="DISPATCH_UNIT_SOLUTION", index=None, con=engine, if_exists="append"
        )


########################################################################################################


class ArchiveUpdater(Archive):
    """Archive subclass, with methods update tables from the archive"""

    csv_table = None

    def __init__(self, archive_name="DispatchIS_Reports"):
        super.__init__(self, archive_name)

    def update_table(self, map_from="REGIONID", map_dict=region_dict):
        for archive_file in self.filelist:
            print(archive_file)
            self.update_archive_file(archive_file, map_from=map_from, map_dict=map_dict)

    def update_archive_file(
        self, archive_file, map_from="REGIONID", map_dict=region_dict
    ):
        session = Session()

        for zf_name, zipfile in self.unzip_archive(archive_file):

            # block for dealing with htm files
            try:
                nemfile = self.unzip_zipfile(zipfile)
            except nemweb_reader.BadZipfile:
                if zf_name.split(".")[-1] == "htm":
                    continue
                elif zf_name in self.skip_files:
                    continue
                else:
                    continue

            df = nemfile.__dict__[self.csv_table].copy()

            # maps region names to regionids
            df[map_from] = df[map_from].apply(lambda x: map_dict[x])

            for i, row in df.iterrows():
                sql = self.row_update(row)
                session.execute(sql)
            session.commit()

        session.close()

    def row_update(self, row):

        sql = update(self.db_table)
        for i in self.index_columns:
            sql = sql.where(self.db_table.__dict__[i] == row[i])
        return sql.values(row[self.update_columns].to_dict())

    def legacy_filelist(self):
        self.filelist = []
        for year in range(2006, 2012):
            self.filelist += glob.glob(
                "/data/marble/nemweb/LEGACY/public_dispatchis/public_dispatchis_{0}/*.zip".format(
                    year
                )
            )


########################################################################################################


class LegacyArchiveUpdater(ArchiveUpdater):
    def __init__(self, archive_name="DispatchIS_Reports"):
        Archive.__init__(self, archive_name)

    # adds anther unzip step to update function
    def update_table(self):
        for zipfile in self.filelist:
            for zf_name, archive_file in self.unzip_archive(zipfile):
                print(zf_name)
                self.update_archive_file(archive_file)

    def legacy_filelist(self, year=2005):
        self.filelist = glob.glob(
            "/data/marble/nemweb/LEGACY/public_dispatchis/public_dispatchis_{0}/*.zip".format(
                year
            )
        )


########################################################################################################
# Instances of updaters


class trading_price_updater(ArchiveUpdater):
    def __init__(self, archive_name="TradingIS_Reports"):
        ArchiveUpdater.__init__(self, archive_name)
        self.csv_table = "PRICE"
        self.db_table = Base.classes["TRADING_PRICE"]
        self.index_columns = ["SETTLEMENTDATE", "REGIONID"]
        self.update_columns = [
            "ROP",
            "RAISE6SECRRP",
            "RAISE6SECROP",
            "RAISE60SECRRP",
            "RAISE60SECROP",
            "RAISE5MINRRP",
            "RAISE5MINROP",
            "RAISEREGRRP",
            "RAISEREGROP",
            "LOWER6SECRRP",
            "LOWER6SECROP",
            "LOWER60SECRRP",
            "LOWER60SECROP",
            "LOWER5MINRRP",
            "LOWER5MINROP",
            "LOWERREGRRP",
            "LOWERREGROP",
        ]


class trading_regionsum_updater(ArchiveUpdater):
    def __init__(self, archive_name="TradingIS_Reports"):
        ArchiveUpdater.__init__(self, archive_name)
        self.csv_table = "REGIONSUM"
        self.db_table = Base.classes["TRADING_REGIONSUM"]
        self.index_columns = ["SETTLEMENTDATE", "REGIONID"]
        self.update_columns = [
            "LOWERREGLOCALDISPATCH",
            "LOWER5MINLOCALDISPATCH",
            "LOWER60SECLOCALDISPATCH",
            "LOWER6SECLOCALDISPATCH",
            "RAISE5MINLOCALDISPATCH",
            "RAISEREGLOCALDISPATCH",
            "RAISE60SECLOCALDISPATCH",
            "RAISE6SECLOCALDISPATCH",
        ]


class dispatch_price_updater(ArchiveUpdater):
    def __init__(self, archive_name="DispatchIS_Reports"):
        ArchiveUpdater.__init__(self, archive_name)
        self.csv_table = "PRICE"
        self.db_table = Base.classes["DISPATCH_PRICE"]
        self.index_columns = ["SETTLEMENTDATE", "REGIONID", "INTERVENTION"]
        self.update_columns = [
            "ROP",
            "APCFLAG",
            "RAISE6SECRRP",
            "RAISE6SECROP",
            "RAISE6SECAPCFLAG",
            "RAISE60SECRRP",
            "RAISE60SECROP",
            "RAISE60SECAPCFLAG",
            "RAISE5MINRRP",
            "RAISE5MINROP",
            "RAISE5MINAPCFLAG",
            "RAISEREGRRP",
            "RAISEREGROP",
            "RAISEREGAPCFLAG",
            "LOWER6SECRRP",
            "LOWER6SECROP",
            "LOWER6SECAPCFLAG",
            "LOWER60SECRRP",
            "LOWER60SECROP",
            "LOWER60SECAPCFLAG",
            "LOWER5MINRRP",
            "LOWER5MINROP",
            "LOWER5MINAPCFLAG",
            "LOWERREGRRP",
            "LOWERREGROP",
            "LOWERREGAPCFLAG",
        ]


class dispatch_regionsum_updater(ArchiveUpdater):
    def __init__(self, archive_name="DispatchIS_Reports"):
        ArchiveUpdater.__init__(self, archive_name)
        self.csv_table = "REGIONSUM"
        self.db_table = Base.classes["DISPATCH_REGIONSUM"]
        self.index_columns = ["SETTLEMENTDATE", "REGIONID", "INTERVENTION"]
        self.update_columns = [
            "LOWERREGLOCALDISPATCH",
            "LOWER5MINLOCALDISPATCH",
            "LOWER60SECLOCALDISPATCH",
            "LOWER6SECLOCALDISPATCH",
            "RAISE5MINLOCALDISPATCH",
            "RAISEREGLOCALDISPATCH",
            "RAISE60SECLOCALDISPATCH",
            "RAISE6SECLOCALDISPATCH",
            "LOWERREGACTUALAVAILABILITY",
            "LOWER5MINACTUALAVAILABILITY",
            "LOWER60SECACTUALAVAILABILITY",
            "LOWER6SECACTUALAVAILABILITY",
            "RAISE5MINACTUALAVAILABILITY",
            "RAISEREGACTUALAVAILABILITY",
            "RAISE60SECACTUALAVAILABILITY",
            "RAISE6SECACTUALAVAILABILITY",
            "AGGREGATEDISPATCHERROR",
        ]


class predispatch_price_updater(ArchiveUpdater):
    def __init__(self, archive_name="PreDispatchIS_Reports"):
        ArchiveUpdater.__init__(self, archive_name)
        self.csv_table = "REGION_PRICES"
        self.db_table = Base.classes["PREDISPATCH_REGION_PRICES"]
        self.index_columns = ["PREDISPATCHSEQNO", "INTERVENTION", "REGIONID", "PERIODID"]
        self.update_columns = [
            "RAISE6SECRRP",
            "RAISE60SECRRP",
            "RAISE5MINRRP",
            "RAISEREGRRP",
            "LOWER6SECRRP",
            "LOWER60SECRRP",
            "LOWER5MINRRP",
            "LOWERREGRRP",
        ]
        self.skip_files += [
            "PUBLIC_PREDISPATCHIS_201610121900_20161012183215.zip",
            "PUBLIC_PREDISPATCHIS_201610130000_20161012233150.zip",
        ]


class bidday_updater(ArchiveUpdater):
    def __init__(self, archive_name="Next_Day_Offer_Energy"):
        ArchiveUpdater.__init__(self, archive_name)
        self.csv_table = "BIDDAYOFFER"
        self.db_table = Base.classes["OFFER_BIDDAYOFFER"]
        self.index_columns = [
            "SETTLEMENTDATE",
            "DUID",
            "OFFERDATE",
            "VERSIONNO",
            "ENTRYTYPE",
            "LASTCHANGED",
        ]
        self.update_columns = ["T1", "T2", "T3", "T4"]


# ==============================Dealing with LIVE data (one less level in archive)
class ScadaInserter(Archive):
    def __init__(self, live_name):
        self.name = live_name
        self.filelist = sorted(
            glob.glob("/data/marble/nemweb/LIVE/{}/*".format(live_name))
        )

    def load_table_data(self):
        for f in self.filelist:
            self.nemfile = nemweb_reader.load_nemfile(f)
            self.key_map()

    def key_map(self, map_from="DUID", map_dict=duid_dict):
        for table in self.nemfile:
            df = self.nemfile.__dict__[table]
            df[map_from] = df[map_from].apply(lambda x: map_dict[x])
            df = df[["SETTLEMENTDATE", "DUID", "SCADAVALUE"]]
            df.to_sql("DISPATCH_UNIT_SCADA", con=engine2, if_exists="append", index=None)


class RegionPriceInserter(Archive):
    def __init__(self, live_name="DispatchIS_Reports"):
        self.name = live_name
        self.filelist = sorted(
            glob.glob("/data/marble/nemweb/LIVE/{}/*".format(live_name))
        )

    def load_table_data(self):
        for f in self.filelist:
            self.nemfile = nemweb_reader.load_nemfile(f)
            self.key_map()

    def key_map(self, map_from="REGIONID", map_dict=region_dict):
        for table in ["DISPATCH_PRICE"]:
            df = self.nemfile.__dict__[table]
            df[map_from] = df[map_from].apply(lambda x: map_dict[x])
            df = df[
                [
                    "SETTLEMENTDATE",
                    "REGIONID",
                    "DISPATCHINTERVAL",
                    "RRP",
                    "ROP",
                    "APCFLAG",
                    "CUMUL_PRE_AP_ENERGY_PRICE",
                    "INTERVENTION",
                    "RAISE6SECRRP",
                    "RAISE6SECROP",
                    "RAISE6SECAPCFLAG",
                    "RAISE60SECRRP",
                    "RAISE60SECROP",
                    "RAISE60SECAPCFLAG",
                    "RAISE5MINRRP",
                    "RAISE5MINROP",
                    "RAISE5MINAPCFLAG",
                    "RAISEREGRRP",
                    "RAISEREGROP",
                    "RAISEREGAPCFLAG",
                    "LOWER6SECRRP",
                    "LOWER6SECROP",
                    "LOWER6SECAPCFLAG",
                    "LOWER60SECRRP",
                    "LOWER60SECROP",
                    "LOWER60SECAPCFLAG",
                    "LOWER5MINRRP",
                    "LOWER5MINROP",
                    "LOWER5MINAPCFLAG",
                    "LOWERREGRRP",
                    "LOWERREGROP",
                    "LOWERREGAPCFLAG",
                ]
            ]
            df.to_sql("DISPATCH_PRICE", con=engine2, if_exists="append", index=None)


class RegionSum(Archive):
    def __init__(self, live_name="DispatchIS_Reports"):
        self.name = live_name
        self.filelist = sorted(
            glob.glob("/data/marble/nemweb/LIVE/{}/*".format(live_name))
        )

    def load_table_data(self):
        for f in self.filelist:
            self.nemfile = nemweb_reader.load_nemfile(f)
            self.key_map()

    def key_map(self, map_from="REGIONID", map_dict=region_dict):
        for table in ["DISPATCH_REGIONSUM"]:
            df = self.nemfile.__dict__[table]
            df[map_from] = df[map_from].apply(lambda x: map_dict[x])
            df = df[
                [
                    "SETTLEMENTDATE",
                    "REGIONID",
                    "TOTALDEMAND",
                    "AVAILABLEGENERATION",
                    "AVAILABLELOAD",
                    "DEMANDFORECAST",
                    "DISPATCHABLEGENERATION",
                    "DISPATCHABLELOAD",
                    "NETINTERCHANGE",
                    "EXCESSGENERATION",
                    "INITIALSUPPLY",
                    "CLEAREDSUPPLY",
                    "TOTALINTERMITTENTGENERATION",
                    "DEMAND_AND_NONSCHEDGEN",
                    "UIGF",
                    "SEMISCHEDULE_CLEAREDMW",
                    "DISPATCHINTERVAL",
                    "SEMISCHEDULE_COMPLIANCEMW",
                    "INTERVENTION",
                    "LOWERREGLOCALDISPATCH",
                    "LOWER5MINLOCALDISPATCH",
                    "LOWER60SECLOCALDISPATCH",
                    "LOWER6SECLOCALDISPATCH",
                    "RAISE5MINLOCALDISPATCH",
                    "RAISEREGLOCALDISPATCH",
                    "RAISE60SECLOCALDISPATCH",
                    "RAISE6SECLOCALDISPATCH",
                    "AGGREGATEDISPATCHERROR",
                    "RAISE6SECACTUALAVAILABILITY",
                    "RAISE5MINACTUALAVAILABILITY",
                    "RAISE60SECACTUALAVAILABILITY",
                    "RAISEREGACTUALAVAILABILITY",
                    "LOWER6SECACTUALAVAILABILITY",
                    "LOWER5MINACTUALAVAILABILITY",
                    "LOWER60SECACTUALAVAILABILITY",
                    "LOWERREGACTUALAVAILABILITY",
                ]
            ]
            df.to_sql("DISPATCH_REGIONSUM", con=engine2, if_exists="append", index=None)


class TradingRegionSum(Archive):
    def __init__(self, live_name="TradingIS_Reports"):
        self.name = live_name
        self.filelist = sorted(
            glob.glob("/data/marble/nemweb/LIVE/{}/*".format(live_name))
        )

    def load_table_data(self):
        for f in self.filelist:
            self.nemfile = nemweb_reader.load_nemfile(f)
            self.key_map()

    def key_map(self, map_from="REGIONID", map_dict=region_dict):
        for table in ["TRADING_REGIONSUM"]:
            df = self.nemfile.__dict__[table]
            df[map_from] = df[map_from].apply(lambda x: map_dict[x])
            df = df[
                [
                    "SETTLEMENTDATE",
                    "REGIONID",
                    "TOTALDEMAND",
                    "AVAILABLEGENERATION",
                    "AVAILABLELOAD",
                    "DEMANDFORECAST",
                    "DISPATCHABLEGENERATION",
                    "DISPATCHABLELOAD",
                    "NETINTERCHANGE",
                    "EXCESSGENERATION",
                    "INITIALSUPPLY",
                    "CLEAREDSUPPLY",
                    "TOTALINTERMITTENTGENERATION",
                    "DEMAND_AND_NONSCHEDGEN",
                    "UIGF",
                    "LOWERREGLOCALDISPATCH",
                    "LOWER5MINLOCALDISPATCH",
                    "LOWER60SECLOCALDISPATCH",
                    "LOWER6SECLOCALDISPATCH",
                    "RAISE5MINLOCALDISPATCH",
                    "RAISEREGLOCALDISPATCH",
                    "RAISE60SECLOCALDISPATCH",
                    "RAISE6SECLOCALDISPATCH",
                ]
            ]
            df.to_sql("TRADING_REGIONSUM", con=engine2, if_exists="append", index=None)


class TradingPrice(Archive):
    def __init__(self, live_name="TradingIS_Reports"):
        self.name = live_name
        self.filelist = sorted(
            glob.glob("/data/marble/nemweb/LIVE/{}/*".format(live_name))
        )

    def load_table_data(self):
        for f in self.filelist:
            self.nemfile = nemweb_reader.load_nemfile(f)
            self.key_map()

    def key_map(self, map_from="REGIONID", map_dict=region_dict):
        for table in ["TRADING_PRICE"]:
            df = self.nemfile.__dict__[table]
            df[map_from] = df[map_from].apply(lambda x: map_dict[x])
            df = df[
                [
                    "SETTLEMENTDATE",
                    "REGIONID",
                    "RRP",
                    "ROP",
                    "RAISE6SECRRP",
                    "RAISE6SECROP",
                    "RAISE60SECRRP",
                    "RAISE60SECROP",
                    "RAISE5MINRRP",
                    "RAISE5MINROP",
                    "RAISEREGRRP",
                    "RAISEREGROP",
                    "LOWER6SECRRP",
                    "LOWER6SECROP",
                    "LOWER60SECRRP",
                    "LOWER60SECROP",
                    "LOWER5MINRRP",
                    "LOWER5MINROP",
                    "LOWERREGRRP",
                    "LOWERREGROP",
                ]
            ]
            df.to_sql("TRADING_PRICE", con=engine2, if_exists="append", index=None)


###############################################################################3
class DispatchUnitSolution(Archive):
    def __init__(self, name="Next_Day_Dispatch"):
        self.name = name
        self.filelist = sorted(
            glob.glob("/data/marble/nemweb/ARCHIVE/{0}/*".format(name))
        )

    def load_table_data(self):
        for f in self.filelist:
            print(f)
            self.nemfile = nemweb_reader.load_nemfile(f)
            self.key_map()

            break

    def key_map(self, map_from="DUID", map_dict=duid_dict):
        for table in ["DISPATCH_UNIT_SOLUTION"]:
            df = self.nemfile.__dict__[table]
            df[map_from] = df[map_from].apply(lambda x: map_dict[x])
            break
            df = df[
                [
                    "SETTLEMENTDATE",
                    "REGIONID",
                    "RRP",
                    "ROP",
                    "RAISE6SECRRP",
                    "RAISE6SECROP",
                    "RAISE60SECRRP",
                    "RAISE60SECROP",
                    "RAISE5MINRRP",
                    "RAISE5MINROP",
                    "RAISEREGRRP",
                    "RAISEREGROP",
                    "LOWER6SECRRP",
                    "LOWER6SECROP",
                    "LOWER60SECRRP",
                    "LOWER60SECROP",
                    "LOWER5MINRRP",
                    "LOWER5MINROP",
                    "LOWERREGRRP",
                    "LOWERREGROP",
                ]
            ]
            # df.to_sql('TRADING_PRICE',con=engine, if_exists= 'append',index=None)


###############################################################################3
class PreDispatchSensitivities(ArchiveInserter):
    def __init__(self, name="Predispatch_Sensitivities"):
        self.name = name
        self.filelist = sorted(
            glob.glob("/data/marble/nemweb/ARCHIVE/{0}/*".format(name))
        )
        # self.filelist = self.filelist[280:]
        # self.filelist = self.filelist[330:]
        self.filelist = self.filelist[368:]

        self.csv_table = "PREDISPATCH_PRICESENSITIVITIES"
        self.cols = Base.classes[
            "PREDISPATCH_PRICESENSITIVITIES"
        ].__table__.columns.keys()
        self.cols.remove("ID")

    def insert_dataframe(self, df, map_from="REGIONID", map_dict=region_dict):
        # maps duid names to duid ids
        df[map_from] = df[map_from].apply(lambda x: map_dict[x])

        df[self.cols].to_sql(
            name="PREDISPATCH_PRICESENSITIVITIES",
            index=None,
            con=engine,
            if_exists="append",
        )

    def insert_archive_file(self, archive_file):
        for zf_name, zipfile in self.unzip_archive(archive_file):
            try:
                nemfile = self.unzip_zipfile(zipfile)
                df = nemfile.__dict__[self.csv_table].copy()
                self.insert_dataframe(df)
            except BadZipFile as E:
                print(zf_name)
                if zf_name in [
                    "PUBLIC_PREDISPATCH_SENSITIVITIES_20161227093218_0000000279137718.zip",
                    "PUBLIC_PREDISPATCH_SENSITIVITIES_20170913020303_0000000287276933.zip",
                ]:
                    pass
                else:
                    raise E
