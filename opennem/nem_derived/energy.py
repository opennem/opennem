import datetime
import pandas as pd
from sqlalchemy import create_engine
from dms_daemon.nem_derived import meta
from dms_daemon import orm

#supress data truncation warnings
import MySQLdb
import warnings
warnings.filterwarnings('ignore', category=MySQLdb.Warning)

engine = orm.engine_derived


def duid_dataframe_generator(df,columns = ['DUID','INITIALMW','QUALITY_FLAG']):
    for duid, dx in df.groupby('DUID'):
        yield DUID(dx[columns],columns[1])
        
def nsduid_dataframe_generator(df,columns = ['DUID','MWH_READING','QUALITY_FLAG']):
    for duid, dx in  df.groupby('DUID'):
        yield NonSchedDUID(dx[columns],columns[1])
        
def data_check(df):
    for ds in duid_dataframe_generator(df):
        try:
            ds.validate_scada_data()
        except Exception as E:
            #first full day of new duid (with no midnight recording)
            if (ds.index[0].time() == datetime.time(0,5)) & (ds.data_length==289):
                continue
            #day before first full day (of new duid)
            elif (ds.index[0].time() == datetime.time(0,5)) & (ds.data_length==1):
                continue
            #last full day of old duid (with no 5 past midnight recording)            
            elif (ds.index[-1].time() == datetime.time(0,0)) & (ds.data_length==289):
                continue
            #day after last full day of old new day 
            elif (ds.index[-1].time() == datetime.time(0,0)) & (ds.data_length==1):                
                continue
            #nothing before hand                
            elif (ds.duid[:3] == "RT_") & (ds.sum()==0):
                #might be data here
                continue
            elif check_duid_range(ds, check="MIN") == True:
                #might be data here
                continue                
            #nothing afterwards                 
            elif check_duid_range(ds, check="MAX") == True:
                #might be data here
                continue
            else:
                raise

def get_solution(d1=datetime.datetime(2017,1,1),db='nemweb'):
    d2 = d1 + datetime.timedelta(1,300)
    sql =    "SELECT S.SETTLEMENTDATE, S.DUID, S.INITIALMW, S.INTERVENTION, 0 as QUALITY_FLAG "\
            "FROM DISPATCH_UNIT_SOLUTION S "\
            "INNER JOIN ("\
                "SELECT SETTLEMENTDATE, DUID, MAX(INTERVENTION) as I_FLAG "\
                "FROM DISPATCH_UNIT_SOLUTION "\
                "WHERE SETTLEMENTDATE >= '{0}' "\
                    "AND SETTLEMENTDATE <=  '{1}' "\
                "GROUP BY SETTLEMENTDATE, DUID) AS S2 "\
            "ON S2.SETTLEMENTDATE = S.SETTLEMENTDATE "\
                "AND S2.DUID = S.DUID "\
                "AND S2.I_FLAG = S.INTERVENTION".format(d1,d2)
    df = pd.read_sql(sql, con=orm.engine2)
    return DailyDispatch(d1,df)    
    
def get_non_schedgen(d1=datetime.datetime(2017,1,1),db='nemweb'):
    d2 = d1 + datetime.timedelta(1,300)
    sql =    "SELECT INTERVAL_DATETIME AS SETTLEMENTDATE, DUID, MWH_READING, 0 as QUALITY_FLAG "\
            "FROM METER_DATA_GEN_DUID "\
            "WHERE INTERVAL_DATETIME >= '{0}' "\
                "AND INTERVAL_DATETIME <=  '{1}'".format(d1,d2)
    df = pd.read_sql(sql, con=orm.engine2)
    return df
    #return DailyDispatch(d1,df)    
                
