import datetime
import pandas as pd
from dms_daemon import orm
from dms_daemon.nem_derived import meta


#supress data truncation warnings
import MySQLdb
import warnings
warnings.filterwarnings('ignore', category=MySQLdb.Warning)

NEMWEB_LIVE = orm.engine2
NEMWEB_META = orm.engine_meta
NEMWEB_DERIVED = orm.engine_derived

def select_price(d=datetime.date(2018,6,1)):
    sql =     "SELECT SETTLEMENTDATE, RRP, REGIONID "\
            "FROM `TRADING_PRICE` "\
            "WHERE SETTLEMENTDATE > '{0}' "\
                "AND SETTLEMENTDATE <= '{1}'"
    return pd.read_sql(    sql.format(d,d+datetime.timedelta(1)), 
                        con=NEMWEB_LIVE)#, index_col="SETTLEMENTDATE")
                        
def select_regionsum(d=datetime.date(2018,6,1)):
    sql =     "SELECT SETTLEMENTDATE, TOTALDEMAND, NETINTERCHANGE, DEMAND_AND_NONSCHEDGEN, REGIONID "\
            "FROM `TRADING_REGIONSUM` "\
            "WHERE SETTLEMENTDATE > '{0}' "\
                "AND SETTLEMENTDATE <= '{1}'"
    return pd.read_sql(    sql.format(d,d+datetime.timedelta(1)), 
                        con=NEMWEB_LIVE)
                        
def select_output(d=datetime.date(2018,6,1)):
    sql =     "SELECT SETTLEMENTDATE, OUTPUT_MWH, QUALITY_FLAG, DUID "\
            "FROM `TRADING_DUID_OUTPUT` "\
            "WHERE SETTLEMENTDATE > '{0}' "\
                "AND SETTLEMENTDATE <= '{1}'"
    return pd.read_sql(    sql.format(d,d+datetime.timedelta(1)), 
                        con=NEMWEB_DERIVED)#, index_col="SETTLEMENTDATE")
                        
def select_rooftop(d=datetime.date(2018,6,1)):
    sql =     "SELECT INTERVAL_DATETIME as SETTLEMENTDATE, REGIONID, POWER as ROOFTOP_SOLAR "\
            "FROM `ROOFTOP_ACTUAL` "\
            "WHERE INTERVAL_DATETIME > '{0}' "\
                "AND INTERVAL_DATETIME <= '{1}'"
    return pd.read_sql(    sql.format(d,d+datetime.timedelta(1)), 
                        con=NEMWEB_LIVE)
def category_map():
    sql =     "SELECT NAME,ID FROM CATEGORY"
    results = NEMWEB_DERIVED.execute(sql)
    return dict(results.fetchall())
    
def mapper(i):    
    duid = meta.DUID_KEYS[i]
    fcas = {'APD01': 5, 'SNOWYGJP': 5, 'ASNENC1':1, 'VENUS1':5, 'ASQENC1':2, 'ASTHYD1': 4}
    if i in meta.REGION_MAP:
        return meta.REGION_MAP[i]
    elif "_" in duid:    
        d = {"NS":1, "QL":2, "SA":3, "TA":4, "VI":5}
        return d[duid.split("_")[1][:2]]
    elif duid in fcas: 
        return fcas[duid]
    else:
        raise KeyError (duid,i)
        
def select_day(d=datetime.date(2018,6,1)):
    df = select_output(d=d)    
    df['REGIONID'] = df.DUID.apply(lambda x: mapper(x))
    df_p = select_price(d=d)
    return pd.merge(df,df_p, left_on=["SETTLEMENTDATE", "REGIONID"], right_on=["SETTLEMENTDATE","REGIONID"])

def revenue_generator(d):
    df = select_day(d)
    for duid,g in df.groupby("DUID"):
       yield (d,duid, g.OUTPUT_MWH.sum(), (g.OUTPUT_MWH*g.RRP).sum(), g.QUALITY_FLAG.max())

def calculate_day(d=datetime.date(2018,6,1)):
    return pd.DataFrame([i for i in revenue_generator(d)],columns=['DATE','DUID', 'OUTPUT_MWH', 'MARKET_VALUE', "QUALITY_FLAG"])

def insert_daily_duid(d):    
    df = calculate_day(d)
    df.to_sql(name="DAILY_DUID_OUTPUT", index=None, con=NEMWEB_DERIVED, if_exists='append')
    
def select_region_day(d=datetime.date(2018,6,1)):
    df = select_regionsum(d=d)    
    df_p = select_price(d=d)
    df_r = select_rooftop(d=d)
    df_tmp = pd.merge(df,df_p, left_on=["SETTLEMENTDATE", "REGIONID"], right_on=["SETTLEMENTDATE","REGIONID"])
    return     pd.merge(df_tmp, df_r, left_on=["SETTLEMENTDATE", "REGIONID"], right_on=["SETTLEMENTDATE","REGIONID"])
    
def split_interchange(df):
    df['NETINTERCHANGE_IMPORT'] = df.NETINTERCHANGE[df.NETINTERCHANGE<=0]
    df['NETINTERCHANGE_EXPORT'] =  df.NETINTERCHANGE[df.NETINTERCHANGE>=0]
    df.fillna(0,inplace=True)
    
def region_summary(df, date, regionid):
    columns = list(meta.CATEGORY_MAP)
    
    energy = df[columns].sum()/2
    energy.name = "ENERGY_MWH"
    
    market_value = df[columns].multiply(df.RRP, axis='index').sum()/2
    market_value.name = "MARKET_VALUE"
    
    dx = pd.DataFrame([energy,market_value]).transpose()
    dx.index.name = 'CATEGORY_ID'    
    dx.reset_index(inplace=True)
    
    dx.CATEGORY_ID = dx.CATEGORY_ID.apply(lambda x: meta.CATEGORY_MAP[x])
    dx['DATE'] = date
    dx['REGIONID'] = regionid
    
    return dx
    
def insert_daily_region_summary(d):
    df = select_region_day(d = d)
    for regionid, df_region in df.groupby(df.REGIONID):
        df_region = df_region.copy()
        split_interchange(df_region)
        dx = region_summary(df_region, d, regionid)
        dx.to_sql(name="DAILY_REGION_SUMMARY", index=None, con=NEMWEB_DERIVED, if_exists='append')
    #working version, completed from 1st May 2015

def daily_aggregator():
    todays_date = datetime.date.today()
    aggregate_duid(todays_date)
    aggregate_regionsum(todays_date)

def aggregate_duid(todays_date):
    sql = "SELECT MAX(DATE) FROM DAILY_DUID_OUTPUT"
    latest_date = NEMWEB_DERIVED.execute(sql).fetchall()[0][0]
    next_date = latest_date + datetime.timedelta(1)
    while next_date < todays_date:
        insert_daily_duid(next_date)
        next_date += datetime.timedelta(1)

def aggregate_regionsum(todays_date):
    sql = "SELECT MAX(DATE) FROM DAILY_REGION_SUMMARY"
    latest_date = NEMWEB_DERIVED.execute(sql).fetchall()[0][0]
    next_date = latest_date + datetime.timedelta(1)
    while next_date < todays_date:
        insert_daily_region_summary(next_date)
        next_date += datetime.timedelta(1)
