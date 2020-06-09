import pandas as pd
from dms_daemon import orm

NEMWEB_META = orm.engine_meta
NEMWEB_DERIVED = orm.engine_derived

def load_gen_meta():
	#load "full register"
	sql = 	"SELECT R.* "\
			"FROM nemweb_meta.REGISTER R "\
			"INNER JOIN "\
				"(SELECT DUID, MAX(DATE) AS LATEST_DATE "\
				 "FROM REGISTER "\
				"GROUP BY DUID) AS D "\
			"ON R.DATE = D.LATEST_DATE and D.DUID = R.DUID"
	return pd.read_sql(sql, con=NEMWEB_META, index_col=None)
	
def duid_keys():
    sql = "SELECT ID, DUID FROM DUID"
    results = NEMWEB_META.execute(sql)
    return dict(results.fetchall())

def category_map():
    sql =     "SELECT NAME,ID FROM CATEGORY"
    results = NEMWEB_DERIVED.execute(sql)
    return dict(results.fetchall())

def region_map():
    sql =   "SELECT R.DUID, R.REGIONID "\
            "FROM REGISTER R "\
            "INNER JOIN LAST_REGISTERED_DATE LRD "\
                "ON LRD.LAST_DATE = R.DATE "\
            "AND LRD.DUID = R.DUID"
    results = NEMWEB_META.execute(sql)
    rdict = dict(results.fetchall())
    manual_mapping(rdict)
    return rdict

def manual_mapping(rdict):
    for duid, regionid in {724: 3,  #ancilliary Service SA (ASSENC1)
                           732: 1,  #ancialliary Service NSW (ASNACTW1)
                           747: 3,
                           753: 5,  #?Not sure - VSSEL1V1
                           763: 5,
                           767: 1,
                           }.items():
        if duid not in rdict:
            rdict[duid] = regionid
        else:
            print ("DUID exists ({0})".format(duid))

REGION_MAP = region_map()
DUID_KEYS = duid_keys()
CATEGORY_MAP = category_map()

#unused
gen_meta = load_gen_meta()

