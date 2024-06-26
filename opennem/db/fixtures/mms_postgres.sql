drop schema if exists mms cascade;

create schema if not exists mms;

set schema 'mms';

create table ANCILLARY_RECOVERY_SPLIT (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   SERVICE              varchar(10)          not null,
   PAYMENTTYPE          varchar(20)          not null,
   CUSTOMER_PORTION     numeric(8,5)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table ANCILLARY_RECOVERY_SPLIT
   add constraint ANCILLARY_RECOVERY_SPLIT_PK primary key (EFFECTIVEDATE, VERSIONNO, SERVICE, PAYMENTTYPE);





create index ANCILLARY_RECOVERY_SPLIT_LCX on ANCILLARY_RECOVERY_SPLIT (
LASTCHANGED ASC
);





create table APCCOMP (
   APCID                varchar(10)          not null,
   REGIONID             varchar(10)          null,
   STARTDATE            timestamp(3)             null,
   STARTPERIOD          numeric(3,0)         null,
   ENDDATE              timestamp(3)             null,
   ENDPERIOD            numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table APCCOMP
   add constraint APCCOMP_PK primary key (APCID);





create index APCCOMP_LCX on APCCOMP (
LASTCHANGED ASC
);





create table APCCOMPAMOUNT (
   APCID                varchar(10)          not null,
   PARTICIPANTID        varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(6,0)         not null,
   AMOUNT               numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table APCCOMPAMOUNT
   add constraint APCCOMPAMOUNT_PK primary key (APCID, PARTICIPANTID, VERSIONNO, PERIODID);





create index APCCOMPAMOUNT_LCX on APCCOMPAMOUNT (
LASTCHANGED ASC
);





create table APCCOMPAMOUNTTRK (
   APCID                varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDBY         varchar(10)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table APCCOMPAMOUNTTRK
   add constraint APCCOMPAMOUNTTRK_PK primary key (APCID, VERSIONNO);





create index APCCOMPAMOUNTTRK_LCX on APCCOMPAMOUNTTRK (
LASTCHANGED ASC
);





create table APEVENT (
   APEVENTID            numeric(22,0)        not null,
   EFFECTIVEFROMINTERVAL timestamp(3)             null,
   EFFECTIVETOINTERVAL  timestamp(3)             null,
   REASON               varchar(2000)        null,
   STARTAUTHORISEDBY    varchar(15)          null,
   STARTAUTHORISEDDATE  timestamp(3)             null,
   ENDAUTHORISEDBY      varchar(15)          null,
   ENDAUTHORISEDDATE    timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table APEVENT
   add constraint APEVENT_PK primary key (APEVENTID);





create index APEVENT_LCX on APEVENT (
LASTCHANGED ASC
);





create table APEVENTREGION (
   APEVENTID            numeric(22,0)        not null,
   REGIONID             varchar(10)          not null,
   LASTCHANGED          timestamp(3)             null,
   ENERGYAPFLAG         numeric(1,0)         null,
   RAISE6SECAPFLAG      numeric(1,0)         null,
   RAISE60SECAPFLAG     numeric(1,0)         null,
   RAISE5MINAPFLAG      numeric(1,0)         null,
   RAISEREGAPFLAG       numeric(1,0)         null,
   LOWER6SECAPFLAG      numeric(1,0)         null,
   LOWER60SECAPFLAG     numeric(1,0)         null,
   LOWER5MINAPFLAG      numeric(1,0)         null,
   LOWERREGAPFLAG       numeric(1,0)         null
);

alter table APEVENTREGION
   add constraint APEVENTREGION_PK primary key (APEVENTID, REGIONID);





create index APEVENTREGION_LCX on APEVENTREGION (
LASTCHANGED ASC
);





create table AUCTION (
   AUCTIONID            varchar(30)          not null,
   AUCTIONDATE          timestamp(3)             null,
   NOTIFYDATE           timestamp(3)             null,
   STARTDATE            timestamp(3)             null,
   ENDDATE              timestamp(3)             null,
   DESCRIPTION          varchar(100)         null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(30)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table AUCTION
   add constraint AUCTION_PK primary key (AUCTIONID);





create index AUCTION_LCX on AUCTION (
LASTCHANGED ASC
);





create table AUCTION_CALENDAR (
   CONTRACTYEAR         numeric(4,0)         not null,
   QUARTER              numeric(1,0)         not null,
   STARTDATE            timestamp(3)             null,
   ENDDATE              timestamp(3)             null,
   NOTIFYDATE           timestamp(3)             null,
   PAYMENTDATE          timestamp(3)             null,
   RECONCILIATIONDATE   timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null,
   PRELIMPURCHASESTMTDATE timestamp(3)             null,
   PRELIMPROCEEDSSTMTDATE timestamp(3)             null,
   FINALPURCHASESTMTDATE timestamp(3)             null,
   FINALPROCEEDSSTMTDATE timestamp(3)             null
);

alter table AUCTION_CALENDAR
   add constraint AUCTION_CALENDAR_PK primary key (CONTRACTYEAR, QUARTER);





create index AUCTION_CALENDAR_LCX on AUCTION_CALENDAR (
LASTCHANGED ASC
);





create table AUCTION_IC_ALLOCATIONS (
   CONTRACTYEAR         numeric(4,0)         not null,
   QUARTER              numeric(1,0)         not null,
   VERSIONNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   MAXIMUMUNITS         numeric(5,0)         null,
   PROPORTION           numeric(8,5)         null,
   AUCTIONFEE           numeric(17,5)        null,
   CHANGEDATE           timestamp(3)             null,
   CHANGEDBY            varchar(15)          null,
   LASTCHANGED          timestamp(3)             null,
   AUCTIONFEE_SALES     numeric(18,8)        null
);

alter table AUCTION_IC_ALLOCATIONS
   add constraint AUCTION_IC_ALLOCATIONS_PK primary key (CONTRACTYEAR, QUARTER, VERSIONNO, INTERCONNECTORID, FROMREGIONID);





create index AUCTION_IC_ALLOCATIONS_LCX on AUCTION_IC_ALLOCATIONS (
LASTCHANGED ASC
);





create table AUCTION_REVENUE_ESTIMATE (
   CONTRACTYEAR         numeric(4,0)         not null,
   QUARTER              numeric(1,0)         not null,
   VALUATIONID          varchar(15)          not null,
   VERSIONNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   MONTHNO              numeric(1,0)         not null,
   STARTDATE            timestamp(3)             null,
   ENDDATE              timestamp(3)             null,
   REVENUE              numeric(17,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table AUCTION_REVENUE_ESTIMATE
   add constraint AUCTION_REVENUE_ESTIMATE_PK primary key (CONTRACTYEAR, QUARTER, VALUATIONID, VERSIONNO, INTERCONNECTORID, FROMREGIONID, MONTHNO);





create index AUCTION_REVENUE_ESTIMATE_LCX on AUCTION_REVENUE_ESTIMATE (
LASTCHANGED ASC
);





create table AUCTION_REVENUE_TRACK (
   CONTRACTYEAR         numeric(4,0)         not null,
   QUARTER              numeric(1,0)         not null,
   VALUATIONID          varchar(15)          not null,
   VERSIONNO            numeric(3,0)         not null,
   EFFECTIVEDATE        timestamp(3)             null,
   STATUS               varchar(10)          null,
   DOCUMENTREF          varchar(30)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table AUCTION_REVENUE_TRACK
   add constraint AUCTION_REVENUE_TRACK_PK primary key (CONTRACTYEAR, QUARTER, VALUATIONID, VERSIONNO);





create index AUCTIONREVTRK_NDX_LCHD on AUCTION_REVENUE_TRACK (
LASTCHANGED ASC
);





create table AUCTION_RP_ESTIMATE (
   CONTRACTYEAR         numeric(4,0)         not null,
   QUARTER              numeric(1,0)         not null,
   VALUATIONID          varchar(15)          not null,
   VERSIONNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   RPESTIMATE           numeric(17,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table AUCTION_RP_ESTIMATE
   add constraint AUCTION_RP_ESTIMATE_PK primary key (CONTRACTYEAR, QUARTER, VALUATIONID, VERSIONNO, INTERCONNECTORID, FROMREGIONID);





create index AUCTION_RP_ESTIMATE_LCX on AUCTION_RP_ESTIMATE (
LASTCHANGED ASC
);





create table AUCTION_TRANCHE (
   CONTRACTYEAR         numeric(4,0)         not null,
   QUARTER              numeric(1,0)         not null,
   VERSIONNO            numeric(3,0)         not null,
   TRANCHE              numeric(2,0)         not null,
   AUCTIONDATE          timestamp(3)             null,
   NOTIFYDATE           timestamp(3)             null,
   UNITALLOCATION       numeric(18,8)        null,
   CHANGEDATE           timestamp(3)             null,
   CHANGEDBY            varchar(15)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table AUCTION_TRANCHE
   add constraint AUCTION_TRANCHE_PK primary key (CONTRACTYEAR, QUARTER, VERSIONNO, TRANCHE);





create index AUCTION_TRANCHE_LCX on AUCTION_TRANCHE (
LASTCHANGED ASC
);





create table BIDDAYOFFER (
   DUID                 varchar(10)          not null,
   BIDTYPE              varchar(10)          not null,
   SETTLEMENTDATE       timestamp(3)             not null,
   OFFERDATE            timestamp(3)             not null,
   VERSIONNO            numeric(22,0)        null,
   PARTICIPANTID        varchar(10)          null,
   DAILYENERGYCONSTRAINT numeric(12,6)        null,
   REBIDEXPLANATION     varchar(500)         null,
   PRICEBAND1           numeric(9,2)         null,
   PRICEBAND2           numeric(9,2)         null,
   PRICEBAND3           numeric(9,2)         null,
   PRICEBAND4           numeric(9,2)         null,
   PRICEBAND5           numeric(9,2)         null,
   PRICEBAND6           numeric(9,2)         null,
   PRICEBAND7           numeric(9,2)         null,
   PRICEBAND8           numeric(9,2)         null,
   PRICEBAND9           numeric(9,2)         null,
   PRICEBAND10          numeric(9,2)         null,
   MINIMUMLOAD          numeric(22,0)        null,
   T1                   numeric(22,0)        null,
   T2                   numeric(22,0)        null,
   T3                   numeric(22,0)        null,
   T4                   numeric(22,0)        null,
   NORMALSTATUS         varchar(3)           null,
   LASTCHANGED          timestamp(3)             null,
   MR_FACTOR            numeric(16,6)        null,
   ENTRYTYPE            varchar(20)          null
);

alter table BIDDAYOFFER
   add constraint BIDDAYOFFER_PK primary key (DUID, BIDTYPE, SETTLEMENTDATE, OFFERDATE);






create index BIDDAYOFFER_LCHD_IDX on BIDDAYOFFER (
LASTCHANGED ASC
);





create index BIDDAYOFFER_PART_IDX on BIDDAYOFFER (
PARTICIPANTID ASC
);





create table BIDDAYOFFER_D (
   SETTLEMENTDATE       timestamp(3)             not null,
   DUID                 varchar(10)          not null,
   BIDTYPE              varchar(10)          not null,
   BIDSETTLEMENTDATE    timestamp(3)             null,
   OFFERDATE            timestamp(3)             null,
   VERSIONNO            numeric(22,0)        null,
   PARTICIPANTID        varchar(10)          null,
   DAILYENERGYCONSTRAINT numeric(12,6)        null,
   REBIDEXPLANATION     varchar(500)         null,
   PRICEBAND1           numeric(9,2)         null,
   PRICEBAND2           numeric(9,2)         null,
   PRICEBAND3           numeric(9,2)         null,
   PRICEBAND4           numeric(9,2)         null,
   PRICEBAND5           numeric(9,2)         null,
   PRICEBAND6           numeric(9,2)         null,
   PRICEBAND7           numeric(9,2)         null,
   PRICEBAND8           numeric(9,2)         null,
   PRICEBAND9           numeric(9,2)         null,
   PRICEBAND10          numeric(9,2)         null,
   MINIMUMLOAD          numeric(22,0)        null,
   T1                   numeric(22,0)        null,
   T2                   numeric(22,0)        null,
   T3                   numeric(22,0)        null,
   T4                   numeric(22,0)        null,
   NORMALSTATUS         varchar(3)           null,
   LASTCHANGED          timestamp(3)             null,
   MR_FACTOR            numeric(16,6)        null,
   ENTRYTYPE            varchar(20)          null
);

alter table BIDDAYOFFER_D
   add constraint BIDDAYOFFER_D_PK primary key (SETTLEMENTDATE, DUID, BIDTYPE);





create index BIDDAYOFFER_D_LCHD_IDX on BIDDAYOFFER_D (
LASTCHANGED ASC
);





create index BIDDAYOFFER_D_PART_IDX on BIDDAYOFFER_D (
PARTICIPANTID ASC
);





create table BIDDUIDDETAILS (
   DUID                 varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   BIDTYPE              varchar(10)          not null,
   MAXCAPACITY          numeric(22,0)        null,
   MINENABLEMENTLEVEL   numeric(22,0)        null,
   MAXENABLEMENTLEVEL   numeric(22,0)        null,
   MAXLOWERANGLE        numeric(3,0)         null,
   MAXUPPERANGLE        numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table BIDDUIDDETAILS
   add constraint BIDDUIDDETAILS_PK primary key (DUID, EFFECTIVEDATE, VERSIONNO, BIDTYPE);





create index BIDDUIDDETAILS_LCHD_IDX on BIDDUIDDETAILS (
LASTCHANGED ASC
);





create table BIDDUIDDETAILSTRK (
   DUID                 varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table BIDDUIDDETAILSTRK
   add constraint BIDDUIDDETAILSTRK_PK primary key (DUID, EFFECTIVEDATE, VERSIONNO);





create index BIDDUIDDETAILSTRK_LCHD_IDX on BIDDUIDDETAILSTRK (
LASTCHANGED ASC
);





create table BIDOFFERFILETRK (
   PARTICIPANTID        varchar(10)          not null,
   OFFERDATE            timestamp(3)             not null,
   FILENAME             varchar(80)          not null,
   STATUS               varchar(10)          null,
   LASTCHANGED          timestamp(3)             null,
   AUTHORISEDBY         varchar(20)          null,
   AUTHORISEDDATE       timestamp(3)             null
);

alter table BIDOFFERFILETRK
   add constraint BIDOFFERFILETRK_FILE_UK unique (FILENAME);


alter table BIDOFFERFILETRK
   add constraint BIDOFFERFILETRK_PK primary key (PARTICIPANTID, OFFERDATE);





create index BIDOFFERFILETRK_LCHD_IDX on BIDOFFERFILETRK (
LASTCHANGED ASC
);





create table BIDPEROFFER (
   DUID                 varchar(10)          not null,
   BIDTYPE              varchar(10)          not null,
   SETTLEMENTDATE       timestamp(3)             not null,
   OFFERDATE            timestamp(3)             not null,
   PERIODID             numeric(22,0)        not null,
   VERSIONNO            numeric(22,0)        null,
   MAXAVAIL             numeric(12,6)        null,
   FIXEDLOAD            numeric(12,6)        null,
   ROCUP                numeric(6,0)         null,
   ROCDOWN              numeric(6,0)         null,
   ENABLEMENTMIN        numeric(6,0)         null,
   ENABLEMENTMAX        numeric(6,0)         null,
   LOWBREAKPOINT        numeric(6,0)         null,
   HIGHBREAKPOINT       numeric(6,0)         null,
   BANDAVAIL1           numeric(22,0)        null,
   BANDAVAIL2           numeric(22,0)        null,
   BANDAVAIL3           numeric(22,0)        null,
   BANDAVAIL4           numeric(22,0)        null,
   BANDAVAIL5           numeric(22,0)        null,
   BANDAVAIL6           numeric(22,0)        null,
   BANDAVAIL7           numeric(22,0)        null,
   BANDAVAIL8           numeric(22,0)        null,
   BANDAVAIL9           numeric(22,0)        null,
   BANDAVAIL10          numeric(22,0)        null,
   LASTCHANGED          timestamp(3)             null,
   PASAAVAILABILITY     numeric(12,0)        null,
   MR_CAPACITY          numeric(6,0)         null
);

alter table BIDPEROFFER
   add constraint BIDPEROFFER_PK primary key (DUID, BIDTYPE, SETTLEMENTDATE, OFFERDATE, PERIODID);





create index BIDPEROFFER_LCHD_IDX on BIDPEROFFER (
LASTCHANGED ASC
);





create table BIDPEROFFER_D (
   SETTLEMENTDATE       timestamp(3)             not null,
   DUID                 varchar(10)          not null,
   BIDTYPE              varchar(10)          not null,
   BIDSETTLEMENTDATE    timestamp(3)             null,
   OFFERDATE            timestamp(3)             null,
   PERIODID             numeric(22,0)        null,
   VERSIONNO            numeric(22,0)        null,
   MAXAVAIL             numeric(12,6)        null,
   FIXEDLOAD            numeric(12,6)        null,
   ROCUP                numeric(6,0)         null,
   ROCDOWN              numeric(6,0)         null,
   ENABLEMENTMIN        numeric(6,0)         null,
   ENABLEMENTMAX        numeric(6,0)         null,
   LOWBREAKPOINT        numeric(6,0)         null,
   HIGHBREAKPOINT       numeric(6,0)         null,
   BANDAVAIL1           numeric(22,0)        null,
   BANDAVAIL2           numeric(22,0)        null,
   BANDAVAIL3           numeric(22,0)        null,
   BANDAVAIL4           numeric(22,0)        null,
   BANDAVAIL5           numeric(22,0)        null,
   BANDAVAIL6           numeric(22,0)        null,
   BANDAVAIL7           numeric(22,0)        null,
   BANDAVAIL8           numeric(22,0)        null,
   BANDAVAIL9           numeric(22,0)        null,
   BANDAVAIL10          numeric(22,0)        null,
   LASTCHANGED          timestamp(3)             null,
   PASAAVAILABILITY     numeric(12,0)        null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   MR_CAPACITY          numeric(6,0)         null
);

alter table BIDPEROFFER_D
   add constraint BIDPEROFFER_D_PK primary key (SETTLEMENTDATE, DUID, BIDTYPE, INTERVAL_DATETIME);





create index BIDPEROFFER_D_LCHD_IDX on BIDPEROFFER_D (
LASTCHANGED ASC
);





create table BIDTYPES (
   BIDTYPE              varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   DESCRIPTION          varchar(64)          null,
   NUMBEROFBANDS        numeric(3,0)         null,
   NUMDAYSAHEADPRICELOCKED numeric(2,0)         null,
   VALIDATIONRULE       varchar(10)          null,
   LASTCHANGED          timestamp(3)             null,
   SPDALIAS             varchar(10)          null
);

alter table BIDTYPES
   add constraint BIDTYPES_PK primary key (BIDTYPE, EFFECTIVEDATE, VERSIONNO);





create index BIDTYPES_LCHD_IDX on BIDTYPES (
LASTCHANGED ASC
);





create table BIDTYPESTRK (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table BIDTYPESTRK
   add constraint BIDTYPESTRK_PK primary key (EFFECTIVEDATE, VERSIONNO);





create index BIDTYPESTRK_LCHD_IDX on BIDTYPESTRK (
LASTCHANGED ASC
);





create table BILLADJUSTMENTS (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         null,
   PARTICIPANTID        varchar(10)          not null,
   PARTICIPANTTYPE      varchar(10)          null,
   ADJCONTRACTYEAR      numeric(4,0)         not null,
   ADJWEEKNO            numeric(3,0)         not null,
   ADJBILLRUNNO         numeric(3,0)         not null,
   PREVAMOUNT           numeric(16,6)        null,
   ADJAMOUNT            numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null,
   LRS                  numeric(15,5)        null,
   PRS                  numeric(15,5)        null,
   OFS                  numeric(15,5)        null,
   IRN                  numeric(15,5)        null,
   IRP                  numeric(15,5)        null,
   INTERESTAMOUNT       numeric(15,5)        null
);

alter table BILLADJUSTMENTS
   add constraint BILLADJUSTMENTS_PK primary key (CONTRACTYEAR, WEEKNO, ADJCONTRACTYEAR, ADJWEEKNO, ADJBILLRUNNO, PARTICIPANTID);





create index BILLADJUSTMENTS_NDX2 on BILLADJUSTMENTS (
PARTICIPANTID ASC
);





create index BILLADJUSTMENTS_LCX on BILLADJUSTMENTS (
LASTCHANGED ASC
);





create table BILLINGAPCCOMPENSATION (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   APCCOMPENSATION      numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINGAPCCOMPENSATION
   add constraint BILLINGAPCCOMPENSATION_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID);





create index BILLINGAPCCOMPENSATION_LCX on BILLINGAPCCOMPENSATION (
LASTCHANGED ASC
);





create table BILLINGAPCRECOVERY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   APCRECOVERY          numeric(15,0)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINGAPCRECOVERY
   add constraint BILLINGAPCRECOVERY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID);





create index BILLINGAPCRECOVERY_LCX on BILLINGAPCRECOVERY (
LASTCHANGED ASC
);





create table BILLINGASPAYMENTS (
   REGIONID             varchar(10)          null,
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONNECTIONPOINTID    varchar(10)          not null,
   RAISE6SEC            numeric(15,5)        null,
   LOWER6SEC            numeric(15,5)        null,
   RAISE60SEC           numeric(15,5)        null,
   LOWER60SEC           numeric(15,5)        null,
   AGC                  numeric(15,5)        null,
   FCASCOMP             numeric(15,5)        null,
   LOADSHED             numeric(15,5)        null,
   RGUL                 numeric(15,5)        null,
   RGUU                 numeric(15,5)        null,
   REACTIVEPOWER        numeric(15,5)        null,
   SYSTEMRESTART        numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   LOWER5MIN            numeric(15,5)        null,
   RAISE5MIN            numeric(15,5)        null,
   LOWERREG             numeric(15,5)        null,
   RAISEREG             numeric(15,5)        null,
   AVAILABILITY_REACTIVE numeric(18,8)        null,
   AVAILABILITY_REACTIVE_RBT numeric(18,8)        null
);

alter table BILLINGASPAYMENTS
   add constraint BILLINGASPAYMENTS_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, CONNECTIONPOINTID);





create index BILLINGASPAYMENTS_LCX on BILLINGASPAYMENTS (
LASTCHANGED ASC
);





create table BILLINGASRECOVERY (
   REGIONID             varchar(10)          not null,
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   RAISE6SEC            numeric(15,5)        null,
   LOWER6SEC            numeric(15,5)        null,
   RAISE60SEC           numeric(15,5)        null,
   LOWER60SEC           numeric(15,5)        null,
   AGC                  numeric(15,5)        null,
   FCASCOMP             numeric(15,5)        null,
   LOADSHED             numeric(15,5)        null,
   RGUL                 numeric(15,5)        null,
   RGUU                 numeric(15,5)        null,
   REACTIVEPOWER        numeric(15,5)        null,
   SYSTEMRESTART        numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   RAISE6SEC_GEN        numeric(15,5)        null,
   LOWER6SEC_GEN        numeric(15,5)        null,
   RAISE60SEC_GEN       numeric(15,5)        null,
   LOWER60SEC_GEN       numeric(15,5)        null,
   AGC_GEN              numeric(15,5)        null,
   FCASCOMP_GEN         numeric(15,5)        null,
   LOADSHED_GEN         numeric(15,5)        null,
   RGUL_GEN             numeric(15,5)        null,
   RGUU_GEN             numeric(15,5)        null,
   REACTIVEPOWER_GEN    numeric(15,5)        null,
   SYSTEMRESTART_GEN    numeric(15,5)        null,
   LOWER5MIN            numeric(15,5)        null,
   RAISE5MIN            numeric(15,5)        null,
   LOWERREG             numeric(15,5)        null,
   RAISEREG             numeric(15,5)        null,
   LOWER5MIN_GEN        numeric(16,6)        null,
   RAISE5MIN_GEN        numeric(16,6)        null,
   LOWERREG_GEN         numeric(16,6)        null,
   RAISEREG_GEN         numeric(16,6)        null,
   AVAILABILITY_REACTIVE numeric(18,8)        null,
   AVAILABILITY_REACTIVE_RBT numeric(18,8)        null,
   AVAILABILITY_REACTIVE_GEN numeric(18,8)        null,
   AVAILABILITY_REACTIVE_RBT_GEN numeric(18,8)        null
);

alter table BILLINGASRECOVERY
   add constraint BILLINGASRECOVERY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID);





create index BILLINGASRECOVERY_LCX on BILLINGASRECOVERY (
LASTCHANGED ASC
);





create table BILLINGCALENDAR (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   STARTDATE            timestamp(3)             null,
   ENDDATE              timestamp(3)             null,
   PRELIMINARYSTATEMENTDATE timestamp(3)             null,
   FINALSTATEMENTDATE   timestamp(3)             null,
   PAYMENTDATE          timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null,
   REVISION1_STATEMENTDATE timestamp(3)             null,
   REVISION2_STATEMENTDATE timestamp(3)             null
);

alter table BILLINGCALENDAR
   add constraint BILLINGCALENDAR_PK primary key (CONTRACTYEAR, WEEKNO);





create index BILLINGCALENDAR_LCX on BILLINGCALENDAR (
LASTCHANGED ASC
);





create table BILLINGCPDATA (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONNECTIONPOINTID    varchar(10)          not null,
   AGGREGATEENERGY      numeric(16,6)        null,
   PURCHASES            numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null,
   MDA                  varchar(10)          not null
);

alter table BILLINGCPDATA
   add constraint BILLINGCPDATA_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, CONNECTIONPOINTID, MDA);





create index BILLINGCPDATA_NDX2 on BILLINGCPDATA (
PARTICIPANTID ASC
);





create index BILLINGCPDATA_LCX on BILLINGCPDATA (
LASTCHANGED ASC
);





create table BILLINGCPSUM (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   PARTICIPANTTYPE      varchar(10)          not null,
   PREVIOUSAMOUNT       numeric(16,6)        null,
   ADJUSTEDAMOUNT       numeric(16,6)        null,
   ADJUSTMENTWEEKNO     numeric(3,0)         null,
   ADJUSTMENTRUNNO      numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINGCPSUM
   add constraint BILLINGCPSUM_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, PARTICIPANTTYPE);





create index BILLINGCPSUM_LCX on BILLINGCPSUM (
LASTCHANGED ASC
);





create index BILLINGCPSUM_NDX2 on BILLINGCPSUM (
PARTICIPANTID ASC
);





create table BILLINGCUSTEXCESSGEN (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   SETTLEMENTDATE       timestamp(3)             not null,
   PERIODID             numeric(3,0)         not null,
   EXCESSGENPAYMENT     numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null,
   REGIONID             varchar(10)          not null
);

alter table BILLINGCUSTEXCESSGEN
   add constraint BILLINGCUSTEXCESSGEN_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID, SETTLEMENTDATE, PERIODID);





create index BILLINGCUSTEXCESSGEN_LCX on BILLINGCUSTEXCESSGEN (
LASTCHANGED ASC
);





create table BILLINGDAYTRK (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINGDAYTRK
   add constraint BILLINGDAYTRK_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, SETTLEMENTDATE);





create index BILLINGDAYTRK_LCX on BILLINGDAYTRK (
LASTCHANGED ASC
);





create table BILLINGEXCESSGEN (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   SETTLEMENTDATE       timestamp(3)             not null,
   PERIODID             numeric(3,0)         not null,
   EXCESSENERGYCOST     numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   REGIONID             varchar(10)          not null
);

alter table BILLINGEXCESSGEN
   add constraint BILLINGEXCESSGEN_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID, SETTLEMENTDATE, PERIODID);





create index BILLINGEXCESSGEN_LCX on BILLINGEXCESSGEN (
LASTCHANGED ASC
);





create index BILLINGEXCESSGEN_NDX2 on BILLINGEXCESSGEN (
PARTICIPANTID ASC
);





create table BILLINGFEES (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   MARKETFEEID          varchar(10)          not null,
   RATE                 numeric(15,5)        null,
   ENERGY               numeric(16,6)        null,
   VALUE                numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   PARTICIPANTCATEGORYID varchar(10)          not null
);

alter table BILLINGFEES
   add constraint BILLINGFEES_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, MARKETFEEID, PARTICIPANTCATEGORYID);





create index BILLINGFEES_LCX on BILLINGFEES (
LASTCHANGED ASC
);





create index BILLINGFEES_NDX2 on BILLINGFEES (
PARTICIPANTID ASC
);





create table BILLINGFINANCIALADJUSTMENTS (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   PARTICIPANTTYPE      varchar(10)          null,
   ADJUSTMENTITEM       varchar(64)          not null,
   AMOUNT               numeric(15,5)        null,
   VALUE                numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   FINANCIALCODE        numeric(10,0)        null,
   BAS_CLASS            varchar(30)          null
);

alter table BILLINGFINANCIALADJUSTMENTS
   add constraint BILLINGFINANCIALADJUSTMENTS_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, ADJUSTMENTITEM);





create index BILLINGFINANCIALADJUSTMEN_LCX on BILLINGFINANCIALADJUSTMENTS (
LASTCHANGED ASC
);





create table BILLINGGENDATA (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONNECTIONPOINTID    varchar(10)          not null,
   STATIONID            varchar(10)          null,
   DUID                 varchar(10)          null,
   AGGREGATEENERGY      numeric(16,6)        null,
   SALES                numeric(16,6)        null,
   PURCHASES            numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null,
   PURCHASEDENERGY      numeric(16,6)        null,
   MDA                  varchar(10)          null
);

alter table BILLINGGENDATA
   add constraint BILLINGGENDATA_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, CONNECTIONPOINTID);





create index BILLINGGENDATA_LCX on BILLINGGENDATA (
LASTCHANGED ASC
);





create index BILLINGGENDATA_NDX2 on BILLINGGENDATA (
PARTICIPANTID ASC
);





create table BILLINGINTERRESIDUES (
   ALLOCATION           numeric(6,3)         null,
   TOTALSURPLUS         numeric(15,5)        null,
   INTERCONNECTORID     varchar(10)          not null,
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   SURPLUSVALUE         numeric(15,6)        null,
   LASTCHANGED          timestamp(3)             null,
   REGIONID             varchar(10)          not null
);

alter table BILLINGINTERRESIDUES
   add constraint BILLINGINTERRESIDUES_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, INTERCONNECTORID, REGIONID);





create index BILLINGINTERRESIDUES_LCX on BILLINGINTERRESIDUES (
LASTCHANGED ASC
);





create table BILLINGINTERVENTION (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   MARKETINTERVENTION   numeric(15,5)        null,
   TOTALINTERVENTION    numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINGINTERVENTION
   add constraint BILLINGINTERVENTION_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID);





create index BILLINGINTERVENTION_LCX on BILLINGINTERVENTION (
LASTCHANGED ASC
);





create table BILLINGINTERVENTIONREGION (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   REGIONINTERVENTION   numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINGINTERVENTIONREGION
   add constraint BILLINGINTERVENTIONREGION_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID);





create index BILLINGINTERVENTIONREGION_LCX on BILLINGINTERVENTIONREGION (
LASTCHANGED ASC
);





create table BILLINGINTRARESIDUES (
   ALLOCATION           numeric(6,3)         null,
   TOTALSURPLUS         numeric(15,5)        null,
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   SURPLUSVALUE         numeric(15,6)        null,
   LASTCHANGED          timestamp(3)             null,
   REGIONID             varchar(10)          not null
);

alter table BILLINGINTRARESIDUES
   add constraint BILLINGINTRARESIDUES_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID);





create index BILLINGINTRARESIDUES_LCX on BILLINGINTRARESIDUES (
LASTCHANGED ASC
);





create table BILLINGIRAUCSURPLUS (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(2,0)         not null,
   RESIDUEYEAR          numeric(4,0)         null,
   QUARTER              numeric(2,0)         null,
   BILLRUNNO            numeric(3,0)         not null,
   CONTRACTID           varchar(30)          not null,
   PARTICIPANTID        varchar(10)          not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   TOTALRESIDUES        numeric(15,5)        null,
   ADJUSTMENT           numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINGIRAUCSURPLUS
   add constraint BILLINGAUCSURPLUS_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, CONTRACTID, INTERCONNECTORID, FROMREGIONID, PARTICIPANTID);





create index BILLINGIRAUCSURPLUS_IDX_LC on BILLINGIRAUCSURPLUS (
LASTCHANGED ASC
);





create table BILLINGIRAUCSURPLUSSUM (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   RESIDUEYEAR          numeric(4,0)         not null,
   QUARTER              numeric(2,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   PARTICIPANTID        varchar(10)          not null,
   TOTALSURPLUS         numeric(15,5)        null,
   AUCTIONFEES          numeric(15,5)        null,
   ACTUALPAYMENT        numeric(15,5)        null,
   AUCTIONFEES_GST      numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   CSP_DEROGATION_AMOUNT numeric(18,8)        null,
   UNADJUSTED_IRSR      numeric(18,8)        null,
   NEGATIVE_RESIDUES    numeric(18,8)        null
);

alter table BILLINGIRAUCSURPLUSSUM
   add constraint BILLINGIRAUCSURPLUSSUM_PK primary key (CONTRACTYEAR, WEEKNO, RESIDUEYEAR, QUARTER, BILLRUNNO, INTERCONNECTORID, FROMREGIONID, PARTICIPANTID);





create index BILLINGIRAUCSURPSUM_LCX on BILLINGIRAUCSURPLUSSUM (
LASTCHANGED ASC
);





create table BILLINGIRFM (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   IRFMPAYMENT          numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINGIRFM
   add constraint BILLINGIRFM_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID);





create index BILLINGIRFM_LCX on BILLINGIRFM (
LASTCHANGED ASC
);





create table BILLINGIRNSPSURPLUS (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(2,0)         not null,
   RESIDUEYEAR          numeric(4,0)         null,
   QUARTER              numeric(2,0)         null,
   BILLRUNNO            numeric(3,0)         not null,
   CONTRACTID           varchar(30)          not null,
   PARTICIPANTID        varchar(10)          not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   TOTALRESIDUES        numeric(15,5)        null,
   ADJUSTMENT           numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINGIRNSPSURPLUS
   add constraint BILLINGNSPSURPLUS_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, CONTRACTID, INTERCONNECTORID, FROMREGIONID, PARTICIPANTID);





create index BILLINGIRNSPSURPLUS_LCX on BILLINGIRNSPSURPLUS (
LASTCHANGED ASC
);





create table BILLINGIRNSPSURPLUSSUM (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   RESIDUEYEAR          numeric(4,0)         not null,
   QUARTER              numeric(2,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   PARTICIPANTID        varchar(10)          not null,
   TOTALSURPLUS         numeric(15,5)        null,
   AUCTIONFEES          numeric(15,5)        null,
   AUCTIONFEES_GST      numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   CSP_DEROGATION_AMOUNT numeric(18,8)        null,
   UNADJUSTED_IRSR      numeric(18,8)        null
);

alter table BILLINGIRNSPSURPLUSSUM
   add constraint BILLINGIRNSPSURPLUSSUM_PK primary key (CONTRACTYEAR, WEEKNO, RESIDUEYEAR, QUARTER, BILLRUNNO, INTERCONNECTORID, FROMREGIONID, PARTICIPANTID);





create index BILLINGIRNSPSURPSUM_LCX on BILLINGIRNSPSURPLUSSUM (
LASTCHANGED ASC
);





create table BILLINGIRPARTSURPLUS (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(2,0)         not null,
   RESIDUEYEAR          numeric(4,0)         null,
   QUARTER              numeric(2,0)         null,
   BILLRUNNO            numeric(3,0)         not null,
   CONTRACTID           varchar(30)          not null,
   PARTICIPANTID        varchar(10)          not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   TOTALRESIDUES        numeric(15,5)        null,
   ADJUSTMENT           numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   ACTUALPAYMENT        numeric(15,5)        null
);

alter table BILLINGIRPARTSURPLUS
   add constraint BILLINGPARTSURPLUS_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, CONTRACTID, INTERCONNECTORID, FROMREGIONID, PARTICIPANTID);





create index BILLINGIRPARTSURPLUS_LCX on BILLINGIRPARTSURPLUS (
LASTCHANGED ASC
);





create table BILLINGIRPARTSURPLUSSUM (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   RESIDUEYEAR          numeric(4,0)         not null,
   QUARTER              numeric(2,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   PARTICIPANTID        varchar(10)          not null,
   TOTALSURPLUS         numeric(15,5)        null,
   AUCTIONFEES          numeric(15,5)        null,
   ACTUALPAYMENT        numeric(15,5)        null,
   AUCTIONFEES_GST      numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   CSP_DEROGATION_AMOUNT numeric(18,8)        null,
   UNADJUSTED_IRSR      numeric(18,8)        null,
   AUCTIONFEES_TOTALGROSS_ADJ numeric(18,8)        null
);

alter table BILLINGIRPARTSURPLUSSUM
   add constraint BILLINGIRPARTSURPLUSSUM_PK primary key (CONTRACTYEAR, WEEKNO, RESIDUEYEAR, QUARTER, BILLRUNNO, INTERCONNECTORID, FROMREGIONID, PARTICIPANTID);





create index BILLINGIRPARTSURPSUM_LCX on BILLINGIRPARTSURPLUSSUM (
LASTCHANGED ASC
);





create index BILLINGIRPARTSURPLUSSUM_I01 on BILLINGIRPARTSURPLUSSUM (
RESIDUEYEAR ASC,
QUARTER ASC
);





create table BILLINGPRIORADJUSTMENTS (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   ADJCONTRACTYEAR      numeric(4,0)         not null,
   ADJWEEKNO            numeric(3,0)         not null,
   ADJBILLRUNNO         numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   PREVAMOUNT           numeric(15,5)        null,
   ADJAMOUNT            numeric(15,5)        null,
   IRN                  numeric(15,5)        null,
   IRP                  numeric(15,5)        null,
   INTERESTAMOUNT       numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   IRSR_PREVAMOUNT      numeric(15,5)        null,
   IRSR_ADJAMOUNT       numeric(15,5)        null,
   IRSR_INTERESTAMOUNT  numeric(15,5)        null
);

alter table BILLINGPRIORADJUSTMENTS
   add constraint BILLINGPRIORADJUSTMENTS_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, ADJCONTRACTYEAR, ADJWEEKNO, ADJBILLRUNNO, PARTICIPANTID);





create index BILLINGPRIORADJUSTMENTS_NDX2 on BILLINGPRIORADJUSTMENTS (
PARTICIPANTID ASC,
LASTCHANGED ASC
);





create index BILLINGPRIORADJMNTS_NDX_LCHD on BILLINGPRIORADJUSTMENTS (
LASTCHANGED ASC
);





create table BILLINGREALLOC (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   COUNTERPARTY         varchar(10)          not null,
   VALUE                numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINGREALLOC
   add constraint BILLINGREALLOC_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, COUNTERPARTY);





create index BILLINGREALLOC_NDX2 on BILLINGREALLOC (
PARTICIPANTID ASC
);





create index BILLINGREALLOC_LCX on BILLINGREALLOC (
LASTCHANGED ASC
);





create table BILLINGREALLOC_DETAIL (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   COUNTERPARTY         varchar(10)          not null,
   REALLOCATIONID       varchar(20)          not null,
   VALUE                numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINGREALLOC_DETAIL
   add constraint BILLINGREALLOC_DETAIL_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, COUNTERPARTY, REALLOCATIONID);





create index BILLINGREALLOC_DETAIL_LCX on BILLINGREALLOC_DETAIL (
LASTCHANGED ASC
);





create table BILLINGREGIONEXPORTS (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   EXPORTTO             varchar(10)          not null,
   ENERGY               numeric(16,6)        null,
   VALUE                numeric(15,5)        null,
   SURPLUSENERGY        numeric(16,6)        null,
   SURPLUSVALUE         numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINGREGIONEXPORTS
   add constraint BILLINGREGIONEXPORTS_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, REGIONID, EXPORTTO);





create index BILLINGREGIONEXPORTS_LCX on BILLINGREGIONEXPORTS (
LASTCHANGED ASC
);





create table BILLINGREGIONFIGURES (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   ENERGYOUT            numeric(16,6)        null,
   VALUEOUT             numeric(16,6)        null,
   ENERGYPURCHASED      numeric(16,6)        null,
   VALUEPURCHASED       numeric(16,6)        null,
   EXCESSGEN            numeric(16,6)        null,
   RESERVETRADING       numeric(16,6)        null,
   INTCOMPO             numeric(16,6)        null,
   ADMINPRICECOMPO      numeric(16,6)        null,
   SETTSURPLUS          numeric(16,6)        null,
   ASPAYMENT            numeric(16,6)        null,
   POOLFEES             numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINGREGIONFIGURES
   add constraint BILLINGREGIONFIGURES_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, REGIONID);





create index BILLINGREGIONFIGURES_LCX on BILLINGREGIONFIGURES (
LASTCHANGED ASC
);





create table BILLINGREGIONIMPORTS (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   IMPORTFROM           varchar(10)          not null,
   ENERGY               numeric(16,6)        null,
   VALUE                numeric(15,5)        null,
   SURPLUSENERGY        numeric(16,6)        null,
   SURPLUSVALUE         numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINGREGIONIMPORTS
   add constraint BILLINGREGIONIMPORTS_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, REGIONID, IMPORTFROM);





create index BILLINGREGIONIMPORTS_LCX on BILLINGREGIONIMPORTS (
LASTCHANGED ASC
);





create table BILLINGRESERVERECOVERY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   MARKETRESERVE        numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINGRESERVERECOVERY
   add constraint BILLRESERVERECOVERY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID);





create index BILLINGRESERVERECOVERY_LCX on BILLINGRESERVERECOVERY (
LASTCHANGED ASC
);





create table BILLINGRESERVEREGIONRECOVERY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   REGIONRESERVE        numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINGRESERVEREGIONRECOVERY
   add constraint BILLRESERVEREGIONRECOVERY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID);





create index BILLINGRESERVEREGIONRECOV_LCX on BILLINGRESERVEREGIONRECOVERY (
LASTCHANGED ASC
);





create table BILLINGRESERVETRADER (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   MARKETRESERVE        numeric(15,5)        null,
   TOTALRESERVE         numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   TOTALCAPDIFFERENCE   numeric(15,5)        null
);

alter table BILLINGRESERVETRADER
   add constraint BILLINGRESERVETRADER_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID);





create index BILLINGRESERVETRADER_LCX on BILLINGRESERVETRADER (
LASTCHANGED ASC
);





create table BILLINGRESERVETRADERREGION (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   REGIONRESERVE        numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINGRESERVETRADERREGION
   add constraint BILLINGRESERVETRADERREGION_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID);





create index BILLINGRESERVETRADERREGIO_LCX on BILLINGRESERVETRADERREGION (
LASTCHANGED ASC
);





create table BILLINGRUNTRK (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   STATUS               varchar(6)           null,
   ADJ_CLEARED          varchar(1)           null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(10)          null,
   POSTDATE             timestamp(3)             null,
   POSTBY               varchar(10)          null,
   LASTCHANGED          timestamp(3)             null,
   RECEIPTPOSTDATE      timestamp(3)             null,
   RECEIPTPOSTBY        varchar(10)          null,
   PAYMENTPOSTDATE      timestamp(3)             null,
   PAYMENTPOSTBY        varchar(10)          null,
   SHORTFALL            numeric(16,6)        null,
   MAKEUP               numeric(15,5)        null
);

alter table BILLINGRUNTRK
   add constraint BILLINGRUNTRK_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO);





create index BILLINGRUNTRK_LCX on BILLINGRUNTRK (
LASTCHANGED ASC
);





create table BILLINGSMELTERREDUCTION (
   CONTRACTYEAR         numeric(22,0)        not null,
   WEEKNO               numeric(22,0)        not null,
   BILLRUNNO            numeric(22,0)        not null,
   PARTICIPANTID        varchar(10)          not null,
   RATE1                numeric(15,6)        null,
   RA1                  numeric(15,6)        null,
   RATE2                numeric(15,6)        null,
   RA2                  numeric(15,6)        null,
   TE                   numeric(15,6)        null,
   PCSD                 numeric(15,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINGSMELTERREDUCTION
   add constraint BILLINGSMELTERREDUCTION_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID);





create index BILLINGSMELTERREDUCT_NDX2 on BILLINGSMELTERREDUCTION (
PARTICIPANTID ASC
);





create index BILLINGSMELTERREDUCTION_LCX on BILLINGSMELTERREDUCTION (
LASTCHANGED ASC
);





create table BILLING_APC_COMPENSATION (
   CONTRACTYEAR         numeric(4)           not null,
   WEEKNO               numeric(3)           not null,
   BILLRUNNO            numeric(3)           not null,
   APEVENTID            numeric(6)           not null,
   CLAIMID              numeric(6)           not null,
   PARTICIPANTID        varchar(20)          null,
   COMPENSATION_AMOUNT  numeric(18,8)        null,
   EVENT_TYPE           varchar(20)          null,
   COMPENSATION_TYPE    varchar(20)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLING_APC_COMPENSATION
   add constraint BILLING_APC_COMPENSATION_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, APEVENTID, CLAIMID);





create table BILLING_APC_RECOVERY (
   CONTRACTYEAR         numeric(4)           not null,
   WEEKNO               numeric(3)           not null,
   BILLRUNNO            numeric(3)           not null,
   APEVENTID            numeric(6)           not null,
   CLAIMID              numeric(6)           not null,
   PARTICIPANTID        varchar(20)          not null,
   REGIONID             varchar(20)          not null,
   RECOVERY_AMOUNT      numeric(18,8)        null,
   ELIGIBILITY_START_INTERVAL timestamp(3)             null,
   ELIGIBILITY_END_INTERVAL timestamp(3)             null,
   PARTICIPANT_DEMAND   numeric(18,8)        null,
   REGION_DEMAND        numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLING_APC_RECOVERY
   add constraint BILLING_APC_RECOVERY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, APEVENTID, CLAIMID, PARTICIPANTID, REGIONID);





create table BILLING_CO2E_PUBLICATION (
   CONTRACTYEAR         numeric(4)           not null,
   WEEKNO               numeric(3)           not null,
   BILLRUNNO            numeric(3)           not null,
   SETTLEMENTDATE       timestamp(3)             not null,
   REGIONID             varchar(20)          not null,
   SENTOUTENERGY        numeric(18,8)        null,
   GENERATOREMISSIONS   numeric(18,8)        null,
   INTENSITYINDEX       numeric(18,8)        null
);

alter table BILLING_CO2E_PUBLICATION
   add constraint BILLING_CO2E_PUBLICATION_PK primary key (CONTRACTYEAR, WEEKNO, SETTLEMENTDATE, REGIONID);





create table BILLING_CO2E_PUBLICATION_TRK (
   CONTRACTYEAR         numeric(4)           not null,
   WEEKNO               numeric(3)           not null,
   BILLRUNNO            numeric(3)           null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLING_CO2E_PUBLICATION_TRK
   add constraint BILLING_CO2E_PUBLICATIO_TRK_PK primary key (CONTRACTYEAR, WEEKNO);





create table BILLING_CSP_DEROGATION_AMOUNT (
   CONTRACTYEAR         numeric(4)           not null,
   WEEKNO               numeric(3)           not null,
   BILLRUNNO            numeric(3)           not null,
   PARTICIPANTID        varchar(10)          not null,
   AMOUNT_ID            varchar(20)          not null,
   DEROGATION_AMOUNT    numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLING_CSP_DEROGATION_AMOUNT
   add constraint BILLING_CSP_DEROGATN_AMNT_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, AMOUNT_ID);





create index BILLING_CSP_DEROGATN_AMNT_NDX1 on BILLING_CSP_DEROGATION_AMOUNT (
LASTCHANGED ASC
);





create table BILLING_DAILY_ENERGY_SUMMARY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   SETTLEMENTDATE       timestamp(3)             not null,
   PARTICIPANTID        varchar(20)          not null,
   REGIONID             varchar(20)          not null,
   CUSTOMER_ENERGY_PURCHASED numeric(18,8)        null,
   GENERATOR_ENERGY_SOLD numeric(18,8)        null,
   GENERATOR_ENERGY_PURCHASED numeric(18,8)        null
);

alter table BILLING_DAILY_ENERGY_SUMMARY
   add constraint BILLING_DAILY_ENRGY_SUMMARY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, SETTLEMENTDATE, PARTICIPANTID, REGIONID);





create table BILLING_DIRECTION_RECONCILIATN (
   CONTRACTYEAR         numeric(4)           not null,
   WEEKNO               numeric(3)           not null,
   BILLRUNNO            numeric(3)           not null,
   DIRECTION_ID         varchar(20)          not null,
   DIRECTION_DESC       varchar(200)         null,
   DIRECTION_START_DATE timestamp(3)             null,
   DIRECTION_END_DATE   timestamp(3)             null,
   COMPENSATION_AMOUNT  numeric(16,6)        null,
   INDEPENDENT_EXPERT_FEE numeric(16,6)        null,
   INTEREST_AMOUNT      numeric(16,6)        null,
   CRA                  numeric(16,6)        null,
   NEM_FEE_ID           varchar(20)          null,
   NEM_FIXED_FEE_AMOUNT numeric(16,6)        null,
   MKT_CUSTOMER_PERC    numeric(16,6)        null,
   GENERATOR_PERC       numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLING_DIRECTION_RECONCILIATN
   add constraint BILLING_DIRECTION_RCNCLTN_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, DIRECTION_ID);





create index BILLING_DIRECTION_RCNCLTN_NDX1 on BILLING_DIRECTION_RECONCILIATN (
LASTCHANGED ASC
);





create table BILLING_DIRECTION_RECON_OTHER (
   CONTRACTYEAR         numeric(4)           not null,
   WEEKNO               numeric(3)           not null,
   BILLRUNNO            numeric(3)           not null,
   DIRECTION_ID         varchar(20)          not null,
   REGIONID             varchar(20)          not null,
   DIRECTION_DESC       varchar(200)         null,
   DIRECTION_TYPE_ID    varchar(20)          null,
   DIRECTION_START_DATE timestamp(3)             null,
   DIRECTION_END_DATE   timestamp(3)             null,
   DIRECTION_START_INTERVAL timestamp(3)             null,
   DIRECTION_END_INTERVAL timestamp(3)             null,
   COMPENSATION_AMOUNT  numeric(18,8)        null,
   INTEREST_AMOUNT      numeric(18,8)        null,
   INDEPENDENT_EXPERT_FEE numeric(18,8)        null,
   CRA                  numeric(18,8)        null,
   REGIONAL_CUSTOMER_ENERGY numeric(18,8)        null,
   REGIONAL_GENERATOR_ENERGY numeric(18,8)        null,
   REGIONAL_BENEFIT_FACTOR numeric(18,8)        null
);

alter table BILLING_DIRECTION_RECON_OTHER
   add constraint BILLING_DIRECTION_REC_OTHER_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, DIRECTION_ID, REGIONID);





create table BILLING_EFTSHORTFALL_AMOUNT (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(20)          not null,
   SHORTFALL_AMOUNT     numeric(18,8)        null,
   SHORTFALL            numeric(18,8)        null,
   SHORTFALL_COMPANY_ID varchar(20)          null,
   COMPANY_SHORTFALL_AMOUNT numeric(18,8)        null,
   PARTICIPANT_NET_ENERGY numeric(18,8)        null,
   COMPANY_NET_ENERGY   numeric(18,8)        null
);

alter table BILLING_EFTSHORTFALL_AMOUNT
   add constraint BILLING_EFTSHORTFALL_AMT_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID);





create table BILLING_EFTSHORTFALL_DETAIL (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(20)          not null,
   TRANSACTION_TYPE     varchar(40)          not null,
   AMOUNT               numeric(18,8)        null
);

alter table BILLING_EFTSHORTFALL_DETAIL
   add constraint BILLING_EFTSHORTFALL_DETL_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, TRANSACTION_TYPE);





create table BILLING_GST_DETAIL (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   BAS_CLASS            varchar(30)          not null,
   TRANSACTION_TYPE     varchar(30)          not null,
   GST_EXCLUSIVE_AMOUNT numeric(15,5)        null,
   GST_AMOUNT           numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLING_GST_DETAIL
   add constraint BILLING_GST_DETAIL_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, TRANSACTION_TYPE, BAS_CLASS);





create index BILLING_GST_DETAIL_LCX on BILLING_GST_DETAIL (
LASTCHANGED ASC
);





create table BILLING_GST_SUMMARY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   BAS_CLASS            varchar(30)          not null,
   GST_EXCLUSIVE_AMOUNT numeric(15,5)        null,
   GST_AMOUNT           numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLING_GST_SUMMARY
   add constraint BILLING_GST_SUMMARY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, BAS_CLASS);





create index BILLING_GST_SUMMARY_LCX on BILLING_GST_SUMMARY (
LASTCHANGED ASC
);





create table BILLING_MR_PAYMENT (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   MR_DATE              timestamp(3)             not null,
   REGIONID             varchar(10)          not null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          not null,
   MR_AMOUNT            numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLING_MR_PAYMENT
   add constraint BILLING_MR_PAYMENT_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, MR_DATE, REGIONID, DUID);





create index BILLING_MR_PAYMENT_LCX on BILLING_MR_PAYMENT (
LASTCHANGED ASC
);





create table BILLING_MR_RECOVERY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   MR_DATE              timestamp(3)             not null,
   REGIONID             varchar(10)          not null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          not null,
   MR_AMOUNT            numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLING_MR_RECOVERY
   add constraint BILLING_MR_RECOVERY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, MR_DATE, REGIONID, DUID);





create index BILLING_MR_RECOVERY_LCX on BILLING_MR_RECOVERY (
LASTCHANGED ASC
);





create table BILLING_MR_SHORTFALL (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   MR_DATE              timestamp(3)             not null,
   REGIONID             varchar(10)          not null,
   PARTICIPANTID        varchar(10)          not null,
   AGE                  numeric(16,6)        null,
   RSA                  numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLING_MR_SHORTFALL
   add constraint BILLING_MR_SHORTFALL_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, MR_DATE, REGIONID, PARTICIPANTID);





create index BILLING_MR_SHORTFALL_LCX on BILLING_MR_SHORTFALL (
LASTCHANGED ASC
);





create table BILLING_MR_SUMMARY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   MR_DATE              timestamp(3)             not null,
   REGIONID             varchar(10)          not null,
   TOTAL_PAYMENTS       numeric(16,6)        null,
   TOTAL_RECOVERY       numeric(16,6)        null,
   TOTAL_RSA            numeric(16,6)        null,
   AAGE                 numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLING_MR_SUMMARY
   add constraint BILLING_MR_SUMMARY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, MR_DATE, REGIONID);





create index BILLING_MR_SUMMARY_LCX on BILLING_MR_SUMMARY (
LASTCHANGED ASC
);





create table BILLING_NMAS_TST_PAYMENTS (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(20)          not null,
   SERVICE              varchar(10)          not null,
   CONTRACTID           varchar(10)          not null,
   PAYMENT_AMOUNT       numeric(18,8)        null
);

alter table BILLING_NMAS_TST_PAYMENTS
   add constraint PK_BILLING_NMAS_TST_PAYMENTS primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, SERVICE, CONTRACTID);





create table BILLING_NMAS_TST_RECOVERY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(20)          not null,
   SERVICE              varchar(10)          not null,
   CONTRACTID           varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   RBF                  numeric(18,8)        null,
   TEST_PAYMENT         numeric(18,8)        null,
   RECOVERY_START_DATE  timestamp(3)             null,
   RECOVERY_END_DATE    timestamp(3)             null,
   PARTICIPANT_ENERGY   numeric(18,8)        null,
   REGION_ENERGY        numeric(18,8)        null,
   NEM_ENERGY           numeric(18,8)        null,
   CUSTOMER_PROPORTION  numeric(18,8)        null,
   GENERATOR_PROPORTION numeric(18,8)        null,
   PARTICIPANT_GENERATION numeric(18,8)        null,
   NEM_GENERATION       numeric(18,8)        null,
   RECOVERY_AMOUNT      numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLING_NMAS_TST_RECOVERY
   add constraint PK_BILLING_NMAS_TST_RECOVERY primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, SERVICE, CONTRACTID, REGIONID);





create index BILLING_NMAS_TST_RECOVERY_LCX on BILLING_NMAS_TST_RECOVERY (
LASTCHANGED ASC
);





create table BILLING_NMAS_TST_RECVRY_RBF (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   SERVICE              varchar(10)          not null,
   CONTRACTID           varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   RBF                  numeric(18,8)        null,
   PAYMENT_AMOUNT       numeric(18,8)        null,
   RECOVERY_AMOUNT      numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLING_NMAS_TST_RECVRY_RBF
   add constraint PK_BILLING_NMAS_TST_RECVRY_RBF primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, SERVICE, CONTRACTID, REGIONID);





create index BILLING_NMAS_TST_RCVRY_RBF_LCX on BILLING_NMAS_TST_RECVRY_RBF (
LASTCHANGED ASC
);





create table BILLING_NMAS_TST_RECVRY_TRK (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   RECOVERY_CONTRACTYEAR numeric(4,0)         not null,
   RECOVERY_WEEKNO      numeric(3,0)         not null,
   RECOVERY_BILLRUNNO   numeric(3,0)         not null
);

alter table BILLING_NMAS_TST_RECVRY_TRK
   add constraint PK_BILLING_NMAS_TST_RECVRY_TRK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, RECOVERY_CONTRACTYEAR, RECOVERY_WEEKNO, RECOVERY_BILLRUNNO);





create table BILLING_RES_TRADER_PAYMENT (
   CONTRACTYEAR         numeric(4)           not null,
   WEEKNO               numeric(3)           not null,
   BILLRUNNO            numeric(3)           not null,
   CONTRACTID           varchar(20)          not null,
   PAYMENT_TYPE         varchar(40)          not null,
   PARTICIPANTID        varchar(20)          not null,
   PAYMENT_AMOUNT       numeric(18,8)        null
);

alter table BILLING_RES_TRADER_PAYMENT
   add constraint BILLING_RES_TRADER_PAYMENT_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, CONTRACTID, PAYMENT_TYPE, PARTICIPANTID);





create table BILLING_RES_TRADER_RECOVERY (
   CONTRACTYEAR         numeric(4)           not null,
   WEEKNO               numeric(3)           not null,
   BILLRUNNO            numeric(3)           not null,
   REGIONID             varchar(20)          not null,
   PARTICIPANTID        varchar(20)          not null,
   RECOVERY_AMOUNT      numeric(18,8)        null
);

alter table BILLING_RES_TRADER_RECOVERY
   add constraint BILLING_RES_TRADER_RECOVERY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, REGIONID, PARTICIPANTID);





create table BILLING_SECDEPOSIT_APPLICATION (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(20)          not null,
   APPLICATION_AMOUNT   numeric(18,8)        null
);

alter table BILLING_SECDEPOSIT_APPLICATION
   add constraint BILLING_SECDEPOSIT_APPL_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID);





create table BILLING_SECDEP_INTEREST_PAY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   SECURITY_DEPOSIT_ID  varchar(20)          not null,
   PARTICIPANTID        varchar(20)          not null,
   INTEREST_AMOUNT      numeric(18,8)        null,
   INTEREST_CALC_TYPE   varchar(20)          null,
   INTEREST_ACCT_ID     varchar(20)          null,
   INTEREST_RATE        numeric(18,8)        null
);

alter table BILLING_SECDEP_INTEREST_PAY
   add constraint BILLING_SECDEP_INTEREST_PAY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, SECURITY_DEPOSIT_ID, PARTICIPANTID);





create table BILLING_SECDEP_INTEREST_RATE (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   INTEREST_ACCT_ID     varchar(20)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   INTEREST_RATE        numeric(18,8)        null
);

alter table BILLING_SECDEP_INTEREST_RATE
   add constraint BILL_SECDEP_INTEREST_RATE_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, INTEREST_ACCT_ID, EFFECTIVEDATE);





create table BILLINTERVENTIONRECOVERY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   MARKETINTERVENTION   numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINTERVENTIONRECOVERY
   add constraint BILLINTERVENTIONRECOVERY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID);





create index BILLINTERVENTIONRECOVERY_LCX on BILLINTERVENTIONRECOVERY (
LASTCHANGED ASC
);





create table BILLINTERVENTIONREGIONRECOVERY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   REGIONINTERVENTION   numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLINTERVENTIONREGIONRECOVERY
   add constraint BILLINTERVENTIONREGIONRECOV_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID);





create index BILLINTERVENTIONREGIONREC_LCX on BILLINTERVENTIONREGIONRECOVERY (
LASTCHANGED ASC
);





create table BILLSMELTERRATE (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   CONTRACTYEAR         numeric(22,0)        not null,
   RAR1                 numeric(6,2)         null,
   RAR2                 numeric(6,2)         null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(10)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table BILLSMELTERRATE
   add constraint BILLSMELTERRATE_PK primary key (EFFECTIVEDATE, VERSIONNO, CONTRACTYEAR);





create index BILLSMELTERRATE_LCX on BILLSMELTERRATE (
LASTCHANGED ASC
);





create table BILLWHITEHOLE (
   CONTRACTYEAR         numeric(22,0)        not null,
   WEEKNO               numeric(22,0)        not null,
   BILLRUNNO            numeric(22,0)        not null,
   PARTICIPANTID        varchar(10)          not null,
   NL                   numeric(15,6)        null,
   PARTICIPANTDEMAND    numeric(15,6)        null,
   REGIONDEMAND         numeric(15,6)        null,
   WHITEHOLEPAYMENT     numeric(15,6)        null,
   LASTCHANGED          timestamp(3)             null,
   INTERCONNECTORID     varchar(10)          not null
);

alter table BILLWHITEHOLE
   add constraint BILLWHITEHOLE_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, INTERCONNECTORID);





create index BILLWHITEHOLE_LCX on BILLWHITEHOLE (
LASTCHANGED ASC
);





create table CONNECTIONPOINT (
   CONNECTIONPOINTID    varchar(10)          not null,
   CONNECTIONPOINTNAME  varchar(80)          null,
   CONNECTIONPOINTTYPE  varchar(20)          null,
   ADDRESS1             varchar(80)          null,
   ADDRESS2             varchar(80)          null,
   ADDRESS3             varchar(80)          null,
   ADDRESS4             varchar(80)          null,
   CITY                 varchar(40)          null,
   STATE                varchar(10)          null,
   POSTCODE             varchar(10)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table CONNECTIONPOINT
   add constraint CONNECTIONPOINT_PK primary key (CONNECTIONPOINTID);





create index CONNECTIONPOINT_LCX on CONNECTIONPOINT (
LASTCHANGED ASC
);





create table CONNECTIONPOINTDETAILS (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   CONNECTIONPOINTID    varchar(10)          not null,
   REGIONID             varchar(10)          null,
   TRANSMISSIONCPTID    varchar(10)          null,
   METERDATAPROVIDER    varchar(10)          null,
   TRANSMISSIONLOSSFACTOR numeric(7,5)         null,
   DISTRIBUTIONLOSSFACTOR numeric(7,5)         null,
   NETWORKSERVICEPROVIDER varchar(10)          null,
   FINRESPORGAN         varchar(10)          null,
   NATIONALMETERINSTALLID numeric(7,5)         null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null,
   INUSE                varchar(1)           null,
   LNSP                 varchar(10)          null,
   MDA                  varchar(10)          null,
   ROLR                 varchar(10)          null,
   RP                   varchar(10)          null,
   AGGREGATEDDATA       varchar(1)           null,
   VALID_TODATE         timestamp(3)             null,
   LR                   varchar(10)          null
);

alter table CONNECTIONPOINTDETAILS
   add constraint CONNECTIONPOINTDETAILS_PK primary key (EFFECTIVEDATE, VERSIONNO, CONNECTIONPOINTID);





create index CONNECTIONPOINTDETAILS_LCX on CONNECTIONPOINTDETAILS (
LASTCHANGED ASC
);





create index CONNECTIONPOINTDETAI_NDX2 on CONNECTIONPOINTDETAILS (
METERDATAPROVIDER ASC,
NETWORKSERVICEPROVIDER ASC,
FINRESPORGAN ASC
);





create index CONNECTIONPOINTDETAI_NDX3 on CONNECTIONPOINTDETAILS (
CONNECTIONPOINTID ASC
);





create table CONNECTIONPOINTOPERATINGSTA (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   CONNECTIONPOINTID    varchar(10)          not null,
   OPERATINGSTATUS      varchar(16)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table CONNECTIONPOINTOPERATINGSTA
   add constraint CPOPSTATUS_PK primary key (EFFECTIVEDATE, VERSIONNO, CONNECTIONPOINTID);





create index CONNECTIONPOINTOPERA_NDX2 on CONNECTIONPOINTOPERATINGSTA (
CONNECTIONPOINTID ASC
);





create index CONNECTIONPOINTOPERATINGS_LCX on CONNECTIONPOINTOPERATINGSTA (
LASTCHANGED ASC
);





create table CONSTRAINTRELAXATION_OCD (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   CONSTRAINTID         varchar(20)          not null,
   RHS                  numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null,
   VERSIONNO            numeric(3,0)         not null default 1
);

alter table CONSTRAINTRELAXATION_OCD
   add constraint PK_CONSTRAINTRELAXATION_OCD primary key (SETTLEMENTDATE, RUNNO, CONSTRAINTID, VERSIONNO);





create index CONSTRAINTRELAX_OCD_LCX on CONSTRAINTRELAXATION_OCD (
LASTCHANGED ASC
);





create table CONTRACTAGC (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   STARTDATE            timestamp(3)             null,
   ENDDATE              timestamp(3)             null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          null,
   CRR                  numeric(4,0)         null,
   CRL                  numeric(4,0)         null,
   RLPRICE              numeric(10,2)        null,
   CCPRICE              numeric(10,2)        null,
   BS                   numeric(10,2)        null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table CONTRACTAGC
   add constraint CONTRACTAGC_PK primary key (CONTRACTID, VERSIONNO);





create index CONTRACTAGC_NDX2 on CONTRACTAGC (
PARTICIPANTID ASC,
CONTRACTID ASC
);





create index CONTRACTAGC_LCX on CONTRACTAGC (
LASTCHANGED ASC
);





create table CONTRACTGOVERNOR (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   STARTDATE            timestamp(3)             null,
   ENDDATE              timestamp(3)             null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          null,
   CCPRICE              numeric(10,2)        null,
   LOWER60SECBREAKPOINT numeric(9,6)         null,
   LOWER60SECMAX        numeric(9,6)         null,
   LOWER6SECBREAKPOINT  numeric(9,6)         null,
   LOWER6SECMAX         numeric(9,6)         null,
   RAISE60SECBREAKPOINT numeric(9,6)         null,
   RAISE60SECCAPACITY   numeric(9,6)         null,
   RAISE60SECMAX        numeric(9,6)         null,
   RAISE6SECBREAKPOINT  numeric(9,6)         null,
   RAISE6SECCAPACITY    numeric(9,6)         null,
   RAISE6SECMAX         numeric(9,6)         null,
   PRICE6SECRAISEMANDATORY numeric(16,6)        null,
   QUANT6SECRAISEMANDATORY numeric(16,6)        null,
   PRICE6SECRAISECONTRACT numeric(16,6)        null,
   QUANT6SECRAISECONTRACT numeric(16,6)        null,
   PRICE60SECRAISEMANDATORY numeric(16,6)        null,
   QUANT60SECRAISEMANDATORY numeric(16,6)        null,
   PRICE60SECRAISECONTRACT numeric(16,6)        null,
   QUANT60SECRAISECONTRACT numeric(16,6)        null,
   PRICE6SECLOWERMANDATORY numeric(16,6)        null,
   QUANT6SECLOWERMANDATORY numeric(16,6)        null,
   PRICE6SECLOWERCONTRACT numeric(16,6)        null,
   QUANT6SECLOWERCONTRACT numeric(16,6)        null,
   PRICE60SECLOWERMANDATORY numeric(16,6)        null,
   QUANT60SECLOWERMANDATORY numeric(16,6)        null,
   PRICE60SECLOWERCONTRACT numeric(16,6)        null,
   QUANT60SECLOWERCONTRACT numeric(16,6)        null,
   DEADBANDUP           numeric(4,2)         null,
   DEADBANDDOWN         numeric(4,2)         null,
   DROOP6SECRAISEBREAKPOINT numeric(9,6)         null,
   DROOP6SECRAISECAPACITY numeric(9,6)         null,
   DROOP6SECRAISEMAX    numeric(9,6)         null,
   DROOP60SECRAISEBREAKPOINT numeric(9,6)         null,
   DROOP60SECRAISECAPACITY numeric(9,6)         null,
   DROOP60SECRAISEMAX   numeric(9,6)         null,
   DROOP6SECLOWERBREAKPOINT numeric(9,6)         null,
   DROOP6SECLOWERMAX    numeric(9,6)         null,
   DROOP60SECLOWERBREAKPOINT numeric(9,6)         null,
   DROOP60SECLOWERMAX   numeric(9,6)         null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table CONTRACTGOVERNOR
   add constraint CONTRACTGOVERNOR_PK primary key (CONTRACTID, VERSIONNO);





create index CONTRACTGOVERNOR_NDX2 on CONTRACTGOVERNOR (
PARTICIPANTID ASC
);





create index CONTRACTGOVERNOR_LCX on CONTRACTGOVERNOR (
LASTCHANGED ASC
);





create table CONTRACTLOADSHED (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   STARTDATE            timestamp(3)             null,
   ENDDATE              timestamp(3)             null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          null,
   LSEPRICE             numeric(6,2)         null,
   MCPPRICE             numeric(12,2)        null,
   TENDEREDPRICE        numeric(6,2)         null,
   LSCR                 numeric(6,2)         null,
   ILSCALINGFACTOR      numeric(15,5)        null,
   LOWER60SECBREAKPOINT numeric(9,6)         null,
   LOWER60SECMAX        numeric(9,6)         null,
   LOWER6SECBREAKPOINT  numeric(9,6)         null,
   LOWER6SECMAX         numeric(9,6)         null,
   RAISE60SECBREAKPOINT numeric(9,6)         null,
   RAISE60SECCAPACITY   numeric(9,6)         null,
   RAISE60SECMAX        numeric(9,6)         null,
   RAISE6SECBREAKPOINT  numeric(9,6)         null,
   RAISE6SECCAPACITY    numeric(9,6)         null,
   RAISE6SECMAX         numeric(9,6)         null,
   PRICE6SECRAISEMANDATORY numeric(16,6)        null,
   QUANT6SECRAISEMANDATORY numeric(9,6)         null,
   PRICE6SECRAISECONTRACT numeric(16,6)        null,
   QUANT6SECRAISECONTRACT numeric(9,6)         null,
   PRICE60SECRAISEMANDATORY numeric(16,6)        null,
   QUANT60SECRAISEMANDATORY numeric(9,6)         null,
   PRICE60SECRAISECONTRACT numeric(16,6)        null,
   QUANT60SECRAISECONTRACT numeric(9,6)         null,
   PRICE6SECLOWERMANDATORY numeric(16,6)        null,
   QUANT6SECLOWERMANDATORY numeric(9,6)         null,
   PRICE6SECLOWERCONTRACT numeric(16,6)        null,
   QUANT6SECLOWERCONTRACT numeric(9,6)         null,
   PRICE60SECLOWERMANDATORY numeric(16,6)        null,
   QUANT60SECLOWERMANDATORY numeric(9,6)         null,
   PRICE60SECLOWERCONTRACT numeric(16,6)        null,
   QUANT60SECLOWERCONTRACT numeric(9,6)         null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null,
   DEFAULT_TESTINGPAYMENT_AMOUNT numeric(18,8)        null,
   SERVICE_START_DATE   timestamp(3)             null
);

alter table CONTRACTLOADSHED
   add constraint CONTRACTLOADSHED_PK primary key (CONTRACTID, VERSIONNO);





create index CONTRACTLOADSHED_NDX2 on CONTRACTLOADSHED (
PARTICIPANTID ASC
);





create index CONTRACTLOADSHED_LCX on CONTRACTLOADSHED (
LASTCHANGED ASC
);





create table CONTRACTREACTIVEPOWER (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   STARTDATE            timestamp(3)             null,
   ENDDATE              timestamp(3)             null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          null,
   SYNCCOMPENSATION     varchar(1)           null,
   MVARAPRICE           numeric(10,2)        null,
   MVAREPRICE           numeric(10,2)        null,
   MVARGPRICE           numeric(10,2)        null,
   CCPRICE              numeric(10,2)        null,
   MTA                  numeric(10,2)        null,
   MTG                  numeric(10,2)        null,
   MMCA                 numeric(10,2)        null,
   MMCG                 numeric(10,2)        null,
   EU                   numeric(10,2)        null,
   PP                   numeric(10,2)        null,
   BS                   numeric(10,2)        null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null,
   DEFAULT_TESTINGPAYMENT_AMOUNT numeric(18,8)        null,
   SERVICE_START_DATE   timestamp(3)             null,
   AVAILABILITY_MWH_THRESHOLD numeric(18,8)        null,
   MVAR_THRESHOLD       numeric(18,8)        null,
   REBATE_CAP           numeric(18,8)        null,
   REBATE_AMOUNT_PER_MVAR numeric(18,8)        null,
   ISREBATEAPPLICABLE   numeric(1,0)         null
);

alter table CONTRACTREACTIVEPOWER
   add constraint CONTRACTREACTIVEPOWER_PK primary key (CONTRACTID, VERSIONNO);





create index CONTRACTREACTIVEPOWE_NDX2 on CONTRACTREACTIVEPOWER (
PARTICIPANTID ASC
);





create index CONTRACTREACTIVEPOWER_LCX on CONTRACTREACTIVEPOWER (
LASTCHANGED ASC
);





create table CONTRACTRESERVEFLAG (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   RCF                  char(1)              null,
   LASTCHANGED          timestamp(3)             null
);

alter table CONTRACTRESERVEFLAG
   add constraint CONTRACTRESERVEFLAG_PK primary key (CONTRACTID, VERSIONNO, PERIODID);





create index CONTRACTRESERVEFLAG_LCX on CONTRACTRESERVEFLAG (
LASTCHANGED ASC
);





create table CONTRACTRESERVETHRESHOLD (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   CRA                  numeric(16,6)        null,
   CRE                  numeric(16,6)        null,
   CRU                  numeric(16,6)        null,
   CTA                  numeric(16,6)        null,
   CTE                  numeric(16,6)        null,
   CTU                  numeric(16,6)        null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table CONTRACTRESERVETHRESHOLD
   add constraint CONTRACTRESERVETHRESHOLD_PK primary key (CONTRACTID, VERSIONNO);





create index CONTRACTRESERVETHRESHOLD_LCX on CONTRACTRESERVETHRESHOLD (
LASTCHANGED ASC
);





create table CONTRACTRESERVETRADER (
   CONTRACTID           varchar(10)          not null,
   DUID                 varchar(10)          null,
   STARTDATE            timestamp(3)             null,
   ENDDATE              timestamp(3)             null,
   STARTPERIOD          numeric(3,0)         null,
   ENDPERIOD            numeric(3,0)         null,
   DEREGISTRATIONDATE   timestamp(3)             null,
   DEREGISTRATIONPERIOD numeric(3,0)         null,
   PARTICIPANTID        varchar(10)          null,
   LASTCHANGED          timestamp(3)             null,
   REGIONID             varchar(10)          null
);

alter table CONTRACTRESERVETRADER
   add constraint CONTRACTRESERVETRADER_PK primary key (CONTRACTID);





create index CONTRACTRESERVETRADER_LCX on CONTRACTRESERVETRADER (
LASTCHANGED ASC
);





create table CONTRACTRESTARTSERVICES (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   STARTDATE            timestamp(3)             null,
   ENDDATE              timestamp(3)             null,
   PARTICIPANTID        varchar(10)          null,
   RESTARTTYPE          numeric(1,0)         null,
   RCPRICE              numeric(6,2)         null,
   TRIPTOHOUSELEVEL     numeric(5,0)         null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null,
   DEFAULT_TESTINGPAYMENT_AMOUNT numeric(18,8)        null,
   SERVICE_START_DATE   timestamp(3)             null
);

alter table CONTRACTRESTARTSERVICES
   add constraint CONTRACTRESTARTSERVICES_PK primary key (CONTRACTID, VERSIONNO);





create index CONTRACTRESTARTSERVI_NDX2 on CONTRACTRESTARTSERVICES (
PARTICIPANTID ASC
);





create index CONTRACTRESTARTSERVICES_LCX on CONTRACTRESTARTSERVICES (
LASTCHANGED ASC
);





create table CONTRACTRESTARTUNITS (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   DUID                 varchar(10)          not null,
   LASTCHANGED          timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null
);

alter table CONTRACTRESTARTUNITS
   add constraint CONTRACTRESTARTUNITS_PK primary key (CONTRACTID, VERSIONNO, DUID);





create index CONTRACTRESTARTUNITS_NDX2 on CONTRACTRESTARTUNITS (
CONTRACTID ASC
);





create index CONTRACTRESTARTUNITS_LCX on CONTRACTRESTARTUNITS (
LASTCHANGED ASC
);





create table CONTRACTUNITLOADING (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   STARTDATE            timestamp(3)             null,
   ENDDATE              timestamp(3)             null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          null,
   RPRICE               numeric(10,2)        null,
   SUPRICE              numeric(10,2)        null,
   CCPRICE              numeric(10,2)        null,
   ACR                  numeric(10,2)        null,
   BS                   numeric(10,2)        null,
   PP                   numeric(10,2)        null,
   EU                   numeric(10,2)        null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table CONTRACTUNITLOADING
   add constraint CONTRACTUNITLOADING_PK primary key (CONTRACTID, VERSIONNO);





create index CONTRACTUNITLOADING_NDX2 on CONTRACTUNITLOADING (
PARTICIPANTID ASC
);





create index CONTRACTUNITLOADING_LCX on CONTRACTUNITLOADING (
LASTCHANGED ASC
);





create table CONTRACTUNITUNLOADING (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   STARTDATE            timestamp(3)             null,
   ENDDATE              timestamp(3)             null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          null,
   RPRICE               numeric(10,2)        null,
   SUPRICE              numeric(10,2)        null,
   CCPRICE              numeric(10,2)        null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table CONTRACTUNITUNLOADING
   add constraint CONTRACTUNITUNLOADING_PK primary key (CONTRACTID, VERSIONNO);





create index CONTRACTUNITUNLOADIN_NDX2 on CONTRACTUNITUNLOADING (
PARTICIPANTID ASC
);





create index CONTRACTUNITUNLOADING_LCX on CONTRACTUNITUNLOADING (
LASTCHANGED ASC
);





create table DAYOFFER (
   SETTLEMENTDATE       timestamp(3)             not null,
   DUID                 varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   OFFERDATE            timestamp(3)             not null,
   SELFCOMMITFLAG       varchar(1)           null,
   DAILYENERGYCONSTRAINT numeric(12,6)        null,
   ENTRYTYPE            varchar(20)          null,
   CONTINGENCYPRICE     numeric(9,2)         null,
   REBIDEXPLANATION     varchar(64)          null,
   BANDQUANTISATIONID   numeric(2,0)         null,
   PRICEBAND1           numeric(9,2)         null,
   PRICEBAND2           numeric(9,2)         null,
   PRICEBAND3           numeric(9,2)         null,
   PRICEBAND4           numeric(9,2)         null,
   PRICEBAND5           numeric(9,2)         null,
   PRICEBAND6           numeric(9,2)         null,
   PRICEBAND7           numeric(9,2)         null,
   PRICEBAND8           numeric(9,2)         null,
   PRICEBAND9           numeric(9,2)         null,
   PRICEBAND10          numeric(9,2)         null,
   MAXRAMPUP            numeric(9,2)         null,
   MAXRAMPDOWN          numeric(9,2)         null,
   MINIMUMLOAD          numeric(6,0)         null,
   T1                   numeric(6,0)         null,
   T2                   numeric(6,0)         null,
   T3                   numeric(6,0)         null,
   T4                   numeric(6,0)         null,
   NORMALSTATUS         varchar(3)           null,
   LASTCHANGED          timestamp(3)             null,
   MR_FACTOR            numeric(16,6)        null
);

alter table DAYOFFER
   add constraint DAYOFFER_PK primary key (SETTLEMENTDATE, DUID, OFFERDATE, VERSIONNO);





create index DAYOFFER_NDX2 on DAYOFFER (
DUID ASC,
LASTCHANGED ASC
);





create index DAYOFFER_LCX on DAYOFFER (
LASTCHANGED ASC
);





create table DAYOFFER_D (
   SETTLEMENTDATE       timestamp(3)             not null,
   DUID                 varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   OFFERDATE            timestamp(3)             not null,
   SELFCOMMITFLAG       varchar(1)           null,
   DAILYENERGYCONSTRAINT numeric(12,6)        null,
   ENTRYTYPE            varchar(20)          null,
   CONTINGENCYPRICE     numeric(9,2)         null,
   REBIDEXPLANATION     varchar(64)          null,
   BANDQUANTISATIONID   numeric(2,0)         null,
   PRICEBAND1           numeric(9,2)         null,
   PRICEBAND2           numeric(9,2)         null,
   PRICEBAND3           numeric(9,2)         null,
   PRICEBAND4           numeric(9,2)         null,
   PRICEBAND5           numeric(9,2)         null,
   PRICEBAND6           numeric(9,2)         null,
   PRICEBAND7           numeric(9,2)         null,
   PRICEBAND8           numeric(9,2)         null,
   PRICEBAND9           numeric(9,2)         null,
   PRICEBAND10          numeric(9,2)         null,
   MAXRAMPUP            numeric(9,2)         null,
   MAXRAMPDOWN          numeric(9,2)         null,
   MINIMUMLOAD          numeric(6,0)         null,
   T1                   numeric(6,0)         null,
   T2                   numeric(6,0)         null,
   T3                   numeric(6,0)         null,
   T4                   numeric(6,0)         null,
   NORMALSTATUS         varchar(3)           null,
   LASTCHANGED          timestamp(3)             null,
   MR_FACTOR            numeric(6,0)         null
);

alter table DAYOFFER_D
   add constraint DAYOFFER_D_PK primary key (SETTLEMENTDATE, DUID, OFFERDATE, VERSIONNO);





create index DAYOFFER_D_NDX2 on DAYOFFER_D (
DUID ASC,
LASTCHANGED ASC
);





create index DAYOFFER_D_LCX on DAYOFFER_D (
LASTCHANGED ASC
);





create table DAYTRACK (
   SETTLEMENTDATE       timestamp(3)             not null,
   REGIONID             varchar(10)          null,
   EXANTERUNSTATUS      varchar(15)          null,
   EXANTERUNNO          numeric(3,0)         null,
   EXPOSTRUNSTATUS      varchar(15)          null,
   EXPOSTRUNNO          numeric(3,0)         not null,
   LASTCHANGED          timestamp(3)             null
);

alter table DAYTRACK
   add constraint DAYTRACK_PK primary key (SETTLEMENTDATE, EXPOSTRUNNO);





create index DAYTRACK_LCX on DAYTRACK (
LASTCHANGED ASC
);





create table DEFAULTDAYOFFER (
   SETTLEMENTDATE       timestamp(3)             not null,
   DUID                 varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   SELFCOMMITFLAG       varchar(1)           null,
   DAILYENERGYCONSTRAINT numeric(12,6)        null,
   ENTRYTYPE            varchar(20)          null,
   CONTINGENCYPRICE     numeric(9,2)         null,
   REBIDEXPLANATION     varchar(64)          null,
   BANDQUANTISATIONID   numeric(2,0)         null,
   PRICEBAND1           numeric(9,2)         null,
   PRICEBAND2           numeric(9,2)         null,
   PRICEBAND3           numeric(9,2)         null,
   PRICEBAND4           numeric(9,2)         null,
   PRICEBAND5           numeric(9,2)         null,
   PRICEBAND6           numeric(9,2)         null,
   PRICEBAND7           numeric(9,2)         null,
   PRICEBAND8           numeric(9,2)         null,
   PRICEBAND9           numeric(9,2)         null,
   PRICEBAND10          numeric(9,2)         null,
   MAXRAMPUP            numeric(9,2)         null,
   MAXRAMPDOWN          numeric(9,2)         null,
   MINIMUMLOAD          numeric(6,0)         null,
   T1                   numeric(6,0)         null,
   T2                   numeric(6,0)         null,
   T3                   numeric(6,0)         null,
   T4                   numeric(6,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table DEFAULTDAYOFFER
   add constraint DEFDAYOFFER_PK primary key (SETTLEMENTDATE, DUID, VERSIONNO);





create index DEFAULTDAYOFFER_LCX on DEFAULTDAYOFFER (
LASTCHANGED ASC
);





create table DEFAULTOFFERTRK (
   DUID                 varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   FILENAME             varchar(40)          null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table DEFAULTOFFERTRK
   add constraint DEFOFFERTRK_PK primary key (DUID, EFFECTIVEDATE, VERSIONNO);





create index DEFAULTOFFERTRK_LCX on DEFAULTOFFERTRK (
LASTCHANGED ASC
);





create table DEFAULTPEROFFER (
   SETTLEMENTDATE       timestamp(3)             not null,
   DUID                 varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   VERSIONNO            numeric(3,0)         not null,
   SELFDISPATCH         numeric(9,6)         null,
   MAXAVAIL             numeric(12,6)        null,
   FIXEDLOAD            numeric(9,6)         null,
   ROCUP                numeric(6,0)         null,
   ROCDOWN              numeric(6,0)         null,
   LASTCHANGED          timestamp(3)             null,
   BANDAVAIL1           numeric(6,0)         null,
   BANDAVAIL2           numeric(6,0)         null,
   BANDAVAIL3           numeric(6,0)         null,
   BANDAVAIL4           numeric(6,0)         null,
   BANDAVAIL5           numeric(6,0)         null,
   BANDAVAIL6           numeric(6,0)         null,
   BANDAVAIL7           numeric(6,0)         null,
   BANDAVAIL8           numeric(6,0)         null,
   BANDAVAIL9           numeric(6,0)         null,
   BANDAVAIL10          numeric(6,0)         null,
   PASAAVAILABILITY     numeric(12,0)        null
);

alter table DEFAULTPEROFFER
   add constraint DEFPEROFFER_PK primary key (DUID, SETTLEMENTDATE, VERSIONNO, PERIODID);





create index DEFAULTPEROFFER_LCX on DEFAULTPEROFFER (
LASTCHANGED ASC
);





create table DELTAMW (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   PERIODID             numeric(2,0)         not null,
   DELTAMW              numeric(6,0)         null,
   LOWER5MIN            numeric(6,0)         null,
   LOWER60SEC           numeric(6,0)         null,
   LOWER6SEC            numeric(6,0)         null,
   RAISE5MIN            numeric(6,0)         null,
   RAISE60SEC           numeric(6,0)         null,
   RAISE6SEC            numeric(6,0)         null,
   LASTCHANGED          timestamp(3)             null,
   RAISEREG             numeric(6,0)         null,
   LOWERREG             numeric(6,0)         null
);

alter table DELTAMW
   add constraint DELTAMW_PK primary key (SETTLEMENTDATE, VERSIONNO, REGIONID, PERIODID);





create index DELTAMW_LCX on DELTAMW (
LASTCHANGED ASC
);





create table DEMANDOPERATIONALACTUAL (
   INTERVAL_DATETIME    timestamp(3)             not null,
   REGIONID             varchar(20)          not null,
   OPERATIONAL_DEMAND   numeric(10,0)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table DEMANDOPERATIONALACTUAL
   add constraint DEMANDOPERATIONALACTUAL_PK primary key (INTERVAL_DATETIME, REGIONID);





create table DEMANDOPERATIONALFORECAST (
   INTERVAL_DATETIME    timestamp(3)             not null,
   REGIONID             varchar(20)          not null,
   LOAD_DATE            timestamp(3)             null,
   OPERATIONAL_DEMAND_POE10 numeric(15,2)        null,
   OPERATIONAL_DEMAND_POE50 numeric(15,2)        null,
   OPERATIONAL_DEMAND_POE90 numeric(15,2)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table DEMANDOPERATIONALFORECAST
   add constraint DEMANDOPERATIONALFORECAST_PK primary key (INTERVAL_DATETIME, REGIONID);





create table DISPATCHABLEUNIT (
   DUID                 varchar(10)          not null,
   DUNAME               varchar(20)          null,
   UNITTYPE             varchar(20)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table DISPATCHABLEUNIT
   add constraint DISPATCHABLEUNIT_PK primary key (DUID);





create index DISPATCHABLEUNIT_LCX on DISPATCHABLEUNIT (
LASTCHANGED ASC
);





create table DISPATCHBIDTRK (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   OFFEREFFECTIVEDATE   timestamp(3)             not null,
   OFFERVERSIONNO       numeric(3,0)         not null,
   DUID                 varchar(10)          not null,
   BIDTYPE              varchar(10)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table DISPATCHBIDTRK
   add constraint DISPATCHBIDTRK_PK primary key (SETTLEMENTDATE, RUNNO, OFFEREFFECTIVEDATE, OFFERVERSIONNO, DUID);





create index DISPATCHBIDTRK_NDX2 on DISPATCHBIDTRK (
DUID ASC,
LASTCHANGED ASC
);





create index DISPATCHBIDTRK_LCX on DISPATCHBIDTRK (
LASTCHANGED ASC
);





create table DISPATCHBLOCKEDCONSTRAINT (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   CONSTRAINTID         varchar(20)          not null
);

alter table DISPATCHBLOCKEDCONSTRAINT
   add constraint DISPATCHBLOCKEDCONSTRAINT_PK primary key (SETTLEMENTDATE, RUNNO, CONSTRAINTID);





create table DISPATCHCASESOLUTION (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   INTERVENTION         numeric(2,0)         not null,
   CASESUBTYPE          varchar(3)           null,
   SOLUTIONSTATUS       numeric(2,0)         null,
   SPDVERSION           varchar(20)          null,
   NONPHYSICALLOSSES    numeric(1,0)         null,
   TOTALOBJECTIVE       numeric(27,10)       null,
   TOTALAREAGENVIOLATION numeric(15,5)        null,
   TOTALINTERCONNECTORVIOLATION numeric(15,5)        null,
   TOTALGENERICVIOLATION numeric(15,5)        null,
   TOTALRAMPRATEVIOLATION numeric(15,5)        null,
   TOTALUNITMWCAPACITYVIOLATION numeric(15,5)        null,
   TOTAL5MINVIOLATION   numeric(15,5)        null,
   TOTALREGVIOLATION    numeric(15,5)        null,
   TOTAL6SECVIOLATION   numeric(15,5)        null,
   TOTAL60SECVIOLATION  numeric(15,5)        null,
   TOTALASPROFILEVIOLATION numeric(15,5)        null,
   TOTALFASTSTARTVIOLATION numeric(15,5)        null,
   TOTALENERGYOFFERVIOLATION numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   SWITCHRUNINITIALSTATUS numeric(1,0)         null,
   SWITCHRUNBESTSTATUS  numeric(1,0)         null,
   SWITCHRUNBESTSTATUS_INT numeric(1,0)         null
);

alter table DISPATCHCASESOLUTION
   add constraint DISPATCHCASESOLUTION_PK primary key (SETTLEMENTDATE, RUNNO);





create index DISPATCHCASESOLUTION_LCX on DISPATCHCASESOLUTION (
LASTCHANGED ASC
);





create table DISPATCHCASESOLUTION_BNC (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   INTERVENTION         numeric(2,0)         not null,
   CASESUBTYPE          varchar(3)           null,
   SOLUTIONSTATUS       numeric(2,0)         null,
   SPDVERSION           numeric(10,3)        null,
   STARTPERIOD          varchar(20)          null,
   NONPHYSICALLOSSES    numeric(1,0)         null,
   TOTALOBJECTIVE       numeric(27,10)       null,
   TOTALAREAGENVIOLATION numeric(15,5)        null,
   TOTALINTERCONNECTORVIOLATION numeric(15,5)        null,
   TOTALGENERICVIOLATION numeric(15,5)        null,
   TOTALRAMPRATEVIOLATION numeric(15,5)        null,
   TOTALUNITMWCAPACITYVIOLATION numeric(15,5)        null,
   TOTAL5MINVIOLATION   numeric(15,5)        null,
   TOTALREGVIOLATION    numeric(15,5)        null,
   TOTAL6SECVIOLATION   numeric(15,5)        null,
   TOTAL60SECVIOLATION  numeric(15,5)        null,
   TOTALENERGYCONSTRVIOLATION numeric(15,5)        null,
   TOTALENERGYOFFERVIOLATION numeric(15,5)        null,
   TOTALASPROFILEVIOLATION numeric(15,5)        null,
   TOTALFASTSTARTVIOLATION numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table DISPATCHCASESOLUTION_BNC
   add constraint PK_DISPATCHCASESOLUTION_BNC primary key (SETTLEMENTDATE, RUNNO, INTERVENTION);





create index DISPATCHCASESOLUTION_BNC_LCX on DISPATCHCASESOLUTION_BNC (
LASTCHANGED ASC
);





create table DISPATCHCASE_OCD (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   LASTCHANGED          timestamp(3)             null
);

alter table DISPATCHCASE_OCD
   add constraint DISPATCHCASE_OCD_PK primary key (SETTLEMENTDATE, RUNNO);





create index DISPATCHCASE_OCD_LCX on DISPATCHCASE_OCD (
LASTCHANGED ASC
);





create table DISPATCHCONSTRAINT (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   CONSTRAINTID         varchar(20)          not null,
   DISPATCHINTERVAL     numeric(22,0)        not null,
   INTERVENTION         numeric(2,0)         not null,
   RHS                  numeric(15,5)        null,
   MARGINALVALUE        numeric(15,5)        null,
   VIOLATIONDEGREE      numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   DUID                 varchar(20)          null,
   GENCONID_EFFECTIVEDATE timestamp(3)             null,
   GENCONID_VERSIONNO   numeric(22,0)        null,
   LHS                  numeric(15,5)        null
);

alter table DISPATCHCONSTRAINT
   add constraint PK_DISPATCHCONSTRAINT primary key (SETTLEMENTDATE, RUNNO, CONSTRAINTID, DISPATCHINTERVAL, INTERVENTION);





create index DISPATCHCONSTRAINT_NDX2 on DISPATCHCONSTRAINT (
SETTLEMENTDATE ASC
);





create index DISPATCHCONSTRAINT_LCX on DISPATCHCONSTRAINT (
LASTCHANGED ASC
);





create table DISPATCHINTERCONNECTORRES (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   DISPATCHINTERVAL     numeric(22,0)        not null,
   INTERVENTION         numeric(2,0)         not null,
   METEREDMWFLOW        numeric(15,5)        null,
   MWFLOW               numeric(15,5)        null,
   MWLOSSES             numeric(15,5)        null,
   MARGINALVALUE        numeric(15,5)        null,
   VIOLATIONDEGREE      numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   EXPORTLIMIT          numeric(15,5)        null,
   IMPORTLIMIT          numeric(15,5)        null,
   MARGINALLOSS         numeric(15,5)        null,
   EXPORTGENCONID       varchar(20)          null,
   IMPORTGENCONID       varchar(20)          null,
   FCASEXPORTLIMIT      numeric(15,5)        null,
   FCASIMPORTLIMIT      numeric(15,5)        null,
   LOCAL_PRICE_ADJUSTMENT_EXPORT numeric(10,2)        null,
   LOCALLY_CONSTRAINED_EXPORT numeric(1,0)         null,
   LOCAL_PRICE_ADJUSTMENT_IMPORT numeric(10,2)        null,
   LOCALLY_CONSTRAINED_IMPORT numeric(1,0)         null
);

alter table DISPATCHINTERCONNECTORRES
   add constraint PK_DISPATCHINTERCONNECTORRES primary key (SETTLEMENTDATE, RUNNO, INTERCONNECTORID, DISPATCHINTERVAL, INTERVENTION);





create index DISPATCHINTERCONNECTORRES_LCX on DISPATCHINTERCONNECTORRES (
LASTCHANGED ASC
);





create table DISPATCHLOAD (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   DUID                 varchar(10)          not null,
   TRADETYPE            numeric(2,0)         null,
   DISPATCHINTERVAL     numeric(22,0)        null,
   INTERVENTION         numeric(2,0)         not null,
   CONNECTIONPOINTID    varchar(12)          null,
   DISPATCHMODE         numeric(2,0)         null,
   AGCSTATUS            numeric(2,0)         null,
   INITIALMW            numeric(15,5)        null,
   TOTALCLEARED         numeric(15,5)        null,
   RAMPDOWNRATE         numeric(15,5)        null,
   RAMPUPRATE           numeric(15,5)        null,
   LOWER5MIN            numeric(15,5)        null,
   LOWER60SEC           numeric(15,5)        null,
   LOWER6SEC            numeric(15,5)        null,
   RAISE5MIN            numeric(15,5)        null,
   RAISE60SEC           numeric(15,5)        null,
   RAISE6SEC            numeric(15,5)        null,
   DOWNEPF              numeric(15,5)        null,
   UPEPF                numeric(15,5)        null,
   MARGINAL5MINVALUE    numeric(15,5)        null,
   MARGINAL60SECVALUE   numeric(15,5)        null,
   MARGINAL6SECVALUE    numeric(15,5)        null,
   MARGINALVALUE        numeric(15,5)        null,
   VIOLATION5MINDEGREE  numeric(15,5)        null,
   VIOLATION60SECDEGREE numeric(15,5)        null,
   VIOLATION6SECDEGREE  numeric(15,5)        null,
   VIOLATIONDEGREE      numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   LOWERREG             numeric(15,5)        null,
   RAISEREG             numeric(15,5)        null,
   AVAILABILITY         numeric(15,5)        null,
   RAISE6SECFLAGS       numeric(3,0)         null,
   RAISE60SECFLAGS      numeric(3,0)         null,
   RAISE5MINFLAGS       numeric(3,0)         null,
   RAISEREGFLAGS        numeric(3,0)         null,
   LOWER6SECFLAGS       numeric(3,0)         null,
   LOWER60SECFLAGS      numeric(3,0)         null,
   LOWER5MINFLAGS       numeric(3,0)         null,
   LOWERREGFLAGS        numeric(3,0)         null,
   RAISEREGAVAILABILITY numeric(15,5)        null,
   RAISEREGENABLEMENTMAX numeric(15,5)        null,
   RAISEREGENABLEMENTMIN numeric(15,5)        null,
   LOWERREGAVAILABILITY numeric(15,5)        null,
   LOWERREGENABLEMENTMAX numeric(15,5)        null,
   LOWERREGENABLEMENTMIN numeric(15,5)        null,
   RAISE6SECACTUALAVAILABILITY numeric(16,6)        null,
   RAISE60SECACTUALAVAILABILITY numeric(16,6)        null,
   RAISE5MINACTUALAVAILABILITY numeric(16,6)        null,
   RAISEREGACTUALAVAILABILITY numeric(16,6)        null,
   LOWER6SECACTUALAVAILABILITY numeric(16,6)        null,
   LOWER60SECACTUALAVAILABILITY numeric(16,6)        null,
   LOWER5MINACTUALAVAILABILITY numeric(16,6)        null,
   LOWERREGACTUALAVAILABILITY numeric(16,6)        null,
   SEMIDISPATCHCAP      numeric(3,0)         null
);

alter table DISPATCHLOAD
   add constraint PK_DISPATCHLOAD primary key (SETTLEMENTDATE, RUNNO, DUID, INTERVENTION);





create index DISPATCHLOAD_LCX on DISPATCHLOAD (
LASTCHANGED ASC
);





create index DISPATCHLOAD_NDX2 on DISPATCHLOAD (
DUID ASC,
LASTCHANGED ASC
);





create table DISPATCHLOAD_BNC (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   DUID                 varchar(10)          not null,
   INTERVENTION         numeric(2,0)         not null,
   CONNECTIONPOINTID    varchar(12)          null,
   DISPATCHMODE         numeric(2,0)         null,
   TOTALCLEARED         numeric(15,5)        null,
   RAISEREG             numeric(15,5)        null,
   RAISE5MIN            numeric(15,5)        null,
   RAISE60SEC           numeric(15,5)        null,
   RAISE6SEC            numeric(15,5)        null,
   LOWERREG             numeric(15,5)        null,
   LOWER5MIN            numeric(15,5)        null,
   LOWER60SEC           numeric(15,5)        null,
   LOWER6SEC            numeric(15,5)        null,
   RAISEREGFLAGS        numeric(3,0)         null,
   RAISE5MINFLAGS       numeric(3,0)         null,
   RAISE60SECFLAGS      numeric(3,0)         null,
   RAISE6SECFLAGS       numeric(3,0)         null,
   LOWERREGFLAGS        numeric(3,0)         null,
   LOWER5MINFLAGS       numeric(3,0)         null,
   LOWER60SECFLAGS      numeric(3,0)         null,
   LOWER6SECFLAGS       numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table DISPATCHLOAD_BNC
   add constraint PK_DISPATCHLOAD_BNC primary key (SETTLEMENTDATE, RUNNO, DUID, INTERVENTION);





create index DISPATCHLOAD_BNC_LCX on DISPATCHLOAD_BNC (
LASTCHANGED ASC
);





create index DISPATCHLOAD_BNC_NDX2 on DISPATCHLOAD_BNC (
DUID ASC,
LASTCHANGED ASC
);





create table DISPATCHOFFERTRK (
   SETTLEMENTDATE       timestamp(3)             not null,
   DUID                 varchar(10)          not null,
   BIDTYPE              varchar(10)          not null,
   BIDSETTLEMENTDATE    timestamp(3)             null,
   BIDOFFERDATE         timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table DISPATCHOFFERTRK
   add constraint DISPATCHOFFERTRK_PK primary key (SETTLEMENTDATE, DUID, BIDTYPE);





create index DISPATCHOFFERTRK_LCHD_IDX on DISPATCHOFFERTRK (
LASTCHANGED ASC
);





create index DISPATCHOFFERTRK_NDX2 on DISPATCHOFFERTRK (
DUID ASC,
LASTCHANGED ASC
);





create table DISPATCHPRICE (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   DISPATCHINTERVAL     varchar(22)          not null,
   INTERVENTION         numeric(2,0)         not null,
   RRP                  numeric(15,5)        null,
   EEP                  numeric(15,5)        null,
   ROP                  numeric(15,5)        null,
   APCFLAG              numeric(3,0)         null,
   MARKETSUSPENDEDFLAG  numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null,
   RAISE6SECRRP         numeric(15,5)        null,
   RAISE6SECROP         numeric(15,5)        null,
   RAISE6SECAPCFLAG     numeric(3,0)         null,
   RAISE60SECRRP        numeric(15,5)        null,
   RAISE60SECROP        numeric(15,5)        null,
   RAISE60SECAPCFLAG    numeric(3,0)         null,
   RAISE5MINRRP         numeric(15,5)        null,
   RAISE5MINROP         numeric(15,5)        null,
   RAISE5MINAPCFLAG     numeric(3,0)         null,
   RAISEREGRRP          numeric(15,5)        null,
   RAISEREGROP          numeric(15,5)        null,
   RAISEREGAPCFLAG      numeric(3,0)         null,
   LOWER6SECRRP         numeric(15,5)        null,
   LOWER6SECROP         numeric(15,5)        null,
   LOWER6SECAPCFLAG     numeric(3,0)         null,
   LOWER60SECRRP        numeric(15,5)        null,
   LOWER60SECROP        numeric(15,5)        null,
   LOWER60SECAPCFLAG    numeric(3,0)         null,
   LOWER5MINRRP         numeric(15,5)        null,
   LOWER5MINROP         numeric(15,5)        null,
   LOWER5MINAPCFLAG     numeric(3,0)         null,
   LOWERREGRRP          numeric(15,5)        null,
   LOWERREGROP          numeric(15,5)        null,
   LOWERREGAPCFLAG      numeric(3,0)         null,
   PRICE_STATUS         varchar(20)          null,
   PRE_AP_ENERGY_PRICE  numeric(15,5)        null,
   PRE_AP_RAISE6_PRICE  numeric(15,5)        null,
   PRE_AP_RAISE60_PRICE numeric(15,5)        null,
   PRE_AP_RAISE5MIN_PRICE numeric(15,5)        null,
   PRE_AP_RAISEREG_PRICE numeric(15,5)        null,
   PRE_AP_LOWER6_PRICE  numeric(15,5)        null,
   PRE_AP_LOWER60_PRICE numeric(15,5)        null,
   PRE_AP_LOWER5MIN_PRICE numeric(15,5)        null,
   PRE_AP_LOWERREG_PRICE numeric(15,5)        null,
   CUMUL_PRE_AP_ENERGY_PRICE numeric(15,5)        null,
   CUMUL_PRE_AP_RAISE6_PRICE numeric(15,5)        null,
   CUMUL_PRE_AP_RAISE60_PRICE numeric(15,5)        null,
   CUMUL_PRE_AP_RAISE5MIN_PRICE numeric(15,5)        null,
   CUMUL_PRE_AP_RAISEREG_PRICE numeric(15,5)        null,
   CUMUL_PRE_AP_LOWER6_PRICE numeric(15,5)        null,
   CUMUL_PRE_AP_LOWER60_PRICE numeric(15,5)        null,
   CUMUL_PRE_AP_LOWER5MIN_PRICE numeric(15,5)        null,
   CUMUL_PRE_AP_LOWERREG_PRICE numeric(15,5)        null,
   OCD_STATUS           varchar(14)          null,
   MII_STATUS           varchar(21)          null
);

alter table DISPATCHPRICE
   add constraint PK_DISPATCHPRICE primary key (SETTLEMENTDATE, RUNNO, REGIONID, DISPATCHINTERVAL, INTERVENTION);





create index DISPATCHPRICE_LCX on DISPATCHPRICE (
LASTCHANGED ASC
);





create table DISPATCHREGIONSUM (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   DISPATCHINTERVAL     numeric(22,0)        not null,
   INTERVENTION         numeric(2,0)         not null,
   TOTALDEMAND          numeric(15,5)        null,
   AVAILABLEGENERATION  numeric(15,5)        null,
   AVAILABLELOAD        numeric(15,5)        null,
   DEMANDFORECAST       numeric(15,5)        null,
   DISPATCHABLEGENERATION numeric(15,5)        null,
   DISPATCHABLELOAD     numeric(15,5)        null,
   NETINTERCHANGE       numeric(15,5)        null,
   EXCESSGENERATION     numeric(15,5)        null,
   LOWER5MINDISPATCH    numeric(15,5)        null,
   LOWER5MINIMPORT      numeric(15,5)        null,
   LOWER5MINLOCALDISPATCH numeric(15,5)        null,
   LOWER5MINLOCALPRICE  numeric(15,5)        null,
   LOWER5MINLOCALREQ    numeric(15,5)        null,
   LOWER5MINPRICE       numeric(15,5)        null,
   LOWER5MINREQ         numeric(15,5)        null,
   LOWER5MINSUPPLYPRICE numeric(15,5)        null,
   LOWER60SECDISPATCH   numeric(15,5)        null,
   LOWER60SECIMPORT     numeric(15,5)        null,
   LOWER60SECLOCALDISPATCH numeric(15,5)        null,
   LOWER60SECLOCALPRICE numeric(15,5)        null,
   LOWER60SECLOCALREQ   numeric(15,5)        null,
   LOWER60SECPRICE      numeric(15,5)        null,
   LOWER60SECREQ        numeric(15,5)        null,
   LOWER60SECSUPPLYPRICE numeric(15,5)        null,
   LOWER6SECDISPATCH    numeric(15,5)        null,
   LOWER6SECIMPORT      numeric(15,5)        null,
   LOWER6SECLOCALDISPATCH numeric(15,5)        null,
   LOWER6SECLOCALPRICE  numeric(15,5)        null,
   LOWER6SECLOCALREQ    numeric(15,5)        null,
   LOWER6SECPRICE       numeric(15,5)        null,
   LOWER6SECREQ         numeric(15,5)        null,
   LOWER6SECSUPPLYPRICE numeric(15,5)        null,
   RAISE5MINDISPATCH    numeric(15,5)        null,
   RAISE5MINIMPORT      numeric(15,5)        null,
   RAISE5MINLOCALDISPATCH numeric(15,5)        null,
   RAISE5MINLOCALPRICE  numeric(15,5)        null,
   RAISE5MINLOCALREQ    numeric(15,5)        null,
   RAISE5MINPRICE       numeric(15,5)        null,
   RAISE5MINREQ         numeric(15,5)        null,
   RAISE5MINSUPPLYPRICE numeric(15,5)        null,
   RAISE60SECDISPATCH   numeric(15,5)        null,
   RAISE60SECIMPORT     numeric(15,5)        null,
   RAISE60SECLOCALDISPATCH numeric(15,5)        null,
   RAISE60SECLOCALPRICE numeric(15,5)        null,
   RAISE60SECLOCALREQ   numeric(15,5)        null,
   RAISE60SECPRICE      numeric(15,5)        null,
   RAISE60SECREQ        numeric(15,5)        null,
   RAISE60SECSUPPLYPRICE numeric(15,5)        null,
   RAISE6SECDISPATCH    numeric(15,5)        null,
   RAISE6SECIMPORT      numeric(15,5)        null,
   RAISE6SECLOCALDISPATCH numeric(15,5)        null,
   RAISE6SECLOCALPRICE  numeric(15,5)        null,
   RAISE6SECLOCALREQ    numeric(15,5)        null,
   RAISE6SECPRICE       numeric(15,5)        null,
   RAISE6SECREQ         numeric(15,5)        null,
   RAISE6SECSUPPLYPRICE numeric(15,5)        null,
   AGGEGATEDISPATCHERROR numeric(15,5)        null,
   AGGREGATEDISPATCHERROR numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   INITIALSUPPLY        numeric(15,5)        null,
   CLEAREDSUPPLY        numeric(15,5)        null,
   LOWERREGIMPORT       numeric(15,5)        null,
   LOWERREGLOCALDISPATCH numeric(15,5)        null,
   LOWERREGLOCALREQ     numeric(15,5)        null,
   LOWERREGREQ          numeric(15,5)        null,
   RAISEREGIMPORT       numeric(15,5)        null,
   RAISEREGLOCALDISPATCH numeric(15,5)        null,
   RAISEREGLOCALREQ     numeric(15,5)        null,
   RAISEREGREQ          numeric(15,5)        null,
   RAISE5MINLOCALVIOLATION numeric(15,5)        null,
   RAISEREGLOCALVIOLATION numeric(15,5)        null,
   RAISE60SECLOCALVIOLATION numeric(15,5)        null,
   RAISE6SECLOCALVIOLATION numeric(15,5)        null,
   LOWER5MINLOCALVIOLATION numeric(15,5)        null,
   LOWERREGLOCALVIOLATION numeric(15,5)        null,
   LOWER60SECLOCALVIOLATION numeric(15,5)        null,
   LOWER6SECLOCALVIOLATION numeric(15,5)        null,
   RAISE5MINVIOLATION   numeric(15,5)        null,
   RAISEREGVIOLATION    numeric(15,5)        null,
   RAISE60SECVIOLATION  numeric(15,5)        null,
   RAISE6SECVIOLATION   numeric(15,5)        null,
   LOWER5MINVIOLATION   numeric(15,5)        null,
   LOWERREGVIOLATION    numeric(15,5)        null,
   LOWER60SECVIOLATION  numeric(15,5)        null,
   LOWER6SECVIOLATION   numeric(15,5)        null,
   RAISE6SECACTUALAVAILABILITY numeric(16,6)        null,
   RAISE60SECACTUALAVAILABILITY numeric(16,6)        null,
   RAISE5MINACTUALAVAILABILITY numeric(16,6)        null,
   RAISEREGACTUALAVAILABILITY numeric(16,6)        null,
   LOWER6SECACTUALAVAILABILITY numeric(16,6)        null,
   LOWER60SECACTUALAVAILABILITY numeric(16,6)        null,
   LOWER5MINACTUALAVAILABILITY numeric(16,6)        null,
   LOWERREGACTUALAVAILABILITY numeric(16,6)        null,
   LORSURPLUS           numeric(16,6)        null,
   LRCSURPLUS           numeric(16,6)        null,
   TOTALINTERMITTENTGENERATION numeric(15,5)        null,
   DEMAND_AND_NONSCHEDGEN numeric(15,5)        null,
   UIGF                 numeric(15,5)        null,
   SEMISCHEDULE_CLEAREDMW numeric(15,5)        null,
   SEMISCHEDULE_COMPLIANCEMW numeric(15,5)        null,
   SS_SOLAR_UIGF        numeric(15,5)        null,
   SS_WIND_UIGF         numeric(15,5)        null,
   SS_SOLAR_CLEAREDMW   numeric(15,5)        null,
   SS_WIND_CLEAREDMW    numeric(15,5)        null,
   SS_SOLAR_COMPLIANCEMW numeric(15,5)        null,
   SS_WIND_COMPLIANCEMW numeric(15,5)        null
);

alter table DISPATCHREGIONSUM
   add constraint PK_DISPATCHREGIONSUM primary key (SETTLEMENTDATE, RUNNO, REGIONID, DISPATCHINTERVAL, INTERVENTION);





create index DISPATCHREGIONSUM_LCX on DISPATCHREGIONSUM (
LASTCHANGED ASC
);





create table DISPATCHTRK (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   REASON               varchar(64)          null,
   SPDRUNNO             numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table DISPATCHTRK
   add constraint DISPATCHTRK_PK primary key (SETTLEMENTDATE, RUNNO);





create index DISPATCHTRK_LCX on DISPATCHTRK (
LASTCHANGED ASC
);





create table DISPATCH_CONSTRAINT_FCAS_OCD (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3)           not null,
   INTERVENTION         numeric(2)           not null,
   CONSTRAINTID         varchar(20)          not null,
   VERSIONNO            numeric(3)           not null,
   LASTCHANGED          timestamp(3)             null,
   RHS                  numeric(15,5)        null,
   MARGINALVALUE        numeric(15,5)        null,
   VIOLATIONDEGREE      numeric(15,5)        null
);

alter table DISPATCH_CONSTRAINT_FCAS_OCD
   add constraint DISPATCH_CONSTRNT_FCAS_OCD_PK primary key (SETTLEMENTDATE, RUNNO, INTERVENTION, CONSTRAINTID, VERSIONNO);





create index DISPATCH_CONSTRNT_FCASOCD_LCX on DISPATCH_CONSTRAINT_FCAS_OCD (
LASTCHANGED ASC
);





create table DISPATCH_FCAS_REQ (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   INTERVENTION         numeric(2,0)         not null,
   GENCONID             varchar(20)          not null,
   REGIONID             varchar(10)          not null,
   BIDTYPE              varchar(10)          not null,
   GENCONEFFECTIVEDATE  timestamp(3)             null,
   GENCONVERSIONNO      numeric(3,0)         null,
   MARGINALVALUE        numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null,
   BASE_COST            numeric(18,8)        null,
   ADJUSTED_COST        numeric(18,8)        null,
   ESTIMATED_CMPF       numeric(18,8)        null,
   ESTIMATED_CRMPF      numeric(18,8)        null,
   RECOVERY_FACTOR_CMPF numeric(18,8)        null,
   RECOVERY_FACTOR_CRMPF numeric(18,8)        null
);

alter table DISPATCH_FCAS_REQ
   add constraint DISPATCH_FCAS_REQ_PK primary key (SETTLEMENTDATE, RUNNO, INTERVENTION, GENCONID, REGIONID, BIDTYPE);





create index DISPATCH_FCAS_REQ_LCX on DISPATCH_FCAS_REQ (
LASTCHANGED ASC
);





create table DISPATCH_INTERCONNECTION (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   INTERVENTION         numeric(2,0)         not null,
   FROM_REGIONID        varchar(20)          not null,
   TO_REGIONID          varchar(20)          not null,
   DISPATCHINTERVAL     numeric(22,0)        null,
   IRLF                 numeric(15,5)        null,
   MWFLOW               numeric(16,6)        null,
   METEREDMWFLOW        numeric(16,6)        null,
   FROM_REGION_MW_LOSSES numeric(16,6)        null,
   TO_REGION_MW_LOSSES  numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table DISPATCH_INTERCONNECTION
   add constraint DISPATCH_INTERCONNECTION_PK primary key (SETTLEMENTDATE, RUNNO, FROM_REGIONID, TO_REGIONID, INTERVENTION);





create table DISPATCH_LOCAL_PRICE (
   SETTLEMENTDATE       timestamp(3)             not null,
   DUID                 varchar(20)          not null,
   LOCAL_PRICE_ADJUSTMENT numeric(10,2)        null,
   LOCALLY_CONSTRAINED  numeric(1,0)         null
);

alter table DISPATCH_LOCAL_PRICE
   add constraint DISPATCH_LOCAL_PRICE_PK primary key (SETTLEMENTDATE, DUID);





create table DISPATCH_MNSPBIDTRK (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   LINKID               varchar(10)          not null,
   OFFERSETTLEMENTDATE  timestamp(3)             null,
   OFFEREFFECTIVEDATE   timestamp(3)             null,
   OFFERVERSIONNO       numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table DISPATCH_MNSPBIDTRK
   add constraint DISPATCH_MNSPBIDTRK_PK primary key (SETTLEMENTDATE, RUNNO, PARTICIPANTID, LINKID);





create index DISPATCH_MNSPBIDTRK_LCX on DISPATCH_MNSPBIDTRK (
LASTCHANGED ASC
);





create table DISPATCH_MR_SCHEDULE_TRK (
   SETTLEMENTDATE       timestamp(3)             not null,
   REGIONID             varchar(10)          not null,
   MR_DATE              timestamp(3)             null,
   VERSION_DATETIME     timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table DISPATCH_MR_SCHEDULE_TRK
   add constraint DISPATCH_MR_SCHEDULE_TRK_PK primary key (SETTLEMENTDATE, REGIONID);





create index DISPATCH_MR_SCHEDULE_TRK_LCX on DISPATCH_MR_SCHEDULE_TRK (
LASTCHANGED ASC
);





create table DISPATCH_PRICE_REVISION (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   INTERVENTION         numeric(2,0)         not null,
   REGIONID             varchar(10)          not null,
   BIDTYPE              varchar(10)          not null,
   VERSIONNO            numeric(3)           not null,
   RRP_NEW              numeric(15,5)        null,
   RRP_OLD              numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table DISPATCH_PRICE_REVISION
   add constraint DISPATCH_PRICE_REVISION_PK primary key (SETTLEMENTDATE, RUNNO, INTERVENTION, REGIONID, BIDTYPE, VERSIONNO);





create index DISPATCH_PRICE_REVISION_LCX on DISPATCH_PRICE_REVISION (
LASTCHANGED ASC
);





create table DISPATCH_UNIT_CONFORMANCE (
   INTERVAL_DATETIME    timestamp(3)             not null,
   DUID                 varchar(20)          not null,
   TOTALCLEARED         numeric(16,6)        null,
   ACTUALMW             numeric(16,6)        null,
   ROC                  numeric(16,6)        null,
   AVAILABILITY         numeric(16,6)        null,
   LOWERREG             numeric(16,6)        null,
   RAISEREG             numeric(16,6)        null,
   STRIGLM              numeric(16,6)        null,
   LTRIGLM              numeric(16,6)        null,
   MWERROR              numeric(16,6)        null,
   MAX_MWERROR          numeric(16,6)        null,
   LECOUNT              numeric(6)           null,
   SECOUNT              numeric(6)           null,
   STATUS               varchar(20)          null,
   PARTICIPANT_STATUS_ACTION varchar(100)         null,
   OPERATING_MODE       varchar(20)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table DISPATCH_UNIT_CONFORMANCE
   add constraint PK_DISPATCH_UNIT_CONFORMANCE primary key (INTERVAL_DATETIME, DUID);





create index DISPATCH_UNIT_CONFORMANCE_LCX on DISPATCH_UNIT_CONFORMANCE (
LASTCHANGED ASC
);





create table DISPATCH_UNIT_SCADA (
   SETTLEMENTDATE       timestamp(3)             not null,
   DUID                 varchar(20)          not null,
   SCADAVALUE           numeric(16,6)        null
);

alter table DISPATCH_UNIT_SCADA
   add constraint DISPATCH_UNIT_SCADA_PK primary key (SETTLEMENTDATE, DUID);





create table DUALLOC (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   DUID                 varchar(10)          not null,
   GENSETID             varchar(20)          not null,
   LASTCHANGED          timestamp(3)             null
);

alter table DUALLOC
   add constraint DUALLOC_PK primary key (DUID, EFFECTIVEDATE, VERSIONNO, GENSETID);





create index DUALLOC_NDX2 on DUALLOC (
DUID ASC
);





create index DUALLOC_LCX on DUALLOC (
LASTCHANGED ASC
);





create table DUDETAIL (
   EFFECTIVEDATE        timestamp(3)             not null,
   DUID                 varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   CONNECTIONPOINTID    varchar(10)          null,
   VOLTLEVEL            varchar(10)          null,
   REGISTEREDCAPACITY   numeric(6,0)         null,
   AGCCAPABILITY        varchar(1)           null,
   DISPATCHTYPE         varchar(10)          null,
   MAXCAPACITY          numeric(6,0)         null,
   STARTTYPE            varchar(20)          null,
   NORMALLYONFLAG       varchar(1)           null,
   PHYSICALDETAILSFLAG  varchar(1)           null,
   SPINNINGRESERVEFLAG  varchar(1)           null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null,
   INTERMITTENTFLAG     varchar(1)           null,
   SEMISCHEDULE_FLAG    varchar(1)           null,
   MAXRATEOFCHANGEUP    numeric(6,0)         null,
   MAXRATEOFCHANGEDOWN  numeric(6,0)         null
);

alter table DUDETAIL
   add constraint DUDETAIL_PK primary key (DUID, EFFECTIVEDATE, VERSIONNO);





create index DUDETAIL_LCX on DUDETAIL (
LASTCHANGED ASC
);





create table DUDETAILSUMMARY (
   DUID                 varchar(10)          not null,
   START_DATE           timestamp(3)             not null,
   END_DATE             timestamp(3)             not null,
   DISPATCHTYPE         varchar(10)          null,
   CONNECTIONPOINTID    varchar(10)          null,
   REGIONID             varchar(10)          null,
   STATIONID            varchar(10)          null,
   PARTICIPANTID        varchar(10)          null,
   LASTCHANGED          timestamp(3)             null,
   TRANSMISSIONLOSSFACTOR numeric(15,5)        null,
   STARTTYPE            varchar(20)          null,
   DISTRIBUTIONLOSSFACTOR numeric(15,5)        null,
   MINIMUM_ENERGY_PRICE numeric(9,2)         null,
   MAXIMUM_ENERGY_PRICE numeric(9,2)         null,
   SCHEDULE_TYPE        varchar(20)          null,
   MIN_RAMP_RATE_UP     numeric(6,0)         null,
   MIN_RAMP_RATE_DOWN   numeric(6,0)         null,
   MAX_RAMP_RATE_UP     numeric(6,0)         null,
   MAX_RAMP_RATE_DOWN   numeric(6,0)         null,
   IS_AGGREGATED        numeric(1,0)         null
);

alter table DUDETAILSUMMARY
   add constraint DUDETAILSUMMARY_PK primary key (DUID, START_DATE);





create index DUDETAILSUMMARY_LCX on DUDETAILSUMMARY (
LASTCHANGED ASC
);





create table EMSMASTER (
   SPD_ID               varchar(21)          not null,
   SPD_TYPE             varchar(1)           not null,
   DESCRIPTION          varchar(255)         null,
   GROUPING_ID          varchar(20)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table EMSMASTER
   add constraint EMSMASTER_PK primary key (SPD_ID, SPD_TYPE);





create index EMSMASTER_LCX on EMSMASTER (
LASTCHANGED ASC
);





create table FORCEMAJEURE (
   FMID                 varchar(10)          not null,
   STARTDATE            timestamp(3)             null,
   STARTPERIOD          numeric(3,0)         null,
   ENDDATE              timestamp(3)             null,
   ENDPERIOD            numeric(3,0)         null,
   APCSTARTDATE         timestamp(3)             null,
   STARTAUTHORISEDBY    varchar(15)          null,
   ENDAUTHORISEDBY      varchar(15)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table FORCEMAJEURE
   add constraint FORCEMAJEURE_PK primary key (FMID);





create index FORCEMAJEURE_LCX on FORCEMAJEURE (
LASTCHANGED ASC
);





create table FORCEMAJEUREREGION (
   FMID                 varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   LASTCHANGED          timestamp(3)             null
);

alter table FORCEMAJEUREREGION
   add constraint FORCEMAJEUREREGION_PK primary key (FMID, REGIONID);





create index FORCEMAJEUREREGION_LCX on FORCEMAJEUREREGION (
LASTCHANGED ASC
);





create table GDINSTRUCT (
   DUID                 varchar(10)          null,
   STATIONID            varchar(10)          null,
   REGIONID             varchar(10)          null,
   ID                   numeric(22,0)        not null,
   INSTRUCTIONTYPEID    varchar(10)          null,
   INSTRUCTIONSUBTYPEID varchar(10)          null,
   INSTRUCTIONCLASSID   varchar(10)          null,
   REASON               varchar(64)          null,
   INSTLEVEL            numeric(6,0)         null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   PARTICIPANTID        varchar(10)          null,
   ISSUEDTIME           timestamp(3)             null,
   TARGETTIME           timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table GDINSTRUCT
   add constraint GDINSTRUCT_PK primary key (ID);





create index GDINSTRUCT_LCX on GDINSTRUCT (
LASTCHANGED ASC
);





create index GDINSTRUCT_NDX2 on GDINSTRUCT (
DUID ASC
);





create index GDINSTRUCT_NDX3 on GDINSTRUCT (
TARGETTIME ASC
);





create table GENCONDATA (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   GENCONID             varchar(20)          not null,
   CONSTRAINTTYPE       varchar(2)           null,
   CONSTRAINTVALUE      numeric(16,6)        null,
   DESCRIPTION          varchar(256)         null,
   STATUS               varchar(8)           null,
   GENERICCONSTRAINTWEIGHT numeric(16,6)        null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   DYNAMICRHS           numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   DISPATCH             varchar(1)           null,
   PREDISPATCH          varchar(1)           null,
   STPASA               varchar(1)           null,
   MTPASA               varchar(1)           null,
   IMPACT               varchar(64)          null,
   SOURCE               varchar(128)         null,
   LIMITTYPE            varchar(64)          null,
   REASON               varchar(256)         null,
   MODIFICATIONS        varchar(256)         null,
   ADDITIONALNOTES      varchar(256)         null,
   P5MIN_SCOPE_OVERRIDE varchar(2)           null,
   LRC                  varchar(1)           null,
   LOR                  varchar(1)           null,
   FORCE_SCADA          numeric(1,0)         null
);

alter table GENCONDATA
   add constraint GENCONDATA_PK primary key (EFFECTIVEDATE, VERSIONNO, GENCONID);





create index GENCONDATA_LCX on GENCONDATA (
LASTCHANGED ASC
);





create table GENCONSET (
   GENCONSETID          varchar(20)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   GENCONID             varchar(20)          not null,
   GENCONEFFDATE        timestamp(3)             null,
   GENCONVERSIONNO      numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table GENCONSET
   add constraint GENCONSET_PK primary key (GENCONSETID, EFFECTIVEDATE, VERSIONNO, GENCONID);





create index GENCONSET_LCX on GENCONSET (
LASTCHANGED ASC
);





create table GENCONSETINVOKE (
   INVOCATION_ID        numeric(9)           not null,
   STARTDATE            timestamp(3)             not null,
   STARTPERIOD          numeric(3,0)         not null,
   GENCONSETID          varchar(20)          not null,
   ENDDATE              timestamp(3)             null,
   ENDPERIOD            numeric(3,0)         null,
   STARTAUTHORISEDBY    varchar(15)          null,
   ENDAUTHORISEDBY      varchar(15)          null,
   INTERVENTION         varchar(1)           null,
   ASCONSTRAINTTYPE     varchar(10)          null,
   LASTCHANGED          timestamp(3)             null,
   STARTINTERVALDATETIME timestamp(3)             null,
   ENDINTERVALDATETIME  timestamp(3)             null,
   SYSTEMNORMAL         varchar(1)           null
);

alter table GENCONSETINVOKE
   add constraint GENCONSETINV_PK primary key (INVOCATION_ID);





create index GENCONSETINVOKE_LCX on GENCONSETINVOKE (
LASTCHANGED ASC
);





create table GENCONSETTRK (
   GENCONSETID          varchar(20)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   DESCRIPTION          varchar(256)         null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null,
   COVERAGE             varchar(64)          null,
   MODIFICATIONS        varchar(256)         null,
   SYSTEMNORMAL         varchar(1)           null,
   OUTAGE               varchar(256)         null
);

alter table GENCONSETTRK
   add constraint GENCONSETTRK_PK primary key (GENCONSETID, EFFECTIVEDATE, VERSIONNO);





create index GENCONSETTRK_LCX on GENCONSETTRK (
LASTCHANGED ASC
);





create table GENERICCONSTRAINTRHS (
   GENCONID             varchar(20)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(22,0)        not null,
   SCOPE                varchar(2)           not null,
   TERMID               numeric(4,0)         not null,
   GROUPID              numeric(3,0)         null,
   SPD_ID               varchar(21)          null,
   SPD_TYPE             varchar(1)           null,
   FACTOR               numeric(16,6)        null,
   OPERATION            varchar(10)          null,
   DEFAULTVALUE         numeric(16,6)        null,
   PARAMETERTERM1       varchar(12)          null,
   PARAMETERTERM2       varchar(12)          null,
   PARAMETERTERM3       varchar(12)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table GENERICCONSTRAINTRHS
   add constraint GENERICCONSTRAINTRHS_PK primary key (GENCONID, EFFECTIVEDATE, VERSIONNO, SCOPE, TERMID);





create index GENERICCONSTRAINTRHS_LCHD_IDX on GENERICCONSTRAINTRHS (
LASTCHANGED ASC
);





create table GENERICEQUATIONDESC (
   EQUATIONID           varchar(20)          not null,
   DESCRIPTION          varchar(256)         null,
   LASTCHANGED          timestamp(3)             null,
   IMPACT               varchar(64)          null,
   SOURCE               varchar(128)         null,
   LIMITTYPE            varchar(64)          null,
   REASON               varchar(256)         null,
   MODIFICATIONS        varchar(256)         null,
   ADDITIONALNOTES      varchar(256)         null
);

alter table GENERICEQUATIONDESC
   add constraint GENERICEQUATIONDESC_PK primary key (EQUATIONID);





create index GENERICEQUATIONDS_LCHD_IDX on GENERICEQUATIONDESC (
LASTCHANGED ASC
);





create table GENERICEQUATIONRHS (
   EQUATIONID           varchar(20)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   TERMID               numeric(3,0)         not null,
   GROUPID              numeric(3,0)         null,
   SPD_ID               varchar(21)          null,
   SPD_TYPE             varchar(1)           null,
   FACTOR               numeric(16,6)        null,
   OPERATION            varchar(10)          null,
   DEFAULTVALUE         numeric(16,6)        null,
   PARAMETERTERM1       varchar(12)          null,
   PARAMETERTERM2       varchar(12)          null,
   PARAMETERTERM3       varchar(12)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table GENERICEQUATIONRHS
   add constraint GENERICEQUATIONRHS_PK primary key (EQUATIONID, EFFECTIVEDATE, VERSIONNO, TERMID);





create index GENERICEQUATION_LCHD_IDX on GENERICEQUATIONRHS (
LASTCHANGED ASC
);





create table GENMETER (
   METERID              varchar(12)          not null,
   GENSETID             varchar(20)          null,
   CONNECTIONPOINTID    varchar(10)          null,
   STATIONID            varchar(10)          null,
   METERTYPE            varchar(20)          null,
   METERCLASS           varchar(10)          null,
   VOLTAGELEVEL         numeric(6,0)         null,
   APPLYDATE            timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDBY         varchar(10)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   COMDATE              timestamp(3)             null,
   DECOMDATE            timestamp(3)             null,
   ENDDATE              timestamp(3)             null,
   STARTDATE            timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table GENMETER
   add constraint GENMETERS_PK primary key (METERID, APPLYDATE, VERSIONNO);





create index GENMETER_LCX on GENMETER (
LASTCHANGED ASC
);





create index GENMETER_NDX2 on GENMETER (
STATIONID ASC
);





create table GENUNITMTRINPERIOD (
   PARTICIPANTID        varchar(10)          not null,
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(6,0)         not null,
   CONNECTIONPOINTID    varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   GENUNITID            varchar(10)          null,
   STATIONID            varchar(10)          null,
   IMPORTENERGYVALUE    numeric(16,6)        null,
   EXPORTENERGYVALUE    numeric(16,6)        null,
   IMPORTREACTIVEVALUE  numeric(16,6)        null,
   EXPORTREACTIVEVALUE  numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null,
   MDA                  varchar(10)          not null,
   LOCAL_RETAILER       varchar(10)          not null default 'POOLNSW'
);

alter table GENUNITMTRINPERIOD
   add constraint GENUNITMTRINPERD_PK primary key (SETTLEMENTDATE, MDA, VERSIONNO, CONNECTIONPOINTID, PARTICIPANTID, LOCAL_RETAILER, PERIODID);





create index GENUNITMTRINPERIOD_LCX on GENUNITMTRINPERIOD (
LASTCHANGED ASC
);





create index GENUNITMTRINPERIOD_NDX2 on GENUNITMTRINPERIOD (
STATIONID ASC
);





create table GENUNITS (
   GENSETID             varchar(20)          not null,
   STATIONID            varchar(10)          null,
   SETLOSSFACTOR        numeric(16,6)        null,
   CDINDICATOR          varchar(10)          null,
   AGCFLAG              varchar(2)           null,
   SPINNINGFLAG         varchar(2)           null,
   VOLTLEVEL            numeric(6,0)         null,
   REGISTEREDCAPACITY   numeric(6,0)         null,
   DISPATCHTYPE         varchar(10)          null,
   STARTTYPE            varchar(20)          null,
   MKTGENERATORIND      varchar(10)          null,
   NORMALSTATUS         varchar(10)          null,
   MAXCAPACITY          numeric(6,0)         null,
   GENSETTYPE           varchar(15)          null,
   GENSETNAME           varchar(40)          null,
   LASTCHANGED          timestamp(3)             null,
   CO2E_EMISSIONS_FACTOR numeric(18,8)        null,
   CO2E_ENERGY_SOURCE   varchar(100)         null,
   CO2E_DATA_SOURCE     varchar(20)          null
);

alter table GENUNITS
   add constraint GENUNIT_PK primary key (GENSETID);





create index GENUNITS_LCX on GENUNITS (
LASTCHANGED ASC
);





create table GENUNITS_UNIT (
   GENSETID             varchar(20)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(6,0)         not null,
   UNIT_GROUPING_LABEL  varchar(20)          not null,
   UNIT_COUNT           numeric(3,0)         null,
   UNIT_SIZE            numeric(8,3)         null,
   UNIT_MAX_SIZE        numeric(8,3)         null,
   AGGREGATION_FLAG     numeric(1,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table GENUNITS_UNIT
   add constraint GENUNITS_UNIT_PK primary key (GENSETID, EFFECTIVEDATE, VERSIONNO, UNIT_GROUPING_LABEL);





create table GST_BAS_CLASS (
   BAS_CLASS            varchar(30)          not null,
   DESCRIPTION          varchar(100)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table GST_BAS_CLASS
   add constraint GST_BAS_CLASS_PK primary key (BAS_CLASS);





create index GST_BAS_CLASS_LCX on GST_BAS_CLASS (
LASTCHANGED ASC
);





create table GST_RATE (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   BAS_CLASS            varchar(30)          not null,
   GST_RATE             numeric(8,5)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table GST_RATE
   add constraint GST_RATE_PK primary key (EFFECTIVEDATE, VERSIONNO, BAS_CLASS);





create index GST_RATE_LCX on GST_RATE (
LASTCHANGED ASC
);





create table GST_TRANSACTION_CLASS (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   TRANSACTION_TYPE     varchar(30)          not null,
   BAS_CLASS            varchar(30)          not null,
   LASTCHANGED          timestamp(3)             null
);

alter table GST_TRANSACTION_CLASS
   add constraint GST_TRANS_CLASS_PK primary key (EFFECTIVEDATE, VERSIONNO, TRANSACTION_TYPE, BAS_CLASS);





create index GST_TRAN_CLASS_LCX on GST_TRANSACTION_CLASS (
LASTCHANGED ASC
);





create table GST_TRANSACTION_TYPE (
   TRANSACTION_TYPE     varchar(30)          not null,
   DESCRIPTION          varchar(100)         null,
   GL_FINANCIALCODE     varchar(10)          null,
   GL_TCODE             varchar(15)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table GST_TRANSACTION_TYPE
   add constraint GST_TRANSACTION_TYPE_PK primary key (TRANSACTION_TYPE);





create index GST_TRANSACTION_TYPE_LCX on GST_TRANSACTION_TYPE (
LASTCHANGED ASC
);





create table INSTRUCTIONSUBTYPE (
   INSTRUCTIONTYPEID    varchar(10)          not null,
   INSTRUCTIONSUBTYPEID varchar(10)          not null,
   DESCRIPTION          varchar(64)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table INSTRUCTIONSUBTYPE
   add constraint INSTRUCTIONSUBTYPE_PK primary key (INSTRUCTIONTYPEID, INSTRUCTIONSUBTYPEID);





create index INSTRUCTIONSUBTYPE_LCX on INSTRUCTIONSUBTYPE (
LASTCHANGED ASC
);





create table INSTRUCTIONTYPE (
   INSTRUCTIONTYPEID    varchar(10)          not null,
   DESCRIPTION          varchar(64)          null,
   REGIONID             varchar(10)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table INSTRUCTIONTYPE
   add constraint INSTRUCTIONTYPE_PK primary key (INSTRUCTIONTYPEID);





create index INSTRUCTIONTYPE_LCX on INSTRUCTIONTYPE (
LASTCHANGED ASC
);





create table INTCONTRACT (
   CONTRACTID           varchar(10)          not null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          null,
   STARTDATE            timestamp(3)             null,
   ENDDATE              timestamp(3)             null,
   STARTPERIOD          numeric(3,0)         null,
   ENDPERIOD            numeric(3,0)         null,
   DEREGISTRATIONDATE   timestamp(3)             null,
   DEREGISTRATIONPERIOD numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null,
   REGIONID             varchar(10)          null
);

alter table INTCONTRACT
   add constraint INTCONTRACT_PK primary key (CONTRACTID);





create index INTCONTRACT_LCX on INTCONTRACT (
LASTCHANGED ASC
);





create table INTCONTRACTAMOUNT (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   AMOUNT               numeric(16,6)        null,
   RCF                  char(1)              null,
   LASTCHANGED          timestamp(3)             not null
);

alter table INTCONTRACTAMOUNT
   add constraint INTCONTRACTAMOUNT_PK primary key (CONTRACTID, VERSIONNO, PERIODID);





create index INTCONTRACTAMOUNT_LCX on INTCONTRACTAMOUNT (
LASTCHANGED ASC
);





create table INTCONTRACTAMOUNTTRK (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table INTCONTRACTAMOUNTTRK
   add constraint INTCONTRACTAMOUNTTRK_PK primary key (CONTRACTID, VERSIONNO);





create index INTCONTRACTAMOUNTTRK_LCX on INTCONTRACTAMOUNTTRK (
LASTCHANGED ASC
);





create table INTERCONNECTOR (
   INTERCONNECTORID     varchar(10)          not null,
   REGIONFROM           varchar(10)          null,
   RSOID                varchar(10)          null,
   REGIONTO             varchar(10)          null,
   DESCRIPTION          varchar(64)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table INTERCONNECTOR
   add constraint INTERCONNECTOR_PK primary key (INTERCONNECTORID);





create index INTERCONNECTOR_LCX on INTERCONNECTOR (
LASTCHANGED ASC
);





create table INTERCONNECTORALLOC (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(5,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   PARTICIPANTID        varchar(10)          not null,
   ALLOCATION           numeric(12,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table INTERCONNECTORALLOC
   add constraint INTERCONNECTORALLOC_PK primary key (EFFECTIVEDATE, VERSIONNO, INTERCONNECTORID, REGIONID, PARTICIPANTID);





create index INTERCONNECTORALLOC_LCX on INTERCONNECTORALLOC (
LASTCHANGED ASC
);





create table INTERCONNECTORCONSTRAINT (
   RESERVEOVERALLLOADFACTOR numeric(5,2)         null,
   FROMREGIONLOSSSHARE  numeric(5,2)         null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   MAXMWIN              numeric(15,5)        null,
   MAXMWOUT             numeric(15,5)        null,
   LOSSCONSTANT         numeric(15,6)        null,
   LOSSFLOWCOEFFICIENT  numeric(27,17)       null,
   EMSMEASURAND         varchar(40)          null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   DYNAMICRHS           varchar(1)           null,
   IMPORTLIMIT          numeric(6,0)         null,
   EXPORTLIMIT          numeric(6,0)         null,
   OUTAGEDERATIONFACTOR numeric(15,5)        null,
   NONPHYSICALLOSSFACTOR numeric(15,5)        null,
   OVERLOADFACTOR60SEC  numeric(15,5)        null,
   OVERLOADFACTOR6SEC   numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   FCASSUPPORTUNAVAILABLE numeric(1,0)         null,
   ICTYPE               varchar(10)          null
);

alter table INTERCONNECTORCONSTRAINT
   add constraint INTCCONSTRAINT_PK primary key (EFFECTIVEDATE, VERSIONNO, INTERCONNECTORID);





create index INTERCONNECTORCONSTRAINT_LCX on INTERCONNECTORCONSTRAINT (
LASTCHANGED ASC
);





create table INTERCONNMWFLOW (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(6,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   IMPORTENERGYVALUE    numeric(15,6)        null,
   EXPORTENERGYVALUE    numeric(15,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table INTERCONNMWFLOW
   add constraint INTERCONNMWFLOW_PK primary key (SETTLEMENTDATE, VERSIONNO, INTERCONNECTORID, PERIODID);





create index INTERCONNMWFLOW_LCIDX on INTERCONNMWFLOW (
LASTCHANGED ASC
);





create table INTERMITTENT_CLUSTER_AVAIL (
   TRADINGDATE          timestamp(3)             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        timestamp(3)             not null,
   CLUSTERID            varchar(20)          not null,
   PERIODID             numeric(3,0)         not null,
   ELEMENTS_UNAVAILABLE numeric(3,0)         null
);

alter table INTERMITTENT_CLUSTER_AVAIL
   add constraint INTERMITTENT_CLUSTER_AVAIL_PK primary key (TRADINGDATE, DUID, OFFERDATETIME, CLUSTERID, PERIODID);





create table INTERMITTENT_CLUSTER_AVAIL_DAY (
   TRADINGDATE          timestamp(3)             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        timestamp(3)             not null,
   CLUSTERID            varchar(20)          not null
);

alter table INTERMITTENT_CLUSTER_AVAIL_DAY
   add constraint INTERMITTENT_CLUST_AVL_DAY_PK primary key (TRADINGDATE, DUID, OFFERDATETIME, CLUSTERID);





create table INTERMITTENT_DS_PRED (
   RUN_DATETIME         timestamp(3)             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        timestamp(3)             not null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   ORIGIN               varchar(20)          not null,
   FORECAST_PRIORITY    numeric(10,0)        not null,
   FORECAST_MEAN        numeric(18,8)        null,
   FORECAST_POE10       numeric(18,8)        null,
   FORECAST_POE50       numeric(18,8)        null,
   FORECAST_POE90       numeric(18,8)        null
);

alter table INTERMITTENT_DS_PRED
   add constraint INTERMITTENT_DS_PRED_PK primary key (RUN_DATETIME, DUID, OFFERDATETIME, INTERVAL_DATETIME, ORIGIN, FORECAST_PRIORITY);





create table INTERMITTENT_DS_RUN (
   RUN_DATETIME         timestamp(3)             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        timestamp(3)             not null,
   ORIGIN               varchar(20)          not null,
   FORECAST_PRIORITY    numeric(10,0)        not null,
   AUTHORISEDBY         varchar(20)          null,
   COMMENTS             varchar(200)         null,
   LASTCHANGED          timestamp(3)             null,
   MODEL                varchar(30)          null,
   PARTICIPANT_TIMESTAMP timestamp(3)             null,
   SUPPRESSED_AEMO      numeric(1,0)         null,
   SUPPRESSED_PARTICIPANT numeric(1,0)         null,
   TRANSACTION_ID       varchar(100)         null
);

alter table INTERMITTENT_DS_RUN
   add constraint INTERMITTENT_DS_RUN_PK primary key (RUN_DATETIME, DUID, OFFERDATETIME, ORIGIN, FORECAST_PRIORITY);





create table INTERMITTENT_FORECAST_TRK (
   SETTLEMENTDATE       timestamp(3)             not null,
   DUID                 varchar(20)          not null,
   ORIGIN               varchar(20)          null,
   FORECAST_PRIORITY    numeric(10,0)        null,
   OFFERDATETIME        timestamp(3)             null
);

alter table INTERMITTENT_FORECAST_TRK
   add constraint INTERMITTENT_FORECAST_TRK_PK primary key (SETTLEMENTDATE, DUID);





create table INTERMITTENT_GEN_FCST (
   RUN_DATETIME         timestamp(3)             not null,
   DUID                 varchar(20)          not null,
   START_INTERVAL_DATETIME timestamp(3)             not null,
   END_INTERVAL_DATETIME timestamp(3)             not null,
   VERSIONNO            numeric(10,0)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table INTERMITTENT_GEN_FCST
   add constraint PK_INTERMITTENT_GEN_FCST primary key (RUN_DATETIME, DUID);





create table INTERMITTENT_GEN_FCST_DATA (
   RUN_DATETIME         timestamp(3)             not null,
   DUID                 varchar(20)          not null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   POWERMEAN            numeric(9,3)         null,
   POWERPOE50           numeric(9,3)         null,
   POWERPOELOW          numeric(9,3)         null,
   POWERPOEHIGH         numeric(9,3)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table INTERMITTENT_GEN_FCST_DATA
   add constraint PK_INTERMITTENT_GEN_FCST_DATA primary key (RUN_DATETIME, DUID, INTERVAL_DATETIME);





create table INTERMITTENT_GEN_LIMIT (
   TRADINGDATE          timestamp(3)             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        timestamp(3)             not null,
   PERIODID             numeric(3,0)         not null,
   UPPERMWLIMIT         numeric(6)           null
);

alter table INTERMITTENT_GEN_LIMIT
   add constraint INTERMITTENT_GEN_LIMIT_PK primary key (TRADINGDATE, DUID, OFFERDATETIME, PERIODID);





create table INTERMITTENT_GEN_LIMIT_DAY (
   TRADINGDATE          timestamp(3)             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        timestamp(3)             not null,
   PARTICIPANTID        varchar(20)          null,
   LASTCHANGED          timestamp(3)             null,
   AUTHORISEDBYUSER     varchar(20)          null,
   AUTHORISEDBYPARTICIPANTID varchar(20)          null
);

alter table INTERMITTENT_GEN_LIMIT_DAY
   add constraint INTERMITTENT_GEN_LIMIT_DAY_PK primary key (TRADINGDATE, DUID, OFFERDATETIME);





create table INTERMITTENT_P5_PRED (
   RUN_DATETIME         timestamp(3)             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        timestamp(3)             not null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   ORIGIN               varchar(20)          not null,
   FORECAST_PRIORITY    numeric(10,0)        not null,
   FORECAST_MEAN        numeric(18,8)        null,
   FORECAST_POE10       numeric(18,8)        null,
   FORECAST_POE50       numeric(18,8)        null,
   FORECAST_POE90       numeric(18,8)        null
);

alter table INTERMITTENT_P5_PRED
   add constraint INTERMITTENT_P5_PRED_PK primary key (RUN_DATETIME, DUID, OFFERDATETIME, INTERVAL_DATETIME, ORIGIN, FORECAST_PRIORITY);





create table INTERMITTENT_P5_RUN (
   RUN_DATETIME         timestamp(3)             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        timestamp(3)             not null,
   ORIGIN               varchar(20)          not null,
   FORECAST_PRIORITY    numeric(10,0)        not null,
   AUTHORISEDBY         varchar(20)          null,
   COMMENTS             varchar(200)         null,
   LASTCHANGED          timestamp(3)             null,
   MODEL                varchar(30)          null,
   PARTICIPANT_TIMESTAMP timestamp(3)             null,
   SUPPRESSED_AEMO      numeric(1,0)         null,
   SUPPRESSED_PARTICIPANT numeric(1,0)         null,
   TRANSACTION_ID       varchar(100)         null
);

alter table INTERMITTENT_P5_RUN
   add constraint INTERMITTENT_P5_RUN_PK primary key (RUN_DATETIME, DUID, OFFERDATETIME, ORIGIN, FORECAST_PRIORITY);





create table INTRAREGIONALLOC (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(5,0)         not null,
   REGIONID             varchar(10)          not null,
   PARTICIPANTID        varchar(10)          not null,
   ALLOCATION           numeric(12,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table INTRAREGIONALLOC
   add constraint INTRAREGIONALLOC_PK primary key (EFFECTIVEDATE, VERSIONNO, REGIONID, PARTICIPANTID);





create index INTRAREGIONALLOC_LCX on INTRAREGIONALLOC (
LASTCHANGED ASC
);





create table IRFMAMOUNT (
   IRFMID               varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(4,0)         not null,
   AMOUNT               numeric(15,5)        null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table IRFMAMOUNT
   add constraint IRFMAMOUNT_PK primary key (IRFMID, VERSIONNO, PERIODID);





create index IRFMAMOUNT_LCX on IRFMAMOUNT (
LASTCHANGED ASC
);





create table IRFMEVENTS (
   IRFMID               varchar(10)          not null,
   STARTDATE            timestamp(3)             null,
   STARTPERIOD          numeric(3,0)         null,
   ENDDATE              timestamp(3)             null,
   ENDPERIOD            numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table IRFMEVENTS
   add constraint IRFMEVENTS_PK primary key (IRFMID);





create index IRFMEVENTS_LCX on IRFMEVENTS (
LASTCHANGED ASC
);





create table LOSSFACTORMODEL (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   DEMANDCOEFFICIENT    numeric(27,17)       null,
   LASTCHANGED          timestamp(3)             null
);

alter table LOSSFACTORMODEL
   add constraint LFMOD_PK primary key (EFFECTIVEDATE, VERSIONNO, INTERCONNECTORID, REGIONID);





create index LOSSFACTORMODEL_LCX on LOSSFACTORMODEL (
LASTCHANGED ASC
);





create table LOSSMODEL (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   PERIODID             varchar(20)          null,
   LOSSSEGMENT          numeric(6,0)         not null,
   MWBREAKPOINT         numeric(6,0)         null,
   LOSSFACTOR           numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table LOSSMODEL
   add constraint LOSSMODEL_PK primary key (EFFECTIVEDATE, VERSIONNO, INTERCONNECTORID, LOSSSEGMENT);





create index LOSSMODEL_LCX on LOSSMODEL (
LASTCHANGED ASC
);





create table MARKETFEE (
   MARKETFEEID          varchar(10)          not null,
   MARKETFEEPERIOD      varchar(20)          null,
   MARKETFEETYPE        varchar(12)          null,
   DESCRIPTION          varchar(64)          null,
   LASTCHANGED          timestamp(3)             null,
   GL_TCODE             varchar(15)          null,
   GL_FINANCIALCODE     varchar(10)          null,
   FEE_CLASS            varchar(40)          null
);

alter table MARKETFEE
   add constraint MARKETFEE_PK primary key (MARKETFEEID);





create index MARKETFEE_LCX on MARKETFEE (
LASTCHANGED ASC
);





create table MARKETFEEDATA (
   MARKETFEEID          varchar(10)          not null,
   MARKETFEEVERSIONNO   numeric(3,0)         not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   MARKETFEEVALUE       numeric(22,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table MARKETFEEDATA
   add constraint MARKETFEEDATA_PK primary key (MARKETFEEID, MARKETFEEVERSIONNO, EFFECTIVEDATE);





create index MARKETFEEDATA_LCX on MARKETFEEDATA (
LASTCHANGED ASC
);





create table MARKETFEETRK (
   MARKETFEEVERSIONNO   numeric(3,0)         not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table MARKETFEETRK
   add constraint MARKETFEETRK_PK primary key (MARKETFEEVERSIONNO, EFFECTIVEDATE);





create index MARKETFEETRK_LCX on MARKETFEETRK (
LASTCHANGED ASC
);





create table MARKETNOTICEDATA (
   NOTICEID             numeric(10,0)        not null,
   EFFECTIVEDATE        timestamp(3)             null,
   TYPEID               varchar(25)          null,
   NOTICETYPE           varchar(25)          null,
   LASTCHANGED          timestamp(3)             null,
   REASON               varchar(2000)        null,
   EXTERNALREFERENCE    varchar(255)         null
);

alter table MARKETNOTICEDATA
   add constraint MARKETNOTICEDATA_PK primary key (NOTICEID);





create index MARKETNOTICEDATA_LCX on MARKETNOTICEDATA (
LASTCHANGED ASC
);





create table MARKETNOTICETYPE (
   TYPEID               varchar(25)          not null,
   DESCRIPTION          varchar(64)          null,
   RAISEDBY             varchar(10)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table MARKETNOTICETYPE
   add constraint MARKETNOTICETYPE_PK primary key (TYPEID);





create index MARKETNOTICETYPE_LCX on MARKETNOTICETYPE (
LASTCHANGED ASC
);





create table MARKETSUSPENSION (
   SUSPENSIONID         varchar(10)          not null,
   STARTDATE            timestamp(3)             null,
   STARTPERIOD          numeric(3,0)         null,
   ENDDATE              timestamp(3)             null,
   ENDPERIOD            numeric(3,0)         null,
   REASON               varchar(64)          null,
   STARTAUTHORISEDBY    varchar(15)          null,
   ENDAUTHORISEDBY      varchar(15)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table MARKETSUSPENSION
   add constraint MARKETSUSPENSION_PK primary key (SUSPENSIONID);





create index MARKETSUSPENSION_LCX on MARKETSUSPENSION (
LASTCHANGED ASC
);





create table MARKETSUSREGION (
   SUSPENSIONID         varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   LASTCHANGED          timestamp(3)             null
);

alter table MARKETSUSREGION
   add constraint MARKETSUSREGION_PK primary key (SUSPENSIONID, REGIONID);





create index MARKETSUSREGION_LCX on MARKETSUSREGION (
LASTCHANGED ASC
);





create table MARKET_FEE_CAT_EXCL (
   MARKETFEEID          varchar(20)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSION_DATETIME     timestamp(3)             not null,
   PARTICIPANT_CATEGORYID varchar(20)          not null
);

alter table MARKET_FEE_CAT_EXCL
   add constraint PK_MARKET_FEE_CAT_EXCL primary key (MARKETFEEID, EFFECTIVEDATE, VERSION_DATETIME, PARTICIPANT_CATEGORYID);





create table MARKET_FEE_CAT_EXCL_TRK (
   MARKETFEEID          varchar(20)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSION_DATETIME     timestamp(3)             not null,
   LASTCHANGED          timestamp(3)             null
);

alter table MARKET_FEE_CAT_EXCL_TRK
   add constraint PK_MARKET_FEE_CAT_EXCL_TRK primary key (MARKETFEEID, EFFECTIVEDATE, VERSION_DATETIME);





create table MARKET_FEE_EXCLUSION (
   PARTICIPANTID        varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   MARKETFEEID          varchar(10)          not null,
   LASTCHANGED          timestamp(3)             null
);

alter table MARKET_FEE_EXCLUSION
   add constraint MARKET_FEE_EXCLUSION_PK primary key (PARTICIPANTID, EFFECTIVEDATE, VERSIONNO, MARKETFEEID);





create index MARKET_FEE_EXCLUSION_LCX on MARKET_FEE_EXCLUSION (
LASTCHANGED ASC
);





create table MARKET_FEE_EXCLUSIONTRK (
   PARTICIPANTID        varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table MARKET_FEE_EXCLUSIONTRK
   add constraint MARKET_FEE_EXCLUSIONTRK_PK primary key (PARTICIPANTID, EFFECTIVEDATE, VERSIONNO);





create index MARKET_FEE_EXCLUSIONTRK_LCX on MARKET_FEE_EXCLUSIONTRK (
LASTCHANGED ASC
);





create table MARKET_PRICE_THRESHOLDS (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(4,0)         not null,
   VOLL                 numeric(15,5)        null,
   MARKETPRICEFLOOR     numeric(15,5)        null,
   ADMINISTERED_PRICE_THRESHOLD numeric(15,5)        null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table MARKET_PRICE_THRESHOLDS
   add constraint MARKET_PRICE_THRESHOLDS_PK primary key (EFFECTIVEDATE, VERSIONNO);





create index MARKET_PRICE_THRESHOLDS_LCX on MARKET_PRICE_THRESHOLDS (
LASTCHANGED ASC
);





create table MARKET_SUSPEND_REGIME_SUM (
   SUSPENSION_ID        varchar(20)          not null,
   REGIONID             varchar(20)          not null,
   START_INTERVAL       timestamp(3)             not null,
   END_INTERVAL         timestamp(3)             null,
   PRICING_REGIME       varchar(20)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table MARKET_SUSPEND_REGIME_SUM
   add constraint MARKET_SUSPEND_REGIME_SUM_PK primary key (SUSPENSION_ID, REGIONID, START_INTERVAL);





create table MARKET_SUSPEND_REGION_SUM (
   SUSPENSION_ID        varchar(20)          not null,
   REGIONID             varchar(20)          not null,
   INITIAL_INTERVAL     timestamp(3)             null,
   END_REGION_INTERVAL  timestamp(3)             null,
   END_SUSPENSION_INTERVAL timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table MARKET_SUSPEND_REGION_SUM
   add constraint MARKET_SUSPEND_REGION_SUM_PK primary key (SUSPENSION_ID, REGIONID);





create table MARKET_SUSPEND_SCHEDULE (
   EFFECTIVEDATE        timestamp(3)             not null,
   DAY_TYPE             varchar(20)          not null,
   REGIONID             varchar(20)          not null,
   PERIODID             numeric(3,0)         not null,
   ENERGY_RRP           numeric(15,5)        null,
   R6_RRP               numeric(15,5)        null,
   R60_RRP              numeric(15,5)        null,
   R5_RRP               numeric(15,5)        null,
   RREG_RRP             numeric(15,5)        null,
   L6_RRP               numeric(15,5)        null,
   L60_RRP              numeric(15,5)        null,
   L5_RRP               numeric(15,5)        null,
   LREG_RRP             numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table MARKET_SUSPEND_SCHEDULE
   add constraint MARKET_SUSPEND_SCHEDULE_PK primary key (EFFECTIVEDATE, DAY_TYPE, REGIONID, PERIODID);





create table MARKET_SUSPEND_SCHEDULE_TRK (
   EFFECTIVEDATE        timestamp(3)             not null,
   SOURCE_START_DATE    timestamp(3)             null,
   SOURCE_END_DATE      timestamp(3)             null,
   COMMENTS             varchar(1000)        null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table MARKET_SUSPEND_SCHEDULE_TRK
   add constraint MARKET_SUSPEND_SCHEDULE_TRK_PK primary key (EFFECTIVEDATE);





create table MAS_CP_CHANGE (
   NMI                  varchar(10)          not null,
   STATUS_FLAG          varchar(1)           null,
   CP_OLD_SECURITY_CODE varchar(4)           null,
   CP_NEW_SECURITY_CODE varchar(4)           null,
   OLD_LOCAL_NETWORK_PROVIDER varchar(10)          null,
   OLD_LOCAL_RETAILER   varchar(10)          null,
   OLD_FINANCIAL_PARTICIPANT varchar(10)          null,
   OLD_METERING_DATA_AGENT varchar(10)          null,
   OLD_RETAILER_OF_LAST_RESORT varchar(10)          null,
   OLD_RESPONSIBLE_PERSON varchar(10)          null,
   NEW_LOCAL_NETWORK_PROVIDER varchar(10)          null,
   NEW_LOCAL_RETAILER   varchar(10)          null,
   NEW_FINANCIAL_PARTICIPANT varchar(10)          null,
   NEW_METERING_DATA_AGENT varchar(10)          null,
   NEW_RETAILER_OF_LAST_RESORT varchar(10)          null,
   NEW_RESPONSIBLE_PERSON varchar(10)          null,
   OLD_LNSP_OK          varchar(1)           null,
   OLD_LR_OK            varchar(1)           null,
   OLD_FRMP_OK          varchar(1)           null,
   OLD_MDA_OK           varchar(1)           null,
   OLD_ROLR_OK          varchar(1)           null,
   OLD_RP_OK            varchar(1)           null,
   NEW_LNSP_OK          varchar(1)           null,
   NEW_LR_OK            varchar(1)           null,
   NEW_FRMP_OK          varchar(1)           null,
   NEW_MDA_OK           varchar(1)           null,
   NEW_ROLR_OK          varchar(1)           null,
   NEW_RP_OK            varchar(1)           null,
   PRUDENTIAL_OK        varchar(1)           null,
   INITIAL_CHANGE_DATE  timestamp(3)             null,
   CURRENT_CHANGE_DATE  timestamp(3)             null,
   CP_NAME              varchar(30)          null,
   CP_DETAIL_1          varchar(30)          null,
   CP_DETAIL_2          varchar(30)          null,
   CITY_SUBURB          varchar(30)          null,
   STATE                varchar(3)           null,
   POST_CODE            varchar(4)           null,
   TX_NODE              varchar(4)           null,
   AGGREGATE_DATA       varchar(1)           null,
   AVERAGE_DAILY_LOAD_KWH numeric(8,0)         null,
   DISTRIBUTION_LOSS    numeric(5,4)         null,
   OLD_LSNP_TEXT        varchar(30)          null,
   OLD_LR_TEXT          varchar(30)          null,
   OLD_FRMP_TEXT        varchar(30)          null,
   OLD_MDA_TEXT         varchar(30)          null,
   OLD_ROLR_TEXT        varchar(30)          null,
   OLD_RP_TEXT          varchar(30)          null,
   NEW_LSNP_TEXT        varchar(30)          null,
   NEW_LR_TEXT          varchar(30)          null,
   NEW_FRMP_TEXT        varchar(30)          null,
   NEW_MDA_TEXT         varchar(30)          null,
   NEW_ROLR_TEXT        varchar(30)          null,
   NEW_RP_TEXT          varchar(30)          null,
   LASTCHANGED          timestamp(3)             null,
   NMI_CLASS            varchar(9)           null,
   METERING_TYPE        varchar(9)           null,
   JURISDICTION         varchar(3)           null,
   CREATE_DATE          timestamp(3)             null,
   EXPIRY_DATE          timestamp(3)             null,
   METER_READ_DATE      timestamp(3)             null
);

alter table MAS_CP_CHANGE
   add constraint PK_MAS_CP_CHANGE primary key (NMI);





create index MAS_CP_CHANGE_LCX on MAS_CP_CHANGE (
LASTCHANGED ASC
);





create table MAS_CP_MASTER (
   NMI                  varchar(10)          not null,
   CP_SECURITY_CODE     varchar(4)           null,
   IN_USE               varchar(1)           null,
   VALID_FROM_DATE      timestamp(3)             not null,
   VALID_TO_DATE        timestamp(3)             not null,
   LOCAL_NETWORK_PROVIDER varchar(10)          null,
   LOCAL_RETAILER       varchar(10)          null,
   FINANCIAL_PARTICIPANT varchar(10)          null,
   METERING_DATA_AGENT  varchar(10)          null,
   RETAILER_OF_LAST_RESORT varchar(10)          null,
   RESPONSIBLE_PERSON   varchar(10)          null,
   CP_NAME              varchar(30)          null,
   CP_DETAIL_1          varchar(30)          null,
   CP_DETAIL_2          varchar(30)          null,
   CITY_SUBURB          varchar(30)          null,
   STATE                varchar(3)           null,
   POST_CODE            varchar(4)           null,
   TX_NODE              varchar(4)           null,
   AGGREGATE_DATA       varchar(1)           null,
   AVERAGE_DAILY_LOAD_KWH numeric(8,0)         null,
   DISTRIBUTION_LOSS    numeric(5,4)         null,
   LSNP_TEXT            varchar(30)          null,
   LR_TEXT              varchar(30)          null,
   FRMP_TEXT            varchar(30)          null,
   MDA_TEXT             varchar(30)          null,
   ROLR_TEXT            varchar(30)          null,
   RP_TEXT              varchar(30)          null,
   LASTCHANGED          timestamp(3)             null,
   NMI_CLASS            varchar(9)           null,
   METERING_TYPE        varchar(9)           null,
   JURISDICTION         varchar(3)           null
);

alter table MAS_CP_MASTER
   add constraint PK_MAS_CP_MASTER primary key (NMI, VALID_FROM_DATE);


alter table MAS_CP_MASTER
   add constraint UC_MAS_CP_MASTER unique (NMI, VALID_TO_DATE);





create index MAS_CP_MASTER_LCX on MAS_CP_MASTER (
LASTCHANGED ASC
);





create table MCC_CASESOLUTION (
   RUN_DATETIME         timestamp(3)             not null
);

alter table MCC_CASESOLUTION
   add constraint MCC_CASESOLUTION_PK primary key (RUN_DATETIME);





create table MCC_CONSTRAINTSOLUTION (
   RUN_DATETIME         timestamp(3)             not null,
   CONSTRAINTID         varchar(20)          not null,
   RHS                  numeric(15,5)        null,
   MARGINALVALUE        numeric(15,5)        null
);

alter table MCC_CONSTRAINTSOLUTION
   add constraint MCC_CONSTRAINTSOLUTION_PK primary key (RUN_DATETIME, CONSTRAINTID);





create table METERDATA (
   PARTICIPANTID        varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   SETTLEMENTDATE       timestamp(3)             not null,
   METERRUNNO           numeric(6,0)         not null,
   CONNECTIONPOINTID    varchar(10)          not null,
   IMPORTENERGYVALUE    numeric(9,6)         null,
   EXPORTENERGYVALUE    numeric(9,6)         null,
   IMPORTREACTIVEVALUE  numeric(9,6)         null,
   EXPORTREACTIVEVALUE  numeric(9,6)         null,
   HOSTDISTRIBUTOR      varchar(10)          not null,
   LASTCHANGED          timestamp(3)             null,
   MDA                  varchar(10)          not null
);

alter table METERDATA
   add constraint METERDATA_PK primary key (SETTLEMENTDATE, MDA, METERRUNNO, CONNECTIONPOINTID, PARTICIPANTID, HOSTDISTRIBUTOR, PERIODID);





create index METERDATA_LCX on METERDATA (
LASTCHANGED ASC
);





create table METERDATATRK (
   SETTLEMENTDATE       timestamp(3)             not null,
   METERRUNNO           numeric(6,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   FILENAME             varchar(40)          null,
   ACKFILENAME          varchar(40)          null,
   CONNECTIONPOINTID    varchar(10)          not null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   METERINGDATAAGENT    varchar(10)          not null,
   HOSTDISTRIBUTOR      varchar(10)          not null,
   LASTCHANGED          timestamp(3)             null
);

alter table METERDATATRK
   add constraint METERDATATRK_PK primary key (SETTLEMENTDATE, METERINGDATAAGENT, METERRUNNO, CONNECTIONPOINTID, PARTICIPANTID, HOSTDISTRIBUTOR);





create index METERDATATRK_LCX on METERDATATRK (
LASTCHANGED ASC
);





create table METERDATA_AGGREGATE_READS (
   CASE_ID              numeric(15,0)        not null,
   SETTLEMENTDATE       timestamp(3)             not null,
   CONNECTIONPOINTID    varchar(20)          not null,
   METER_TYPE           varchar(20)          not null,
   FRMP                 varchar(20)          not null,
   LR                   varchar(20)          not null,
   PERIODID             numeric(3,0)         not null,
   IMPORTVALUE          numeric(18,8)        not null,
   EXPORTVALUE          numeric(18,8)        not null,
   LASTCHANGED          timestamp(3)             null
);

alter table METERDATA_AGGREGATE_READS
   add constraint METERDATA_AGGREGATE_READS_PK primary key (CASE_ID, SETTLEMENTDATE, CONNECTIONPOINTID, METER_TYPE, FRMP, LR, PERIODID);





create table METERDATA_GEN_DUID (
   INTERVAL_DATETIME    timestamp(3)             not null,
   DUID                 varchar(10)          not null,
   MWH_READING          numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table METERDATA_GEN_DUID
   add constraint METERDATA_GEN_DUID_PK primary key (INTERVAL_DATETIME, DUID);





create index METERDATA_GEN_DUID_LCX on METERDATA_GEN_DUID (
LASTCHANGED ASC
);





create table METERDATA_INDIVIDUAL_READS (
   CASE_ID              numeric(15,0)        not null,
   SETTLEMENTDATE       timestamp(3)             not null,
   METER_ID             varchar(20)          not null,
   METER_ID_SUFFIX      varchar(20)          not null,
   FRMP                 varchar(20)          not null,
   LR                   varchar(20)          not null,
   PERIODID             numeric(3,0)         not null,
   CONNECTIONPOINTID    varchar(20)          not null,
   METER_TYPE           varchar(20)          not null,
   IMPORTVALUE          numeric(18,8)        not null,
   EXPORTVALUE          numeric(18,8)        not null,
   LASTCHANGED          timestamp(3)             null
);

alter table METERDATA_INDIVIDUAL_READS
   add constraint METERDATA_INDIVIDUAL_READS_PK primary key (CASE_ID, SETTLEMENTDATE, METER_ID, METER_ID_SUFFIX, PERIODID);





create table METERDATA_INTERCONNECTOR (
   CASE_ID              numeric(15,0)        not null,
   SETTLEMENTDATE       timestamp(3)             not null,
   INTERCONNECTORID     varchar(20)          not null,
   PERIODID             numeric(3,0)         not null,
   IMPORTVALUE          numeric(18,8)        null,
   EXPORTVALUE          numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table METERDATA_INTERCONNECTOR
   add constraint METERDATA_INTERCONNECTOR_PK primary key (CASE_ID, SETTLEMENTDATE, INTERCONNECTORID, PERIODID);





create table METERDATA_TRK (
   CASE_ID              numeric(15,0)        not null,
   AGGREGATE_READS_LOAD_DATETIME timestamp(3)             null,
   INDIVIDUAL_READS_LOAD_DATETIME timestamp(3)             null,
   STARTDATE            timestamp(3)             null,
   ENDDATE              timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table METERDATA_TRK
   add constraint METERDATA_TRK_PK primary key (CASE_ID);





create table MMS_DATA_MODEL_AUDIT (
   INSTALLATION_DATE    timestamp(3)             not null,
   MMSDM_VERSION        varchar(20)          not null,
   INSTALL_TYPE         varchar(10)          not null,
   SCRIPT_VERSION       varchar(20)          null,
   NEM_CHANGE_NOTICE    varchar(20)          null,
   PROJECT_TITLE        varchar(200)         null,
   USERNAME             varchar(40)          null,
   STATUS               varchar(10)          null
);

alter table MMS_DATA_MODEL_AUDIT
   add constraint MMS_DATA_MODEL_AUDIT_PK primary key (INSTALLATION_DATE, MMSDM_VERSION, INSTALL_TYPE);





create table MNSP_DAYOFFER (
   SETTLEMENTDATE       timestamp(3)             not null,
   OFFERDATE            timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   LINKID               varchar(10)          not null,
   ENTRYTYPE            varchar(20)          null,
   REBIDEXPLANATION     varchar(500)         null,
   PRICEBAND1           numeric(9,2)         null,
   PRICEBAND2           numeric(9,2)         null,
   PRICEBAND3           numeric(9,2)         null,
   PRICEBAND4           numeric(9,2)         null,
   PRICEBAND5           numeric(9,2)         null,
   PRICEBAND6           numeric(9,2)         null,
   PRICEBAND7           numeric(9,2)         null,
   PRICEBAND8           numeric(9,2)         null,
   PRICEBAND9           numeric(9,2)         null,
   PRICEBAND10          numeric(9,2)         null,
   LASTCHANGED          timestamp(3)             null,
   MR_FACTOR            numeric(16,6)        null
);

alter table MNSP_DAYOFFER
   add constraint MNSP_DAYOFFER_PK primary key (SETTLEMENTDATE, OFFERDATE, VERSIONNO, PARTICIPANTID, LINKID);





create index MNSP_DAYOFFER_LCX on MNSP_DAYOFFER (
LASTCHANGED ASC
);





create table MNSP_FILETRK (
   SETTLEMENTDATE       timestamp(3)             not null,
   OFFERDATE            timestamp(3)             not null,
   PARTICIPANTID        varchar(10)          not null,
   FILENAME             varchar(40)          not null,
   STATUS               varchar(10)          null,
   ACKFILENAME          varchar(40)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table MNSP_FILETRK
   add constraint MNSP_FILETRK_PK primary key (SETTLEMENTDATE, OFFERDATE, PARTICIPANTID, FILENAME);





create index MNSP_FILETRK_LCX on MNSP_FILETRK (
LASTCHANGED ASC
);





create table MNSP_INTERCONNECTOR (
   LINKID               varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          null,
   FROMREGION           varchar(10)          null,
   TOREGION             varchar(10)          null,
   MAXCAPACITY          numeric(5,0)         null,
   TLF                  numeric(12,7)        null,
   LHSFACTOR            numeric(12,7)        null,
   METERFLOWCONSTANT    numeric(12,7)        null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   LASTCHANGED          timestamp(3)             null,
   FROM_REGION_TLF      numeric(12,7)        null,
   TO_REGION_TLF        numeric(12,7)        null
);

alter table MNSP_INTERCONNECTOR
   add constraint MNSP_INTERCONNECTOR_PK primary key (LINKID, EFFECTIVEDATE, VERSIONNO);





create index MNSP_INTERCONNECTOR_LCX on MNSP_INTERCONNECTOR (
LASTCHANGED ASC
);





create table MNSP_OFFERTRK (
   SETTLEMENTDATE       timestamp(3)             not null,
   OFFERDATE            timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   FILENAME             varchar(40)          not null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table MNSP_OFFERTRK
   add constraint MNSP_OFFERTRK_PK primary key (SETTLEMENTDATE, OFFERDATE, VERSIONNO, PARTICIPANTID, FILENAME);





create index MNSP_OFFERTRK_LCX on MNSP_OFFERTRK (
LASTCHANGED ASC
);





create table MNSP_PARTICIPANT (
   INTERCONNECTORID     varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   LASTCHANGED          timestamp(3)             null
);

alter table MNSP_PARTICIPANT
   add constraint MNSP_PARTICIPANT_PK primary key (INTERCONNECTORID, EFFECTIVEDATE, VERSIONNO, PARTICIPANTID);





create index MNSP_PARTICIPANT_LCX on MNSP_PARTICIPANT (
LASTCHANGED ASC
);





create table MNSP_PEROFFER (
   SETTLEMENTDATE       timestamp(3)             not null,
   OFFERDATE            timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   LINKID               varchar(10)          not null,
   PERIODID             numeric(22,0)        not null,
   MAXAVAIL             numeric(6,0)         null,
   BANDAVAIL1           numeric(6,0)         null,
   BANDAVAIL2           numeric(6,0)         null,
   BANDAVAIL3           numeric(6,0)         null,
   BANDAVAIL4           numeric(6,0)         null,
   BANDAVAIL5           numeric(6,0)         null,
   BANDAVAIL6           numeric(6,0)         null,
   BANDAVAIL7           numeric(6,0)         null,
   BANDAVAIL8           numeric(6,0)         null,
   BANDAVAIL9           numeric(6,0)         null,
   BANDAVAIL10          numeric(6,0)         null,
   LASTCHANGED          timestamp(3)             null,
   FIXEDLOAD            numeric(12,6)        null,
   RAMPUPRATE           numeric(6,0)         null,
   PASAAVAILABILITY     numeric(12,0)        null,
   MR_CAPACITY          numeric(6,0)         null
);

alter table MNSP_PEROFFER
   add constraint MNSP_PEROFFER_PK primary key (SETTLEMENTDATE, OFFERDATE, VERSIONNO, PARTICIPANTID, LINKID, PERIODID);





create index MNSP_PEROFFER_LCX on MNSP_PEROFFER (
LASTCHANGED ASC
);





create table MR_DAYOFFER_STACK (
   MR_DATE              timestamp(3)             not null,
   REGIONID             varchar(10)          not null,
   VERSION_DATETIME     timestamp(3)             not null,
   STACK_POSITION       numeric(3,0)         not null,
   DUID                 varchar(10)          null,
   AUTHORISED           numeric(1,0)         null,
   OFFER_SETTLEMENTDATE timestamp(3)             null,
   OFFER_OFFERDATE      timestamp(3)             null,
   OFFER_VERSIONNO      numeric(3,0)         null,
   OFFER_TYPE           varchar(20)          null,
   LAOF                 numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table MR_DAYOFFER_STACK
   add constraint MR_DAYOFFER_STACK_PK primary key (MR_DATE, REGIONID, VERSION_DATETIME, STACK_POSITION);





create index MR_DAYOFFER_STACK_LCX on MR_DAYOFFER_STACK (
LASTCHANGED ASC
);





create table MR_EVENT (
   MR_DATE              timestamp(3)             not null,
   REGIONID             varchar(10)          not null,
   DESCRIPTION          varchar(200)         null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(20)          null,
   OFFER_CUT_OFF_TIME   timestamp(3)             null,
   SETTLEMENT_COMPLETE  numeric(1,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table MR_EVENT
   add constraint MR_EVENT_PK primary key (MR_DATE, REGIONID);





create index MR_EVENT_LCX on MR_EVENT (
LASTCHANGED ASC
);





create table MR_EVENT_SCHEDULE (
   MR_DATE              timestamp(3)             not null,
   REGIONID             varchar(10)          not null,
   VERSION_DATETIME     timestamp(3)             not null,
   DEMAND_EFFECTIVEDATE timestamp(3)             null,
   DEMAND_OFFERDATE     timestamp(3)             null,
   DEMAND_VERSIONNO     numeric(3,0)         null,
   AUTHORISEDBY         varchar(20)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table MR_EVENT_SCHEDULE
   add constraint MR_EVENT_SCHEDULE_PK primary key (MR_DATE, REGIONID, VERSION_DATETIME);





create index MR_EVENT_SCHEDULE_LCX on MR_EVENT_SCHEDULE (
LASTCHANGED ASC
);





create table MR_PEROFFER_STACK (
   MR_DATE              timestamp(3)             not null,
   REGIONID             varchar(10)          not null,
   VERSION_DATETIME     timestamp(3)             not null,
   STACK_POSITION       numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   DUID                 varchar(10)          null,
   ACCEPTED_CAPACITY    numeric(6,0)         null,
   DEDUCTED_CAPACITY    numeric(6,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table MR_PEROFFER_STACK
   add constraint MR_PEROFFER_STACK_PK primary key (MR_DATE, REGIONID, VERSION_DATETIME, STACK_POSITION, PERIODID);





create index MR_PEROFFER_STACK_LCX on MR_PEROFFER_STACK (
LASTCHANGED ASC
);





create table MTPASACONSTRAINTSOLUTION_D (
   DATETIME             timestamp(3)             not null,
   CONSTRAINT_ID        varchar(20)          not null,
   DEGREE_OF_VIOLATION  numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null,
   RUN_DATETIME         timestamp(3)             null
);

alter table MTPASACONSTRAINTSOLUTION_D
   add constraint MTPASACONSTRAINTSOLUTION_D_PK primary key (DATETIME, CONSTRAINT_ID);





create index MTPASACONSOLUTION_D_LCX on MTPASACONSTRAINTSOLUTION_D (
LASTCHANGED ASC
);





create table MTPASAINTERCONNECTORSOLUTION_D (
   DATETIME             timestamp(3)             not null,
   INTERCONNECTOR_ID    varchar(12)          not null,
   POSITIVE_INTERCONNECTOR_FLOW numeric(16,6)        null,
   POSITIVE_TRANSFER_LIMITS numeric(16,6)        null,
   POSITIVE_BINDING     varchar(10)          null,
   NEGATIVE_INTERCONNECTOR_FLOW numeric(16,6)        null,
   NEGATIVE_TRANSFER_LIMITS numeric(16,6)        null,
   NEGATIVE_BINDING     varchar(10)          null,
   LASTCHANGED          timestamp(3)             null,
   RUN_DATETIME         timestamp(3)             null
);

alter table MTPASAINTERCONNECTORSOLUTION_D
   add constraint MTPASAINTERCONSOLUTION_D_PK primary key (DATETIME, INTERCONNECTOR_ID);





create index MTPASAINTERCONSOLUTION_D_LCX on MTPASAINTERCONNECTORSOLUTION_D (
LASTCHANGED ASC
);





create table MTPASAREGIONSOLUTION_D (
   DATETIME             timestamp(3)             not null,
   REGION_ID            varchar(12)          not null,
   RUN_DATETIME         timestamp(3)             null,
   RESERVE_CONDITION    varchar(50)          null,
   RESERVE_SURPLUS      numeric(16,6)        null,
   CAPACITY_REQUIREMENT numeric(16,6)        null,
   MINIMUM_RESERVE_REQUIREMENT numeric(16,6)        null,
   REGION_DEMAND_10POE  numeric(16,6)        null,
   DEMAND_MINUS_SCHEDULED_LOAD numeric(16,6)        null,
   CONSTRAINED_CAPACITY numeric(16,6)        null,
   UNCONSTRAINED_CAPACITY numeric(16,6)        null,
   NET_INTERCHANGE      numeric(16,6)        null,
   ENERGY_REQUIREMENT_10POE numeric(16,6)        null,
   REPORTED_BLOCK_ID    numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table MTPASAREGIONSOLUTION_D
   add constraint MTPASAREGIONSOLUTION_D_PK primary key (DATETIME, REGION_ID);





create index MTPASAREGIONSOLUTION_D_LCX on MTPASAREGIONSOLUTION_D (
LASTCHANGED ASC
);





create table MTPASA_CASERESULT (
   RUN_DATETIME         timestamp(3)             not null,
   RUN_NO               numeric(4)           not null,
   PLEXOS_VERSION       varchar(20)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table MTPASA_CASERESULT
   add constraint MTPASA_CASERESULT_PK primary key (RUN_DATETIME, RUN_NO);





create table MTPASA_CASESOLUTION (
   RUN_DATETIME         timestamp(3)             not null,
   RUN_NO               numeric(3,0)         not null,
   PASAVERSION          varchar(10)          null,
   RESERVECONDITION     numeric(1,0)         null,
   LORCONDITION         numeric(1,0)         null,
   CAPACITYOBJFUNCTION  numeric(12,3)        null,
   CAPACITYOPTION       numeric(12,3)        null,
   MAXSURPLUSRESERVEOPTION numeric(12,3)        null,
   MAXSPARECAPACITYOPTION numeric(12,3)        null,
   INTERCONNECTORFLOWPENALTY numeric(12,3)        null,
   LASTCHANGED          timestamp(3)             null,
   RUNTYPE              varchar(50)          null,
   RELIABILITYLRCDEMANDOPTION numeric(12,3)        null,
   OUTAGELRCDEMANDOPTION numeric(12,3)        null,
   LORDEMANDOPTION      numeric(12,3)        null,
   RELIABILITYLRCCAPACITYOPTION varchar(10)          null,
   OUTAGELRCCAPACITYOPTION varchar(10)          null,
   LORCAPACITYOPTION    varchar(10)          null,
   LORUIGFOPTION        numeric(3,0)         null,
   RELIABILITYLRCUIGFOPTION numeric(3,0)         null,
   OUTAGELRCUIGFOPTION  numeric(3,0)         null
);

alter table MTPASA_CASESOLUTION
   add constraint MTPASA_CASESOLUTION_PK primary key (RUN_DATETIME, RUN_NO);





create index MTPASA_CASESOLUTION_LCX on MTPASA_CASESOLUTION (
LASTCHANGED ASC
);





create table MTPASA_CASE_SET (
   RUN_DATETIME         timestamp(3)             not null,
   RUN_NO               numeric(3,0)         not null,
   CASESETID            numeric(3,0)         null,
   RUNTYPEID            numeric(1,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table MTPASA_CASE_SET
   add constraint MTPASA_CASE_SET_PK primary key (RUN_DATETIME, RUN_NO);





create index MTPASA_CASE_SET_LCX on MTPASA_CASE_SET (
LASTCHANGED ASC
);





create table MTPASA_CONSTRAINTRESULT (
   RUN_DATETIME         timestamp(3)             not null,
   RUN_NO               numeric(4)           not null,
   RUNTYPE              varchar(20)          not null,
   DEMAND_POE_TYPE      varchar(20)          not null,
   DAY                  timestamp(3)             not null,
   CONSTRAINTID         varchar(20)          not null,
   EFFECTIVEDATE        timestamp(3)             null,
   VERSIONNO            numeric(3,0)         null,
   PERIODID             numeric(3,0)         null,
   PROBABILITYOFBINDING numeric(8,5)         null,
   PROBABILITYOFVIOLATION numeric(8,5)         null,
   CONSTRAINTVIOLATION90 numeric(12,2)        null,
   CONSTRAINTVIOLATION50 numeric(12,2)        null,
   CONSTRAINTVIOLATION10 numeric(12,2)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table MTPASA_CONSTRAINTRESULT
   add constraint MTPASA_CONSTRAINTRESULT_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, DEMAND_POE_TYPE, DAY, CONSTRAINTID);





create table MTPASA_CONSTRAINTSOLUTION (
   RUN_DATETIME         timestamp(3)             not null,
   RUN_NO               numeric(3,0)         not null,
   ENERGYBLOCK          timestamp(3)             not null,
   DAY                  timestamp(3)             not null,
   LDCBLOCK             numeric(3,0)         not null,
   CONSTRAINTID         varchar(20)          not null,
   CAPACITYRHS          numeric(12,2)        null,
   CAPACITYMARGINALVALUE numeric(12,2)        null,
   CAPACITYVIOLATIONDEGREE numeric(12,2)        null,
   LASTCHANGED          timestamp(3)             null,
   RUNTYPE              varchar(20)          not null default 'OUTAGE_LRC'
);

alter table MTPASA_CONSTRAINTSOLUTION
   add constraint MTPASA_CONSTRAINTSOLUTION_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, ENERGYBLOCK, DAY, LDCBLOCK, CONSTRAINTID);





create index MTPASA_CONSTRAINTSOLUTION_NDX2 on MTPASA_CONSTRAINTSOLUTION (
LASTCHANGED ASC
);





create table MTPASA_CONSTRAINTSUMMARY (
   RUN_DATETIME         timestamp(3)             not null,
   RUN_NO               numeric(4)           not null,
   RUNTYPE              varchar(20)          not null,
   DEMAND_POE_TYPE      varchar(20)          not null,
   DAY                  timestamp(3)             not null,
   CONSTRAINTID         varchar(20)          not null,
   EFFECTIVEDATE        timestamp(3)             null,
   VERSIONNO            numeric(3,0)         null,
   AGGREGATION_PERIOD   varchar(20)          not null,
   CONSTRAINTHOURSBINDING numeric(12,2)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table MTPASA_CONSTRAINTSUMMARY
   add constraint MTPASA_CONSTRAINTSUMMARY_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, DEMAND_POE_TYPE, DAY, CONSTRAINTID, AGGREGATION_PERIOD);





create table MTPASA_INTERCONNECTORRESULT (
   RUN_DATETIME         timestamp(3)             not null,
   RUN_NO               numeric(4)           not null,
   RUNTYPE              varchar(20)          not null,
   DEMAND_POE_TYPE      varchar(20)          not null,
   DAY                  timestamp(3)             not null,
   INTERCONNECTORID     varchar(20)          not null,
   PERIODID             numeric(3,0)         null,
   FLOW90               numeric(12,2)        null,
   FLOW50               numeric(12,2)        null,
   FLOW10               numeric(12,2)        null,
   PROBABILITYOFBINDINGEXPORT numeric(8,5)         null,
   PROBABILITYOFBINDINGIMPORT numeric(8,5)         null,
   CALCULATEDEXPORTLIMIT numeric(12,2)        null,
   CALCULATEDIMPORTLIMIT numeric(12,2)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table MTPASA_INTERCONNECTORRESULT
   add constraint MTPASA_INTERCONNECTORRESULT_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, DEMAND_POE_TYPE, DAY, INTERCONNECTORID);





create table MTPASA_INTERCONNECTORSOLUTION (
   RUN_DATETIME         timestamp(3)             not null,
   RUN_NO               numeric(3,0)         not null,
   ENERGYBLOCK          timestamp(3)             not null,
   DAY                  timestamp(3)             not null,
   LDCBLOCK             numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   CAPACITYMWFLOW       numeric(12,2)        null,
   CAPACITYMARGINALVALUE numeric(12,2)        null,
   CAPACITYVIOLATIONDEGREE numeric(12,2)        null,
   CALCULATEDEXPORTLIMIT numeric(12,2)        null,
   CALCULATEDIMPORTLIMIT numeric(12,2)        null,
   LASTCHANGED          timestamp(3)             null,
   RUNTYPE              varchar(20)          not null default 'OUTAGE_LRC',
   EXPORTLIMITCONSTRAINTID varchar(20)          null,
   IMPORTLIMITCONSTRAINTID varchar(20)          null
);

alter table MTPASA_INTERCONNECTORSOLUTION
   add constraint MTPASA_INTERCONNECTORSOLN_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, ENERGYBLOCK, DAY, LDCBLOCK, INTERCONNECTORID);





create index MTPASA_INTERCONNECTORSOLN_NDX2 on MTPASA_INTERCONNECTORSOLUTION (
LASTCHANGED ASC
);





create table MTPASA_INTERMITTENT_AVAIL (
   TRADINGDATE          timestamp(3)             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        timestamp(3)             not null,
   CLUSTERID            varchar(20)          not null,
   LASTCHANGED          timestamp(3)             null,
   ELEMENTS_UNAVAILABLE numeric(3,0)         null
);

alter table MTPASA_INTERMITTENT_AVAIL
   add constraint MTPASA_INTERMITTENT_AVAIL_PK primary key (TRADINGDATE, DUID, OFFERDATETIME, CLUSTERID);





create table MTPASA_INTERMITTENT_LIMIT (
   TRADINGDATE          timestamp(3)             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        timestamp(3)             not null,
   LASTCHANGED          timestamp(3)             null,
   UPPERMWLIMIT         numeric(6)           null,
   AUTHORISEDBYUSER     varchar(20)          null,
   AUTHORISEDBYPARTICIPANTID varchar(20)          null
);

alter table MTPASA_INTERMITTENT_LIMIT
   add constraint MTPASA_INTERMITTENT_LIMIT_PK primary key (TRADINGDATE, DUID, OFFERDATETIME);





create table MTPASA_LOLPRESULT (
   RUN_DATETIME         timestamp(3)             not null,
   RUN_NO               numeric(4)           not null,
   RUNTYPE              varchar(20)          not null,
   DAY                  timestamp(3)             not null,
   REGIONID             varchar(20)          not null,
   WORST_INTERVAL_PERIODID numeric(3,0)         null,
   WORST_INTERVAL_DEMAND numeric(12,2)        null,
   WORST_INTERVAL_INTGEN numeric(12,2)        null,
   WORST_INTERVAL_DSP   numeric(12,2)        null,
   LOSSOFLOADPROBABILITY numeric(8,5)         null,
   LOSSOFLOADMAGNITUDE  varchar(20)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table MTPASA_LOLPRESULT
   add constraint MTPASA_LOLPRESULT_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, DAY, REGIONID);





create table MTPASA_OFFERDATA (
   PARTICIPANTID        varchar(20)          not null,
   OFFERDATETIME        timestamp(3)             not null,
   UNITID               varchar(20)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   ENERGY               numeric(9)           null,
   CAPACITY1            numeric(9)           null,
   CAPACITY2            numeric(9)           null,
   CAPACITY3            numeric(9)           null,
   CAPACITY4            numeric(9)           null,
   CAPACITY5            numeric(9)           null,
   CAPACITY6            numeric(9)           null,
   CAPACITY7            numeric(9)           null,
   LASTCHANGED          timestamp(3)             null
);

alter table MTPASA_OFFERDATA
   add constraint MTPASA_OFFERDATA_PK primary key (PARTICIPANTID, OFFERDATETIME, UNITID, EFFECTIVEDATE);





create index MTPASA_OFFERDATA_LCX on MTPASA_OFFERDATA (
LASTCHANGED ASC
);





create table MTPASA_OFFERFILETRK (
   PARTICIPANTID        varchar(20)          not null,
   OFFERDATETIME        timestamp(3)             not null,
   FILENAME             varchar(200)         null
);

alter table MTPASA_OFFERFILETRK
   add constraint MTPASA_OFFERFILETRK_PK primary key (PARTICIPANTID, OFFERDATETIME);





create table MTPASA_REGIONAVAILABILITY (
   PUBLISH_DATETIME     timestamp(3)             not null,
   DAY                  timestamp(3)             not null,
   REGIONID             varchar(20)          not null,
   PASAAVAILABILITY_SCHEDULED numeric(12,0)        null,
   LATEST_OFFER_DATETIME timestamp(3)             null,
   ENERGYUNCONSTRAINEDCAPACITY numeric(12,0)        null,
   ENERGYCONSTRAINEDCAPACITY numeric(12,0)        null,
   NONSCHEDULEDGENERATION numeric(12,2)        null,
   DEMAND10             numeric(12,2)        null,
   DEMAND50             numeric(12,2)        null,
   ENERGYREQDEMAND10    numeric(12,2)        null,
   ENERGYREQDEMAND50    numeric(12,2)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table MTPASA_REGIONAVAILABILITY
   add constraint MTPASA_REGIONAVAILABILITY_PK primary key (PUBLISH_DATETIME, DAY, REGIONID);





create table MTPASA_REGIONAVAIL_TRK (
   PUBLISH_DATETIME     timestamp(3)             not null,
   STARTDATE            timestamp(3)             null,
   ENDDATE              timestamp(3)             null,
   LATEST_OFFER_DATETIME timestamp(3)             null
);

alter table MTPASA_REGIONAVAIL_TRK
   add constraint MTPASA_REGIONAVAIL_TRK_PK primary key (PUBLISH_DATETIME);





create table MTPASA_REGIONITERATION (
   RUN_DATETIME         timestamp(3)             not null,
   RUN_NO               numeric(4)           not null,
   RUNTYPE              varchar(20)          not null,
   DEMAND_POE_TYPE      varchar(20)          not null,
   AGGREGATION_PERIOD   varchar(20)          not null,
   PERIOD_ENDING        timestamp(3)             not null,
   REGIONID             varchar(20)          not null,
   USE_ITERATION_ID     numeric(5)           not null,
   USE_ITERATION_EVENT_NUMBER numeric(12,2)        null,
   USE_ITERATION_EVENT_AVERAGE numeric(12,2)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table MTPASA_REGIONITERATION
   add constraint MTPASA_REGIONITERATION_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, DEMAND_POE_TYPE, AGGREGATION_PERIOD, PERIOD_ENDING, REGIONID, USE_ITERATION_ID);





create table MTPASA_REGIONRESULT (
   RUN_DATETIME         timestamp(3)             not null,
   RUN_NO               numeric(4)           not null,
   RUNTYPE              varchar(20)          not null,
   DEMAND_POE_TYPE      varchar(20)          not null,
   DAY                  timestamp(3)             not null,
   REGIONID             varchar(20)          not null,
   PERIODID             numeric(3,0)         null,
   DEMAND               numeric(12,2)        null,
   AGGREGATEINSTALLEDCAPACITY numeric(12,2)        null,
   NUMBEROFITERATIONS   numeric(12,2)        null,
   USE_NUMBEROFITERATIONS numeric(12,2)        null,
   USE_MAX              numeric(12,2)        null,
   USE_UPPERQUARTILE    numeric(12,2)        null,
   USE_MEDIAN           numeric(12,2)        null,
   USE_LOWERQUARTILE    numeric(12,2)        null,
   USE_MIN              numeric(12,2)        null,
   USE_AVERAGE          numeric(12,2)        null,
   USE_EVENT_AVERAGE    numeric(12,2)        null,
   TOTALSCHEDULEDGEN90  numeric(12,2)        null,
   TOTALSCHEDULEDGEN50  numeric(12,2)        null,
   TOTALSCHEDULEDGEN10  numeric(12,2)        null,
   TOTALINTERMITTENTGEN90 numeric(12,2)        null,
   TOTALINTERMITTENTGEN50 numeric(12,2)        null,
   TOTALINTERMITTENTGEN10 numeric(12,2)        null,
   DEMANDSIDEPARTICIPATION90 numeric(12,2)        null,
   DEMANDSIDEPARTICIPATION50 numeric(12,2)        null,
   DEMANDSIDEPARTICIPATION10 numeric(12,2)        null,
   LASTCHANGED          timestamp(3)             null,
   TOTALSEMISCHEDULEGEN90 numeric(12,2)        null,
   TOTALSEMISCHEDULEGEN50 numeric(12,2)        null,
   TOTALSEMISCHEDULEGEN10 numeric(12,2)        null
);

alter table MTPASA_REGIONRESULT
   add constraint MTPASA_REGIONRESULT_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, DEMAND_POE_TYPE, DAY, REGIONID);





create table MTPASA_REGIONSOLUTION (
   RUN_DATETIME         timestamp(3)             not null,
   RUN_NO               numeric(3,0)         not null,
   ENERGYBLOCK          timestamp(3)             not null,
   DAY                  timestamp(3)             not null,
   LDCBLOCK             numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   DEMAND10             numeric(12,2)        null,
   RESERVEREQ           numeric(12,2)        null,
   CAPACITYREQ          numeric(12,2)        null,
   ENERGYREQDEMAND10    numeric(12,2)        null,
   UNCONSTRAINEDCAPACITY numeric(12,0)        null,
   CONSTRAINEDCAPACITY  numeric(12,0)        null,
   NETINTERCHANGEUNDERSCARCITY numeric(12,2)        null,
   SURPLUSCAPACITY      numeric(12,2)        null,
   SURPLUSRESERVE       numeric(12,2)        null,
   RESERVECONDITION     numeric(1,0)         null,
   MAXSURPLUSRESERVE    numeric(12,2)        null,
   MAXSPARECAPACITY     numeric(12,2)        null,
   LORCONDITION         numeric(1,0)         null,
   AGGREGATECAPACITYAVAILABLE numeric(12,2)        null,
   AGGREGATESCHEDULEDLOAD numeric(12,2)        null,
   LASTCHANGED          timestamp(3)             null,
   AGGREGATEPASAAVAILABILITY numeric(12,0)        null,
   RUNTYPE              varchar(20)          not null default 'OUTAGE_LRC',
   CALCULATEDLOR1LEVEL  numeric(16,6)        null,
   CALCULATEDLOR2LEVEL  numeric(16,6)        null,
   MSRNETINTERCHANGEUNDERSCARCITY numeric(12,2)        null,
   LORNETINTERCHANGEUNDERSCARCITY numeric(12,2)        null,
   TOTALINTERMITTENTGENERATION numeric(15,5)        null,
   DEMAND50             numeric(12,2)        null,
   DEMAND_AND_NONSCHEDGEN numeric(15,5)        null,
   UIGF                 numeric(12,2)        null,
   SEMISCHEDULEDCAPACITY numeric(12,2)        null,
   LOR_SEMISCHEDULEDCAPACITY numeric(12,2)        null,
   DEFICITRESERVE       numeric(16,6)        null,
   MAXUSEFULRESPONSE    numeric(12,2)        null,
   MURNETINTERCHANGEUNDERSCARCITY numeric(12,2)        null,
   LORTOTALINTERMITTENTGENERATION numeric(15,5)        null,
   ENERGYREQDEMAND50    numeric(12,2)        null
);

alter table MTPASA_REGIONSOLUTION
   add constraint MTPASA_REGIONSOLUTION_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, ENERGYBLOCK, DAY, LDCBLOCK, REGIONID);





create index MTPASA_REGIONSOLUTION_NDX2 on MTPASA_REGIONSOLUTION (
LASTCHANGED ASC
);





create table MTPASA_REGIONSUMMARY (
   RUN_DATETIME         timestamp(3)             not null,
   RUN_NO               numeric(4)           not null,
   RUNTYPE              varchar(20)          not null,
   DEMAND_POE_TYPE      varchar(20)          not null,
   AGGREGATION_PERIOD   varchar(20)          not null,
   PERIOD_ENDING        timestamp(3)             not null,
   REGIONID             varchar(20)          not null,
   NATIVEDEMAND         numeric(12,2)        null,
   USE_PERCENTILE10     numeric(12,2)        null,
   USE_PERCENTILE20     numeric(12,2)        null,
   USE_PERCENTILE30     numeric(12,2)        null,
   USE_PERCENTILE40     numeric(12,2)        null,
   USE_PERCENTILE50     numeric(12,2)        null,
   USE_PERCENTILE60     numeric(12,2)        null,
   USE_PERCENTILE70     numeric(12,2)        null,
   USE_PERCENTILE80     numeric(12,2)        null,
   USE_PERCENTILE90     numeric(12,2)        null,
   USE_PERCENTILE100    numeric(12,2)        null,
   USE_AVERAGE          numeric(12,2)        null,
   NUMBEROFITERATIONS   numeric(12,2)        null,
   USE_NUMBEROFITERATIONS numeric(12,2)        null,
   USE_EVENT_MAX        numeric(12,2)        null,
   USE_EVENT_UPPERQUARTILE numeric(12,2)        null,
   USE_EVENT_MEDIAN     numeric(12,2)        null,
   USE_EVENT_LOWERQUARTILE numeric(12,2)        null,
   USE_EVENT_MIN        numeric(12,2)        null,
   WEIGHT               numeric(16,6)        null,
   USE_WEIGHTED_AVG     numeric(16,6)        null,
   LRC                  numeric(12,2)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table MTPASA_REGIONSUMMARY
   add constraint MTPASA_REGIONSUMMARY_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, DEMAND_POE_TYPE, AGGREGATION_PERIOD, PERIOD_ENDING, REGIONID);





create table MTPASA_RESERVELIMIT (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSION_DATETIME     timestamp(3)             not null,
   RESERVELIMITID       varchar(20)          not null,
   DESCRIPTION          varchar(200)         null,
   RHS                  numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table MTPASA_RESERVELIMIT
   add constraint PK_MTPASA_RESERVELIMIT primary key (EFFECTIVEDATE, VERSION_DATETIME, RESERVELIMITID);





create table MTPASA_RESERVELIMITSOLUTION (
   RUN_DATETIME         timestamp(3)             not null,
   RUN_NO               numeric(3,0)         not null,
   RUNTYPE              varchar(20)          not null,
   ENERGYBLOCK          timestamp(3)             not null,
   DAY                  timestamp(3)             not null,
   LDCBLOCK             numeric(3,0)         not null,
   RESERVELIMITID       varchar(20)          not null,
   MARGINALVALUE        numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table MTPASA_RESERVELIMITSOLUTION
   add constraint PK_MTPASA_RESERVELIMITSOLUTION primary key (RUN_DATETIME, RUN_NO, RUNTYPE, ENERGYBLOCK, DAY, LDCBLOCK, RESERVELIMITID);





create table MTPASA_RESERVELIMIT_REGION (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSION_DATETIME     timestamp(3)             not null,
   RESERVELIMITID       varchar(20)          not null,
   REGIONID             varchar(20)          not null,
   COEF                 numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table MTPASA_RESERVELIMIT_REGION
   add constraint PK_MTPASA_RESERVELIMIT_REGION primary key (EFFECTIVEDATE, VERSION_DATETIME, RESERVELIMITID, REGIONID);





create table MTPASA_RESERVELIMIT_SET (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSION_DATETIME     timestamp(3)             not null,
   RESERVELIMIT_SET_ID  varchar(20)          null,
   DESCRIPTION          varchar(200)         null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(20)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table MTPASA_RESERVELIMIT_SET
   add constraint PK_MTPASA_RESERVELIMIT_SET primary key (EFFECTIVEDATE, VERSION_DATETIME);





create table NEGATIVE_RESIDUE (
   SETTLEMENTDATE       timestamp(3)             not null,
   NRM_DATETIME         timestamp(3)             not null,
   DIRECTIONAL_INTERCONNECTORID varchar(30)          not null,
   NRM_ACTIVATED_FLAG   numeric(1,0)         null,
   CUMUL_NEGRESIDUE_AMOUNT numeric(15,5)        null,
   CUMUL_NEGRESIDUE_PREV_TI numeric(15,5)        null,
   NEGRESIDUE_CURRENT_TI numeric(15,5)        null,
   NEGRESIDUE_PD_NEXT_TI numeric(15,5)        null,
   PRICE_REVISION       varchar(30)          null,
   PREDISPATCHSEQNO     varchar(20)          null,
   EVENT_ACTIVATED_DI   timestamp(3)             null,
   EVENT_DEACTIVATED_DI timestamp(3)             null,
   DI_NOTBINDING_COUNT  numeric(2,0)         null,
   DI_VIOLATED_COUNT    numeric(2,0)         null,
   NRMCONSTRAINT_BLOCKED_FLAG numeric(1,0)         null
);

alter table NEGATIVE_RESIDUE
   add constraint NEGATIVE_RESIDUE_PK primary key (SETTLEMENTDATE, NRM_DATETIME, DIRECTIONAL_INTERCONNECTORID);





create table NETWORK_EQUIPMENTDETAIL (
   SUBSTATIONID         varchar(30)          not null,
   EQUIPMENTTYPE        varchar(10)          not null,
   EQUIPMENTID          varchar(30)          not null,
   VALIDFROM            timestamp(3)             not null,
   VALIDTO              timestamp(3)             null,
   VOLTAGE              varchar(20)          null,
   DESCRIPTION          varchar(100)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table NETWORK_EQUIPMENTDETAIL
   add constraint PK_NETWORK_EQUIPMENTDETAIL primary key (SUBSTATIONID, EQUIPMENTTYPE, EQUIPMENTID, VALIDFROM);





create index NETWORK_EQUIPMENTDETAIL_LCX on NETWORK_EQUIPMENTDETAIL (
LASTCHANGED ASC
);





create table NETWORK_OUTAGECONSTRAINTSET (
   OUTAGEID             numeric(15,0)        not null,
   GENCONSETID          varchar(50)          not null,
   STARTINTERVAL        timestamp(3)             null,
   ENDINTERVAL          timestamp(3)             null
);

alter table NETWORK_OUTAGECONSTRAINTSET
   add constraint PK_NETWORK_OUTAGECONSTRAINTSET primary key (OUTAGEID, GENCONSETID);





create table NETWORK_OUTAGEDETAIL (
   OUTAGEID             numeric(15,0)        not null,
   SUBSTATIONID         varchar(30)          not null,
   EQUIPMENTTYPE        varchar(10)          not null,
   EQUIPMENTID          varchar(30)          not null,
   STARTTIME            timestamp(3)             not null,
   ENDTIME              timestamp(3)             null,
   SUBMITTEDDATE        timestamp(3)             null,
   OUTAGESTATUSCODE     varchar(10)          null,
   RESUBMITREASON       varchar(50)          null,
   RESUBMITOUTAGEID     numeric(15,0)        null,
   RECALLTIMEDAY        numeric(10,0)        null,
   RECALLTIMENIGHT      numeric(10,0)        null,
   LASTCHANGED          timestamp(3)             null,
   REASON               varchar(100)         null,
   ISSECONDARY          numeric(1,0)         null,
   ACTUAL_STARTTIME     timestamp(3)             null,
   ACTUAL_ENDTIME       timestamp(3)             null,
   COMPANYREFCODE       varchar(20)          null
);

alter table NETWORK_OUTAGEDETAIL
   add constraint PK_NETWORK_OUTAGEDETAIL primary key (OUTAGEID, SUBSTATIONID, EQUIPMENTTYPE, EQUIPMENTID, STARTTIME);





create index NETWORK_OUTAGEDETAIL_LCX on NETWORK_OUTAGEDETAIL (
LASTCHANGED ASC
);





create table NETWORK_OUTAGESTATUSCODE (
   OUTAGESTATUSCODE     varchar(10)          not null,
   DESCRIPTION          varchar(100)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table NETWORK_OUTAGESTATUSCODE
   add constraint PK_NETWORK_OUTAGESTATUSCODE primary key (OUTAGESTATUSCODE);





create table NETWORK_RATING (
   SPD_ID               varchar(21)          not null,
   VALIDFROM            timestamp(3)             not null,
   VALIDTO              timestamp(3)             null,
   REGIONID             varchar(10)          null,
   SUBSTATIONID         varchar(30)          null,
   EQUIPMENTTYPE        varchar(10)          null,
   EQUIPMENTID          varchar(30)          null,
   RATINGLEVEL          varchar(10)          null,
   ISDYNAMIC            numeric(1,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table NETWORK_RATING
   add constraint PK_NETWORK_RATING primary key (SPD_ID, VALIDFROM);





create index NETWORK_RATING_LCX on NETWORK_RATING (
LASTCHANGED ASC
);





create table NETWORK_REALTIMERATING (
   SETTLEMENTDATE       timestamp(3)             not null,
   SPD_ID               varchar(21)          not null,
   RATINGVALUE          numeric(16,6)        not null
);

alter table NETWORK_REALTIMERATING
   add constraint PK_NETWORK_REALTIMERATING primary key (SETTLEMENTDATE, SPD_ID);





create table NETWORK_STATICRATING (
   SUBSTATIONID         varchar(30)          not null,
   EQUIPMENTTYPE        varchar(10)          not null,
   EQUIPMENTID          varchar(30)          not null,
   RATINGLEVEL          varchar(10)          not null,
   APPLICATIONID        varchar(20)          not null,
   VALIDFROM            timestamp(3)             not null,
   VALIDTO              timestamp(3)             null,
   RATINGVALUE          numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table NETWORK_STATICRATING
   add constraint PK_NETWORK_STATICRATING primary key (SUBSTATIONID, EQUIPMENTTYPE, EQUIPMENTID, RATINGLEVEL, APPLICATIONID, VALIDFROM);





create index NETWORK_STATICRATING_LCX on NETWORK_STATICRATING (
LASTCHANGED ASC
);





create table NETWORK_SUBSTATIONDETAIL (
   SUBSTATIONID         varchar(30)          not null,
   VALIDFROM            timestamp(3)             not null,
   VALIDTO              timestamp(3)             null,
   DESCRIPTION          varchar(100)         null,
   REGIONID             varchar(10)          null,
   OWNERID              varchar(30)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table NETWORK_SUBSTATIONDETAIL
   add constraint PK_NETWORK_SUBSTATIONDETAIL primary key (SUBSTATIONID, VALIDFROM);





create index NETWORK_SUBSTATIONDETAIL_LCX on NETWORK_SUBSTATIONDETAIL (
LASTCHANGED ASC
);





create table OARTRACK (
   SETTLEMENTDATE       timestamp(3)             not null,
   OFFERDATE            timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   FILENAME             varchar(40)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(10)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table OARTRACK
   add constraint OARTRACK_PK primary key (SETTLEMENTDATE, OFFERDATE, VERSIONNO, PARTICIPANTID);





create index OARTRACK_NDX2 on OARTRACK (
PARTICIPANTID ASC
);





create index OARTRACK_LCX on OARTRACK (
LASTCHANGED ASC
);





create table OFFERAGCDATA (
   CONTRACTID           varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   AVAILABILITY         numeric(4,0)         null,
   UPPERLIMIT           numeric(4,0)         null,
   LOWERLIMIT           numeric(4,0)         null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   FILENAME             varchar(40)          null,
   LASTCHANGED          timestamp(3)             null,
   PERIODID             numeric(3,0)         not null,
   AGCUP                numeric(3,0)         null,
   AGCDOWN              numeric(3,0)         null
);

alter table OFFERAGCDATA
   add constraint OFFERAGCDATA_PK primary key (CONTRACTID, EFFECTIVEDATE, VERSIONNO, PERIODID);





create index OFFERAGCDATA_NDX2 on OFFERAGCDATA (
CONTRACTID ASC
);





create index OFFERAGCDATA_LCX on OFFERAGCDATA (
LASTCHANGED ASC
);





create table OFFERASTRK (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   FILENAME             varchar(40)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table OFFERASTRK
   add constraint OFFERASTRK_PK primary key (EFFECTIVEDATE, VERSIONNO, PARTICIPANTID);





create index OFFERASTRK_LCX on OFFERASTRK (
LASTCHANGED ASC
);





create table OFFERFILETRK (
   OFFERDATE            timestamp(3)             not null,
   PARTICIPANTID        varchar(10)          not null,
   STATUS               varchar(10)          null,
   ACKFILENAME          varchar(40)          null,
   ENDDATE              timestamp(3)             null,
   FILENAME             varchar(40)          not null,
   LASTCHANGED          timestamp(3)             null
);

alter table OFFERFILETRK
   add constraint OFFERFILETRK_PK primary key (OFFERDATE, FILENAME, PARTICIPANTID);





create index OFFERFILETRK_NDX2 on OFFERFILETRK (
PARTICIPANTID ASC
);





create index OFFERFILETRK_LCX on OFFERFILETRK (
LASTCHANGED ASC
);





create table OFFERGOVDATA (
   CONTRACTID           varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   SEC6AVAILUP          numeric(6,0)         null,
   SEC6AVAILDOWN        numeric(6,0)         null,
   SEC60AVAILUP         numeric(6,0)         null,
   SEC60AVAILDOWN       numeric(6,0)         null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   FILENAME             varchar(40)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table OFFERGOVDATA
   add constraint OFFERGOVDATA_PK primary key (CONTRACTID, EFFECTIVEDATE, VERSIONNO, PERIODID);





create index OFFERGOVDATA_NDX2 on OFFERGOVDATA (
CONTRACTID ASC
);





create index OFFERGOVDATA_LCX on OFFERGOVDATA (
LASTCHANGED ASC
);





create table OFFERLSHEDDATA (
   CONTRACTID           varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   AVAILABLELOAD        numeric(4,0)         null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   FILENAME             varchar(40)          null,
   LASTCHANGED          timestamp(3)             null,
   PERIODID             numeric(3,0)         not null
);

alter table OFFERLSHEDDATA
   add constraint OFFERLSHEDDATA_PK primary key (CONTRACTID, EFFECTIVEDATE, VERSIONNO, PERIODID);





create index OFFERLSHEDDATA_LCX on OFFERLSHEDDATA (
LASTCHANGED ASC
);





create table OFFERRESTARTDATA (
   CONTRACTID           varchar(10)          not null,
   OFFERDATE            timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   AVAILABILITY         varchar(3)           null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   FILENAME             varchar(40)          null,
   LASTCHANGED          timestamp(3)             null,
   PERIODID             numeric(3,0)         not null
);

alter table OFFERRESTARTDATA
   add constraint OFFERRESTARTDATA_PK primary key (CONTRACTID, OFFERDATE, VERSIONNO, PERIODID);





create index OFFERRESTARTDATA_LCX on OFFERRESTARTDATA (
LASTCHANGED ASC
);





create table OFFERRPOWERDATA (
   CONTRACTID           varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   AVAILABILITY         numeric(3,0)         null,
   MTA                  numeric(6,0)         null,
   MTG                  numeric(6,0)         null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   FILENAME             varchar(40)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table OFFERRPOWERDATA
   add constraint OFFERRPOWERDATA_PK primary key (CONTRACTID, EFFECTIVEDATE, VERSIONNO, PERIODID);





create index OFFERRPOWERDATA_NDX2 on OFFERRPOWERDATA (
CONTRACTID ASC
);





create index OFFERRPOWERDATA_LCX on OFFERRPOWERDATA (
LASTCHANGED ASC
);





create table OFFERULOADINGDATA (
   CONTRACTID           varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   AVAILABLELOAD        numeric(4,0)         null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   FILENAME             varchar(40)          null,
   LASTCHANGED          timestamp(3)             null,
   PERIODID             numeric(3,0)         not null
);

alter table OFFERULOADINGDATA
   add constraint OFFERULOADINGDATA_PK primary key (CONTRACTID, EFFECTIVEDATE, VERSIONNO, PERIODID);





create index OFFERULOADINGDATA_NDX2 on OFFERULOADINGDATA (
CONTRACTID ASC
);





create index OFFERULOADINGDATA_LCX on OFFERULOADINGDATA (
LASTCHANGED ASC
);





create table OFFERUNLOADINGDATA (
   CONTRACTID           varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   AVAILABLELOAD        numeric(4,0)         null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   FILENAME             varchar(40)          null,
   LASTCHANGED          timestamp(3)             null,
   PERIODID             numeric(3,0)         not null
);

alter table OFFERUNLOADINGDATA
   add constraint OFFERUNLOADINGDATA_PK primary key (CONTRACTID, EFFECTIVEDATE, VERSIONNO, PERIODID);





create index OFFERUNLOADINGDATA_NDX2 on OFFERUNLOADINGDATA (
CONTRACTID ASC
);





create index OFFERUNLOADINGDATA_LCX on OFFERUNLOADINGDATA (
LASTCHANGED ASC
);





create table OVERRIDERRP (
   REGIONID             varchar(10)          not null,
   STARTDATE            timestamp(3)             not null,
   STARTPERIOD          numeric(3,0)         not null,
   ENDDATE              timestamp(3)             null,
   ENDPERIOD            numeric(3,0)         null,
   RRP                  numeric(15,0)        null,
   DESCRIPTION          varchar(128)         null,
   AUTHORISESTART       varchar(15)          null,
   AUTHORISEEND         varchar(15)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table OVERRIDERRP
   add constraint OVERRIDERRP_PK primary key (STARTDATE, STARTPERIOD, REGIONID);





create index OVERRIDERRP_LCX on OVERRIDERRP (
LASTCHANGED ASC
);





create table P5MIN_BLOCKEDCONSTRAINT (
   RUN_DATETIME         timestamp(3)             not null,
   CONSTRAINTID         varchar(20)          not null
);

alter table P5MIN_BLOCKEDCONSTRAINT
   add constraint P5MIN_BLOCKEDCONSTRAINT_PK primary key (RUN_DATETIME, CONSTRAINTID);





create table P5MIN_CASESOLUTION (
   RUN_DATETIME         timestamp(3)             not null,
   STARTINTERVAL_DATETIME varchar(20)          null,
   TOTALOBJECTIVE       numeric(27,10)       null,
   NONPHYSICALLOSSES    numeric(1,0)         null,
   TOTALAREAGENVIOLATION numeric(15,5)        null,
   TOTALINTERCONNECTORVIOLATION numeric(15,5)        null,
   TOTALGENERICVIOLATION numeric(15,5)        null,
   TOTALRAMPRATEVIOLATION numeric(15,5)        null,
   TOTALUNITMWCAPACITYVIOLATION numeric(15,5)        null,
   TOTAL5MINVIOLATION   numeric(15,5)        null,
   TOTALREGVIOLATION    numeric(15,5)        null,
   TOTAL6SECVIOLATION   numeric(15,5)        null,
   TOTAL60SECVIOLATION  numeric(15,5)        null,
   TOTALENERGYCONSTRVIOLATION numeric(15,5)        null,
   TOTALENERGYOFFERVIOLATION numeric(15,5)        null,
   TOTALASPROFILEVIOLATION numeric(15,5)        null,
   TOTALFASTSTARTVIOLATION numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   INTERVENTION         numeric(2,0)         null
);

alter table P5MIN_CASESOLUTION
   add constraint P5MIN_CASESOLUTION_PK primary key (RUN_DATETIME);





create index P5MIN_CASESOLUTION_LCX on P5MIN_CASESOLUTION (
LASTCHANGED ASC
);





create table P5MIN_CONSTRAINTSOLUTION (
   RUN_DATETIME         timestamp(3)             not null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   CONSTRAINTID         varchar(20)          not null,
   RHS                  numeric(15,5)        null,
   MARGINALVALUE        numeric(15,5)        null,
   VIOLATIONDEGREE      numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   DUID                 varchar(20)          null,
   GENCONID_EFFECTIVEDATE timestamp(3)             null,
   GENCONID_VERSIONNO   numeric(22,0)        null,
   LHS                  numeric(15,5)        null,
   INTERVENTION         numeric(2,0)         null
);

alter table P5MIN_CONSTRAINTSOLUTION
   add constraint P5MIN_CONSTRAINTSOLUTION_PK primary key (RUN_DATETIME, CONSTRAINTID, INTERVAL_DATETIME);





create index P5MIN_CONSTRAINTSOLUTION_LCX on P5MIN_CONSTRAINTSOLUTION (
LASTCHANGED ASC
);





create table P5MIN_INTERCONNECTORSOLN (
   RUN_DATETIME         timestamp(3)             not null,
   INTERCONNECTORID     varchar(10)          not null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   METEREDMWFLOW        numeric(15,5)        null,
   MWFLOW               numeric(15,5)        null,
   MWLOSSES             numeric(15,5)        null,
   MARGINALVALUE        numeric(15,5)        null,
   VIOLATIONDEGREE      numeric(15,5)        null,
   MNSP                 numeric(1,0)         null,
   EXPORTLIMIT          numeric(15,5)        null,
   IMPORTLIMIT          numeric(15,5)        null,
   MARGINALLOSS         numeric(15,5)        null,
   EXPORTGENCONID       varchar(20)          null,
   IMPORTGENCONID       varchar(20)          null,
   FCASEXPORTLIMIT      numeric(15,5)        null,
   FCASIMPORTLIMIT      numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   LOCAL_PRICE_ADJUSTMENT_EXPORT numeric(10,2)        null,
   LOCALLY_CONSTRAINED_EXPORT numeric(1,0)         null,
   LOCAL_PRICE_ADJUSTMENT_IMPORT numeric(10,2)        null,
   LOCALLY_CONSTRAINED_IMPORT numeric(1,0)         null,
   INTERVENTION         numeric(2,0)         null
);

alter table P5MIN_INTERCONNECTORSOLN
   add constraint P5MIN_INTERCONNECTORSOLN_PK primary key (RUN_DATETIME, INTERCONNECTORID, INTERVAL_DATETIME);





create index P5MIN_INTERCONNECTORSOLN_LCX on P5MIN_INTERCONNECTORSOLN (
LASTCHANGED ASC
);





create table P5MIN_LOCAL_PRICE (
   RUN_DATETIME         timestamp(3)             not null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   DUID                 varchar(20)          not null,
   LOCAL_PRICE_ADJUSTMENT numeric(10,2)        null,
   LOCALLY_CONSTRAINED  numeric(1,0)         null
);

alter table P5MIN_LOCAL_PRICE
   add constraint P5MIN_LOCAL_PRICE_PK primary key (RUN_DATETIME, INTERVAL_DATETIME, DUID);





create table P5MIN_REGIONSOLUTION (
   RUN_DATETIME         timestamp(3)             not null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   REGIONID             varchar(10)          not null,
   RRP                  numeric(15,5)        null,
   ROP                  numeric(15,5)        null,
   EXCESSGENERATION     numeric(15,5)        null,
   RAISE6SECRRP         numeric(15,5)        null,
   RAISE6SECROP         numeric(15,5)        null,
   RAISE60SECRRP        numeric(15,5)        null,
   RAISE60SECROP        numeric(15,5)        null,
   RAISE5MINRRP         numeric(15,5)        null,
   RAISE5MINROP         numeric(15,5)        null,
   RAISEREGRRP          numeric(15,5)        null,
   RAISEREGROP          numeric(15,5)        null,
   LOWER6SECRRP         numeric(15,5)        null,
   LOWER6SECROP         numeric(15,5)        null,
   LOWER60SECRRP        numeric(15,5)        null,
   LOWER60SECROP        numeric(15,5)        null,
   LOWER5MINRRP         numeric(15,5)        null,
   LOWER5MINROP         numeric(15,5)        null,
   LOWERREGRRP          numeric(15,5)        null,
   LOWERREGROP          numeric(15,5)        null,
   TOTALDEMAND          numeric(15,5)        null,
   AVAILABLEGENERATION  numeric(15,5)        null,
   AVAILABLELOAD        numeric(15,5)        null,
   DEMANDFORECAST       numeric(15,5)        null,
   DISPATCHABLEGENERATION numeric(15,5)        null,
   DISPATCHABLELOAD     numeric(15,5)        null,
   NETINTERCHANGE       numeric(15,5)        null,
   LOWER5MINDISPATCH    numeric(15,5)        null,
   LOWER5MINIMPORT      numeric(15,5)        null,
   LOWER5MINLOCALDISPATCH numeric(15,5)        null,
   LOWER5MINLOCALREQ    numeric(15,5)        null,
   LOWER5MINREQ         numeric(15,5)        null,
   LOWER60SECDISPATCH   numeric(15,5)        null,
   LOWER60SECIMPORT     numeric(15,5)        null,
   LOWER60SECLOCALDISPATCH numeric(15,5)        null,
   LOWER60SECLOCALREQ   numeric(15,5)        null,
   LOWER60SECREQ        numeric(15,5)        null,
   LOWER6SECDISPATCH    numeric(15,5)        null,
   LOWER6SECIMPORT      numeric(15,5)        null,
   LOWER6SECLOCALDISPATCH numeric(15,5)        null,
   LOWER6SECLOCALREQ    numeric(15,5)        null,
   LOWER6SECREQ         numeric(15,5)        null,
   RAISE5MINDISPATCH    numeric(15,5)        null,
   RAISE5MINIMPORT      numeric(15,5)        null,
   RAISE5MINLOCALDISPATCH numeric(15,5)        null,
   RAISE5MINLOCALREQ    numeric(15,5)        null,
   RAISE5MINREQ         numeric(15,5)        null,
   RAISE60SECDISPATCH   numeric(15,5)        null,
   RAISE60SECIMPORT     numeric(15,5)        null,
   RAISE60SECLOCALDISPATCH numeric(15,5)        null,
   RAISE60SECLOCALREQ   numeric(15,5)        null,
   RAISE60SECREQ        numeric(15,5)        null,
   RAISE6SECDISPATCH    numeric(15,5)        null,
   RAISE6SECIMPORT      numeric(15,5)        null,
   RAISE6SECLOCALDISPATCH numeric(15,5)        null,
   RAISE6SECLOCALREQ    numeric(15,5)        null,
   RAISE6SECREQ         numeric(15,5)        null,
   AGGREGATEDISPATCHERROR numeric(15,5)        null,
   INITIALSUPPLY        numeric(15,5)        null,
   CLEAREDSUPPLY        numeric(15,5)        null,
   LOWERREGIMPORT       numeric(15,5)        null,
   LOWERREGDISPATCH     numeric(15,5)        null,
   LOWERREGLOCALDISPATCH numeric(15,5)        null,
   LOWERREGLOCALREQ     numeric(15,5)        null,
   LOWERREGREQ          numeric(15,5)        null,
   RAISEREGIMPORT       numeric(15,5)        null,
   RAISEREGDISPATCH     numeric(15,5)        null,
   RAISEREGLOCALDISPATCH numeric(15,5)        null,
   RAISEREGLOCALREQ     numeric(15,5)        null,
   RAISEREGREQ          numeric(15,5)        null,
   RAISE5MINLOCALVIOLATION numeric(15,5)        null,
   RAISEREGLOCALVIOLATION numeric(15,5)        null,
   RAISE60SECLOCALVIOLATION numeric(15,5)        null,
   RAISE6SECLOCALVIOLATION numeric(15,5)        null,
   LOWER5MINLOCALVIOLATION numeric(15,5)        null,
   LOWERREGLOCALVIOLATION numeric(15,5)        null,
   LOWER60SECLOCALVIOLATION numeric(15,5)        null,
   LOWER6SECLOCALVIOLATION numeric(15,5)        null,
   RAISE5MINVIOLATION   numeric(15,5)        null,
   RAISEREGVIOLATION    numeric(15,5)        null,
   RAISE60SECVIOLATION  numeric(15,5)        null,
   RAISE6SECVIOLATION   numeric(15,5)        null,
   LOWER5MINVIOLATION   numeric(15,5)        null,
   LOWERREGVIOLATION    numeric(15,5)        null,
   LOWER60SECVIOLATION  numeric(15,5)        null,
   LOWER6SECVIOLATION   numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   TOTALINTERMITTENTGENERATION numeric(15,5)        null,
   DEMAND_AND_NONSCHEDGEN numeric(15,5)        null,
   UIGF                 numeric(15,5)        null,
   SEMISCHEDULE_CLEAREDMW numeric(15,5)        null,
   SEMISCHEDULE_COMPLIANCEMW numeric(15,5)        null,
   INTERVENTION         numeric(2,0)         null,
   SS_SOLAR_UIGF        numeric(15,5)        null,
   SS_WIND_UIGF         numeric(15,5)        null,
   SS_SOLAR_CLEAREDMW   numeric(15,5)        null,
   SS_WIND_CLEAREDMW    numeric(15,5)        null,
   SS_SOLAR_COMPLIANCEMW numeric(15,5)        null,
   SS_WIND_COMPLIANCEMW numeric(15,5)        null
);

alter table P5MIN_REGIONSOLUTION
   add constraint P5MIN_REGIONSOLUTION_PK primary key (RUN_DATETIME, REGIONID, INTERVAL_DATETIME);





create index P5MIN_REGIONSOLUTION_LCX on P5MIN_REGIONSOLUTION (
LASTCHANGED ASC
);





create table P5MIN_UNITSOLUTION (
   RUN_DATETIME         timestamp(3)             not null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   DUID                 varchar(10)          not null,
   CONNECTIONPOINTID    varchar(12)          null,
   TRADETYPE            numeric(2,0)         null,
   AGCSTATUS            numeric(2,0)         null,
   INITIALMW            numeric(15,5)        null,
   TOTALCLEARED         numeric(15,5)        null,
   RAMPDOWNRATE         numeric(15,5)        null,
   RAMPUPRATE           numeric(15,5)        null,
   LOWER5MIN            numeric(15,5)        null,
   LOWER60SEC           numeric(15,5)        null,
   LOWER6SEC            numeric(15,5)        null,
   RAISE5MIN            numeric(15,5)        null,
   RAISE60SEC           numeric(15,5)        null,
   RAISE6SEC            numeric(15,5)        null,
   LOWERREG             numeric(15,5)        null,
   RAISEREG             numeric(15,5)        null,
   AVAILABILITY         numeric(15,5)        null,
   RAISE6SECFLAGS       numeric(3,0)         null,
   RAISE60SECFLAGS      numeric(3,0)         null,
   RAISE5MINFLAGS       numeric(3,0)         null,
   RAISEREGFLAGS        numeric(3,0)         null,
   LOWER6SECFLAGS       numeric(3,0)         null,
   LOWER60SECFLAGS      numeric(3,0)         null,
   LOWER5MINFLAGS       numeric(3,0)         null,
   LOWERREGFLAGS        numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null,
   SEMIDISPATCHCAP      numeric(3,0)         null,
   INTERVENTION         numeric(2,0)         null
);

alter table P5MIN_UNITSOLUTION
   add constraint P5MIN_UNITSOLUTION_PK primary key (RUN_DATETIME, DUID, INTERVAL_DATETIME);





create index P5MIN_UNITSOLUTION_LCX on P5MIN_UNITSOLUTION (
LASTCHANGED ASC
);





create table PARTICIPANT (
   PARTICIPANTID        varchar(10)          not null,
   PARTICIPANTCLASSID   varchar(20)          null,
   NAME                 varchar(80)          null,
   DESCRIPTION          varchar(64)          null,
   ACN                  varchar(9)           null,
   PRIMARYBUSINESS      varchar(40)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table PARTICIPANT
   add constraint PARTICIPANT_PK primary key (PARTICIPANTID);





create index PARTICIPANT_LCX on PARTICIPANT (
LASTCHANGED ASC
);





create table PARTICIPANTACCOUNT (
   ACCOUNTNAME          varchar(80)          null,
   PARTICIPANTID        varchar(10)          not null,
   ACCOUNTNUMBER        varchar(16)          null,
   BANKNAME             varchar(16)          null,
   BANKNUMBER           numeric(10,0)        null,
   BRANCHNAME           varchar(16)          null,
   BRANCHNUMBER         numeric(10,0)        null,
   BSBNUMBER            varchar(20)          null,
   NEMMCOCREDITACCOUNTNUMBER numeric(10,0)        null,
   NEMMCODEBITACCOUNTNUMBER numeric(10,0)        null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   EFFECTIVEDATE        timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null,
   ABN                  varchar(20)          null
);

alter table PARTICIPANTACCOUNT
   add constraint PARTICIPANTACCOUNT_PK primary key (PARTICIPANTID);





create index PARTICIPANTACCOUNT_LCX on PARTICIPANTACCOUNT (
LASTCHANGED ASC
);





create table PARTICIPANTCATEGORY (
   PARTICIPANTCATEGORYID varchar(10)          not null,
   DESCRIPTION          varchar(64)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table PARTICIPANTCATEGORY
   add constraint PARTICIPANTCATEGORY_PK primary key (PARTICIPANTCATEGORYID);





create index PARTICIPANTCATEGORY_LCX on PARTICIPANTCATEGORY (
LASTCHANGED ASC
);





create table PARTICIPANTCATEGORYALLOC (
   PARTICIPANTCATEGORYID varchar(10)          not null,
   PARTICIPANTID        varchar(10)          not null,
   LASTCHANGED          timestamp(3)             null
);

alter table PARTICIPANTCATEGORYALLOC
   add constraint PARTICIPANTCATALLOC_PK primary key (PARTICIPANTCATEGORYID, PARTICIPANTID);





create index PARTICIPANTCATEGORYALLOC_LCX on PARTICIPANTCATEGORYALLOC (
LASTCHANGED ASC
);





create table PARTICIPANTCLASS (
   PARTICIPANTCLASSID   varchar(20)          not null,
   DESCRIPTION          varchar(64)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table PARTICIPANTCLASS
   add constraint PARTCLASS_PK primary key (PARTICIPANTCLASSID);





create index PARTICIPANTCLASS_LCX on PARTICIPANTCLASS (
LASTCHANGED ASC
);





create table PARTICIPANTCREDITDETAIL (
   EFFECTIVEDATE        timestamp(3)             not null,
   PARTICIPANTID        varchar(10)          not null,
   CREDITLIMIT          numeric(10,0)        null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table PARTICIPANTCREDITDETAIL
   add constraint PARTCREDDET_PK primary key (EFFECTIVEDATE, PARTICIPANTID);





create index PARTICIPANTCREDITDETAIL_LCX on PARTICIPANTCREDITDETAIL (
LASTCHANGED ASC
);





create index PARTICIPANTCREDITDET_NDX2 on PARTICIPANTCREDITDETAIL (
PARTICIPANTID ASC
);





create table PARTICIPANTNOTICETRK (
   PARTICIPANTID        varchar(10)          not null,
   NOTICEID             numeric(10,0)        not null,
   LASTCHANGED          timestamp(3)             null
);

alter table PARTICIPANTNOTICETRK
   add constraint PARTICIPANTNOTICETRK_PK primary key (PARTICIPANTID, NOTICEID);





create index PARTICIPANTNOTICETRK_NDX2 on PARTICIPANTNOTICETRK (
PARTICIPANTID ASC
);





create index PARTICIPANTNOTICETRK_LCX on PARTICIPANTNOTICETRK (
LASTCHANGED ASC
);





create table PARTICIPANT_BANDFEE_ALLOC (
   PARTICIPANTID        varchar(10)          not null,
   MARKETFEEID          varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTCATEGORYID varchar(10)          not null,
   MARKETFEEVALUE       numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table PARTICIPANT_BANDFEE_ALLOC
   add constraint PARTICIPANT_BANDFEE_ALLOC_PK primary key (PARTICIPANTID, MARKETFEEID, EFFECTIVEDATE, VERSIONNO, PARTICIPANTCATEGORYID);





create index PARTICIPANT_BANDFEE_ALOC_LCX on PARTICIPANT_BANDFEE_ALLOC (
LASTCHANGED ASC
);





create table PASACASESOLUTION (
   CASEID               varchar(20)          not null,
   SOLUTIONCOMPLETE     numeric(16,6)        null,
   PASAVERSION          numeric(27,10)       null,
   EXCESSGENERATION     numeric(16,6)        null,
   DEFICITCAPACITY      numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null,
   DATETIME             timestamp(3)             null
);

alter table PASACASESOLUTION
   add constraint PASACASESOLUTION_PK primary key (CASEID);





create index PASACASESOLUTION_LCX on PASACASESOLUTION (
LASTCHANGED ASC
);





create table PASACONSTRAINTSOLUTION (
   CASEID               varchar(20)          not null,
   CONSTRAINTID         varchar(20)          not null,
   PERIODID             varchar(20)          not null,
   CAPACITYMARGINALVALUE numeric(16,6)        null,
   CAPACITYVIOLATIONDEGREE numeric(16,6)        null,
   EXCESSGENMARGINALVALUE numeric(16,6)        null,
   EXCESSGENVIOLATIONDEGREE numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null,
   DATETIME             timestamp(3)             null
);

alter table PASACONSTRAINTSOLUTION
   add constraint PASACONSTRAINTSOLUTION_PK primary key (PERIODID, CONSTRAINTID);





create index PASACONSTRAINTSOLUTION_LCX on PASACONSTRAINTSOLUTION (
LASTCHANGED ASC
);





create table PASAINTERCONNECTORSOLUTION (
   CASEID               varchar(20)          not null,
   INTERCONNECTORID     varchar(10)          not null,
   PERIODID             varchar(20)          not null,
   CAPACITYMWFLOW       numeric(16,6)        null,
   CAPACITYMARGINALVALUE numeric(16,6)        null,
   CAPACITYVIOLATIONDEGREE numeric(16,6)        null,
   EXCESSGENMWFLOW      numeric(16,6)        null,
   EXCESSGENMARGINALVALUE numeric(16,6)        null,
   EXCESSGENVIOLATIONDEGREE numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null,
   IMPORTLIMIT          numeric(15,5)        null,
   EXPORTLIMIT          numeric(15,5)        null,
   DATETIME             timestamp(3)             null
);

alter table PASAINTERCONNECTORSOLUTION
   add constraint PASAINTERCONNECTORSOLUTION_PK primary key (PERIODID, INTERCONNECTORID);





create index PASAINTERCONNECTORSOLUTIO_LCX on PASAINTERCONNECTORSOLUTION (
LASTCHANGED ASC
);





create table PASAREGIONSOLUTION (
   CASEID               varchar(20)          not null,
   REGIONID             varchar(10)          not null,
   PERIODID             varchar(20)          not null,
   DEMAND10             numeric(16,6)        null,
   DEMAND50             numeric(16,6)        null,
   DEMAND90             numeric(16,6)        null,
   UNCONSTRAINEDCAPACITY numeric(16,6)        null,
   CONSTRAINEDCAPACITY  numeric(16,6)        null,
   CAPACITYSURPLUS      numeric(16,6)        null,
   RESERVEREQ           numeric(16,6)        null,
   RESERVECONDITION     numeric(16,6)        null,
   RESERVESURPLUS       numeric(16,6)        null,
   LOADREJECTIONRESERVEREQ numeric(16,6)        null,
   LOADREJECTIONRESERVESURPLUS numeric(16,6)        null,
   NETINTERCHANGEUNDEREXCESS numeric(16,6)        null,
   NETINTERCHANGEUNDERSCARCITY numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null,
   EXCESSGENERATION     numeric(22,0)        null,
   ENERGYREQUIRED       numeric(15,5)        null,
   CAPACITYREQUIRED     numeric(15,5)        null,
   DATETIME             timestamp(3)             null
);

alter table PASAREGIONSOLUTION
   add constraint PASAREGIONSOLUTION_PK primary key (PERIODID, REGIONID);





create index PASAREGIONSOLUTION_LCX on PASAREGIONSOLUTION (
LASTCHANGED ASC
);





create table PDPASA_CASESOLUTION (
   RUN_DATETIME         timestamp(3)             not null,
   PASAVERSION          varchar(10)          null,
   RESERVECONDITION     numeric(1,0)         null,
   LORCONDITION         numeric(1,0)         null,
   CAPACITYOBJFUNCTION  numeric(12,3)        null,
   CAPACITYOPTION       numeric(12,3)        null,
   MAXSURPLUSRESERVEOPTION numeric(12,3)        null,
   MAXSPARECAPACITYOPTION numeric(12,3)        null,
   INTERCONNECTORFLOWPENALTY numeric(12,3)        null,
   LASTCHANGED          timestamp(3)             null,
   RELIABILITYLRCDEMANDOPTION numeric(12,3)        null,
   OUTAGELRCDEMANDOPTION numeric(12,3)        null,
   LORDEMANDOPTION      numeric(12,3)        null,
   RELIABILITYLRCCAPACITYOPTION varchar(10)          null,
   OUTAGELRCCAPACITYOPTION varchar(10)          null,
   LORCAPACITYOPTION    varchar(10)          null,
   LORUIGFOPTION        numeric(3,0)         null,
   RELIABILITYLRCUIGFOPTION numeric(3,0)         null,
   OUTAGELRCUIGFOPTION  numeric(3,0)         null
);

alter table PDPASA_CASESOLUTION
   add constraint PDPASA_CASESOLUTION_PK primary key (RUN_DATETIME);





create index PDPASA_CASESOLUTION_LCX on PDPASA_CASESOLUTION (
LASTCHANGED ASC
);





create table PDPASA_REGIONSOLUTION (
   RUN_DATETIME         timestamp(3)             not null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   REGIONID             varchar(10)          not null,
   DEMAND10             numeric(12,2)        null,
   DEMAND50             numeric(12,2)        null,
   DEMAND90             numeric(12,2)        null,
   RESERVEREQ           numeric(12,2)        null,
   CAPACITYREQ          numeric(12,2)        null,
   ENERGYREQDEMAND50    numeric(12,2)        null,
   UNCONSTRAINEDCAPACITY numeric(12,0)        null,
   CONSTRAINEDCAPACITY  numeric(12,0)        null,
   NETINTERCHANGEUNDERSCARCITY numeric(12,2)        null,
   SURPLUSCAPACITY      numeric(12,2)        null,
   SURPLUSRESERVE       numeric(12,2)        null,
   RESERVECONDITION     numeric(1,0)         null,
   MAXSURPLUSRESERVE    numeric(12,2)        null,
   MAXSPARECAPACITY     numeric(12,2)        null,
   LORCONDITION         numeric(1,0)         null,
   AGGREGATECAPACITYAVAILABLE numeric(12,2)        null,
   AGGREGATESCHEDULEDLOAD numeric(12,2)        null,
   LASTCHANGED          timestamp(3)             null,
   AGGREGATEPASAAVAILABILITY numeric(12,0)        null,
   RUNTYPE              varchar(20)          not null default 'OUTAGE_LRC',
   ENERGYREQDEMAND10    numeric(12,2)        null,
   CALCULATEDLOR1LEVEL  numeric(16,6)        null,
   CALCULATEDLOR2LEVEL  numeric(16,6)        null,
   MSRNETINTERCHANGEUNDERSCARCITY numeric(12,2)        null,
   LORNETINTERCHANGEUNDERSCARCITY numeric(12,2)        null,
   TOTALINTERMITTENTGENERATION numeric(15,5)        null,
   DEMAND_AND_NONSCHEDGEN numeric(15,5)        null,
   UIGF                 numeric(12,2)        null,
   SEMISCHEDULEDCAPACITY numeric(12,2)        null,
   LOR_SEMISCHEDULEDCAPACITY numeric(12,2)        null,
   LCR                  numeric(16,6)        null,
   LCR2                 numeric(16,6)        null,
   FUM                  numeric(16,6)        null,
   SS_SOLAR_UIGF        numeric(12,2)        null,
   SS_WIND_UIGF         numeric(12,2)        null,
   SS_SOLAR_CAPACITY    numeric(12,2)        null,
   SS_WIND_CAPACITY     numeric(12,2)        null,
   SS_SOLAR_CLEARED     numeric(12,2)        null,
   SS_WIND_CLEARED      numeric(12,2)        null
);

alter table PDPASA_REGIONSOLUTION
   add constraint PDPASA_REGIONSOLUTION_PK primary key (RUN_DATETIME, RUNTYPE, INTERVAL_DATETIME, REGIONID);





create index PDPASA_REGIONSOLUTION_LCX on PDPASA_REGIONSOLUTION (
LASTCHANGED ASC
);





create table PERDEMAND (
   EFFECTIVEDATE        timestamp(3)             null,
   SETTLEMENTDATE       timestamp(3)             not null,
   REGIONID             varchar(10)          not null,
   OFFERDATE            timestamp(3)             not null,
   PERIODID             numeric(3,0)         not null,
   VERSIONNO            numeric(3,0)         not null,
   RESDEMAND            numeric(10,0)        null,
   DEMAND90PROBABILITY  numeric(10,0)        null,
   DEMAND10PROBABILITY  numeric(10,0)        null,
   LASTCHANGED          timestamp(3)             null,
   MR_SCHEDULE          numeric(6,0)         null
);

alter table PERDEMAND
   add constraint PERDEMAND_PK primary key (SETTLEMENTDATE, REGIONID, OFFERDATE, VERSIONNO, PERIODID);





create index PERDEMAND_LCX on PERDEMAND (
LASTCHANGED ASC
);





create table PEROFFER (
   SETTLEMENTDATE       timestamp(3)             not null,
   DUID                 varchar(10)          not null,
   OFFERDATE            timestamp(3)             not null,
   PERIODID             numeric(3,0)         not null,
   VERSIONNO            numeric(3,0)         not null,
   SELFDISPATCH         numeric(12,6)        null,
   MAXAVAIL             numeric(12,6)        null,
   FIXEDLOAD            numeric(12,6)        null,
   ROCUP                numeric(6,0)         null,
   ROCDOWN              numeric(6,0)         null,
   BANDAVAIL1           numeric(6,0)         null,
   BANDAVAIL2           numeric(6,0)         null,
   BANDAVAIL3           numeric(6,0)         null,
   BANDAVAIL4           numeric(6,0)         null,
   BANDAVAIL5           numeric(6,0)         null,
   BANDAVAIL6           numeric(6,0)         null,
   BANDAVAIL7           numeric(6,0)         null,
   BANDAVAIL8           numeric(6,0)         null,
   BANDAVAIL9           numeric(6,0)         null,
   BANDAVAIL10          numeric(6,0)         null,
   LASTCHANGED          timestamp(3)             null,
   PASAAVAILABILITY     numeric(12,0)        null,
   MR_CAPACITY          numeric(6,0)         null
);

alter table PEROFFER
   add constraint PEROFFER_PK primary key (SETTLEMENTDATE, DUID, OFFERDATE, VERSIONNO, PERIODID);





create index PEROFFER_NDX2 on PEROFFER (
DUID ASC,
LASTCHANGED ASC
);





create index PEROFFER_LCX on PEROFFER (
LASTCHANGED ASC
);





create table PEROFFER_D (
   SETTLEMENTDATE       timestamp(3)             not null,
   DUID                 varchar(10)          not null,
   OFFERDATE            timestamp(3)             not null,
   PERIODID             numeric(3,0)         not null,
   VERSIONNO            numeric(3,0)         not null,
   SELFDISPATCH         numeric(12,6)        null,
   MAXAVAIL             numeric(12,6)        null,
   FIXEDLOAD            numeric(12,6)        null,
   ROCUP                numeric(6,0)         null,
   ROCDOWN              numeric(6,0)         null,
   BANDAVAIL1           numeric(6,0)         null,
   BANDAVAIL2           numeric(6,0)         null,
   BANDAVAIL3           numeric(6,0)         null,
   BANDAVAIL4           numeric(6,0)         null,
   BANDAVAIL5           numeric(6,0)         null,
   BANDAVAIL6           numeric(6,0)         null,
   BANDAVAIL7           numeric(6,0)         null,
   BANDAVAIL8           numeric(6,0)         null,
   BANDAVAIL9           numeric(6,0)         null,
   BANDAVAIL10          numeric(6,0)         null,
   LASTCHANGED          timestamp(3)             null,
   PASAAVAILABILITY     numeric(12,0)        null,
   MR_CAPACITY          numeric(6,0)         null
);

alter table PEROFFER_D
   add constraint PEROFFER_D_PK primary key (SETTLEMENTDATE, DUID, OFFERDATE, VERSIONNO, PERIODID);





create index PEROFFER_D_NDX2 on PEROFFER_D (
DUID ASC,
LASTCHANGED ASC
);





create index PEROFFER_D_LCX on PEROFFER_D (
LASTCHANGED ASC
);





create table PREDISPATCHBIDTRK (
   PREDISPATCHSEQNO     varchar(20)          not null,
   DUID                 varchar(10)          not null,
   PERIODID             varchar(20)          not null,
   BIDTYPE              varchar(10)          null,
   OFFERDATE            timestamp(3)             null,
   VERSIONNO            numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null,
   SETTLEMENTDATE       timestamp(3)             null,
   DATETIME             timestamp(3)             null
);

alter table PREDISPATCHBIDTRK
   add constraint PREDISPATCHBIDTRK_PK primary key (PREDISPATCHSEQNO, DUID, PERIODID);





create index PREDISPATCHBIDTRK_LCX on PREDISPATCHBIDTRK (
LASTCHANGED ASC
);





create index PREDISPATCHBIDTRK_NDX2 on PREDISPATCHBIDTRK (
DUID ASC,
LASTCHANGED ASC
);





create index PREDISPATCHBIDTRK_NDX3 on PREDISPATCHBIDTRK (
DUID ASC,
SETTLEMENTDATE ASC
);





create table PREDISPATCHBLOCKEDCONSTRAINT (
   PREDISPATCHSEQNO     varchar(20)          not null,
   CONSTRAINTID         varchar(20)          not null
);

alter table PREDISPATCHBLOCKEDCONSTRAINT
   add constraint PK_PREDISPATCHBLOCKEDCONSTR primary key (PREDISPATCHSEQNO, CONSTRAINTID);





create table PREDISPATCHCASESOLUTION (
   PREDISPATCHSEQNO     varchar(20)          not null,
   RUNNO                numeric(3,0)         not null,
   SOLUTIONSTATUS       numeric(2,0)         null,
   SPDVERSION           varchar(20)          null,
   NONPHYSICALLOSSES    numeric(1,0)         null,
   TOTALOBJECTIVE       numeric(27,10)       null,
   TOTALAREAGENVIOLATION numeric(15,5)        null,
   TOTALINTERCONNECTORVIOLATION numeric(15,5)        null,
   TOTALGENERICVIOLATION numeric(15,5)        null,
   TOTALRAMPRATEVIOLATION numeric(15,5)        null,
   TOTALUNITMWCAPACITYVIOLATION numeric(15,5)        null,
   TOTAL5MINVIOLATION   numeric(15,5)        null,
   TOTALREGVIOLATION    numeric(15,5)        null,
   TOTAL6SECVIOLATION   numeric(15,5)        null,
   TOTAL60SECVIOLATION  numeric(15,5)        null,
   TOTALASPROFILEVIOLATION numeric(15,5)        null,
   TOTALENERGYCONSTRVIOLATION numeric(15,5)        null,
   TOTALENERGYOFFERVIOLATION numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   INTERVENTION         numeric(2,0)         null
);

alter table PREDISPATCHCASESOLUTION
   add constraint PREDISPATCHCASESOLUTION_PK primary key (PREDISPATCHSEQNO, RUNNO);





create index PREDISPATCHCASESOL_NDX_LCHD on PREDISPATCHCASESOLUTION (
LASTCHANGED ASC
);





create table PREDISPATCHCONSTRAINT (
   PREDISPATCHSEQNO     varchar(20)          null,
   RUNNO                numeric(3,0)         null,
   CONSTRAINTID         varchar(20)          not null,
   PERIODID             varchar(20)          null,
   INTERVENTION         numeric(2,0)         null,
   RHS                  numeric(15,5)        null,
   MARGINALVALUE        numeric(15,5)        null,
   VIOLATIONDEGREE      numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   DATETIME             timestamp(3)             not null,
   DUID                 varchar(20)          null,
   GENCONID_EFFECTIVEDATE timestamp(3)             null,
   GENCONID_VERSIONNO   numeric(22,0)        null,
   LHS                  numeric(15,5)        null
);

alter table PREDISPATCHCONSTRAINT
   add constraint PK_PREDISPATCHCONSTRAINT primary key (DATETIME, CONSTRAINTID);





create index PREDISPATCHCONSTRAIN_NDX2 on PREDISPATCHCONSTRAINT (
PREDISPATCHSEQNO ASC
);





create index PREDISPATCHCONSTRAINT_LCX on PREDISPATCHCONSTRAINT (
LASTCHANGED ASC
);





create table PREDISPATCHINTERCONNECTORRES (
   PREDISPATCHSEQNO     varchar(20)          null,
   RUNNO                numeric(3,0)         null,
   INTERCONNECTORID     varchar(10)          not null,
   PERIODID             varchar(20)          null,
   INTERVENTION         numeric(2,0)         null,
   METEREDMWFLOW        numeric(15,5)        null,
   MWFLOW               numeric(15,5)        null,
   MWLOSSES             numeric(15,5)        null,
   MARGINALVALUE        numeric(15,5)        null,
   VIOLATIONDEGREE      numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   DATETIME             timestamp(3)             not null,
   EXPORTLIMIT          numeric(15,5)        null,
   IMPORTLIMIT          numeric(15,5)        null,
   MARGINALLOSS         numeric(15,5)        null,
   EXPORTGENCONID       varchar(20)          null,
   IMPORTGENCONID       varchar(20)          null,
   FCASEXPORTLIMIT      numeric(15,5)        null,
   FCASIMPORTLIMIT      numeric(15,5)        null,
   LOCAL_PRICE_ADJUSTMENT_EXPORT numeric(10,2)        null,
   LOCALLY_CONSTRAINED_EXPORT numeric(1,0)         null,
   LOCAL_PRICE_ADJUSTMENT_IMPORT numeric(10,2)        null,
   LOCALLY_CONSTRAINED_IMPORT numeric(1,0)         null
);

alter table PREDISPATCHINTERCONNECTORRES
   add constraint PK_PREDISPATCHINTCONRES primary key (DATETIME, INTERCONNECTORID);





create index PREDISPATCHINTERCONNECTOR_LCX on PREDISPATCHINTERCONNECTORRES (
LASTCHANGED ASC
);





create index PREDISPATCHINTCONRES_NDX3 on PREDISPATCHINTERCONNECTORRES (
PREDISPATCHSEQNO ASC
);





create table PREDISPATCHINTERSENSITIVITIES (
   PREDISPATCHSEQNO     varchar(20)          null,
   RUNNO                numeric(3,0)         null,
   INTERCONNECTORID     varchar(10)          not null,
   PERIODID             varchar(20)          null,
   INTERVENTION         numeric(2,0)         null,
   DATETIME             timestamp(3)             not null,
   INTERVENTION_ACTIVE  numeric(1,0)         null,
   MWFLOW1              numeric(15,5)        null,
   MWFLOW2              numeric(15,5)        null,
   MWFLOW3              numeric(15,5)        null,
   MWFLOW4              numeric(15,5)        null,
   MWFLOW5              numeric(15,5)        null,
   MWFLOW6              numeric(15,5)        null,
   MWFLOW7              numeric(15,5)        null,
   MWFLOW8              numeric(15,5)        null,
   MWFLOW9              numeric(15,5)        null,
   MWFLOW10             numeric(15,5)        null,
   MWFLOW11             numeric(15,5)        null,
   MWFLOW12             numeric(15,5)        null,
   MWFLOW13             numeric(15,5)        null,
   MWFLOW14             numeric(15,5)        null,
   MWFLOW15             numeric(15,5)        null,
   MWFLOW16             numeric(15,5)        null,
   MWFLOW17             numeric(15,5)        null,
   MWFLOW18             numeric(15,5)        null,
   MWFLOW19             numeric(15,5)        null,
   MWFLOW20             numeric(15,5)        null,
   MWFLOW21             numeric(15,5)        null,
   MWFLOW22             numeric(15,5)        null,
   MWFLOW23             numeric(15,5)        null,
   MWFLOW24             numeric(15,5)        null,
   MWFLOW25             numeric(15,5)        null,
   MWFLOW26             numeric(15,5)        null,
   MWFLOW27             numeric(15,5)        null,
   MWFLOW28             numeric(15,5)        null,
   MWFLOW29             numeric(15,5)        null,
   MWFLOW30             numeric(15,5)        null,
   MWFLOW31             numeric(15,5)        null,
   MWFLOW32             numeric(15,5)        null,
   MWFLOW33             numeric(15,5)        null,
   MWFLOW34             numeric(15,5)        null,
   MWFLOW35             numeric(15,5)        null,
   MWFLOW36             numeric(15,5)        null,
   MWFLOW37             numeric(15,5)        null,
   MWFLOW38             numeric(15,5)        null,
   MWFLOW39             numeric(15,5)        null,
   MWFLOW40             numeric(15,5)        null,
   MWFLOW41             numeric(15,5)        null,
   MWFLOW42             numeric(15,5)        null,
   MWFLOW43             numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table PREDISPATCHINTERSENSITIVITIES
   add constraint PREDISPATCHINTERSENSITIVIT_PK primary key (INTERCONNECTORID, DATETIME);





create index PREDISPATCHINTERSENSITIVIT_LCX on PREDISPATCHINTERSENSITIVITIES (
LASTCHANGED ASC
);





create table PREDISPATCHLOAD (
   PREDISPATCHSEQNO     varchar(20)          null,
   RUNNO                numeric(3,0)         null,
   DUID                 varchar(10)          not null,
   TRADETYPE            numeric(2,0)         null,
   PERIODID             varchar(20)          null,
   INTERVENTION         numeric(2,0)         null,
   CONNECTIONPOINTID    varchar(12)          null,
   AGCSTATUS            numeric(2,0)         null,
   DISPATCHMODE         numeric(2,0)         null,
   INITIALMW            numeric(15,5)        null,
   TOTALCLEARED         numeric(15,5)        null,
   LOWER5MIN            numeric(15,5)        null,
   LOWER60SEC           numeric(15,5)        null,
   LOWER6SEC            numeric(15,5)        null,
   RAISE5MIN            numeric(15,5)        null,
   RAISE60SEC           numeric(15,5)        null,
   RAISE6SEC            numeric(15,5)        null,
   RAMPDOWNRATE         numeric(15,5)        null,
   RAMPUPRATE           numeric(15,5)        null,
   DOWNEPF              numeric(15,5)        null,
   UPEPF                numeric(15,5)        null,
   MARGINAL5MINVALUE    numeric(15,5)        null,
   MARGINAL60SECVALUE   numeric(15,5)        null,
   MARGINAL6SECVALUE    numeric(15,5)        null,
   MARGINALVALUE        numeric(15,5)        null,
   VIOLATION5MINDEGREE  numeric(15,5)        null,
   VIOLATION60SECDEGREE numeric(15,5)        null,
   VIOLATION6SECDEGREE  numeric(15,5)        null,
   VIOLATIONDEGREE      numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   DATETIME             timestamp(3)             not null,
   LOWERREG             numeric(15,5)        null,
   RAISEREG             numeric(15,5)        null,
   AVAILABILITY         numeric(15,5)        null,
   RAISE6SECFLAGS       numeric(3,0)         null,
   RAISE60SECFLAGS      numeric(3,0)         null,
   RAISE5MINFLAGS       numeric(3,0)         null,
   RAISEREGFLAGS        numeric(3,0)         null,
   LOWER6SECFLAGS       numeric(3,0)         null,
   LOWER60SECFLAGS      numeric(3,0)         null,
   LOWER5MINFLAGS       numeric(3,0)         null,
   LOWERREGFLAGS        numeric(3,0)         null,
   RAISE6SECACTUALAVAILABILITY numeric(16,6)        null,
   RAISE60SECACTUALAVAILABILITY numeric(16,6)        null,
   RAISE5MINACTUALAVAILABILITY numeric(16,6)        null,
   RAISEREGACTUALAVAILABILITY numeric(16,6)        null,
   LOWER6SECACTUALAVAILABILITY numeric(16,6)        null,
   LOWER60SECACTUALAVAILABILITY numeric(16,6)        null,
   LOWER5MINACTUALAVAILABILITY numeric(16,6)        null,
   LOWERREGACTUALAVAILABILITY numeric(16,6)        null,
   SEMIDISPATCHCAP      numeric(3,0)         null
);

alter table PREDISPATCHLOAD
   add constraint PK_PREDISPATCHLOAD primary key (DATETIME, DUID);





create index PREDISPATCHLOAD_NDX2 on PREDISPATCHLOAD (
DUID ASC,
LASTCHANGED ASC
);





create index PREDISPATCHLOAD_NDX3 on PREDISPATCHLOAD (
PREDISPATCHSEQNO ASC
);





create index PREDISPATCHLOAD_LCX on PREDISPATCHLOAD (
LASTCHANGED ASC
);





create table PREDISPATCHOFFERTRK (
   PREDISPATCHSEQNO     varchar(20)          not null,
   DUID                 varchar(10)          not null,
   BIDTYPE              varchar(20)          not null,
   PERIODID             varchar(20)          not null,
   BIDSETTLEMENTDATE    timestamp(3)             null,
   BIDOFFERDATE         timestamp(3)             null,
   DATETIME             timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table PREDISPATCHOFFERTRK
   add constraint PREDISPATCHOFFERTRK_PK primary key (PREDISPATCHSEQNO, DUID, BIDTYPE, PERIODID);





create index PREDISPATCHOFFERTRK_LCHD_IDX on PREDISPATCHOFFERTRK (
LASTCHANGED ASC
);





create table PREDISPATCHPRICE (
   PREDISPATCHSEQNO     varchar(20)          null,
   RUNNO                numeric(3,0)         null,
   REGIONID             varchar(10)          not null,
   PERIODID             varchar(20)          null,
   INTERVENTION         numeric(2,0)         null,
   RRP                  numeric(15,5)        null,
   EEP                  numeric(15,5)        null,
   RRP1                 numeric(15,5)        null,
   EEP1                 numeric(15,5)        null,
   RRP2                 numeric(15,5)        null,
   EEP2                 numeric(15,5)        null,
   RRP3                 numeric(15,5)        null,
   EEP3                 numeric(15,5)        null,
   RRP4                 numeric(15,5)        null,
   EEP4                 numeric(15,5)        null,
   RRP5                 numeric(15,5)        null,
   EEP5                 numeric(15,5)        null,
   RRP6                 numeric(15,5)        null,
   EEP6                 numeric(15,5)        null,
   RRP7                 numeric(15,5)        null,
   EEP7                 numeric(15,5)        null,
   RRP8                 numeric(15,5)        null,
   EEP8                 numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   DATETIME             timestamp(3)             not null,
   RAISE6SECRRP         numeric(15,5)        null,
   RAISE60SECRRP        numeric(15,5)        null,
   RAISE5MINRRP         numeric(15,5)        null,
   RAISEREGRRP          numeric(15,5)        null,
   LOWER6SECRRP         numeric(15,5)        null,
   LOWER60SECRRP        numeric(15,5)        null,
   LOWER5MINRRP         numeric(15,5)        null,
   LOWERREGRRP          numeric(15,5)        null
);

alter table PREDISPATCHPRICE
   add constraint PK_PREDISPATCHPRICE primary key (DATETIME, REGIONID);





create index PREDISPATCHPRICE_NDX3 on PREDISPATCHPRICE (
PREDISPATCHSEQNO ASC
);





create index PREDISPATCHPRICE_LCX on PREDISPATCHPRICE (
LASTCHANGED ASC
);





create table PREDISPATCHPRICESENSITIVITIES (
   PREDISPATCHSEQNO     varchar(20)          null,
   RUNNO                numeric(3,0)         null,
   REGIONID             varchar(10)          not null,
   PERIODID             varchar(20)          null,
   INTERVENTION         numeric(2,0)         null,
   RRPEEP1              numeric(15,5)        null,
   RRPEEP2              numeric(15,5)        null,
   RRPEEP3              numeric(15,5)        null,
   RRPEEP4              numeric(15,5)        null,
   RRPEEP5              numeric(15,5)        null,
   RRPEEP6              numeric(15,5)        null,
   RRPEEP7              numeric(15,5)        null,
   RRPEEP8              numeric(15,5)        null,
   RRPEEP9              numeric(15,5)        null,
   RRPEEP10             numeric(15,5)        null,
   RRPEEP11             numeric(15,5)        null,
   RRPEEP12             numeric(15,5)        null,
   RRPEEP13             numeric(15,5)        null,
   RRPEEP14             numeric(15,5)        null,
   RRPEEP15             numeric(15,5)        null,
   RRPEEP16             numeric(15,5)        null,
   RRPEEP17             numeric(15,5)        null,
   RRPEEP18             numeric(15,5)        null,
   RRPEEP19             numeric(15,5)        null,
   RRPEEP20             numeric(15,5)        null,
   RRPEEP21             numeric(15,5)        null,
   RRPEEP22             numeric(15,5)        null,
   RRPEEP23             numeric(15,5)        null,
   RRPEEP24             numeric(15,5)        null,
   RRPEEP25             numeric(15,5)        null,
   RRPEEP26             numeric(15,5)        null,
   RRPEEP27             numeric(15,5)        null,
   RRPEEP28             numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   DATETIME             timestamp(3)             not null,
   RRPEEP29             numeric(15,5)        null,
   RRPEEP30             numeric(15,5)        null,
   RRPEEP31             numeric(15,5)        null,
   RRPEEP32             numeric(15,5)        null,
   RRPEEP33             numeric(15,5)        null,
   RRPEEP34             numeric(15,5)        null,
   RRPEEP35             numeric(15,5)        null,
   INTERVENTION_ACTIVE  numeric(1,0)         null,
   RRPEEP36             numeric(15,5)        null,
   RRPEEP37             numeric(15,5)        null,
   RRPEEP38             numeric(15,5)        null,
   RRPEEP39             numeric(15,5)        null,
   RRPEEP40             numeric(15,5)        null,
   RRPEEP41             numeric(15,5)        null,
   RRPEEP42             numeric(15,5)        null,
   RRPEEP43             numeric(15,5)        null
);

alter table PREDISPATCHPRICESENSITIVITIES
   add constraint PREDISPATCHPRICESENS_PK primary key (DATETIME, REGIONID);





create index PREDISPATCHPRCESENS_NDX3 on PREDISPATCHPRICESENSITIVITIES (
PREDISPATCHSEQNO ASC
);





create index PREDISPATCHPRICESENSITIVI_LCX on PREDISPATCHPRICESENSITIVITIES (
LASTCHANGED ASC
);





create table PREDISPATCHREGIONSUM (
   PREDISPATCHSEQNO     varchar(20)          null,
   RUNNO                numeric(3,0)         null,
   REGIONID             varchar(10)          not null,
   PERIODID             varchar(20)          null,
   INTERVENTION         numeric(2,0)         null,
   TOTALDEMAND          numeric(15,5)        null,
   AVAILABLEGENERATION  numeric(15,5)        null,
   AVAILABLELOAD        numeric(15,5)        null,
   DEMANDFORECAST       numeric(15,5)        null,
   DISPATCHABLEGENERATION numeric(15,5)        null,
   DISPATCHABLELOAD     numeric(15,5)        null,
   NETINTERCHANGE       numeric(15,5)        null,
   EXCESSGENERATION     numeric(15,5)        null,
   LOWER5MINDISPATCH    numeric(15,5)        null,
   LOWER5MINIMPORT      numeric(15,5)        null,
   LOWER5MINLOCALDISPATCH numeric(15,5)        null,
   LOWER5MINLOCALPRICE  numeric(15,5)        null,
   LOWER5MINLOCALREQ    numeric(15,5)        null,
   LOWER5MINPRICE       numeric(15,5)        null,
   LOWER5MINREQ         numeric(15,5)        null,
   LOWER5MINSUPPLYPRICE numeric(15,5)        null,
   LOWER60SECDISPATCH   numeric(15,5)        null,
   LOWER60SECIMPORT     numeric(15,5)        null,
   LOWER60SECLOCALDISPATCH numeric(15,5)        null,
   LOWER60SECLOCALPRICE numeric(15,5)        null,
   LOWER60SECLOCALREQ   numeric(15,5)        null,
   LOWER60SECPRICE      numeric(15,5)        null,
   LOWER60SECREQ        numeric(15,5)        null,
   LOWER60SECSUPPLYPRICE numeric(15,5)        null,
   LOWER6SECDISPATCH    numeric(15,5)        null,
   LOWER6SECIMPORT      numeric(15,5)        null,
   LOWER6SECLOCALDISPATCH numeric(15,5)        null,
   LOWER6SECLOCALPRICE  numeric(15,5)        null,
   LOWER6SECLOCALREQ    numeric(15,5)        null,
   LOWER6SECPRICE       numeric(15,5)        null,
   LOWER6SECREQ         numeric(15,5)        null,
   LOWER6SECSUPPLYPRICE numeric(15,5)        null,
   RAISE5MINDISPATCH    numeric(15,5)        null,
   RAISE5MINIMPORT      numeric(15,5)        null,
   RAISE5MINLOCALDISPATCH numeric(15,5)        null,
   RAISE5MINLOCALPRICE  numeric(15,5)        null,
   RAISE5MINLOCALREQ    numeric(15,5)        null,
   RAISE5MINPRICE       numeric(15,5)        null,
   RAISE5MINREQ         numeric(15,5)        null,
   RAISE5MINSUPPLYPRICE numeric(15,5)        null,
   RAISE60SECDISPATCH   numeric(15,5)        null,
   RAISE60SECIMPORT     numeric(15,5)        null,
   RAISE60SECLOCALDISPATCH numeric(15,5)        null,
   RAISE60SECLOCALPRICE numeric(15,5)        null,
   RAISE60SECLOCALREQ   numeric(15,5)        null,
   RAISE60SECPRICE      numeric(15,5)        null,
   RAISE60SECREQ        numeric(15,5)        null,
   RAISE60SECSUPPLYPRICE numeric(15,5)        null,
   RAISE6SECDISPATCH    numeric(15,5)        null,
   RAISE6SECIMPORT      numeric(15,5)        null,
   RAISE6SECLOCALDISPATCH numeric(15,5)        null,
   RAISE6SECLOCALPRICE  numeric(15,5)        null,
   RAISE6SECLOCALREQ    numeric(15,5)        null,
   RAISE6SECPRICE       numeric(15,5)        null,
   RAISE6SECREQ         numeric(15,5)        null,
   RAISE6SECSUPPLYPRICE numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   DATETIME             timestamp(3)             not null,
   INITIALSUPPLY        numeric(15,5)        null,
   CLEAREDSUPPLY        numeric(15,5)        null,
   LOWERREGIMPORT       numeric(15,5)        null,
   LOWERREGLOCALDISPATCH numeric(15,5)        null,
   LOWERREGLOCALREQ     numeric(15,5)        null,
   LOWERREGREQ          numeric(15,5)        null,
   RAISEREGIMPORT       numeric(15,5)        null,
   RAISEREGLOCALDISPATCH numeric(15,5)        null,
   RAISEREGLOCALREQ     numeric(15,5)        null,
   RAISEREGREQ          numeric(15,5)        null,
   RAISE5MINLOCALVIOLATION numeric(15,5)        null,
   RAISEREGLOCALVIOLATION numeric(15,5)        null,
   RAISE60SECLOCALVIOLATION numeric(15,5)        null,
   RAISE6SECLOCALVIOLATION numeric(15,5)        null,
   LOWER5MINLOCALVIOLATION numeric(15,5)        null,
   LOWERREGLOCALVIOLATION numeric(15,5)        null,
   LOWER60SECLOCALVIOLATION numeric(15,5)        null,
   LOWER6SECLOCALVIOLATION numeric(15,5)        null,
   RAISE5MINVIOLATION   numeric(15,5)        null,
   RAISEREGVIOLATION    numeric(15,5)        null,
   RAISE60SECVIOLATION  numeric(15,5)        null,
   RAISE6SECVIOLATION   numeric(15,5)        null,
   LOWER5MINVIOLATION   numeric(15,5)        null,
   LOWERREGVIOLATION    numeric(15,5)        null,
   LOWER60SECVIOLATION  numeric(15,5)        null,
   LOWER6SECVIOLATION   numeric(15,5)        null,
   RAISE6SECACTUALAVAILABILITY numeric(16,6)        null,
   RAISE60SECACTUALAVAILABILITY numeric(16,6)        null,
   RAISE5MINACTUALAVAILABILITY numeric(16,6)        null,
   RAISEREGACTUALAVAILABILITY numeric(16,6)        null,
   LOWER6SECACTUALAVAILABILITY numeric(16,6)        null,
   LOWER60SECACTUALAVAILABILITY numeric(16,6)        null,
   LOWER5MINACTUALAVAILABILITY numeric(16,6)        null,
   LOWERREGACTUALAVAILABILITY numeric(16,6)        null,
   DECAVAILABILITY      numeric(16,6)        null,
   LORSURPLUS           numeric(16,6)        null,
   LRCSURPLUS           numeric(16,6)        null,
   TOTALINTERMITTENTGENERATION numeric(15,5)        null,
   DEMAND_AND_NONSCHEDGEN numeric(15,5)        null,
   UIGF                 numeric(15,5)        null,
   SEMISCHEDULE_CLEAREDMW numeric(15,5)        null,
   SEMISCHEDULE_COMPLIANCEMW numeric(15,5)        null,
   SS_SOLAR_UIGF        numeric(15,5)        null,
   SS_WIND_UIGF         numeric(15,5)        null,
   SS_SOLAR_CLEAREDMW   numeric(15,5)        null,
   SS_WIND_CLEAREDMW    numeric(15,5)        null,
   SS_SOLAR_COMPLIANCEMW numeric(15,5)        null,
   SS_WIND_COMPLIANCEMW numeric(15,5)        null
);

alter table PREDISPATCHREGIONSUM
   add constraint PK_PREDISPATCHREGIONSUM primary key (DATETIME, REGIONID);





create index PREDISPATCHRGNSUM_NDX3 on PREDISPATCHREGIONSUM (
PREDISPATCHSEQNO ASC
);





create index PREDISPATCHREGIONSUM_LCX on PREDISPATCHREGIONSUM (
LASTCHANGED ASC
);





create table PREDISPATCHSCENARIODEMAND (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3)           not null,
   SCENARIO             numeric(2)           not null,
   REGIONID             varchar(20)          not null,
   DELTAMW              numeric(4)           null
);

alter table PREDISPATCHSCENARIODEMAND
   add constraint PREDISPATCHSCENARIODEMAND_PK primary key (EFFECTIVEDATE, VERSIONNO, SCENARIO, REGIONID);





create table PREDISPATCHSCENARIODEMANDTRK (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3)           not null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table PREDISPATCHSCENARIODEMANDTRK
   add constraint PREDISPATCHSCENARIODMNDTRK_PK primary key (EFFECTIVEDATE, VERSIONNO);





create index PREDISPATCHSCENARIODMNDTRK_LCX on PREDISPATCHSCENARIODEMANDTRK (
LASTCHANGED ASC
);





create table PREDISPATCH_FCAS_REQ (
   PREDISPATCHSEQNO     varchar(20)          null,
   RUNNO                numeric(3,0)         null,
   INTERVENTION         numeric(2,0)         null,
   PERIODID             varchar(20)          null,
   GENCONID             varchar(20)          not null,
   REGIONID             varchar(10)          not null,
   BIDTYPE              varchar(10)          not null,
   GENCONEFFECTIVEDATE  timestamp(3)             null,
   GENCONVERSIONNO      numeric(3,0)         null,
   MARGINALVALUE        numeric(16,6)        null,
   DATETIME             timestamp(3)             not null,
   LASTCHANGED          timestamp(3)             null,
   BASE_COST            numeric(18,8)        null,
   ADJUSTED_COST        numeric(18,8)        null,
   ESTIMATED_CMPF       numeric(18,8)        null,
   ESTIMATED_CRMPF      numeric(18,8)        null,
   RECOVERY_FACTOR_CMPF numeric(18,8)        null,
   RECOVERY_FACTOR_CRMPF numeric(18,8)        null
);

alter table PREDISPATCH_FCAS_REQ
   add constraint PREDISPATCH_FCAS_REQ_PK primary key (DATETIME, GENCONID, REGIONID, BIDTYPE);





create index PREDISPATCH_FCAS_REQ_LCX on PREDISPATCH_FCAS_REQ (
LASTCHANGED ASC
);





create table PREDISPATCH_LOCAL_PRICE (
   PREDISPATCHSEQNO     varchar(20)          not null,
   DATETIME             timestamp(3)             not null,
   DUID                 varchar(20)          not null,
   PERIODID             varchar(20)          null,
   LOCAL_PRICE_ADJUSTMENT numeric(10,2)        null,
   LOCALLY_CONSTRAINED  numeric(1,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table PREDISPATCH_LOCAL_PRICE
   add constraint PREDISPATCH_LOCAL_PRICE_PK primary key (DATETIME, DUID);





create table PREDISPATCH_MNSPBIDTRK (
   PREDISPATCHSEQNO     varchar(20)          not null,
   LINKID               varchar(10)          not null,
   PERIODID             varchar(20)          not null,
   PARTICIPANTID        varchar(10)          null,
   SETTLEMENTDATE       timestamp(3)             null,
   OFFERDATE            timestamp(3)             null,
   VERSIONNO            numeric(3,0)         null,
   DATETIME             timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table PREDISPATCH_MNSPBIDTRK
   add constraint PREDISPATCH_MNSPBIDTRK_PK primary key (PREDISPATCHSEQNO, LINKID, PERIODID);





create index PREDISPATCH_MNSPBIDTRK_LCX on PREDISPATCH_MNSPBIDTRK (
LASTCHANGED ASC
);





create table PRUDENTIALCOMPANYPOSITION (
   PRUDENTIAL_DATE      timestamp(3)             not null,
   RUNNO                numeric(3)           not null,
   COMPANY_ID           varchar(20)          not null,
   MCL                  numeric(16,6)        null,
   CREDIT_SUPPORT       numeric(16,6)        null,
   TRADING_LIMIT        numeric(16,6)        null,
   CURRENT_AMOUNT_BALANCE numeric(16,6)        null,
   SECURITY_DEPOSIT_PROVISION numeric(16,6)        null,
   SECURITY_DEPOSIT_OFFSET numeric(16,6)        null,
   SECURITY_DEPOSIT_BALANCE numeric(16,6)        null,
   EXPOST_REALLOC_BALANCE numeric(16,6)        null,
   DEFAULT_BALANCE      numeric(16,6)        null,
   OUTSTANDINGS         numeric(16,6)        null,
   TRADING_MARGIN       numeric(16,6)        null,
   TYPICAL_ACCRUAL      numeric(16,6)        null,
   PRUDENTIAL_MARGIN    numeric(16,6)        null,
   EARLY_PAYMENT_AMOUNT numeric(18,8)        null,
   PERCENTAGE_OUTSTANDINGS numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table PRUDENTIALCOMPANYPOSITION
   add constraint PRUDENTIALCOMPANYPOSITION_PK primary key (PRUDENTIAL_DATE, RUNNO, COMPANY_ID);





create index PRUDENTIALCOMPANYPOSITION_LCX on PRUDENTIALCOMPANYPOSITION (
LASTCHANGED ASC
);





create table PRUDENTIALRUNTRK (
   PRUDENTIAL_DATE      timestamp(3)             not null,
   RUNNO                numeric(3)           not null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table PRUDENTIALRUNTRK
   add constraint PRUDENTIALRUNTRK_PK primary key (PRUDENTIAL_DATE, RUNNO);





create index PRUDENTIALRUNTRK_LCX on PRUDENTIALRUNTRK (
LASTCHANGED ASC
);





create table REALLOCATION (
   REALLOCATIONID       varchar(20)          not null,
   CREDITPARTICIPANTID  varchar(10)          null,
   DEBITPARTICIPANTID   varchar(10)          null,
   REGIONID             varchar(10)          null,
   AGREEMENTTYPE        varchar(10)          null,
   CREDITREFERENCE      varchar(400)         null,
   DEBITREFERENCE       varchar(400)         null,
   LASTCHANGED          timestamp(3)             null,
   STARTDATE            timestamp(3)             null,
   ENDDATE              timestamp(3)             null,
   CURRENT_STEPID       varchar(20)          null,
   DAYTYPE              varchar(20)          null,
   REALLOCATION_TYPE    varchar(1)           null,
   CALENDARID           varchar(30)          null,
   INTERVALLENGTH       numeric(3,0)         null
);

alter table REALLOCATION
   add constraint REALLOCATION_PK primary key (REALLOCATIONID);





create index REALLOCATION_LCX on REALLOCATION (
LASTCHANGED ASC
);





create table REALLOCATIONDETAILS (
   REALLOCATIONID       varchar(20)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(10)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table REALLOCATIONDETAILS
   add constraint REALLOCATIONDETAILS_PK primary key (REALLOCATIONID, EFFECTIVEDATE, VERSIONNO);





create index REALLOCATIONDETAILS_LCX on REALLOCATIONDETAILS (
LASTCHANGED ASC
);





create table REALLOCATIONINTERVAL (
   REALLOCATIONID       varchar(20)          not null,
   PERIODID             numeric(3)           not null,
   VALUE                numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   NRP                  numeric(15,5)        null
);

alter table REALLOCATIONINTERVAL
   add constraint REALLOCATIONINTERVAL_PK primary key (REALLOCATIONID, PERIODID);





create index REALLOCATIONINTERVAL_LCX on REALLOCATIONINTERVAL (
LASTCHANGED ASC
);





create table REALLOCATIONINTERVALS (
   REALLOCATIONID       varchar(20)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   REALLOCATIONVALUE    numeric(6,2)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table REALLOCATIONINTERVALS
   add constraint REALLOCATIONINTERVALS_PK primary key (REALLOCATIONID, EFFECTIVEDATE, VERSIONNO, PERIODID);





create index REALLOCATIONINTERVALS_LCX on REALLOCATIONINTERVALS (
LASTCHANGED ASC
);





create table REALLOCATIONS (
   REALLOCATIONID       varchar(20)          not null,
   STARTDATE            timestamp(3)             null,
   STARTPERIOD          numeric(3,0)         null,
   ENDDATE              timestamp(3)             null,
   ENDPERIOD            numeric(3,0)         null,
   PARTICIPANTTOID      varchar(10)          null,
   PARTICIPANTFROMID    varchar(10)          null,
   AGREEMENTTYPE        varchar(10)          null,
   DEREGISTRATIONDATE   timestamp(3)             null,
   DEREGISTRATIONPERIOD numeric(3,0)         null,
   REGIONID             varchar(10)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table REALLOCATIONS
   add constraint REALLOCATIONS_PK primary key (REALLOCATIONID);





create index REALLOCATIONS_LCX on REALLOCATIONS (
LASTCHANGED ASC
);





create table REGION (
   REGIONID             varchar(10)          not null,
   DESCRIPTION          varchar(64)          null,
   REGIONSTATUS         varchar(8)           null,
   LASTCHANGED          timestamp(3)             null
);

alter table REGION
   add constraint REGION_PK primary key (REGIONID);





create index REGION_LCX on REGION (
LASTCHANGED ASC
);





create table REGIONAPC (
   REGIONID             varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(10)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table REGIONAPC
   add constraint REGIONAPC_PK primary key (REGIONID, EFFECTIVEDATE, VERSIONNO);





create index REGIONAPC_LCX on REGIONAPC (
LASTCHANGED ASC
);





create table REGIONAPCINTERVALS (
   REGIONID             varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   APCVALUE             numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null,
   APCTYPE              numeric(3,0)         null,
   FCASAPCVALUE         numeric(16,6)        null,
   APFVALUE             numeric(16,6)        null
);

alter table REGIONAPCINTERVALS
   add constraint REGIONAPCINTERVALS_PK primary key (REGIONID, EFFECTIVEDATE, VERSIONNO, PERIODID);





create index REGIONAPCINTERVALS_LCX on REGIONAPCINTERVALS (
LASTCHANGED ASC
);





create table REGIONFCASRELAXATION_OCD (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   SERVICETYPE          varchar(10)          not null,
   GLOBAL               numeric(1,0)         not null,
   REQUIREMENT          numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table REGIONFCASRELAXATION_OCD
   add constraint PK_REGIONFCASRELAXATION_OCD primary key (SETTLEMENTDATE, RUNNO, REGIONID, SERVICETYPE, GLOBAL);





create index REGIONFCASRELAXATION_OCD_LCX on REGIONFCASRELAXATION_OCD (
LASTCHANGED ASC
);





create table REGIONSTANDINGDATA (
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   RSOID                varchar(10)          null,
   REGIONALREFERENCEPOINTID varchar(10)          null,
   PEAKTRADINGPERIOD    numeric(3,0)         null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   SCALINGFACTOR        numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table REGIONSTANDINGDATA
   add constraint REGIONSTANDINGDATA_PK primary key (EFFECTIVEDATE, VERSIONNO, REGIONID);





create index REGIONSTANDINGDATA_LCX on REGIONSTANDINGDATA (
LASTCHANGED ASC
);





create table RESDEMANDTRK (
   EFFECTIVEDATE        timestamp(3)             not null,
   REGIONID             varchar(10)          not null,
   OFFERDATE            timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   FILENAME             varchar(40)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(10)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table RESDEMANDTRK
   add constraint RESDEMANDTRK_PK primary key (REGIONID, EFFECTIVEDATE, OFFERDATE, VERSIONNO);





create index RESDEMANDTRK_LCX on RESDEMANDTRK (
LASTCHANGED ASC
);





create table RESERVE (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   REGIONID             varchar(12)          not null,
   PERIODID             numeric(2,0)         not null,
   LOWER5MIN            numeric(6,0)         null,
   LOWER60SEC           numeric(6,0)         null,
   LOWER6SEC            numeric(6,0)         null,
   RAISE5MIN            numeric(6,0)         null,
   RAISE60SEC           numeric(6,0)         null,
   RAISE6SEC            numeric(6,0)         null,
   LASTCHANGED          timestamp(3)             null,
   PASARESERVE          numeric(6,0)         null,
   LOADREJECTIONRESERVEREQ numeric(10,0)        null,
   RAISEREG             numeric(6,0)         null,
   LOWERREG             numeric(6,0)         null,
   LOR1LEVEL            numeric(6,0)         null,
   LOR2LEVEL            numeric(6,0)         null
);

alter table RESERVE
   add constraint RESERVE_PK primary key (SETTLEMENTDATE, REGIONID, VERSIONNO, PERIODID);





create index RESERVE_LCX on RESERVE (
LASTCHANGED ASC
);





create table RESIDUECONTRACTPAYMENTS (
   CONTRACTID           varchar(30)          not null,
   PARTICIPANTID        varchar(10)          not null,
   LASTCHANGED          timestamp(3)             null
);

alter table RESIDUECONTRACTPAYMENTS
   add constraint RESIDUECONTRACTPAYMENTS_PK primary key (CONTRACTID, PARTICIPANTID);





create index RESIDUECONTRACTPAYMENTS_LCX on RESIDUECONTRACTPAYMENTS (
LASTCHANGED ASC
);





create table RESIDUEFILETRK (
   CONTRACTID           varchar(30)          null,
   PARTICIPANTID        varchar(10)          not null,
   LOADDATE             timestamp(3)             not null,
   FILENAME             varchar(40)          null,
   ACKFILENAME          varchar(40)          null,
   STATUS               varchar(10)          null,
   LASTCHANGED          timestamp(3)             null,
   AUCTIONID            varchar(30)          not null
);

alter table RESIDUEFILETRK
   add constraint RESIDUEFILETRK_PK primary key (AUCTIONID, PARTICIPANTID, LOADDATE);





create index RESIDUEFILETRK_NDX_LCHD on RESIDUEFILETRK (
LASTCHANGED ASC
);





create table RESIDUE_BID_TRK (
   CONTRACTID           varchar(30)          null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   BIDLOADDATE          timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null,
   AUCTIONID            varchar(30)          not null
);

alter table RESIDUE_BID_TRK
   add constraint RESIDUE_BID_TRK_PK primary key (AUCTIONID, VERSIONNO, PARTICIPANTID);





create index RESIDUEBID_NDX_LCHD on RESIDUE_BID_TRK (
LASTCHANGED ASC
);





create table RESIDUE_CONTRACTS (
   CONTRACTYEAR         numeric(4,0)         not null,
   QUARTER              numeric(1,0)         not null,
   TRANCHE              numeric(2,0)         not null,
   CONTRACTID           varchar(30)          null,
   STARTDATE            timestamp(3)             null,
   ENDDATE              timestamp(3)             null,
   NOTIFYDATE           timestamp(3)             null,
   AUCTIONDATE          timestamp(3)             null,
   CALCMETHOD           varchar(20)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   NOTIFYPOSTDATE       timestamp(3)             null,
   NOTIFYBY             varchar(15)          null,
   POSTDATE             timestamp(3)             null,
   POSTEDBY             varchar(15)          null,
   LASTCHANGED          timestamp(3)             null,
   DESCRIPTION          varchar(80)          null,
   AUCTIONID            varchar(30)          null
);

alter table RESIDUE_CONTRACTS
   add constraint RESIDUE_CONTRACTS_PK primary key (CONTRACTYEAR, QUARTER, TRANCHE);





create index RESIDUE_CONTRACTS_LCX on RESIDUE_CONTRACTS (
LASTCHANGED ASC
);





create table RESIDUE_CON_DATA (
   CONTRACTID           varchar(30)          not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   UNITSPURCHASED       numeric(17,5)        null,
   LINKPAYMENT          numeric(17,5)        null,
   LASTCHANGED          timestamp(3)             null,
   SECONDARY_UNITS_SOLD numeric(18,8)        null
);

alter table RESIDUE_CON_DATA
   add constraint RESIDUE_CON_DATA_PK primary key (CONTRACTID, VERSIONNO, PARTICIPANTID, INTERCONNECTORID, FROMREGIONID);





create index RESIDUE_CON_DATA_LCX on RESIDUE_CON_DATA (
LASTCHANGED ASC
);





create table RESIDUE_CON_ESTIMATES_TRK (
   CONTRACTID           varchar(30)          not null,
   CONTRACTYEAR         numeric(4,0)         not null,
   QUARTER              numeric(1,0)         not null,
   VALUATIONID          varchar(15)          not null,
   VERSIONNO            numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table RESIDUE_CON_ESTIMATES_TRK
   add constraint RESIDUE_CON_ESTIMATES_TRK_PK primary key (CONTRACTID, CONTRACTYEAR, QUARTER, VALUATIONID);





create index REVCONESTIMATESTRK_NDX_LCHD on RESIDUE_CON_ESTIMATES_TRK (
LASTCHANGED ASC
);




create table RESIDUE_CON_FUNDS (
   CONTRACTID           varchar(30)          not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   DEFAULTUNITS         numeric(5,0)         null,
   ROLLOVERUNITS        numeric(5,0)         null,
   REALLOCATEDUNITS     numeric(5,0)         null,
   UNITSOFFERED         numeric(5,0)         null,
   MEANRESERVEPRICE     numeric(9,2)         null,
   SCALEFACTOR          numeric(8,5)         null,
   ACTUALRESERVEPRICE   numeric(9,2)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table RESIDUE_CON_FUNDS
   add constraint RESIDUE_CON_FUNDS_PK primary key (CONTRACTID, INTERCONNECTORID, FROMREGIONID);





create index RESIDUE_CON_FUNDS_LCX on RESIDUE_CON_FUNDS (
LASTCHANGED ASC
);





create table RESIDUE_FUNDS_BID (
   CONTRACTID           varchar(30)          not null,
   PARTICIPANTID        varchar(10)          not null,
   LOADDATE             timestamp(3)             not null,
   OPTIONID             numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   UNITS                numeric(5,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table RESIDUE_FUNDS_BID
   add constraint RESIDUE_FUNDS_BID_PK primary key (CONTRACTID, PARTICIPANTID, LOADDATE, OPTIONID, INTERCONNECTORID, FROMREGIONID);





create index RESIDUE_FUNDS_BID_LCX on RESIDUE_FUNDS_BID (
LASTCHANGED ASC
);





create table RESIDUE_PRICE_BID (
   CONTRACTID           varchar(30)          null,
   PARTICIPANTID        varchar(10)          not null,
   LOADDATE             timestamp(3)             not null,
   OPTIONID             numeric(3,0)         not null,
   BIDPRICE             numeric(17,5)        null,
   LASTCHANGED          timestamp(3)             null,
   AUCTIONID            varchar(30)          not null
);

alter table RESIDUE_PRICE_BID
   add constraint RESIDUE_PRICE_BID_PK primary key (AUCTIONID, PARTICIPANTID, LOADDATE, OPTIONID);





create index RESIDUE_PRICE_BID_LCX on RESIDUE_PRICE_BID (
LASTCHANGED ASC
);





create table RESIDUE_PRICE_FUNDS_BID (
   CONTRACTID           varchar(30)          not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   UNITS                numeric(5,0)         null,
   BIDPRICE             numeric(17,5)        null,
   LINKEDBIDFLAG        numeric(6,0)         not null,
   AUCTIONID            varchar(30)          not null,
   LASTCHANGED          timestamp(3)             null
);

alter table RESIDUE_PRICE_FUNDS_BID
   add constraint RESIDUE_PRICE_FUNDS_BID_PK primary key (AUCTIONID, CONTRACTID, INTERCONNECTORID, FROMREGIONID, LINKEDBIDFLAG);





create index RESIDUE_PRICE_FUNDS_BID_LCX on RESIDUE_PRICE_FUNDS_BID (
LASTCHANGED ASC
);





create table RESIDUE_PUBLIC_DATA (
   CONTRACTID           varchar(30)          not null,
   VERSIONNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   UNITSOFFERED         numeric(5,0)         null,
   UNITSSOLD            numeric(16,6)        null,
   CLEARINGPRICE        numeric(17,5)        null,
   RESERVEPRICE         numeric(17,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table RESIDUE_PUBLIC_DATA
   add constraint RESIDUE_PUBLIC_DATA_PK primary key (CONTRACTID, VERSIONNO, INTERCONNECTORID, FROMREGIONID);





create index RESIDUE_PUBLIC_DATA_LCX on RESIDUE_PUBLIC_DATA (
LASTCHANGED ASC
);





create table RESIDUE_TRK (
   CONTRACTID           varchar(30)          null,
   VERSIONNO            numeric(3,0)         not null,
   RUNDATE              timestamp(3)             null,
   AUTHORISEDDATE       timestamp(3)             null,
   AUTHORISEDBY         varchar(15)          null,
   POSTDATE             timestamp(3)             null,
   POSTEDBY             varchar(15)          null,
   LASTCHANGED          timestamp(3)             null,
   STATUS               varchar(15)          null,
   AUCTIONID            varchar(30)          not null
);

alter table RESIDUE_TRK
   add constraint RESIDUE_TRK_PK primary key (AUCTIONID, VERSIONNO);





create index RESIDUETRK_NDX_LCHD on RESIDUE_TRK (
LASTCHANGED ASC
);





create table ROOFTOP_PV_ACTUAL (
   INTERVAL_DATETIME    timestamp(3)             not null,
   TYPE                 varchar(20)          not null,
   REGIONID             varchar(20)          not null,
   POWER                numeric(12,3)        null,
   QI                   numeric(2,1)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table ROOFTOP_PV_ACTUAL
   add constraint ROOFTOP_PV_ACTUAL_PK primary key (INTERVAL_DATETIME, TYPE, REGIONID);





create table ROOFTOP_PV_FORECAST (
   VERSION_DATETIME     timestamp(3)             not null,
   REGIONID             varchar(20)          not null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   POWERMEAN            numeric(12,3)        null,
   POWERPOE50           numeric(12,3)        null,
   POWERPOELOW          numeric(12,3)        null,
   POWERPOEHIGH         numeric(12,3)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table ROOFTOP_PV_FORECAST
   add constraint ROOFTOP_PV_FORECAST_PK primary key (VERSION_DATETIME, INTERVAL_DATETIME, REGIONID);





create table SECDEPOSIT_INTEREST_RATE (
   INTEREST_ACCT_ID     varchar(20)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSION_DATETIME     timestamp(3)             not null,
   INTEREST_RATE        numeric(18,8)        null
);

alter table SECDEPOSIT_INTEREST_RATE
   add constraint SECDEPOSIT_INTEREST_RATE_PK primary key (INTEREST_ACCT_ID, EFFECTIVEDATE, VERSION_DATETIME);





create table SECDEPOSIT_PROVISION (
   SECURITY_DEPOSIT_ID  varchar(20)          not null,
   PARTICIPANTID        varchar(20)          not null,
   TRANSACTION_DATE     timestamp(3)             null,
   MATURITY_CONTRACTYEAR numeric(4,0)         null,
   MATURITY_WEEKNO      numeric(3,0)         null,
   AMOUNT               numeric(18,8)        null,
   INTEREST_RATE        numeric(18,8)        null,
   INTEREST_CALC_TYPE   varchar(20)          null,
   INTEREST_ACCT_ID     varchar(20)          null
);

alter table SECDEPOSIT_PROVISION
   add constraint SECDEPOSIT_PROVISION_PK primary key (SECURITY_DEPOSIT_ID, PARTICIPANTID);





create table SETAGCPAYMENT (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONTRACTID           varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   DUID                 varchar(10)          null,
   REGIONID             varchar(10)          null,
   TLF                  numeric(7,5)         null,
   EBP                  numeric(15,5)        null,
   RRP                  numeric(15,5)        null,
   CLEAREDMW            numeric(15,5)        null,
   INITIALMW            numeric(15,5)        null,
   ENABLINGPAYMENT      numeric(15,5)        null,
   CONTRACTVERSIONNO    numeric(3,0)         null,
   OFFERDATE            timestamp(3)             null,
   OFFERVERSIONNO       numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETAGCPAYMENT
   add constraint SETAGCPAYMENT_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, CONTRACTID, PERIODID);





create index SETAGCPAYMENT_NDX2 on SETAGCPAYMENT (
PARTICIPANTID ASC
);





create index SETAGCPAYMENT_LCX on SETAGCPAYMENT (
LASTCHANGED ASC
);





create table SETAGCRECOVERY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONTRACTID           varchar(10)          null,
   PERIODID             numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   ENABLINGPAYMENT      numeric(15,5)        null,
   PARTICIPANTDEMAND    numeric(15,5)        null,
   REGIONDEMAND         numeric(15,5)        null,
   ENABLINGRECOVERY     numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   ENABLINGRECOVERY_GEN numeric(15,5)        null,
   PARTICIPANTDEMAND_GEN numeric(15,5)        null,
   REGIONDEMAND_GEN     numeric(15,5)        null
);

alter table SETAGCRECOVERY
   add constraint SETAGCRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, PERIODID, REGIONID);





create index SETAGCRECOVERY_LCX on SETAGCRECOVERY (
LASTCHANGED ASC
);





create table SETAPCCOMPENSATION (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   APCCOMPENSATION      numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETAPCCOMPENSATION
   add constraint SETAPCCOMPENSATION_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, REGIONID, PERIODID);





create index SETAPCCOMPENSATION_LCX on SETAPCCOMPENSATION (
LASTCHANGED ASC
);





create table SETAPCRECOVERY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   TOTALCOMPENSATION    numeric(15,5)        null,
   PARTICIPANTDEMAND    numeric(15,5)        null,
   REGIONDEMAND         numeric(15,5)        null,
   APCRECOVERY          numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETAPCRECOVERY
   add constraint SETAPCRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, REGIONID, PERIODID);





create index SETAPCRECOVERY_LCX on SETAPCRECOVERY (
LASTCHANGED ASC
);





create table SETCFG_PARTICIPANT_MPF (
   PARTICIPANTID        varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTCATEGORYID varchar(10)          not null,
   CONNECTIONPOINTID    varchar(10)          not null,
   MPF                  numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETCFG_PARTICIPANT_MPF
   add constraint SETCFG_PARTICIPANT_MPF_PK primary key (PARTICIPANTID, EFFECTIVEDATE, VERSIONNO, PARTICIPANTCATEGORYID, CONNECTIONPOINTID);





create index SETCFG_PARTI_MPF_LCHD_IDX on SETCFG_PARTICIPANT_MPF (
LASTCHANGED ASC
);





create table SETCFG_PARTICIPANT_MPFTRK (
   PARTICIPANTID        varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETCFG_PARTICIPANT_MPFTRK
   add constraint SETCFG_PARTICIPANT_MPFTRK_PK primary key (PARTICIPANTID, EFFECTIVEDATE, VERSIONNO);





create index SETCFG_PARTI_MPFTRK_LCHD_IDX on SETCFG_PARTICIPANT_MPFTRK (
LASTCHANGED ASC
);





create table SETCPDATA (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(10,0)        not null,
   PERIODID             numeric(10,0)        not null,
   PARTICIPANTID        varchar(10)          not null,
   TCPID                varchar(10)          not null,
   REGIONID             varchar(10)          null,
   IGENERGY             numeric(16,6)        null,
   XGENERGY             numeric(16,6)        null,
   INENERGY             numeric(16,6)        null,
   XNENERGY             numeric(16,6)        null,
   IPOWER               numeric(16,6)        null,
   XPOWER               numeric(16,6)        null,
   RRP                  numeric(20,5)        null,
   EEP                  numeric(16,6)        null,
   TLF                  numeric(7,5)         null,
   CPRRP                numeric(16,6)        null,
   CPEEP                numeric(16,6)        null,
   TA                   numeric(16,6)        null,
   EP                   numeric(16,6)        null,
   APC                  numeric(16,6)        null,
   RESC                 numeric(16,6)        null,
   RESP                 numeric(16,6)        null,
   METERRUNNO           numeric(10,0)        null,
   LASTCHANGED          timestamp(3)             null,
   HOSTDISTRIBUTOR      varchar(10)          null,
   MDA                  varchar(10)          not null
);

alter table SETCPDATA
   add constraint SETCPDATA_PK primary key (SETTLEMENTDATE, VERSIONNO, PERIODID, PARTICIPANTID, TCPID, MDA);





create index SETCPDATA_NDX2 on SETCPDATA (
PARTICIPANTID ASC
);





create index SETCPDATA_LCX on SETCPDATA (
LASTCHANGED ASC
);





create table SETCPDATAREGION (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(22,10)       not null,
   PERIODID             numeric(22,10)       not null,
   REGIONID             varchar(10)          not null,
   SUMIGENERGY          numeric(27,5)        null,
   SUMXGENERGY          numeric(27,5)        null,
   SUMINENERGY          numeric(27,5)        null,
   SUMXNENERGY          numeric(27,5)        null,
   SUMIPOWER            numeric(22,0)        null,
   SUMXPOWER            numeric(22,0)        null,
   LASTCHANGED          timestamp(3)             null,
   SUMEP                numeric(15,5)        null
);

alter table SETCPDATAREGION
   add constraint SETCPDATAREGION_PK primary key (SETTLEMENTDATE, VERSIONNO, PERIODID, REGIONID);





create index SETCPDATAREGION_LCX on SETCPDATAREGION (
LASTCHANGED ASC
);





create table SETFCASCOMP (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   DUID                 varchar(10)          not null,
   REGIONID             varchar(10)          null,
   PERIODID             numeric(3,0)         not null,
   CCPRICE              numeric(15,5)        null,
   CLEAREDMW            numeric(15,5)        null,
   UNCONSTRAINEDMW      numeric(15,5)        null,
   EBP                  numeric(15,5)        null,
   TLF                  numeric(7,5)         null,
   RRP                  numeric(15,5)        null,
   EXCESSGEN            numeric(15,5)        null,
   FCASCOMP             numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETFCASCOMP
   add constraint SETFCASCOMP_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, DUID, PERIODID);





create index SETFCASCOMP_LCX on SETFCASCOMP (
LASTCHANGED ASC
);





create table SETFCASRECOVERY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   DUID                 varchar(10)          null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   FCASCOMP             numeric(15,5)        null,
   PARTICIPANTDEMAND    numeric(15,5)        null,
   REGIONDEMAND         numeric(15,5)        null,
   FCASRECOVERY         numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   FCASRECOVERY_GEN     numeric(15,5)        null,
   PARTICIPANTDEMAND_GEN numeric(15,5)        null,
   REGIONDEMAND_GEN     numeric(15,5)        null
);

alter table SETFCASRECOVERY
   add constraint SETFCASRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, REGIONID, PERIODID);





create index SETFCASRECOVERY_LCX on SETFCASRECOVERY (
LASTCHANGED ASC
);





create table SETFCASREGIONRECOVERY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   BIDTYPE              varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   GENERATORREGIONENERGY numeric(16,6)        null,
   CUSTOMERREGIONENERGY numeric(16,6)        null,
   REGIONRECOVERY       numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETFCASREGIONRECOVERY
   add constraint SETFCASREGIONRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, BIDTYPE, REGIONID, PERIODID);





create index SETFCASREGIONRECOVERY_NDX_LCHD on SETFCASREGIONRECOVERY (
LASTCHANGED ASC
);





create table SETGENDATA (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(10,0)        not null,
   PERIODID             numeric(10,0)        not null,
   PARTICIPANTID        varchar(10)          null,
   STATIONID            varchar(10)          not null,
   DUID                 varchar(10)          not null,
   GENSETID             varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   GENERGY              numeric(16,6)        null,
   AENERGY              numeric(16,6)        null,
   GPOWER               numeric(16,6)        null,
   APOWER               numeric(16,6)        null,
   RRP                  numeric(20,5)        null,
   EEP                  numeric(16,6)        null,
   TLF                  numeric(7,5)         null,
   CPRRP                numeric(16,6)        null,
   CPEEP                numeric(16,6)        null,
   NETENERGY            numeric(16,6)        null,
   ENERGYCOST           numeric(16,6)        null,
   EXCESSENERGYCOST     numeric(16,6)        null,
   APC                  numeric(16,6)        null,
   RESC                 numeric(16,6)        null,
   RESP                 numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null,
   EXPENERGY            numeric(15,6)        null,
   EXPENERGYCOST        numeric(15,6)        null,
   METERRUNNO           numeric(6,0)         null,
   MDA                  varchar(10)          null,
   SECONDARY_TLF        numeric(7,5)         null
);

alter table SETGENDATA
   add constraint SETGENDATA_PK primary key (SETTLEMENTDATE, VERSIONNO, REGIONID, STATIONID, DUID, GENSETID, PERIODID);





create index SETGENDATA_NDX2 on SETGENDATA (
PARTICIPANTID ASC
);





create index SETGENDATA_LCX on SETGENDATA (
LASTCHANGED ASC
);





create table SETGENDATAREGION (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(22,10)       not null,
   PERIODID             numeric(22,10)       not null,
   REGIONID             varchar(10)          not null,
   GENERGY              numeric(22,0)        null,
   AENERGY              numeric(22,0)        null,
   GPOWER               numeric(22,0)        null,
   APOWER               numeric(22,0)        null,
   NETENERGY            numeric(27,5)        null,
   ENERGYCOST           numeric(27,5)        null,
   EXCESSENERGYCOST     numeric(27,5)        null,
   EXPENERGY            numeric(27,6)        null,
   EXPENERGYCOST        numeric(27,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETGENDATAREGION
   add constraint SETGENDATAREGION_PK primary key (SETTLEMENTDATE, VERSIONNO, PERIODID, REGIONID);





create index SETGENDATAREGION_LCX on SETGENDATAREGION (
LASTCHANGED ASC
);





create table SETGOVPAYMENT (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONTRACTID           varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   DUID                 varchar(10)          null,
   REGIONID             varchar(10)          null,
   TLF                  numeric(7,5)         null,
   RL6SECRAISE          numeric(15,5)        null,
   RL60SECRAISE         numeric(15,5)        null,
   RL6SECLOWER          numeric(15,5)        null,
   RL60SECLOWER         numeric(15,5)        null,
   DEADBANDUP           numeric(7,5)         null,
   DEADBANDDOWN         numeric(7,5)         null,
   R6                   numeric(15,5)        null,
   R60                  numeric(15,5)        null,
   L6                   numeric(15,5)        null,
   L60                  numeric(15,5)        null,
   RL6                  numeric(15,5)        null,
   RL60                 numeric(15,5)        null,
   LL6                  numeric(15,5)        null,
   LL60                 numeric(15,5)        null,
   ENABLING6RPAYMENT    numeric(15,5)        null,
   ENABLING60RPAYMENT   numeric(15,5)        null,
   ENABLING6LPAYMENT    numeric(15,5)        null,
   ENABLING60LPAYMENT   numeric(15,5)        null,
   CONTRACTVERSIONNO    numeric(3,0)         null,
   OFFERDATE            timestamp(3)             null,
   OFFERVERSIONNO       numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETGOVPAYMENT
   add constraint SETGOVPAYMENT_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, CONTRACTID, PERIODID);





create index SETGOVPAYMENT_NDX2 on SETGOVPAYMENT (
PARTICIPANTID ASC
);





create index SETGOVPAYMENT_LCX on SETGOVPAYMENT (
LASTCHANGED ASC
);





create table SETGOVRECOVERY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONTRACTID           varchar(10)          null,
   PERIODID             numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   ENABLING6RPAYMENT    numeric(15,5)        null,
   ENABLING60RPAYMENT   numeric(15,5)        null,
   ENABLING6LPAYMENT    numeric(15,5)        null,
   ENABLING60LPAYMENT   numeric(15,5)        null,
   PARTICIPANTDEMAND    numeric(15,5)        null,
   REGIONDEMAND         numeric(15,5)        null,
   ENABLING6RRECOVERY   numeric(15,5)        null,
   ENABLING60RRECOVERY  numeric(15,5)        null,
   ENABLING6LRECOVERY   numeric(15,5)        null,
   ENABLING60LRECOVERY  numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   ENABLING6LRECOVERY_GEN numeric(15,5)        null,
   ENABLING6RRECOVERY_GEN numeric(15,5)        null,
   ENABLING60LRECOVERY_GEN numeric(15,5)        null,
   ENABLING60RRECOVERY_GEN numeric(15,5)        null,
   PARTICIPANTDEMAND_GEN numeric(15,5)        null,
   REGIONDEMAND_GEN     numeric(15,5)        null
);

alter table SETGOVRECOVERY
   add constraint SETGOVRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, PERIODID, REGIONID);





create index SETGOVRECOVERY_LCX on SETGOVRECOVERY (
LASTCHANGED ASC
);





create table SETINTERVENTION (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   CONTRACTID           varchar(10)          null,
   CONTRACTVERSION      numeric(3,0)         null,
   PARTICIPANTID        varchar(10)          null,
   REGIONID             varchar(10)          null,
   DUID                 varchar(10)          not null,
   RCF                  char(1)              null,
   INTERVENTIONPAYMENT  numeric(12,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETINTERVENTION
   add constraint SETINTERVENTION_PK primary key (SETTLEMENTDATE, VERSIONNO, DUID, PERIODID);





create index SETINTERVENTION_LCX on SETINTERVENTION (
LASTCHANGED ASC
);





create table SETINTERVENTIONRECOVERY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   CONTRACTID           varchar(10)          not null,
   RCF                  char(1)              null,
   PARTICIPANTID        varchar(10)          not null,
   PARTICIPANTDEMAND    numeric(12,5)        null,
   TOTALDEMAND          numeric(12,5)        null,
   INTERVENTIONPAYMENT  numeric(12,5)        null,
   INTERVENTIONAMOUNT   numeric(12,5)        null,
   LASTCHANGED          timestamp(3)             null,
   REGIONID             varchar(10)          null
);

alter table SETINTERVENTIONRECOVERY
   add constraint SETINTERVENTIONRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, CONTRACTID, PARTICIPANTID, PERIODID);





create index SETINTERVENTIONRECOVERY_LCX on SETINTERVENTIONRECOVERY (
LASTCHANGED ASC
);





create table SETINTRAREGIONRESIDUES (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3)           not null,
   PERIODID             numeric(3)           not null,
   REGIONID             varchar(10)          not null,
   EP                   numeric(15,5)        null,
   EC                   numeric(15,5)        null,
   RRP                  numeric(15,5)        null,
   EXP                  numeric(15,5)        null,
   IRSS                 numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETINTRAREGIONRESIDUES
   add constraint PK_SETINTRAREGIONRESIDUES primary key (SETTLEMENTDATE, RUNNO, PERIODID, REGIONID);





create index SETINTRAREGIONRESIDUES_LCX on SETINTRAREGIONRESIDUES (
LASTCHANGED ASC
);





create table SETIRAUCSURPLUS (
   SETTLEMENTDATE       timestamp(3)             not null,
   SETTLEMENTRUNNO      numeric(3,0)         not null,
   CONTRACTID           varchar(10)          not null,
   PERIODID             numeric(2,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   TOTALSURPLUS         numeric(15,5)        null,
   CONTRACTALLOCATION   numeric(8,5)         null,
   SURPLUSVALUE         numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   CSP_DEROGATION_AMOUNT numeric(18,8)        null,
   UNADJUSTED_IRSR      numeric(18,8)        null
);

alter table SETIRAUCSURPLUS
   add constraint SETIRAUCSURPLUS_PK primary key (SETTLEMENTDATE, SETTLEMENTRUNNO, CONTRACTID, INTERCONNECTORID, FROMREGIONID, PARTICIPANTID, PERIODID);





create index SETIRAUCSURPLUS_LCX on SETIRAUCSURPLUS (
LASTCHANGED ASC
);





create table SETIRFMRECOVERY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   IRFMID               varchar(10)          not null,
   IRMFVERSION          numeric(3,0)         null,
   PARTICIPANTID        varchar(10)          not null,
   PARTICIPANTDEMAND    numeric(12,5)        null,
   TOTALTCD             numeric(12,5)        null,
   TOTALTFD             numeric(12,5)        null,
   IRFMAMOUNT           numeric(12,5)        null,
   IRFMPAYMENT          numeric(12,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETIRFMRECOVERY
   add constraint SETIRFMRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, IRFMID, PARTICIPANTID, PERIODID);





create index SETIRFMRECOVERY_LCX on SETIRFMRECOVERY (
LASTCHANGED ASC
);





create table SETIRNSPSURPLUS (
   SETTLEMENTDATE       timestamp(3)             not null,
   SETTLEMENTRUNNO      numeric(3,0)         not null,
   CONTRACTID           varchar(10)          not null,
   PERIODID             numeric(2,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   TOTALSURPLUS         numeric(15,5)        null,
   CONTRACTALLOCATION   numeric(8,5)         null,
   SURPLUSVALUE         numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   CSP_DEROGATION_AMOUNT numeric(18,8)        null,
   UNADJUSTED_IRSR      numeric(18,8)        null
);

alter table SETIRNSPSURPLUS
   add constraint SETIRNSPSURPLUS_PK primary key (SETTLEMENTDATE, SETTLEMENTRUNNO, CONTRACTID, INTERCONNECTORID, FROMREGIONID, PARTICIPANTID, PERIODID);





create index SETIRNSPSURPLUS_LCX on SETIRNSPSURPLUS (
LASTCHANGED ASC
);





create table SETIRPARTSURPLUS (
   SETTLEMENTDATE       timestamp(3)             not null,
   SETTLEMENTRUNNO      numeric(3,0)         not null,
   CONTRACTID           varchar(10)          not null,
   PERIODID             numeric(2,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   TOTALSURPLUS         numeric(15,5)        null,
   CONTRACTALLOCATION   numeric(8,5)         null,
   SURPLUSVALUE         numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   CSP_DEROGATION_AMOUNT numeric(18,8)        null,
   UNADJUSTED_IRSR      numeric(18,8)        null
);

alter table SETIRPARTSURPLUS
   add constraint SETIRPARTSURPLUS_PK primary key (SETTLEMENTDATE, SETTLEMENTRUNNO, CONTRACTID, INTERCONNECTORID, FROMREGIONID, PARTICIPANTID, PERIODID);





create index SETIRPARTSURPLUS_LCX on SETIRPARTSURPLUS (
LASTCHANGED ASC
);





create table SETIRSURPLUS (
   SETTLEMENTDATE       timestamp(3)             not null,
   SETTLEMENTRUNNO      numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   MWFLOW               numeric(15,6)        null,
   LOSSFACTOR           numeric(15,5)        null,
   SURPLUSVALUE         numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   CSP_DEROGATION_AMOUNT numeric(18,8)        null,
   UNADJUSTED_IRSR      numeric(18,8)        null
);

alter table SETIRSURPLUS
   add constraint SETIRSURPLUS_PK primary key (SETTLEMENTDATE, SETTLEMENTRUNNO, PERIODID, INTERCONNECTORID, REGIONID);





create index SETIRSURPLUS_LCX on SETIRSURPLUS (
LASTCHANGED ASC
);





create table SETLSHEDPAYMENT (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONTRACTID           varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   DUID                 varchar(10)          null,
   REGIONID             varchar(10)          null,
   TLF                  numeric(7,5)         null,
   RRP                  numeric(15,5)        null,
   LSEPRICE             numeric(15,5)        null,
   MCPPRICE             numeric(15,5)        null,
   LSCR                 numeric(4,0)         null,
   LSEPAYMENT           numeric(15,5)        null,
   CCPAYMENT            numeric(15,5)        null,
   CONSTRAINEDMW        numeric(15,5)        null,
   UNCONSTRAINEDMW      numeric(15,5)        null,
   ALS                  numeric(15,5)        null,
   INITIALDEMAND        numeric(15,5)        null,
   FINALDEMAND          numeric(15,5)        null,
   CONTRACTVERSIONNO    numeric(3,0)         null,
   OFFERDATE            timestamp(3)             null,
   OFFERVERSIONNO       numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null,
   AVAILABILITYPAYMENT  numeric(16,6)        null
);

alter table SETLSHEDPAYMENT
   add constraint SETLSHEDPAYMENT_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, CONTRACTID, PERIODID);





create index SETLSHEDPAYMENT_NDX2 on SETLSHEDPAYMENT (
PARTICIPANTID ASC
);





create index SETLSHEDPAYMENT_LCX on SETLSHEDPAYMENT (
LASTCHANGED ASC
);





create table SETLSHEDRECOVERY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONTRACTID           varchar(10)          null,
   PERIODID             numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   LSEPAYMENT           numeric(15,5)        null,
   CCPAYMENT            numeric(15,5)        null,
   PARTICIPANTDEMAND    numeric(15,5)        null,
   REGIONDEMAND         numeric(15,5)        null,
   LSERECOVERY          numeric(15,5)        null,
   CCRECOVERY           numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   LSERECOVERY_GEN      numeric(15,5)        null,
   CCRECOVERY_GEN       numeric(15,5)        null,
   PARTICIPANTDEMAND_GEN numeric(15,5)        null,
   REGIONDEMAND_GEN     numeric(15,5)        null,
   AVAILABILITYRECOVERY numeric(16,6)        null,
   AVAILABILITYRECOVERY_GEN numeric(16,6)        null
);

alter table SETLSHEDRECOVERY
   add constraint SETLSHEDRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, PERIODID, REGIONID);





create index SETLSHEDRECOVERY_LCX on SETLSHEDRECOVERY (
LASTCHANGED ASC
);





create table SETLULOADPAYMENT (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONTRACTID           varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   DUID                 varchar(10)          null,
   REGIONID             varchar(10)          null,
   TLF                  numeric(7,5)         null,
   EBP                  numeric(15,5)        null,
   RRP                  numeric(15,5)        null,
   ENABLINGPRICE        numeric(15,5)        null,
   USAGEPRICE           numeric(15,5)        null,
   CCPRICE              numeric(15,5)        null,
   BLOCKSIZE            numeric(4,0)         null,
   ACR                  numeric(6,2)         null,
   UNITOUTPUT           numeric(15,5)        null,
   UNITEXCESSGEN        numeric(15,5)        null,
   ENABLINGPAYMENT      numeric(15,5)        null,
   USAGEPAYMENT         numeric(15,5)        null,
   COMPENSATIONPAYMENT  numeric(15,5)        null,
   CONTRACTVERSIONNO    numeric(3,0)         null,
   OFFERDATE            timestamp(3)             null,
   OFFERVERSIONNO       numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETLULOADPAYMENT
   add constraint SETLULOADPAYMENT_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, CONTRACTID, PERIODID);





create index SETLULOADPAYMENT_NDX2 on SETLULOADPAYMENT (
PARTICIPANTID ASC
);





create index SETLULOADPAYMENT_LCX on SETLULOADPAYMENT (
LASTCHANGED ASC
);





create table SETLULOADRECOVERY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONTRACTID           varchar(10)          null,
   PERIODID             numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   ENABLINGPAYMENT      numeric(15,5)        null,
   USAGEPAYMENT         numeric(15,5)        null,
   COMPENSATIONPAYMENT  numeric(15,5)        null,
   PARTICIPANTDEMAND    numeric(15,5)        null,
   REGIONDEMAND         numeric(15,5)        null,
   ENABLINGRECOVERY     numeric(15,5)        null,
   USAGERECOVERY        numeric(15,5)        null,
   COMPENSATIONRECOVERY numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   ENABLINGRECOVERY_GEN numeric(15,5)        null,
   USAGERECOVERY_GEN    numeric(15,5)        null,
   COMPENSATIONRECOVERY_GEN numeric(15,5)        null,
   PARTICIPANTDEMAND_GEN numeric(15,5)        null,
   REGIONDEMAND_GEN     numeric(15,5)        null
);

alter table SETLULOADRECOVERY
   add constraint SETLULOADRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, PERIODID, REGIONID);





create index SETLULOADRECOVERY_LCX on SETLULOADRECOVERY (
LASTCHANGED ASC
);





create table SETLUNLOADPAYMENT (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONTRACTID           varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   DUID                 varchar(10)          null,
   REGIONID             varchar(10)          null,
   TLF                  numeric(7,5)         null,
   EBP                  numeric(15,5)        null,
   RRP                  numeric(15,5)        null,
   ENABLINGPRICE        numeric(15,5)        null,
   USAGEPRICE           numeric(15,5)        null,
   CCPRICE              numeric(15,5)        null,
   CLEAREDMW            numeric(15,5)        null,
   UNCONSTRAINEDMW      numeric(15,5)        null,
   CONTROLRANGE         numeric(4,0)         null,
   ENABLINGPAYMENT      numeric(15,5)        null,
   USAGEPAYMENT         numeric(15,5)        null,
   COMPENSATIONPAYMENT  numeric(15,5)        null,
   CONTRACTVERSIONNO    numeric(3,0)         null,
   OFFERDATE            timestamp(3)             null,
   OFFERVERSIONNO       numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETLUNLOADPAYMENT
   add constraint SETLUNLOADPAYMENT_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, CONTRACTID, PERIODID);





create index SETLUNLOADPAYMENT_NDX2 on SETLUNLOADPAYMENT (
PARTICIPANTID ASC
);





create index SETLUNLOADPAYMENT_LCX on SETLUNLOADPAYMENT (
LASTCHANGED ASC
);





create table SETLUNLOADRECOVERY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONTRACTID           varchar(10)          null,
   PERIODID             numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   ENABLINGPAYMENT      numeric(15,5)        null,
   USAGEPAYMENT         numeric(15,5)        null,
   COMPENSATIONPAYMENT  numeric(15,5)        null,
   PARTICIPANTDEMAND    numeric(15,5)        null,
   REGIONDEMAND         numeric(15,5)        null,
   ENABLINGRECOVERY     numeric(15,5)        null,
   USAGERECOVERY        numeric(15,5)        null,
   COMPENSATIONRECOVERY numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   ENABLINGRECOVERY_GEN numeric(15,5)        null,
   USAGERECOVERY_GEN    numeric(15,5)        null,
   COMPENSATIONRECOVERY_GEN numeric(15,5)        null,
   PARTICIPANTDEMAND_GEN numeric(15,5)        null,
   REGIONDEMAND_GEN     numeric(15,5)        null
);

alter table SETLUNLOADRECOVERY
   add constraint SETLUNLOADRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, PERIODID, REGIONID);





create index SETLUNLOADRECOVERY_LCX on SETLUNLOADRECOVERY (
LASTCHANGED ASC
);





create table SETMARKETFEES (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   MARKETFEEID          varchar(10)          not null,
   MARKETFEEVALUE       numeric(15,5)        null,
   ENERGY               numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null,
   PARTICIPANTCATEGORYID varchar(10)          not null
);

alter table SETMARKETFEES
   add constraint SETMARKETFEES_PK primary key (SETTLEMENTDATE, RUNNO, PARTICIPANTID, MARKETFEEID, PARTICIPANTCATEGORYID, PERIODID);





create index SETMARKETFEES_LCX on SETMARKETFEES (
LASTCHANGED ASC
);





create table SETREALLOCATIONS (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   REALLOCATIONID       varchar(20)          not null,
   REALLOCATIONVALUE    numeric(15,5)        null,
   ENERGY               numeric(15,5)        null,
   RRP                  numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETREALLOCATIONS
   add constraint SETREALLOCATIONS_PK primary key (SETTLEMENTDATE, RUNNO, PERIODID, PARTICIPANTID, REALLOCATIONID);





create index SETREALLOCATIONS_LCX on SETREALLOCATIONS (
LASTCHANGED ASC
);





create table SETRESERVERECOVERY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   CONTRACTID           varchar(10)          not null,
   RCF                  char(1)              null,
   SPOTPAYMENT          numeric(12,5)        null,
   PARTICIPANTID        varchar(10)          not null,
   PARTICIPANTDEMAND    numeric(12,5)        null,
   TOTALDEMAND          numeric(12,5)        null,
   RESERVEPAYMENT       numeric(12,5)        null,
   RESERVEAMOUNT        numeric(12,5)        null,
   LASTCHANGED          timestamp(3)             null,
   REGIONID             varchar(10)          null
);

alter table SETRESERVERECOVERY
   add constraint SETRESERVERECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, CONTRACTID, PARTICIPANTID, PERIODID);





create index SETRESERVERECOVERY_LCX on SETRESERVERECOVERY (
LASTCHANGED ASC
);





create table SETRESERVETRADER (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   CONTRACTID           varchar(10)          null,
   CONTRACTVERSION      numeric(3,0)         null,
   PARTICIPANTID        varchar(10)          null,
   REGIONID             varchar(10)          null,
   DUID                 varchar(10)          not null,
   RCF                  char(1)              null,
   UNITAVAIL            numeric(6,2)         null,
   CPA                  numeric(12,5)        null,
   CPE                  numeric(12,5)        null,
   CPU                  numeric(12,5)        null,
   CPTOTAL              numeric(12,5)        null,
   CAPDIFFERENCE        numeric(12,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETRESERVETRADER
   add constraint SETRESERVETRADER_PK primary key (SETTLEMENTDATE, VERSIONNO, DUID, PERIODID);





create index SETRESERVETRADER_LCX on SETRESERVETRADER (
LASTCHANGED ASC
);





create table SETRESTARTPAYMENT (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONTRACTID           varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   REGIONID             varchar(10)          null,
   RESTARTTYPE          numeric(1,0)         null,
   AVAFLAG              numeric(1,0)         null,
   AVAILABILITYPRICE    numeric(15,5)        null,
   TCF                  numeric(1,0)         null,
   AVAILABILITYPAYMENT  numeric(15,5)        null,
   CONTRACTVERSIONNO    numeric(3,0)         null,
   OFFERDATE            timestamp(3)             null,
   OFFERVERSIONNO       numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null,
   ENABLINGPAYMENT      numeric(18,8)        null
);

alter table SETRESTARTPAYMENT
   add constraint SETRESTARTPAYMENT_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, CONTRACTID, PERIODID);






create index SETRESTARTPAYMENT_NDX2 on SETRESTARTPAYMENT (
PARTICIPANTID ASC
);





create index SETRESTARTPAYMENT_LCX on SETRESTARTPAYMENT (
LASTCHANGED ASC
);





create table SETRESTARTRECOVERY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONTRACTID           varchar(10)          null,
   PERIODID             numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   AVAILABILITYPAYMENT  numeric(15,5)        null,
   PARTICIPANTDEMAND    numeric(15,5)        null,
   REGIONDEMAND         numeric(15,5)        null,
   AVAILABILITYRECOVERY numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   AVAILABILITYRECOVERY_GEN numeric(15,5)        null,
   PARTICIPANTDEMAND_GEN numeric(15,5)        null,
   REGIONDEMAND_GEN     numeric(15,5)        null,
   ENABLINGPAYMENT      numeric(18,8)        null,
   ENABLINGRECOVERY     numeric(18,8)        null,
   ENABLINGRECOVERY_GEN numeric(18,8)        null
);

alter table SETRESTARTRECOVERY
   add constraint SETRESTARTRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, PERIODID, REGIONID);





create index SETRESTARTRECOVERY_LCX on SETRESTARTRECOVERY (
LASTCHANGED ASC
);





create table SETRPOWERPAYMENT (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONTRACTID           varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   DUID                 varchar(10)          null,
   REGIONID             varchar(10)          null,
   TLF                  numeric(7,5)         null,
   EBP                  numeric(15,5)        null,
   RRP                  numeric(15,5)        null,
   MVARAPRICE           numeric(15,5)        null,
   MVAREPRICE           numeric(15,5)        null,
   MVARGPRICE           numeric(15,5)        null,
   CCPRICE              numeric(15,5)        null,
   SYNCCOMPENSATION     numeric(1,0)         null,
   MTA                  numeric(15,5)        null,
   MTG                  numeric(15,5)        null,
   BLOCKSIZE            numeric(4,0)         null,
   AVAFLAG              numeric(1,0)         null,
   CLEAREDMW            numeric(15,5)        null,
   UNCONSTRAINEDMW      numeric(15,5)        null,
   AVAILABILITYPAYMENT  numeric(15,5)        null,
   ENABLINGPAYMENT      numeric(15,5)        null,
   CCPAYMENT            numeric(15,5)        null,
   CONTRACTVERSIONNO    numeric(3,0)         null,
   OFFERDATE            timestamp(3)             null,
   OFFERVERSIONNO       numeric(3,0)         null,
   LASTCHANGED          timestamp(3)             null,
   AVAILABILITYPAYMENT_REBATE numeric(18,8)        null
);

alter table SETRPOWERPAYMENT
   add constraint SETRPOWERPAYMENT_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, CONTRACTID, PERIODID);





create index SETRPOWERPAYMENT_LCX on SETRPOWERPAYMENT (
LASTCHANGED ASC
);





create table SETRPOWERRECOVERY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONTRACTID           varchar(10)          null,
   PERIODID             numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   AVAILABILITYPAYMENT  numeric(15,5)        null,
   ENABLINGPAYMENT      numeric(15,5)        null,
   CCPAYMENT            numeric(15,5)        null,
   PARTICIPANTDEMAND    numeric(15,5)        null,
   REGIONDEMAND         numeric(15,5)        null,
   AVAILABILITYRECOVERY numeric(15,5)        null,
   ENABLINGRECOVERY     numeric(15,5)        null,
   CCRECOVERY           numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   AVAILABILITYRECOVERY_GEN numeric(15,5)        null,
   ENABLINGRECOVERY_GEN numeric(15,5)        null,
   CCRECOVERY_GEN       numeric(15,5)        null,
   PARTICIPANTDEMAND_GEN numeric(15,5)        null,
   REGIONDEMAND_GEN     numeric(15,5)        null
);

alter table SETRPOWERRECOVERY
   add constraint SETRPOWERRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, PERIODID, REGIONID);





create index SETRPOWERRECOVERY_LCX on SETRPOWERRECOVERY (
LASTCHANGED ASC
);





create table SETSMALLGENDATA (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   CONNECTIONPOINTID    varchar(20)          not null,
   PERIODID             numeric(3,0)         not null,
   PARTICIPANTID        varchar(20)          not null,
   REGIONID             varchar(20)          null,
   IMPORTENERGY         numeric(18,8)        null,
   EXPORTENERGY         numeric(18,8)        null,
   RRP                  numeric(18,8)        null,
   TLF                  numeric(18,8)        null,
   IMPENERGYCOST        numeric(18,8)        null,
   EXPENERGYCOST        numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETSMALLGENDATA
   add constraint PK_SETSMALLGENDATA primary key (SETTLEMENTDATE, VERSIONNO, CONNECTIONPOINTID, PERIODID, PARTICIPANTID);





create table SETVICBOUNDARYENERGY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   BOUNDARYENERGY       numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETVICBOUNDARYENERGY
   add constraint SETVICBOUNDARYENERGY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, PERIODID);





create index SETVICBOUNDARYENERGY_LCX on SETVICBOUNDARYENERGY (
LASTCHANGED ASC
);





create table SETVICENERGYFIGURES (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   TOTALGENOUTPUT       numeric(15,5)        null,
   TOTALPCSD            numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   TLR                  numeric(15,6)        null,
   MLF                  numeric(15,6)        null
);

alter table SETVICENERGYFIGURES
   add constraint SETVICENERGYFIGURES_PK primary key (SETTLEMENTDATE, VERSIONNO, PERIODID);





create index SETVICENERGYFIGURES_LCX on SETVICENERGYFIGURES (
LASTCHANGED ASC
);





create table SETVICENERGYFLOW (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   NETFLOW              numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SETVICENERGYFLOW
   add constraint SETVICENERGYFLOW_PK primary key (SETTLEMENTDATE, VERSIONNO, PERIODID);





create index SETVICENERGYFLOW_LCX on SETVICENERGYFLOW (
LASTCHANGED ASC
);





create table SET_ANCILLARY_SUMMARY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   SERVICE              varchar(20)          not null,
   PAYMENTTYPE          varchar(20)          not null,
   REGIONID             varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   PAYMENTAMOUNT        numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SET_ANCILLARY_SUMMARY
   add constraint SET_ANCILLARY_SUMMARY_PK primary key (SETTLEMENTDATE, VERSIONNO, SERVICE, PAYMENTTYPE, REGIONID, PERIODID);





create index SET_ANCILLARY_SUMMARY_LCHD_IDX on SET_ANCILLARY_SUMMARY (
LASTCHANGED ASC
);





create table SET_APC_COMPENSATION (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3)           not null,
   APEVENTID            numeric(6)           not null,
   CLAIMID              numeric(6)           not null,
   PARTICIPANTID        varchar(20)          not null,
   PERIODID             numeric(3)           not null,
   COMPENSATION_AMOUNT  numeric(18,8)        null
);

alter table SET_APC_COMPENSATION
   add constraint SET_APC_COMPENSATION_PK primary key (SETTLEMENTDATE, VERSIONNO, APEVENTID, CLAIMID, PARTICIPANTID, PERIODID);





create table SET_APC_RECOVERY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3)           not null,
   APEVENTID            numeric(6)           not null,
   CLAIMID              numeric(6)           not null,
   PARTICIPANTID        varchar(20)          not null,
   PERIODID             numeric(3)           not null,
   REGIONID             varchar(20)          not null,
   RECOVERY_AMOUNT      numeric(18,8)        null,
   REGION_RECOVERY_AMOUNT numeric(18,8)        null
);

alter table SET_APC_RECOVERY
   add constraint SET_APC_RECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, APEVENTID, CLAIMID, PARTICIPANTID, PERIODID, REGIONID);





create table SET_CSP_DEROGATION_AMOUNT (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3)           not null,
   PERIODID             numeric(3)           not null,
   PARTICIPANTID        varchar(10)          not null,
   AMOUNT_ID            varchar(20)          not null,
   DEROGATION_AMOUNT    numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SET_CSP_DEROGATION_AMOUNT
   add constraint SET_CSP_DEROGATION_AMOUNT_PK primary key (SETTLEMENTDATE, VERSIONNO, PERIODID, PARTICIPANTID, AMOUNT_ID);





create index SET_CSP_DEROGATION_AMOUNT_NDX1 on SET_CSP_DEROGATION_AMOUNT (
LASTCHANGED ASC
);





create table SET_CSP_SUPPORTDATA_CONSTRAINT (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3)           not null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   CONSTRAINTID         varchar(20)          not null,
   PERIODID             numeric(3)           not null,
   MARGINALVALUE        numeric(18,8)        null,
   RHS                  numeric(18,8)        null,
   LOWERTUMUT_FACTOR    numeric(18,8)        null,
   UPPERTUMUT_FACTOR    numeric(18,8)        null,
   LOWERTUMUT_CSPA_COEFF numeric(18,8)        null,
   UPPERTUMUT_CSPA_COEFF numeric(18,8)        null,
   ABS_X                numeric(18,8)        null,
   ABS_Y                numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SET_CSP_SUPPORTDATA_CONSTRAINT
   add constraint SET_CSP_SUPPORTDATA_CNSTR_PK primary key (SETTLEMENTDATE, VERSIONNO, INTERVAL_DATETIME, CONSTRAINTID, PERIODID);





create index SET_CSP_SUPPORTDATA_CNSTR_NDX1 on SET_CSP_SUPPORTDATA_CONSTRAINT (
LASTCHANGED ASC
);





create table SET_CSP_SUPPORTDATA_ENERGYDIFF (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3)           not null,
   PERIODID             numeric(3)           not null,
   LOWERTUMUT_SPDP      numeric(18,8)        null,
   UPPERTUMUT_SPDP      numeric(18,8)        null,
   LOWERTUMUT_EVDP      numeric(18,8)        null,
   UPPERTUMUT_EVDP      numeric(18,8)        null,
   FLOW_DIRECTION       varchar(20)          null,
   TOTAL_X              numeric(18,8)        null,
   TOTAL_Y              numeric(18,8)        null,
   LOWERTUMUT_AGE       numeric(18,8)        null,
   UPPERTUMUT_AGE       numeric(18,8)        null,
   EVA                  numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SET_CSP_SUPPORTDATA_ENERGYDIFF
   add constraint SET_CSP_SUPPDATA_ENERGYDF_PK primary key (SETTLEMENTDATE, VERSIONNO, PERIODID);





create index SET_CSP_SUPPDATA_ENERGYDF_NDX1 on SET_CSP_SUPPORTDATA_ENERGYDIFF (
LASTCHANGED ASC
);





create table SET_CSP_SUPPORTDATA_SUBPRICE (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3)           not null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   PERIODID             numeric(3)           null,
   RRP                  numeric(18,8)        null,
   IS_CSP_INTERVAL      numeric(1)           null,
   LOWERTUMUT_TLF       numeric(18,8)        null,
   UPPERTUMUT_TLF       numeric(18,8)        null,
   LOWERTUMUT_PRICE     numeric(18,8)        null,
   UPPERTUMUT_PRICE     numeric(18,8)        null,
   LOWERTUMUT_CSPA_COEFF numeric(18,8)        null,
   UPPERTUMUT_CSPA_COEFF numeric(18,8)        null,
   LOWERTUMUT_SPDP_UNCAPPED numeric(18,8)        null,
   UPPERTUMUT_SPDP_UNCAPPED numeric(18,8)        null,
   LOWERTUMUT_SPDP      numeric(18,8)        null,
   UPPERTUMUT_SPDP      numeric(18,8)        null,
   INTERVAL_ABS_X       numeric(18,8)        null,
   INTERVAL_ABS_Y       numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SET_CSP_SUPPORTDATA_SUBPRICE
   add constraint SET_CSP_SUPPDATA_SUBPRCE_PK primary key (SETTLEMENTDATE, VERSIONNO, INTERVAL_DATETIME);





create index SET_CSP_SUPPDATA_SUBPRCE_NDX1 on SET_CSP_SUPPORTDATA_SUBPRICE (
LASTCHANGED ASC
);





create table SET_FCAS_PAYMENT (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          not null,
   REGIONID             varchar(10)          null,
   PERIODID             numeric(3,0)         not null,
   LOWER6SEC_PAYMENT    numeric(18,8)        null,
   RAISE6SEC_PAYMENT    numeric(18,8)        null,
   LOWER60SEC_PAYMENT   numeric(18,8)        null,
   RAISE60SEC_PAYMENT   numeric(18,8)        null,
   LOWER5MIN_PAYMENT    numeric(18,8)        null,
   RAISE5MIN_PAYMENT    numeric(18,8)        null,
   LOWERREG_PAYMENT     numeric(18,8)        null,
   RAISEREG_PAYMENT     numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SET_FCAS_PAYMENT
   add constraint SET_FCAS_PAYMENT_PK primary key (SETTLEMENTDATE, VERSIONNO, DUID, PERIODID);





create index SET_FCAS_PAYMENT_LCHD_IDX on SET_FCAS_PAYMENT (
LASTCHANGED ASC
);





create table SET_FCAS_RECOVERY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            varchar(3)           not null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   LOWER6SEC_RECOVERY   numeric(18,8)        null,
   RAISE6SEC_RECOVERY   numeric(18,8)        null,
   LOWER60SEC_RECOVERY  numeric(18,8)        null,
   RAISE60SEC_RECOVERY  numeric(18,8)        null,
   LOWER5MIN_RECOVERY   numeric(18,8)        null,
   RAISE5MIN_RECOVERY   numeric(18,8)        null,
   LOWERREG_RECOVERY    numeric(18,8)        null,
   RAISEREG_RECOVERY    numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null,
   LOWER6SEC_RECOVERY_GEN numeric(18,8)        null,
   RAISE6SEC_RECOVERY_GEN numeric(18,8)        null,
   LOWER60SEC_RECOVERY_GEN numeric(18,8)        null,
   RAISE60SEC_RECOVERY_GEN numeric(18,8)        null,
   LOWER5MIN_RECOVERY_GEN numeric(18,8)        null,
   RAISE5MIN_RECOVERY_GEN numeric(18,8)        null,
   LOWERREG_RECOVERY_GEN numeric(18,8)        null,
   RAISEREG_RECOVERY_GEN numeric(18,8)        null
);

alter table SET_FCAS_RECOVERY
   add constraint SET_FCAS_RECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, REGIONID, PERIODID);





create index SET_FCAS_RECOVERY_LCHD_IDX on SET_FCAS_RECOVERY (
LASTCHANGED ASC
);





create table SET_FCAS_REGULATION_TRK (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   CONSTRAINTID         varchar(20)          not null,
   CMPF                 numeric(18,8)        null,
   CRMPF                numeric(18,8)        null,
   RECOVERY_FACTOR_CMPF numeric(18,8)        null,
   RECOVERY_FACTOR_CRMPF numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SET_FCAS_REGULATION_TRK
   add constraint SET_FCAS_REGULATION_TRK_PK primary key (SETTLEMENTDATE, VERSIONNO, INTERVAL_DATETIME, CONSTRAINTID);





create index SET_FCAS_REGUL_TRK_LCHD_IDX on SET_FCAS_REGULATION_TRK (
LASTCHANGED ASC
);





create table SET_MR_PAYMENT (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   MR_CAPACITY          numeric(16,6)        null,
   UNCAPPED_PAYMENT     numeric(16,6)        null,
   CAPPED_PAYMENT       numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SET_MR_PAYMENT
   add constraint SET_MR_PAYMENT_PK primary key (SETTLEMENTDATE, VERSIONNO, REGIONID, DUID, PERIODID);





create index SET_MR_PAYMENT_LCX on SET_MR_PAYMENT (
LASTCHANGED ASC
);





create table SET_MR_RECOVERY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   ARODEF               numeric(16,6)        null,
   NTA                  numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SET_MR_RECOVERY
   add constraint SET_MR_RECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, REGIONID, DUID, PERIODID);





create index SET_MR_RECOVERY_LCX on SET_MR_RECOVERY (
LASTCHANGED ASC
);





create table SET_NMAS_RECOVERY (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   PARTICIPANTID        varchar(20)          not null,
   SERVICE              varchar(10)          not null,
   CONTRACTID           varchar(10)          not null,
   PAYMENTTYPE          varchar(20)          not null,
   REGIONID             varchar(10)          not null,
   RBF                  numeric(18,8)        null,
   PAYMENT_AMOUNT       numeric(18,8)        null,
   PARTICIPANT_ENERGY   numeric(18,8)        null,
   REGION_ENERGY        numeric(18,8)        null,
   RECOVERY_AMOUNT      numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null,
   PARTICIPANT_GENERATION numeric(18,8)        null,
   REGION_GENERATION    numeric(18,8)        null,
   RECOVERY_AMOUNT_CUSTOMER numeric(18,8)        null,
   RECOVERY_AMOUNT_GENERATOR numeric(18,8)        null
);

alter table SET_NMAS_RECOVERY
   add constraint PK_SET_NMAS_RECOVERY primary key (SETTLEMENTDATE, VERSIONNO, PERIODID, PARTICIPANTID, SERVICE, CONTRACTID, PAYMENTTYPE, REGIONID);





create index SET_NMAS_RECOVERY_LCX on SET_NMAS_RECOVERY (
LASTCHANGED ASC
);





create table SET_NMAS_RECOVERY_RBF (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   SERVICE              varchar(10)          not null,
   CONTRACTID           varchar(10)          not null,
   PAYMENTTYPE          varchar(20)          not null,
   REGIONID             varchar(10)          not null,
   RBF                  numeric(18,8)        null,
   PAYMENT_AMOUNT       numeric(18,8)        null,
   RECOVERY_AMOUNT      numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SET_NMAS_RECOVERY_RBF
   add constraint PK_SET_NMAS_RECOVERY_RBF primary key (SETTLEMENTDATE, VERSIONNO, PERIODID, SERVICE, CONTRACTID, PAYMENTTYPE, REGIONID);





create index SET_NMAS_RECOVERY_RBF_LCX on SET_NMAS_RECOVERY_RBF (
LASTCHANGED ASC
);





create table SET_RUN_PARAMETER (
   SETTLEMENTDATE       timestamp(3)             not null,
   VERSIONNO            numeric(3)           not null,
   PARAMETERID          varchar(20)          not null,
   NUMVALUE             numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SET_RUN_PARAMETER
   add constraint PK_SET_RUN_PARAMETER primary key (SETTLEMENTDATE, VERSIONNO, PARAMETERID);





create index SET_RUN_PARAMETER_LCX on SET_RUN_PARAMETER (
LASTCHANGED ASC
);





create table SPDCONNECTIONPOINTCONSTRAINT (
   CONNECTIONPOINTID    varchar(12)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   GENCONID             varchar(20)          not null,
   FACTOR               numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null,
   BIDTYPE              varchar(12)          not null
);

alter table SPDCONNECTIONPOINTCONSTRAINT
   add constraint SPDCONNECTIONPTCONSTRAINT_PK primary key (GENCONID, EFFECTIVEDATE, VERSIONNO, BIDTYPE, CONNECTIONPOINTID);





create index SPDCONNECTIONPOINTCONSTRA_LCX on SPDCONNECTIONPOINTCONSTRAINT (
LASTCHANGED ASC
);





create table SPDINTERCONNECTORCONSTRAINT (
   INTERCONNECTORID     varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   GENCONID             varchar(20)          not null,
   FACTOR               numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SPDINTERCONNECTORCONSTRAINT
   add constraint SPDINTERCONNECTORCONSTRAINT_PK primary key (GENCONID, EFFECTIVEDATE, VERSIONNO, INTERCONNECTORID);





create index SPDINTERCONNECTORCONSTRAI_LCX on SPDINTERCONNECTORCONSTRAINT (
LASTCHANGED ASC
);





create table SPDREGIONCONSTRAINT (
   REGIONID             varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(3,0)         not null,
   GENCONID             varchar(20)          not null,
   FACTOR               numeric(16,6)        null,
   LASTCHANGED          timestamp(3)             null,
   BIDTYPE              varchar(10)          not null
);

alter table SPDREGIONCONSTRAINT
   add constraint SPDREGIONCONSTRAINT_PK primary key (GENCONID, EFFECTIVEDATE, VERSIONNO, REGIONID, BIDTYPE);





create index SPDREGIONCONSTRAINT_LCX on SPDREGIONCONSTRAINT (
LASTCHANGED ASC
);





create table SRA_CASH_SECURITY (
   CASH_SECURITY_ID     varchar(36)          not null,
   PARTICIPANTID        varchar(10)          null,
   PROVISION_DATE       timestamp(3)             null,
   CASH_AMOUNT          numeric(18,8)        null,
   INTEREST_ACCT_ID     varchar(20)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   FINALRETURNDATE      timestamp(3)             null,
   CASH_SECURITY_RETURNED numeric(18,8)        null,
   DELETIONDATE         timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table SRA_CASH_SECURITY
   add constraint SRA_CASH_SECURITY_PK primary key (CASH_SECURITY_ID);





create table SRA_FINANCIAL_AUCPAY_DETAIL (
   SRA_YEAR             numeric(4)           not null,
   SRA_QUARTER          numeric(3)           not null,
   SRA_RUNNO            numeric(3)           not null,
   PARTICIPANTID        varchar(10)          not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   CONTRACTID           varchar(10)          not null,
   MAXIMUM_UNITS        numeric(18,8)        null,
   UNITS_SOLD           numeric(18,8)        null,
   SHORTFALL_UNITS      numeric(18,8)        null,
   RESERVE_PRICE        numeric(18,8)        null,
   CLEARING_PRICE       numeric(18,8)        null,
   PAYMENT_AMOUNT       numeric(18,8)        null,
   SHORTFALL_AMOUNT     numeric(18,8)        null,
   ALLOCATION           numeric(18,8)        null,
   NET_PAYMENT_AMOUNT   numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SRA_FINANCIAL_AUCPAY_DETAIL
   add constraint SRA_FINANCIAL_AUCPAY_DETAIL_PK primary key (SRA_YEAR, SRA_QUARTER, SRA_RUNNO, PARTICIPANTID, INTERCONNECTORID, FROMREGIONID, CONTRACTID);





create table SRA_FINANCIAL_AUCPAY_SUM (
   SRA_YEAR             numeric(4)           not null,
   SRA_QUARTER          numeric(3)           not null,
   SRA_RUNNO            numeric(3)           not null,
   PARTICIPANTID        varchar(10)          not null,
   GROSS_PROCEEDS_AMOUNT numeric(18,8)        null,
   TOTAL_GROSS_PROCEEDS_AMOUNT numeric(18,8)        null,
   SHORTFALL_AMOUNT     numeric(18,8)        null,
   TOTAL_SHORTFALL_AMOUNT numeric(18,8)        null,
   NET_PAYMENT_AMOUNT   numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table SRA_FINANCIAL_AUCPAY_SUM
   add constraint SRA_FINANCIAL_AUCPAY_SUM_PK primary key (SRA_YEAR, SRA_QUARTER, SRA_RUNNO, PARTICIPANTID);





create table SRA_FINANCIAL_AUC_MARDETAIL (
   SRA_YEAR             numeric(4)           not null,
   SRA_QUARTER          numeric(3)           not null,
   SRA_RUNNO            numeric(3)           not null,
   PARTICIPANTID        varchar(10)          not null,
   CASH_SECURITY_ID     varchar(36)          not null,
   RETURNED_AMOUNT      numeric(18,8)        null,
   RETURNED_INTEREST    numeric(18,8)        null
);

alter table SRA_FINANCIAL_AUC_MARDETAIL
   add constraint SRA_FINANCIAL_AUC_MARDETAIL_PK primary key (SRA_YEAR, SRA_QUARTER, SRA_RUNNO, PARTICIPANTID, CASH_SECURITY_ID);





create table SRA_FINANCIAL_AUC_MARGIN (
   SRA_YEAR             numeric(4)           not null,
   SRA_QUARTER          numeric(3)           not null,
   SRA_RUNNO            numeric(3)           not null,
   PARTICIPANTID        varchar(10)          not null,
   TOTAL_CASH_SECURITY  numeric(18,8)        null,
   REQUIRED_MARGIN      numeric(18,8)        null,
   RETURNED_MARGIN      numeric(18,8)        null,
   RETURNED_MARGIN_INTEREST numeric(18,8)        null
);

alter table SRA_FINANCIAL_AUC_MARGIN
   add constraint SRA_FINANCIAL_AUC_MARGIN_PK primary key (SRA_YEAR, SRA_QUARTER, SRA_RUNNO, PARTICIPANTID);





create table SRA_FINANCIAL_AUC_RECEIPTS (
   SRA_YEAR             numeric(4)           not null,
   SRA_QUARTER          numeric(3)           not null,
   SRA_RUNNO            numeric(3)           not null,
   PARTICIPANTID        varchar(10)          not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   CONTRACTID           varchar(10)          not null,
   UNITS_PURCHASED      numeric(18,8)        null,
   CLEARING_PRICE       numeric(18,8)        null,
   RECEIPT_AMOUNT       numeric(18,8)        null,
   LASTCHANGED          timestamp(3)             null,
   PROCEEDS_AMOUNT      numeric(18,8)        null,
   UNITS_SOLD           numeric(18,8)        null
);

alter table SRA_FINANCIAL_AUC_RECEIPTS
   add constraint SRA_FINANCIAL_AUC_RECEIPTS_PK primary key (SRA_YEAR, SRA_QUARTER, SRA_RUNNO, PARTICIPANTID, INTERCONNECTORID, FROMREGIONID, CONTRACTID);





create table SRA_FINANCIAL_RUNTRK (
   SRA_YEAR             numeric(4)           not null,
   SRA_QUARTER          numeric(3)           not null,
   SRA_RUNNO            numeric(3)           not null,
   RUNTYPE              varchar(20)          null,
   RUNDATE              timestamp(3)             null,
   POSTEDDATE           timestamp(3)             null,
   INTEREST_VERSIONNO   numeric(3)           null,
   MAKEUP_VERSIONNO     numeric(3)           null,
   LASTCHANGED          timestamp(3)             null
);

alter table SRA_FINANCIAL_RUNTRK
   add constraint SRA_FINANCIAL_RUNTRK_PK primary key (SRA_YEAR, SRA_QUARTER, SRA_RUNNO);





create table SRA_OFFER_PRODUCT (
   AUCTIONID            varchar(30)          not null,
   PARTICIPANTID        varchar(10)          not null,
   LOADDATE             timestamp(3)             not null,
   OPTIONID             numeric(4)           not null,
   INTERCONNECTORID     varchar(10)          null,
   FROMREGIONID         varchar(10)          null,
   OFFER_QUANTITY       numeric(5)           null,
   OFFER_PRICE          numeric(18,8)        null,
   TRANCHEID            varchar(30)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table SRA_OFFER_PRODUCT
   add constraint SRA_OFFER_PRODUCT_PK primary key (AUCTIONID, PARTICIPANTID, LOADDATE, OPTIONID);





create table SRA_OFFER_PROFILE (
   AUCTIONID            varchar(30)          not null,
   PARTICIPANTID        varchar(10)          not null,
   LOADDATE             timestamp(3)             not null,
   FILENAME             varchar(40)          null,
   ACKFILENAME          varchar(40)          null,
   TRANSACTIONID        varchar(100)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table SRA_OFFER_PROFILE
   add constraint SRA_OFFER_PROFILE_PK primary key (AUCTIONID, PARTICIPANTID, LOADDATE);





create table SRA_PRUDENTIAL_CASH_SECURITY (
   PRUDENTIAL_DATE      timestamp(3)             not null,
   PRUDENTIAL_RUNNO     numeric(8)           not null,
   PARTICIPANTID        varchar(10)          not null,
   CASH_SECURITY_ID     varchar(36)          not null,
   CASH_SECURITY_AMOUNT numeric(18,8)        null
);

alter table SRA_PRUDENTIAL_CASH_SECURITY
   add constraint SRA_PRUDENTIAL_CASH_SEC_PK primary key (PRUDENTIAL_DATE, PRUDENTIAL_RUNNO, PARTICIPANTID, CASH_SECURITY_ID);





create table SRA_PRUDENTIAL_COMP_POSITION (
   PRUDENTIAL_DATE      timestamp(3)             not null,
   PRUDENTIAL_RUNNO     numeric(8)           not null,
   PARTICIPANTID        varchar(10)          not null,
   TRADING_LIMIT        numeric(18,8)        null,
   PRUDENTIAL_EXPOSURE_AMOUNT numeric(18,8)        null,
   TRADING_MARGIN       numeric(18,8)        null
);

alter table SRA_PRUDENTIAL_COMP_POSITION
   add constraint SRA_PRUDENTIAL_COMP_PK primary key (PRUDENTIAL_DATE, PRUDENTIAL_RUNNO, PARTICIPANTID);





create table SRA_PRUDENTIAL_EXPOSURE (
   PRUDENTIAL_DATE      timestamp(3)             not null,
   PRUDENTIAL_RUNNO     numeric(8)           not null,
   PARTICIPANTID        varchar(10)          not null,
   SRA_YEAR             numeric(4)           not null,
   SRA_QUARTER          numeric(3)           not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   MAX_TRANCHE          numeric(2)           null,
   AUCTIONID            varchar(30)          null,
   OFFER_SUBMISSIONTIME timestamp(3)             null,
   AVERAGE_PURCHASE_PRICE numeric(18,8)        null,
   AVERAGE_CANCELLATION_PRICE numeric(18,8)        null,
   CANCELLATION_VOLUME  numeric(18,8)        null,
   TRADING_POSITION     numeric(18,8)        null
);

alter table SRA_PRUDENTIAL_EXPOSURE
   add constraint SRA_PRUDENTIAL_EXPOSURE_PK primary key (PRUDENTIAL_DATE, PRUDENTIAL_RUNNO, PARTICIPANTID, SRA_YEAR, SRA_QUARTER, INTERCONNECTORID, FROMREGIONID);





create table SRA_PRUDENTIAL_RUN (
   PRUDENTIAL_DATE      timestamp(3)             not null,
   PRUDENTIAL_RUNNO     numeric(8)           not null
);

alter table SRA_PRUDENTIAL_RUN
   add constraint SRA_PRUDENTIAL_RUN_PK primary key (PRUDENTIAL_DATE, PRUDENTIAL_RUNNO);





create table STADUALLOC (
   DUID                 varchar(10)          not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   STATIONID            varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   LASTCHANGED          timestamp(3)             null
);

alter table STADUALLOC
   add constraint STADULLOC_PK primary key (STATIONID, EFFECTIVEDATE, VERSIONNO, DUID);





create index STADUALLOC_LCX on STADUALLOC (
LASTCHANGED ASC
);





create index STADUALLOC_NDX2 on STADUALLOC (
STATIONID ASC,
EFFECTIVEDATE ASC,
VERSIONNO ASC
);





create index STADUALLOC_NDX3 on STADUALLOC (
DUID ASC
);





create table STATION (
   STATIONID            varchar(10)          not null,
   STATIONNAME          varchar(80)          null,
   ADDRESS1             varchar(80)          null,
   ADDRESS2             varchar(80)          null,
   ADDRESS3             varchar(80)          null,
   ADDRESS4             varchar(80)          null,
   CITY                 varchar(40)          null,
   STATE                varchar(10)          null,
   POSTCODE             varchar(10)          null,
   LASTCHANGED          timestamp(3)             null,
   CONNECTIONPOINTID    varchar(10)          null
);

alter table STATION
   add constraint STATION_PK primary key (STATIONID);





create index STATION_LCX on STATION (
LASTCHANGED ASC
);





create table STATIONOPERATINGSTATUS (
   EFFECTIVEDATE        timestamp(3)             not null,
   STATIONID            varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   STATUS               varchar(20)          null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table STATIONOPERATINGSTATUS
   add constraint STATIONOPERATINGSTATUS_PK primary key (EFFECTIVEDATE, STATIONID, VERSIONNO);





create index STATIONOPERATINGSTATUS_LCX on STATIONOPERATINGSTATUS (
LASTCHANGED ASC
);





create table STATIONOWNER (
   EFFECTIVEDATE        timestamp(3)             not null,
   PARTICIPANTID        varchar(10)          not null,
   STATIONID            varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   LASTCHANGED          timestamp(3)             null
);

alter table STATIONOWNER
   add constraint STATIONOWNER_PK primary key (PARTICIPANTID, EFFECTIVEDATE, VERSIONNO, STATIONID);





create index STATIONOWNER_LCX on STATIONOWNER (
LASTCHANGED ASC
);





create index STATIONOWNER_NDX2 on STATIONOWNER (
STATIONID ASC,
EFFECTIVEDATE ASC,
VERSIONNO ASC
);





create index STATIONOWNER_NDX3 on STATIONOWNER (
PARTICIPANTID ASC
);





create table STATIONOWNERTRK (
   EFFECTIVEDATE        timestamp(3)             not null,
   PARTICIPANTID        varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       timestamp(3)             null,
   LASTCHANGED          timestamp(3)             null
);

alter table STATIONOWNERTRK
   add constraint STATIONOWNERTRK_PK primary key (PARTICIPANTID, EFFECTIVEDATE, VERSIONNO);





create index STATIONOWNERTRK_LCX on STATIONOWNERTRK (
LASTCHANGED ASC
);





create table STPASA_CASESOLUTION (
   RUN_DATETIME         timestamp(3)             not null,
   PASAVERSION          varchar(10)          null,
   RESERVECONDITION     numeric(1,0)         null,
   LORCONDITION         numeric(1,0)         null,
   CAPACITYOBJFUNCTION  numeric(12,3)        null,
   CAPACITYOPTION       numeric(12,3)        null,
   MAXSURPLUSRESERVEOPTION numeric(12,3)        null,
   MAXSPARECAPACITYOPTION numeric(12,3)        null,
   INTERCONNECTORFLOWPENALTY numeric(12,3)        null,
   LASTCHANGED          timestamp(3)             null,
   RELIABILITYLRCDEMANDOPTION numeric(12,3)        null,
   OUTAGELRCDEMANDOPTION numeric(12,3)        null,
   LORDEMANDOPTION      numeric(12,3)        null,
   RELIABILITYLRCCAPACITYOPTION varchar(10)          null,
   OUTAGELRCCAPACITYOPTION varchar(10)          null,
   LORCAPACITYOPTION    varchar(10)          null,
   LORUIGFOPTION        numeric(3,0)         null,
   RELIABILITYLRCUIGFOPTION numeric(3,0)         null,
   OUTAGELRCUIGFOPTION  numeric(3,0)         null
);

alter table STPASA_CASESOLUTION
   add constraint CASESOLUTION_PK primary key (RUN_DATETIME);





create index STPASA_CASESOLUTION_LCX on STPASA_CASESOLUTION (
LASTCHANGED ASC
);





create table STPASA_CONSTRAINTSOLUTION (
   RUN_DATETIME         timestamp(3)             not null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   CONSTRAINTID         varchar(20)          not null,
   CAPACITYRHS          numeric(12,2)        null,
   CAPACITYMARGINALVALUE numeric(12,2)        null,
   CAPACITYVIOLATIONDEGREE numeric(12,2)        null,
   LASTCHANGED          timestamp(3)             null,
   RUNTYPE              varchar(20)          not null default 'OUTAGE_LRC'
);

alter table STPASA_CONSTRAINTSOLUTION
   add constraint CONSTRAINTSOLUTION_PK primary key (RUN_DATETIME, RUNTYPE, INTERVAL_DATETIME, CONSTRAINTID);





create index STPASA_CONSTRAINTSOLUTION_LCX on STPASA_CONSTRAINTSOLUTION (
LASTCHANGED ASC
);





create table STPASA_INTERCONNECTORSOLN (
   RUN_DATETIME         timestamp(3)             not null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   INTERCONNECTORID     varchar(10)          not null,
   CAPACITYMWFLOW       numeric(12,2)        null,
   CAPACITYMARGINALVALUE numeric(12,2)        null,
   CAPACITYVIOLATIONDEGREE numeric(12,2)        null,
   CALCULATEDEXPORTLIMIT numeric(12,2)        null,
   CALCULATEDIMPORTLIMIT numeric(12,2)        null,
   LASTCHANGED          timestamp(3)             null,
   RUNTYPE              varchar(20)          not null default 'OUTAGE_LRC',
   EXPORTLIMITCONSTRAINTID varchar(20)          null,
   IMPORTLIMITCONSTRAINTID varchar(20)          null
);

alter table STPASA_INTERCONNECTORSOLN
   add constraint INTERCONNECTORSOLUTION_PK primary key (RUN_DATETIME, RUNTYPE, INTERVAL_DATETIME, INTERCONNECTORID);





create index STPASA_INTERCONNECTORSOLN_LCX on STPASA_INTERCONNECTORSOLN (
LASTCHANGED ASC
);





create table STPASA_REGIONSOLUTION (
   RUN_DATETIME         timestamp(3)             not null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   REGIONID             varchar(10)          not null,
   DEMAND10             numeric(12,2)        null,
   DEMAND50             numeric(12,2)        null,
   DEMAND90             numeric(12,2)        null,
   RESERVEREQ           numeric(12,2)        null,
   CAPACITYREQ          numeric(12,2)        null,
   ENERGYREQDEMAND50    numeric(12,2)        null,
   UNCONSTRAINEDCAPACITY numeric(12,0)        null,
   CONSTRAINEDCAPACITY  numeric(12,0)        null,
   NETINTERCHANGEUNDERSCARCITY numeric(12,2)        null,
   SURPLUSCAPACITY      numeric(12,2)        null,
   SURPLUSRESERVE       numeric(12,2)        null,
   RESERVECONDITION     numeric(1,0)         null,
   MAXSURPLUSRESERVE    numeric(12,2)        null,
   MAXSPARECAPACITY     numeric(12,2)        null,
   LORCONDITION         numeric(1,0)         null,
   AGGREGATECAPACITYAVAILABLE numeric(12,2)        null,
   AGGREGATESCHEDULEDLOAD numeric(12,2)        null,
   LASTCHANGED          timestamp(3)             null,
   AGGREGATEPASAAVAILABILITY numeric(12,0)        null,
   RUNTYPE              varchar(20)          not null default 'OUTAGE_LRC',
   ENERGYREQDEMAND10    numeric(12,2)        null,
   CALCULATEDLOR1LEVEL  numeric(16,6)        null,
   CALCULATEDLOR2LEVEL  numeric(16,6)        null,
   MSRNETINTERCHANGEUNDERSCARCITY numeric(12,2)        null,
   LORNETINTERCHANGEUNDERSCARCITY numeric(12,2)        null,
   TOTALINTERMITTENTGENERATION numeric(15,5)        null,
   DEMAND_AND_NONSCHEDGEN numeric(15,5)        null,
   UIGF                 numeric(12,2)        null,
   SEMISCHEDULEDCAPACITY numeric(12,2)        null,
   LOR_SEMISCHEDULEDCAPACITY numeric(12,2)        null,
   LCR                  numeric(16,6)        null,
   LCR2                 numeric(16,6)        null,
   FUM                  numeric(16,6)        null,
   SS_SOLAR_UIGF        numeric(12,2)        null,
   SS_WIND_UIGF         numeric(12,2)        null,
   SS_SOLAR_CAPACITY    numeric(12,2)        null,
   SS_WIND_CAPACITY     numeric(12,2)        null,
   SS_SOLAR_CLEARED     numeric(12,2)        null,
   SS_WIND_CLEARED      numeric(12,2)        null
);

alter table STPASA_REGIONSOLUTION
   add constraint REGIONSOLUTION_PK primary key (RUN_DATETIME, RUNTYPE, INTERVAL_DATETIME, REGIONID);





create index STPASA_REGIONSOLUTION_LCX on STPASA_REGIONSOLUTION (
LASTCHANGED ASC
);





create table STPASA_SYSTEMSOLUTION (
   RUN_DATETIME         timestamp(3)             not null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   SYSTEMDEMAND50       numeric(12,2)        null,
   RESERVEREQ           numeric(12,2)        null,
   UNCONSTRAINEDCAPACITY numeric(12,2)        null,
   CONSTRAINEDCAPACITY  numeric(12,2)        null,
   SURPLUSCAPACITY      numeric(12,2)        null,
   SURPLUSRESERVE       numeric(12,2)        null,
   RESERVECONDITION     numeric(1,0)         null,
   LASTCHANGED          timestamp(3)             null
);

alter table STPASA_SYSTEMSOLUTION
   add constraint SYSTEMSOLUTION_PK primary key (INTERVAL_DATETIME);





create index STPASA_SYSTEMSOLUTION_LCX on STPASA_SYSTEMSOLUTION (
LASTCHANGED ASC
);





create index STPASA_SYSTEMSOLUTION_NDX1 on STPASA_SYSTEMSOLUTION (
RUN_DATETIME ASC
);





create table STPASA_UNITSOLUTION (
   RUN_DATETIME         timestamp(3)             not null,
   INTERVAL_DATETIME    timestamp(3)             not null,
   DUID                 varchar(10)          not null,
   CONNECTIONPOINTID    varchar(10)          null,
   EXPECTEDMAXCAPACITY  numeric(12,2)        null,
   CAPACITYMARGINALVALUE numeric(12,2)        null,
   CAPACITYVIOLATIONDEGREE numeric(12,2)        null,
   CAPACITYAVAILABLE    numeric(12,2)        null,
   ENERGYCONSTRAINED    numeric(1,0)         null,
   ENERGYAVAILABLE      numeric(10,0)        null,
   LASTCHANGED          timestamp(3)             null,
   PASAAVAILABILITY     numeric(12,0)        null,
   RUNTYPE              varchar(20)          not null default 'OUTAGE_LRC'
);

alter table STPASA_UNITSOLUTION
   add constraint UNITSOLUTION_PK primary key (RUN_DATETIME, RUNTYPE, INTERVAL_DATETIME, DUID);





create index STPASA_UNITSOLUTION_LCX on STPASA_UNITSOLUTION (
LASTCHANGED ASC
);





create table TRADINGINTERCONNECT (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   METEREDMWFLOW        numeric(15,5)        null,
   MWFLOW               numeric(15,5)        null,
   MWLOSSES             numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null
);

alter table TRADINGINTERCONNECT
   add constraint PK_TRADINGINTERCONNECT primary key (SETTLEMENTDATE, RUNNO, INTERCONNECTORID, PERIODID);





create index TRADINGINTERCONNECT_LCX on TRADINGINTERCONNECT (
LASTCHANGED ASC
);





create table TRADINGLOAD (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   DUID                 varchar(10)          not null,
   TRADETYPE            numeric(2,0)         not null,
   PERIODID             numeric(3,0)         not null,
   INITIALMW            numeric(15,5)        null,
   TOTALCLEARED         numeric(15,5)        null,
   RAMPDOWNRATE         numeric(15,5)        null,
   RAMPUPRATE           numeric(15,5)        null,
   LOWER5MIN            numeric(15,5)        null,
   LOWER60SEC           numeric(15,5)        null,
   LOWER6SEC            numeric(15,5)        null,
   RAISE5MIN            numeric(15,5)        null,
   RAISE60SEC           numeric(15,5)        null,
   RAISE6SEC            numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   LOWERREG             numeric(15,5)        null,
   RAISEREG             numeric(15,5)        null,
   AVAILABILITY         numeric(15,5)        null,
   SEMIDISPATCHCAP      numeric(3,0)         null
);

alter table TRADINGLOAD
   add constraint PK_TRADINGLOAD primary key (SETTLEMENTDATE, RUNNO, DUID, TRADETYPE, PERIODID);





create index TRADINGLOAD_NDX2 on TRADINGLOAD (
DUID ASC,
LASTCHANGED ASC
);





create index TRADINGLOAD_LCX on TRADINGLOAD (
LASTCHANGED ASC
);





create table TRADINGPRICE (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   RRP                  numeric(15,5)        null,
   EEP                  numeric(15,5)        null,
   INVALIDFLAG          varchar(1)           null,
   LASTCHANGED          timestamp(3)             null,
   ROP                  numeric(15,5)        null,
   RAISE6SECRRP         numeric(15,5)        null,
   RAISE6SECROP         numeric(15,5)        null,
   RAISE60SECRRP        numeric(15,5)        null,
   RAISE60SECROP        numeric(15,5)        null,
   RAISE5MINRRP         numeric(15,5)        null,
   RAISE5MINROP         numeric(15,5)        null,
   RAISEREGRRP          numeric(15,5)        null,
   RAISEREGROP          numeric(15,5)        null,
   LOWER6SECRRP         numeric(15,5)        null,
   LOWER6SECROP         numeric(15,5)        null,
   LOWER60SECRRP        numeric(15,5)        null,
   LOWER60SECROP        numeric(15,5)        null,
   LOWER5MINRRP         numeric(15,5)        null,
   LOWER5MINROP         numeric(15,5)        null,
   LOWERREGRRP          numeric(15,5)        null,
   LOWERREGROP          numeric(15,5)        null,
   PRICE_STATUS         varchar(20)          null
);

alter table TRADINGPRICE
   add constraint PK_TRADINGPRICE primary key (SETTLEMENTDATE, RUNNO, REGIONID, PERIODID);





create index TRADINGPRICE_LCX on TRADINGPRICE (
LASTCHANGED ASC
);





create table TRADINGREGIONSUM (
   SETTLEMENTDATE       timestamp(3)             not null,
   RUNNO                numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   TOTALDEMAND          numeric(15,5)        null,
   AVAILABLEGENERATION  numeric(15,5)        null,
   AVAILABLELOAD        numeric(15,5)        null,
   DEMANDFORECAST       numeric(15,5)        null,
   DISPATCHABLEGENERATION numeric(15,5)        null,
   DISPATCHABLELOAD     numeric(15,5)        null,
   NETINTERCHANGE       numeric(15,5)        null,
   EXCESSGENERATION     numeric(15,5)        null,
   LOWER5MINDISPATCH    numeric(15,5)        null,
   LOWER5MINIMPORT      numeric(15,5)        null,
   LOWER5MINLOCALDISPATCH numeric(15,5)        null,
   LOWER5MINLOCALPRICE  numeric(15,5)        null,
   LOWER5MINLOCALREQ    numeric(15,5)        null,
   LOWER5MINPRICE       numeric(15,5)        null,
   LOWER5MINREQ         numeric(15,5)        null,
   LOWER5MINSUPPLYPRICE numeric(15,5)        null,
   LOWER60SECDISPATCH   numeric(15,5)        null,
   LOWER60SECIMPORT     numeric(15,5)        null,
   LOWER60SECLOCALDISPATCH numeric(15,5)        null,
   LOWER60SECLOCALPRICE numeric(15,5)        null,
   LOWER60SECLOCALREQ   numeric(15,5)        null,
   LOWER60SECPRICE      numeric(15,5)        null,
   LOWER60SECREQ        numeric(15,5)        null,
   LOWER60SECSUPPLYPRICE numeric(15,5)        null,
   LOWER6SECDISPATCH    numeric(15,5)        null,
   LOWER6SECIMPORT      numeric(15,5)        null,
   LOWER6SECLOCALDISPATCH numeric(15,5)        null,
   LOWER6SECLOCALPRICE  numeric(15,5)        null,
   LOWER6SECLOCALREQ    numeric(15,5)        null,
   LOWER6SECPRICE       numeric(15,5)        null,
   LOWER6SECREQ         numeric(15,5)        null,
   LOWER6SECSUPPLYPRICE numeric(15,5)        null,
   RAISE5MINDISPATCH    numeric(15,5)        null,
   RAISE5MINIMPORT      numeric(15,5)        null,
   RAISE5MINLOCALDISPATCH numeric(15,5)        null,
   RAISE5MINLOCALPRICE  numeric(15,5)        null,
   RAISE5MINLOCALREQ    numeric(15,5)        null,
   RAISE5MINPRICE       numeric(15,5)        null,
   RAISE5MINREQ         numeric(15,5)        null,
   RAISE5MINSUPPLYPRICE numeric(15,5)        null,
   RAISE60SECDISPATCH   numeric(15,5)        null,
   RAISE60SECIMPORT     numeric(15,5)        null,
   RAISE60SECLOCALDISPATCH numeric(15,5)        null,
   RAISE60SECLOCALPRICE numeric(15,5)        null,
   RAISE60SECLOCALREQ   numeric(15,5)        null,
   RAISE60SECPRICE      numeric(15,5)        null,
   RAISE60SECREQ        numeric(15,5)        null,
   RAISE60SECSUPPLYPRICE numeric(15,5)        null,
   RAISE6SECDISPATCH    numeric(15,5)        null,
   RAISE6SECIMPORT      numeric(15,5)        null,
   RAISE6SECLOCALDISPATCH numeric(15,5)        null,
   RAISE6SECLOCALPRICE  numeric(15,5)        null,
   RAISE6SECLOCALREQ    numeric(15,5)        null,
   RAISE6SECPRICE       numeric(15,5)        null,
   RAISE6SECREQ         numeric(15,5)        null,
   RAISE6SECSUPPLYPRICE numeric(15,5)        null,
   LASTCHANGED          timestamp(3)             null,
   INITIALSUPPLY        numeric(15,5)        null,
   CLEAREDSUPPLY        numeric(15,5)        null,
   LOWERREGIMPORT       numeric(15,5)        null,
   LOWERREGLOCALDISPATCH numeric(15,5)        null,
   LOWERREGLOCALREQ     numeric(15,5)        null,
   LOWERREGREQ          numeric(15,5)        null,
   RAISEREGIMPORT       numeric(15,5)        null,
   RAISEREGLOCALDISPATCH numeric(15,5)        null,
   RAISEREGLOCALREQ     numeric(15,5)        null,
   RAISEREGREQ          numeric(15,5)        null,
   RAISE5MINLOCALVIOLATION numeric(15,5)        null,
   RAISEREGLOCALVIOLATION numeric(15,5)        null,
   RAISE60SECLOCALVIOLATION numeric(15,5)        null,
   RAISE6SECLOCALVIOLATION numeric(15,5)        null,
   LOWER5MINLOCALVIOLATION numeric(15,5)        null,
   LOWERREGLOCALVIOLATION numeric(15,5)        null,
   LOWER60SECLOCALVIOLATION numeric(15,5)        null,
   LOWER6SECLOCALVIOLATION numeric(15,5)        null,
   RAISE5MINVIOLATION   numeric(15,5)        null,
   RAISEREGVIOLATION    numeric(15,5)        null,
   RAISE60SECVIOLATION  numeric(15,5)        null,
   RAISE6SECVIOLATION   numeric(15,5)        null,
   LOWER5MINVIOLATION   numeric(15,5)        null,
   LOWERREGVIOLATION    numeric(15,5)        null,
   LOWER60SECVIOLATION  numeric(15,5)        null,
   LOWER6SECVIOLATION   numeric(15,5)        null,
   TOTALINTERMITTENTGENERATION numeric(15,5)        null,
   DEMAND_AND_NONSCHEDGEN numeric(15,5)        null,
   UIGF                 numeric(15,5)        null
);

alter table TRADINGREGIONSUM
   add constraint PK_TRADNGREGIONSUM primary key (SETTLEMENTDATE, RUNNO, REGIONID, PERIODID);





create index TRADINGREGIONSUM_LCX on TRADINGREGIONSUM (
LASTCHANGED ASC
);





create table TRANSMISSIONLOSSFACTOR (
   TRANSMISSIONLOSSFACTOR numeric(15,5)        not null,
   EFFECTIVEDATE        timestamp(3)             not null,
   VERSIONNO            numeric(22,0)        not null,
   CONNECTIONPOINTID    varchar(10)          not null,
   REGIONID             varchar(10)          null,
   LASTCHANGED          timestamp(3)             null,
   SECONDARY_TLF        numeric(18,8)        null
);

alter table TRANSMISSIONLOSSFACTOR
   add constraint TRANSMISSIONLOSSFACTOR_PK primary key (CONNECTIONPOINTID, EFFECTIVEDATE, VERSIONNO);





create index TRANSMISSIONLOSSFACTOR_LCX on TRANSMISSIONLOSSFACTOR (
LASTCHANGED ASC
);





create table VALUATIONID (
   VALUATIONID          varchar(15)          not null,
   DESCRIPTION          varchar(80)          null,
   LASTCHANGED          timestamp(3)             null
);

alter table VALUATIONID
   add constraint VALUATIONID_PK primary key (VALUATIONID);





create index VALUATIONID_NDX_LCHD on VALUATIONID (
LASTCHANGED ASC
);





create table VOLTAGE_INSTRUCTION (
   RUN_DATETIME         timestamp(3)             not null,
   EMS_ID               varchar(60)          not null,
   PARTICIPANTID        varchar(20)          null,
   STATION_ID           varchar(60)          null,
   DEVICE_ID            varchar(60)          null,
   DEVICE_TYPE          varchar(20)          null,
   CONTROL_TYPE         varchar(20)          null,
   TARGET               numeric(15,0)        null,
   CONFORMING           numeric(1,0)         null,
   INSTRUCTION_SUMMARY  varchar(400)         null,
   VERSION_DATETIME     timestamp(3)             not null,
   INSTRUCTION_SEQUENCE numeric(4,0)         null,
   ADDITIONAL_NOTES     varchar(60)          null
);

alter table VOLTAGE_INSTRUCTION
   add constraint VOLTAGE_INSTRUCTION_PK primary key (RUN_DATETIME, VERSION_DATETIME, EMS_ID);





create table VOLTAGE_INSTRUCTION_TRK (
   RUN_DATETIME         timestamp(3)             not null,
   FILE_TYPE            varchar(20)          null,
   VERSION_DATETIME     timestamp(3)             not null,
   SE_DATETIME          timestamp(3)             null,
   SOLUTION_CATEGORY    varchar(60)          null,
   SOLUTION_STATUS      varchar(60)          null,
   OPERATING_MODE       varchar(60)          null,
   OPERATING_STATUS     varchar(100)         null,
   EST_EXPIRY           timestamp(3)             null,
   EST_NEXT_INSTRUCTION timestamp(3)             null
);

alter table VOLTAGE_INSTRUCTION_TRK
   add constraint VOLTAGE_INSTRUCTION_TRK_PK primary key (RUN_DATETIME, VERSION_DATETIME);