class DailyDispatch(pd.DataFrame):
    """ pandas DataFrame sublcass 
        - additional meta data (date of dispatch data)
        - additional methods to process (insert) duid data"""
    def __init__(self, d1, df):
        pd.DataFrame.__init__(self,df)                
        self.date = d1.date()
        self.d1 = d1
        self.d2 = self.d1 + datetime.timedelta(1,300)
        
    def data_transaction(self):    
        connection =  engine.connect()
        self.__transaction =  connection.begin()
        
        try:
            self.process_data()
            self.__transaction.commit()                    
            connection.close()
        except Exception as E:
            self.__transaction.rollback()
            connection.close()
            raise E
            
    def process_data(self):
        for duid in duid_dataframe_generator(self):
            if (duid.data_length == 1) & (duid.df.INITIALMW.sum()==0):
                continue
            if (duid.data_length == 1) & (duid.df.index[0]==datetime.datetime(2011,5,17)) & (duid.duid_id == 63):        
                continue
            if (duid.data_length == 1) & (duid.df.index[0]==datetime.datetime(2014,8,29,0,5)) & (duid.duid_id == 293):        
                continue

            if (duid.data_length == 1) & (duid.df.index[0]==datetime.datetime(2015,7,1,0,5)) & (duid.duid_id == 339):        
                continue

            if (duid.data_length == 1) & (duid.df.index[0]==datetime.datetime(2015,7,1,0,5)) & (duid.duid_id == 349):        
                continue

            if (duid.data_length == 1) & (duid.df.index[0]==datetime.datetime(2015,7,1,0,5)) & (duid.duid_id == 350):        
                continue

            if (duid.data_length == 1) & (duid.df.index[0]==datetime.datetime(2015,7,1)) & (duid.duid_id == 218):        
                continue

            if (duid.data_length == 1) & (duid.df.index[0]==datetime.datetime(2015,7,1)) & (duid.duid_id == 236):        
                continue

            if (duid.data_length == 1) & (duid.df.index[0]==datetime.datetime(2010,8,20,0,5)) & (duid.duid_id == 161):
                #waterloo wf        
                continue            
                
            if (duid.data_length == 1) & (duid.df.index[0]==datetime.datetime(2009,9,22)) & (duid.duid_id == 298):
                #mckay2 gt 
                continue                        
            
            if (duid.data_length == 1) & (duid.df.index[0]==datetime.datetime(2019,6,19,0,5)) & (duid.duid_id == 749):
                #first_day lal lal / Yendoon
                continue                        

            if (duid.data_length == 1) & (duid.df.index[0]==datetime.datetime(2020,4,7,0,5)) & (duid.duid_id == 769):
                #Elaine
                continue
                
            if (duid.df.index[0]==datetime.datetime(2019,10,22)) & (duid.duid_id == 3):
                #Blowering problem (missing day)
                continue                        

            if (duid.df.index[0]==datetime.datetime(2019,10,23,4,5)) & (duid.duid_id == 3):
                #Blowering problem (missing day = 22-23)
                continue                        

            else: 
                duid.validate_scada_data(self.d1,self.d2)                
                self.__insert_duid_data__(duid)
                    
    def __insert_duid_data__(self,duid,test=""):
        df_t =duid.trading_energy_data()        
        df_t.to_sql(name="TRADING_DUID_OUTPUT{}".format(test), index=None, con=self.__transaction.connection, if_exists='append')        
        
class DailyNonSched(DailyDispatch): 
    def __init__(self, d1, df):
        DailyDispatch.__init__(self,d1,df)    
        
    def process_data(self):
        for duid in nsduid_dataframe_generator(self, columns=['DUID','MWH_READING','QUALITY_FLAG']):        
            if (duid.duid == 'GERMCRK') & (duid.df.index[0].date() == datetime.date(2018,4,9)):
                df = german_creek(duid.df, self.d1, self.d2, backward=False)
                gc_interpolater_one(df, test="")#_TEST        
                continue
            try:            
                duid.validate_scada_data(self.d1,self.d2)
            except:                    
                try:
                    duid._NonSchedDUID__interpolate_missing_data(self.d1,self.d2)
                except:
                    not_na = duid.df[duid.df.MWH_READING.notna()]
                    if (duid.data_length == 1) & (not_na.index[0].time() == datetime.time(0,5)):
                        continue
                    elif (duid.duid == "LRSF1") & (duid.df.index[0].date() <= datetime.date(2018,5,5)):
                        print("LRSF1 commissioning")
                        continue
                    elif (duid.duid == 'GERMCRK') & (duid.df.index[0].date() == datetime.date(2018,4,12)):            
                        df = german_creek(duid.df, self.d1, self.d2, backward=True)
                        gc_interpolater(df, test="")#_TEST        
                        continue                    
                    else:
                        raise Exception ("New issue", duid, duid.duid_id, duid.df.index[0].date())
            self.__insert_duid_data__(duid,test="")#_TEST        
            
class DUID():
    """Class for storing a days worth of duid data"""
    def __init__(self,dataframe,data_col='INITIALMW'):            
        self.duid_id = dataframe.DUID[0]
        self.duid = meta.DUID_KEYS[self.duid_id]
        self.df = dataframe    
        self.data_length = len(set(self.df.index))
        self.data_col = data_col
    
    def __repr__(self):
        return "{0}".format(self.duid)
        
    def validate_scada_data(self,d1,d2):                

        if self.data_length < 290:
            self.__process_missing_data(d1,d2)
            
        elif self.data_length > 290:
            if self.df.index[0] == datetime.datetime(2001,4,8):
                #huge gap over 2 days (2001-04-08)                
                self.__interpolate_missing_data(d1,d2,quality_flag=2)
            else:        
                raise ExtraDataError(self.data_length,self.duid_id,self.df.index[0].date())                    
            
            
    def __process_missing_data(self,d1,d2):
        #last data point missing (e.g. where duid retired)
        #need to interpolate (fill) last value (quality unaffected, flag is zero)
        if (self.df.index[-1].time() == datetime.time(0,0)) & (self.data_length==289):                
            self.__interpolate_missing_data(d1,d2,quality_flag=0)            
        
        #first day, new duid (duid = 639, HDWF3)
        elif (self.df[self.data_col].sum()==0) & (self.duid_id == 639):                
            self.__interpolate_missing_data(d1,d2,quality_flag=0)
            
        #first day, new duid (duid = 691)
        elif (self.df.index[0]==datetime.datetime(2018,7,19,0,5)) & (self.duid_id == 691):                
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #first day, new duid (duid = 133, LKBONNY2)
        elif (self.df.index[0]==datetime.datetime(2007,5,31,10,55)) & (self.duid_id == 133):                
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #first day, new duid (duid = 86, KPP_1)
        elif (self.df.index[0]==datetime.datetime(2007,4,3,10,50)) & (self.duid_id == 86):                
            self.__interpolate_missing_data(d1,d2,quality_flag=0)    
            
        #first day, new duid (duid = 164,165,166, BBTHREE 1,2,3)
        elif (self.df.index[0]==datetime.datetime(2006,6,8,11,0)) & (self.duid_id >= 164) & (self.duid_id <= 166):                
            self.__interpolate_missing_data(d1,d2,quality_flag=0)
            
        #first day, new duid (duid = 56 Braemar1)
        elif (self.df.index[0]==datetime.datetime(2006,4,26,10,15)) & (self.duid_id >= 56) & (self.duid_id <= 58):                
            self.__interpolate_missing_data(d1,d2,quality_flag=0)
            
        #first day, new duid (duid = 218 LAVNORTH)
        elif (self.df.index[0]==datetime.datetime(2006,3,2,16,20)) & (self.duid_id == 218):                
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #first day, new duid (duid = 236 VPGS)
        elif (self.df.index[0]==datetime.datetime(2006,1,31,13,35)) & (self.duid_id == 236):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #last day, old duids (duid = 336, 337, 338, 339, 340, 341)
        elif (self.df.index[0]==datetime.datetime(2006,1,31,0,0)) & (self.duid_id >= 336) & (self.duid_id <= 341):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #skip RTs, where sum = zero
        elif (self.duid[:3] == "RT_") & (self.df[self.data_col].sum()==0):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #skip DGs, where sum = zero (dummy generators)
        elif (self.duid[:3] == "DG_") & (self.df[self.data_col].sum()==0):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #first day (bastyon, 163)         #possible re-registration as scheduled?
        elif (self.df.index[0]==datetime.datetime(2005,5,16,13,35)) & (self.duid_id == 163):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #first day (CETHUNA, 168) possible re-registration as scheduled?
        elif (self.df.index[0]==datetime.datetime(2005,5,16,13,35)) & (self.duid_id == 168):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #first day (DEVILS_G, 170) possible re-registration as scheduled - whole heap of tas hydro generator re-classified)
        elif (self.df.index[0]==datetime.datetime(2005,5,16,13,35)) & (self.duid_id >= 170) & (self.duid_id <= 190):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #first day (ANGAS1 & ANGAS2, 119,120)
        elif (self.df.index[0]==datetime.datetime(2004,12,30,12,55)) & (self.duid_id >= 119) & (self.duid_id <= 120):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #first day (YABULU2, 116)
        elif (self.df.index[0]==datetime.datetime(2004,10,21,11,5)) & (self.duid_id == 116):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #first day (BellBay3, 342) possible re-registration as scheduled - whole heap of tas hydro generator re-classified)
        elif (self.df.index[0]==datetime.datetime(2005,5,16,13,35)) & (self.duid_id >= 342) & (self.duid_id <= 343):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)


        #last day (swanbank D, 314) 
        elif (self.df.index[0]==datetime.datetime(2004,6,1)) & (self.duid_id == 314):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #last day (swanbank E, 313)
        elif (self.df.index[0]==datetime.datetime(2003,3,4)) & (self.duid_id == 313):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #last day (TNPS1, 112)
        elif (self.df.index[0]==datetime.datetime(2002,9,16,17,5)) & (self.duid_id == 112):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #last day ('MRIDGE', 299)
        elif (self.df.index[0]==datetime.datetime(2002,7,16,0,0)) & (self.duid_id == 299):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #first day (Swanbank E, 107)
        elif (self.df.index[0]==datetime.datetime(2002,5,15,10,35)) & (self.duid_id == 107):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #first day (AGLSOM, 193)
        elif (self.df.index[0]==datetime.datetime(2002,1,10,10,5)) & (self.duid_id == 193):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #first day (AGLHAL, 118)
        elif (self.df.index[0]==datetime.datetime(2001,12,18,9,5)) & (self.duid_id == 118):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #first day (BDL02, 196)
        elif (self.df.index[0]==datetime.datetime(2001,12,13,8,5)) & (self.duid_id == 196):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #first day (LYGS1, 330)
        elif (self.df.index[0]==datetime.datetime(2001,12,12,8,5)) & (self.duid_id >= 330) & (self.duid_id <= 335):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)


        #last day SWAN A, 307)
        elif (self.df.index[0]==datetime.datetime(2002,7,16,0,0)) & (self.duid_id >= 307) & (self.duid_id <= 313):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)
            
            
        #first day QPS1, 146
        elif (self.df.index[0]==datetime.datetime(2001,11,8,10,50)) & (self.duid_id >= 145) & (self.duid_id <= 148):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)
            
        #last day NGTS, 300
        elif (self.df.index[0]==datetime.datetime(2001,10,9)) & (self.duid_id == 300):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)
            
        #last day SNOWY 1-6, 301-306
        elif (self.df.index[0]==datetime.datetime(2001,9,24)) & (self.duid_id >= 301) & (self.duid_id <= 306):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)


        #first data point missing (e.g. where duid first added)    
        #can ignore first data point (not used in interpolation)
        elif (self.df.index[0].time() == datetime.time(0,5)) & (self.data_length==289):                        
            pass
            
            
        #actual gap in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2001,9,25)):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)


        #actual gap in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2001,8,20)):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)            
        
        #actual gap in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2001,8,7)):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)
        
        #actual gap in the data!     ("known gap")    
        elif (self.df.index[0]==datetime.datetime(2001,6,18)):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)
            
        #actual gap in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2001,8,6)):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)
            
        #actual gap in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2001,7,5)):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)
            
        #two gaps in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2001,6,5)):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)
            
        #three gaps in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2001,5,21)):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)            
            
        #two gaps in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2001,3,28)):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)            
            
        #three gaps in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2001,2,27)):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)        
            
        #single gaps in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2001,2,19)):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)        
            
        #double gap in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2001,2,5)):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)        
            
        #two gaps in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2000,12,7)):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)        
    
        #four gaps in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2000,8,24)):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)        

        #big gap in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2000,8,23)):
            self.__interpolate_missing_data(d1,d2,quality_flag=2)        

        # gap in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2000,8,22)):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)
            
        # gap in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2000,8,1)):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)

        # gap in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2000,7,17)):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)    
            
        # big gap in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2000,5,13)):
            self.__interpolate_missing_data(d1,d2,quality_flag=2)    

        # gap in the data!     ("known gap")
        elif (self.df.index[0]==datetime.datetime(2000,6,27)):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)    
            
        # BW01 out of service or similar?
        elif (self.duid_id ==5 ) & (self.df.index[0]==datetime.datetime(2000,5,9,12)):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)
            
        #HUME NSW
        elif (self.duid_id ==22 ) & (self.df.index[0]==datetime.datetime(2000,5,9,13,35)):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)
            
        #HVGTS NSW
        elif (self.duid_id ==23 ) & (self.df.index[0]==datetime.datetime(2000,5,9,13,35)):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)
            
        #LD01
        elif (self.duid_id ==25 ) & (self.df.index[0]==datetime.datetime(2000,5,9,13,35)):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)

        #MM4
        elif (self.duid_id ==30 ) & (self.df.index[0]==datetime.datetime(2000,5,9,13,35)):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)
        
        #??
        elif (self.df[self.data_col].sum() == 0 ) & (self.df.index[0].date() == datetime.date(2000,5,9)):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)
            
        #pump1
        elif (self.duid_id==49) & (self.df.index[0]==datetime.datetime(2000,5,9,3,35)):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)
            
        #BARCALDN
        elif (self.duid_id==53) & (self.df.index[0]==datetime.datetime(2000,5,9,6,5)):
            self.__interpolate_missing_data(d1,d2,quality_flag=0)                
                
        #first non_sched_gen
        elif (self.duid_id==277) & (self.df.index[0]==datetime.datetime(2016,1,1,0,0)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            #gap of 1.5 hours
            self.__interpolate_missing_data(d1,d2,quality_flag=2)                    
            
        #ANGAS non_sched_gen
        elif (self.duid_id>=119) & (self.duid_id<=120) & (self.df.index[0]==datetime.datetime(2016,1,5,0,0)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            #long gap, but zero output
            self.__interpolate_missing_data(d1,d2,quality_flag=2)            
            
        #CHALLHWF non_sched_gen
        elif (self.duid_id==197) & (self.df.index[0]==datetime.datetime(2016,1,12,0,0)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            #long gap, but zero output
            self.__interpolate_missing_data(d1,d2,quality_flag=2)            
            
        #Angas non-sched
        elif (self.duid_id>=119) & (self.duid_id<=120) & (self.df.index[0]==datetime.datetime(2016,1,15,0,0)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            #long gap, but zero output
            self.__interpolate_missing_data(d1,d2,quality_flag=1)            
        
        #Angas non-sched
        elif (self.duid_id>=119) & (self.duid_id<=120) & (self.df.index[0]==datetime.datetime(2016,1,16,1,25)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            #long gap, but zero output
            self.__interpolate_missing_data(d1,d2,quality_flag=1)
            
        #CLOVER non_sched_gen
        elif (self.duid_id==198) & (self.df.index[0]==datetime.datetime(2016,1,17,0,0)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            #long gap, but zero output
            self.__interpolate_missing_data(d1,d2,quality_flag=1)            
            
        #PORTWF non_sched_gen
        elif (self.duid_id==234) & (self.df.index[0]==datetime.datetime(2016,1,17,0,0)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            #long gap, but zero output
            self.__interpolate_missing_data(d1,d2,quality_flag=1)
            
        #WAUBRAWF non_sched_gen
        elif (self.duid_id==237) & (self.df.index[0]==datetime.datetime(2016,1,17,0,0)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            #long gap, but zero output
            self.__interpolate_missing_data(d1,d2,quality_flag=1)
            
        #MLWF non_sched_gen
        elif (self.duid_id==277) & (self.df.index[0]==datetime.datetime(2016,1,17,0,0)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            self.__interpolate_missing_data(d1,d2,quality_flag=1)
            
        #GERMCRK non_sched_gen
        elif (self.duid_id==280) & (self.df.index[0]==datetime.datetime(2016,1,22,0,0)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            self.__interpolate_missing_data(d1,d2,quality_flag=1)
            
        #GERMCRK non_sched_gen
        elif (self.duid_id==280) & (self.df.index[0]==datetime.datetime(2016,1,23,0,25)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            #day long gap
            self.__interpolate_missing_data(d1,d2,quality_flag=3)
            
        #GERMCRK non_sched_gen
        elif (self.duid_id==280) & (self.df.index[0]==datetime.datetime(2016,1,25,9,5)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            #day long gap
            self.__interpolate_missing_data(d1,d2,quality_flag=3)
            
        #YAMBUKWF non_sched_gen
        elif (self.duid_id==240) & (self.df.index[0]==datetime.datetime(2016,1,31)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            self.__interpolate_missing_data(d1,d2,quality_flag=2)
            
        #YAMBUKWF non_sched_gen
        elif (self.duid_id==240) & (self.df.index[0]==datetime.datetime(2016,2,6)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            self.__interpolate_missing_data(d1,d2,quality_flag=1)
            
        #YAMBUKWF non_sched_gen
        elif (self.duid_id==240) & (self.df.index[0]==datetime.datetime(2016,2,7,6,10)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            self.__interpolate_missing_data(d1,d2,quality_flag=2)
            
        #MLWF non_sched_gen
        elif (self.duid_id==277) & (self.df.index[0]==datetime.datetime(2016,2,7)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            self.__interpolate_missing_data(d1,d2,quality_flag=1)
            
        #ANGAS non_sched_gen
        elif (self.duid_id>=119) & (self.duid_id<=120) & (self.df.index[0]==datetime.datetime(2016,2,10)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            #zero)
            self.__interpolate_missing_data(d1,d2,quality_flag=0)
            
        #Generic ANGAS
        elif (self.duid_id>=119) & (self.duid_id<=120):
            self.__interpolate_missing_data(d1,d2,quality_flag=1)
            print ("Zero interpolation for ANGAS")
            if self.df[self.df.QUALITY_FLAG==1].max()[self.data_col] != 0:                
                raise MissingDataError(self.data_length,self.duid_id,self.df.index[0].date())
                
        #YAMBUKWF non_sched_gen
        elif (self.duid_id==240) & (self.df.index[0]==datetime.datetime(2016,2,13,0,5)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            self.__interpolate_missing_data(d1,d2,quality_flag=1)
            
            
        elif (self.df.index[0].time() ==datetime.time(0,0)) & (self.df.index[-1].time() ==datetime.time(0,5)):
            if self.data_length>285:
                self.__interpolate_missing_data(d1,d2,quality_flag=1)    
                print ("Interpolated data:", self.duid_id, self.duid, self.df.index[0].date())
            else:
                raise MissingDataError(self.data_length,self.duid_id,self.df.index[0].date())
            
        #generic first data and sum ==0
        elif (self.df[self.data_col].sum()==0) & self.__first_data():
            print (self.duid_id, self.duid, self.df.index[0]) 
            self.__interpolate_missing_data(d1,d2,quality_flag=0)            

       #First data = BULGANA1     
        elif (self.duid_id==771) & (self.df.index[0]==datetime.datetime(2020,5,12,0,5)):
            print (self.duid_id, self.duid, self.df.index[0]) 
            self.__interpolate_missing_data(d1,d2,quality_flag=0)            
            
        else:
            self.__interpolate_missing_data(d1,d2,quality_flag=1)
            print ("Zero interpolation for {0}".format(self.duid_id))
            if self.df[self.df.QUALITY_FLAG==1].max()[self.data_col] != 0:                
                raise MissingDataError(self.data_length,self.duid_id,self.df.index[0].date())
            
    def __interpolate_missing_data(self,d1,d2,quality_flag):            
        index = pd.date_range(start= d1, end= d2, freq='5min')
        self.df = self.df.reindex(index)
        self.df[self.data_col].interpolate(inplace=True, limit_direction='both')
        self.df['QUALITY_FLAG'].fillna(quality_flag, inplace=True)
    
    def trading_energy_data(self):
        df = pd.DataFrame(    [d for d in self.__trading_energy_generator()], 
                            columns = ['SETTLEMENTDATE', 'DUID','OUTPUT_MWH', 'QUALITY_FLAG' ]    )
        return df
            
    def __trading_energy_generator(self):
        self.df.sort_index(inplace=True)
        date = self.df.index[0].date()
        t_start = datetime.datetime(date.year, date.month,date.day,0,5)
    
        #48 trading intervals in the day 
        #(could be better with groupby function)
        for TI in range(48):
            #t_i initial timestamp of trading_interval, t_f = final timestamp of trading interval
            t_i = t_start + datetime.timedelta(0,1800*TI)
            t_f = t_start + datetime.timedelta(0,1800*(TI+1))
            
            d_ti = self.df[(self.df.index>=t_i) & (self.df.index<=t_f)]    
            #yield d_ti.index[-2], self.duid_id, self.__trapezium_integration(d_ti), d_ti['QUALITY_FLAG'].min()
            yield d_ti.index[-2], self.duid_id, self.__trapezium_integration(d_ti), d_ti['QUALITY_FLAG'].max()
    
    def __trapezium_integration(self,d_ti):
        return 0.5*(d_ti[self.data_col] * [1,2,2,2,2,2,1]).sum()/12        
        
    def __first_data(self):
        sql =    "SELECT MIN(SETTLEMENTDATE) FROM DISPATCH_UNIT_SOLUTION_OLD "\
            "WHERE DUID = {0}".format(self.duid_id)
        cursor = engine.execute(sql)            
        return self.df.index[0]==cursor.fetchall()[0][0]
        

def aggregater(d = datetime.datetime(2010,12,31),db="nemweb"):
    while True:
        df = get_solution(d1=d,db=db)
        try:
            df.data_transaction()
        except DataError as E:
            raise E
            
        print(d)
        d-= datetime.timedelta(1)
        
def nonsched_aggregater(d = datetime.datetime(2016,1,12),db="nemweb"):
    #started at 2016-1-1
    #completed up to at 2016-1-2
    while True:
        df_raw = get_non_schedgen(d1=d,db=db)
        df = DailyNonSched(d1=d,df=df_raw)
        try:
            df.data_transaction()
        except DataError as E:
            raise E
            
        print(d)
        d+= datetime.timedelta(1)

def solution_aggregater(d,db="nemweb_live"):
    #d = "SELECT max(SETTLEMENTDATE) FROM nemweb_derived.TRADING_DUID_OUTPUT"
    d = datetime.datetime(d.year,d.month,d.day)
    while d.date() < datetime.date.today():
        df = get_solution(d1=d,db=db)
        try:
            df.data_transaction()
        except DataError as E:
            raise E        
        d+= datetime.timedelta(1)
        
def trading_aggregator():
    #TODO - check non sched / sched tables aggregation aligns
    cursor = orm.engine_derived.execute("SELECT max(SETTLEMENTDATE) FROM nemweb_derived.TRADING_DUID_OUTPUT")
    solution_aggregater(cursor.fetchall()[0][0],db="nemweb_live")
    non_schedgen_aggregator(cursor.fetchall()[0][0], db="nemweb_live")
            
class NonSchedDUID(DUID):
    """Class for storing a days worth of non-sched duid data"""
    def __init__(self,dataframe,data_col='MWH_READING'):    
        DUID.__init__(self, dataframe,data_col)
        
    def validate_scada_data(self,d1,d2):                
        if self.data_length < 290:
            self.__interpolate_missing_data(d1,d2)
        
    def __interpolate_missing_data(self,d1,d2):            
        index = pd.date_range(start= d1, end= d2, freq='5min')
        self.df = self.df.reindex(index)
        self.df = pd.concat(self.non_sched_yielder(d1=d1,d2=d2))
        self.df.MWH_READING.interpolate(inplace=True)
    
    def non_sched_yielder(self,d1=None,d2=None):
        new_group_flag = self.df.MWH_READING.isna() & self.df.MWH_READING.shift().notna()
        for i,group in self.df.groupby(new_group_flag.cumsum()):                        
            nan_count = sum(group.MWH_READING.isna())
            dx = group.copy()
            if self.df.MWH_READING.max() == 0:
                #Interpolating zero gen
                dx.loc[dx.MWH_READING.isna(),"QUALITY_FLAG"]=1                
            
            elif nan_count <= 6:
                #one trading_interval or less interpolated
                dx.loc[dx.MWH_READING.isna(),"QUALITY_FLAG"]=1                
            elif nan_count <= 24:
                #one more than one trading interval, less than 2 hours interpolated
                dx.loc[dx.MWH_READING.isna(),"QUALITY_FLAG"]=2
            elif nan_count <= 144:
                print ("Warning: {0} nan count = {1}".format(self.duid, nan_count))
                #one more than 2 hours trading interval, less than 12 hours interpolated
                dx.loc[dx.MWH_READING.isna(),"QUALITY_FLAG"]=3
            elif (self.duid == 'GRIFSF1') & (self.df.index[0].date() <= datetime.date(2018,4,20)):                
                #essentially interpolating zero ? Commissioning?
                # first gen for Griffith solar farm
                dx.loc[dx.MWH_READING.isna(),"QUALITY_FLAG"]=1
            else:
                print (nan_count)
                raise MissingDataError(self.data_length,self.duid_id,self.df.index[0].date())            
            yield dx
            

def gc_interpolater(df, test=""): #_test
    #only included current and complete empty days
    dx = df[df.index.date>df.index[0].date()]
    d0 = dx.index[0] 
    dn = d0 + datetime.timedelta(1,300)
    
    while dn <= dx.index[-1]:
        d = dx[(dx.index>=d0) & (dx.index<=dn)]
        duid = NonSchedDUID(d)
        df_t = duid.trading_energy_data()

        df_t.to_sql(name="TRADING_DUID_OUTPUT{}".format(test), index=None, con=engine, if_exists='append')                

        d0 += datetime.timedelta(1)
        dn += datetime.timedelta(1)    
        
def gc_interpolater_one(df, test=""): #_test
    #only first day    
    d0 = df.index[0] 
    dn = d0 + datetime.timedelta(1,300)
    
    
    d = df[(df.index>=d0) & (df.index<=dn)]

    duid = NonSchedDUID(d)
    df_t = duid.trading_energy_data()

    df_t.to_sql(name="TRADING_DUID_OUTPUT{}".format(test), index=None, con=engine, if_exists='append')            

def non_schedgen_aggregator(d_trading, db="nemweb_live"):    
    #d_trading = "SELECT max(SETTLEMENTDATE) FROM nemweb_derived.TRADING_DUID_OUTPUT"
    
    #this needs to be more sophisticates
    #last date metered = YYYY-MM-DD 04:00
    #last date trading = YYYY-MM-DD 00:00  (metered minus 4hrs)    
    
    cursor = orm.engine2.execute("SELECT MAX(INTERVAL_DATETIME) FROM nemweb_live.METER_DATA_GEN_DUID")
    d_metered = cursor.fetchall()[0][0]
    
    d = datetime.datetime(d_trading.year,d_trading.month,d_trading.day)

    while d.date() < d_metered.date():
        print (d)    
        df_ns = get_non_schedgen(d1=d,db=db)
        ns =  DailyNonSched(d,df_ns)
            
        ns.data_transaction()
        d+= datetime.timedelta(1)
        
                        
    
                
def check_duid_range(ds, check="MIN"):
    sql =    "SELECT {0}(SETTLEMENTDATE) FROM DISPATCH_UNIT_SOLUTION_OLD "\
            "WHERE DUID = {1}".format(check,ds.duid_id)

    cursor = engine.execute(sql)
    result = cursor.fetchall()[0][0]
            
    if (ds.index[0]==result) & (check == "MIN"):
        return True            
        
    elif (ds.index[-1]==result) & (check == "MAX"):
        return True
        
    else:
        return False

def range_check():
    ds = datetime.datetime(2014,8,28)
    while True:
        ds -= datetime.timedelta(1)
        print(ds)
        df = select_day_solution(d1=ds)
        data_check(df)        
        
def select_state(regionid=3):
    sql = "SELECT D.TECHFUEL_ID,SUM(T.SCADAVALUE)/12000 as GWH "\
            "FROM nemweb.DISPATCH_UNIT_SCADA T "\
            "INNER JOIN nemweb_live.DUID D "\
            "ON D.ID = T.DUID "\
            "WHERE D.REGIONID = {0} "\
                "AND T.SETTLEMENTDATE > '2017-7-1' "\
            "GROUP BY D.TECHFUEL_ID".format(regionid)

    df = pd.read_sql(sql, con=orm.engine_derived, index_col="TECHFUEL_ID")        
    return df
        
class DataError(ValueError):
    def __str__(self):
        return "{0} data points for DUID {1} ({2})".format(self.args[0],self.args[1],self.args[2])

class MissingDataError(DataError):
    pass
    
class ExtraDataError(DataError):
    pass
    
    

"""
89 MPP_2 2001-08-15 09:35:00
72 CPP_4 2001-07-24 10:00:00
3 BLOWERNG 2001-06-22 11:35:00
21 GUTHEGA 2001-06-22 11:35:00
37 TUMUT3 2001-06-22 11:35:00
38 UPPTUMUT 2001-06-22 11:35:00
231 MURRAY 2001-06-22 11:35:00

"""

"""
interpolated_data"
- 2000-6-26
- 2000-6-16
- 2000-6-13
- 2000-5-15
"""
