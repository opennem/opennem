/*==============================================================*/
/* DBMS name:      AEMO Microsoft SQL Server generic            */
/* Created on:     26/11/2019 11:44:34 AM                       */
/*==============================================================*/


/*==============================================================*/
/* Table: ANCILLARY_RECOVERY_SPLIT                              */
/*==============================================================*/
create table ANCILLARY_RECOVERY_SPLIT (
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   SERVICE              varchar(10)          not null,
   PAYMENTTYPE          varchar(20)          not null,
   CUSTOMER_PORTION     numeric(8,5)         null,
   LASTCHANGED          datetime             null
)
go

alter table ANCILLARY_RECOVERY_SPLIT
   add constraint ANCILLARY_RECOVERY_SPLIT_PK primary key (EFFECTIVEDATE, VERSIONNO, SERVICE, PAYMENTTYPE)
go

/*==============================================================*/
/* Index: ANCILLARY_RECOVERY_SPLIT_LCX                          */
/*==============================================================*/
create index ANCILLARY_RECOVERY_SPLIT_LCX on ANCILLARY_RECOVERY_SPLIT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: APCCOMP                                               */
/*==============================================================*/
create table APCCOMP (
   APCID                varchar(10)          not null,
   REGIONID             varchar(10)          null,
   STARTDATE            datetime             null,
   STARTPERIOD          numeric(3,0)         null,
   ENDDATE              datetime             null,
   ENDPERIOD            numeric(3,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table APCCOMP
   add constraint APCCOMP_PK primary key (APCID)
go

/*==============================================================*/
/* Index: APCCOMP_LCX                                           */
/*==============================================================*/
create index APCCOMP_LCX on APCCOMP (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: APCCOMPAMOUNT                                         */
/*==============================================================*/
create table APCCOMPAMOUNT (
   APCID                varchar(10)          not null,
   PARTICIPANTID        varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(6,0)         not null,
   AMOUNT               numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table APCCOMPAMOUNT
   add constraint APCCOMPAMOUNT_PK primary key (APCID, PARTICIPANTID, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: APCCOMPAMOUNT_LCX                                     */
/*==============================================================*/
create index APCCOMPAMOUNT_LCX on APCCOMPAMOUNT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: APCCOMPAMOUNTTRK                                      */
/*==============================================================*/
create table APCCOMPAMOUNTTRK (
   APCID                varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDBY         varchar(10)          null,
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table APCCOMPAMOUNTTRK
   add constraint APCCOMPAMOUNTTRK_PK primary key (APCID, VERSIONNO)
go

/*==============================================================*/
/* Index: APCCOMPAMOUNTTRK_LCX                                  */
/*==============================================================*/
create index APCCOMPAMOUNTTRK_LCX on APCCOMPAMOUNTTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: APEVENT                                               */
/*==============================================================*/
create table APEVENT (
   APEVENTID            numeric(22,0)        not null,
   EFFECTIVEFROMINTERVAL datetime             null,
   EFFECTIVETOINTERVAL  datetime             null,
   REASON               varchar(2000)        null,
   STARTAUTHORISEDBY    varchar(15)          null,
   STARTAUTHORISEDDATE  datetime             null,
   ENDAUTHORISEDBY      varchar(15)          null,
   ENDAUTHORISEDDATE    datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table APEVENT
   add constraint APEVENT_PK primary key (APEVENTID)
go

/*==============================================================*/
/* Index: APEVENT_LCX                                           */
/*==============================================================*/
create index APEVENT_LCX on APEVENT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: APEVENTREGION                                         */
/*==============================================================*/
create table APEVENTREGION (
   APEVENTID            numeric(22,0)        not null,
   REGIONID             varchar(10)          not null,
   LASTCHANGED          datetime             null,
   ENERGYAPFLAG         numeric(1,0)         null,
   RAISE6SECAPFLAG      numeric(1,0)         null,
   RAISE60SECAPFLAG     numeric(1,0)         null,
   RAISE5MINAPFLAG      numeric(1,0)         null,
   RAISEREGAPFLAG       numeric(1,0)         null,
   LOWER6SECAPFLAG      numeric(1,0)         null,
   LOWER60SECAPFLAG     numeric(1,0)         null,
   LOWER5MINAPFLAG      numeric(1,0)         null,
   LOWERREGAPFLAG       numeric(1,0)         null
)
go

alter table APEVENTREGION
   add constraint APEVENTREGION_PK primary key (APEVENTID, REGIONID)
go

/*==============================================================*/
/* Index: APEVENTREGION_LCX                                     */
/*==============================================================*/
create index APEVENTREGION_LCX on APEVENTREGION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: AUCTION                                               */
/*==============================================================*/
create table AUCTION (
   AUCTIONID            varchar(30)          not null,
   AUCTIONDATE          datetime             null,
   NOTIFYDATE           datetime             null,
   STARTDATE            datetime             null,
   ENDDATE              datetime             null,
   DESCRIPTION          varchar(100)         null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(30)          null,
   LASTCHANGED          datetime             null
)
go

alter table AUCTION
   add constraint AUCTION_PK primary key (AUCTIONID)
go

/*==============================================================*/
/* Index: AUCTION_LCX                                           */
/*==============================================================*/
create index AUCTION_LCX on AUCTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: AUCTION_CALENDAR                                      */
/*==============================================================*/
create table AUCTION_CALENDAR (
   CONTRACTYEAR         numeric(4,0)         not null,
   QUARTER              numeric(1,0)         not null,
   STARTDATE            datetime             null,
   ENDDATE              datetime             null,
   NOTIFYDATE           datetime             null,
   PAYMENTDATE          datetime             null,
   RECONCILIATIONDATE   datetime             null,
   LASTCHANGED          datetime             null,
   PRELIMPURCHASESTMTDATE datetime             null,
   PRELIMPROCEEDSSTMTDATE datetime             null,
   FINALPURCHASESTMTDATE datetime             null,
   FINALPROCEEDSSTMTDATE datetime             null
)
go

alter table AUCTION_CALENDAR
   add constraint AUCTION_CALENDAR_PK primary key (CONTRACTYEAR, QUARTER)
go

/*==============================================================*/
/* Index: AUCTION_CALENDAR_LCX                                  */
/*==============================================================*/
create index AUCTION_CALENDAR_LCX on AUCTION_CALENDAR (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: AUCTION_IC_ALLOCATIONS                                */
/*==============================================================*/
create table AUCTION_IC_ALLOCATIONS (
   CONTRACTYEAR         numeric(4,0)         not null,
   QUARTER              numeric(1,0)         not null,
   VERSIONNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   MAXIMUMUNITS         numeric(5,0)         null,
   PROPORTION           numeric(8,5)         null,
   AUCTIONFEE           numeric(17,5)        null,
   CHANGEDATE           datetime             null,
   CHANGEDBY            varchar(15)          null,
   LASTCHANGED          datetime             null,
   AUCTIONFEE_SALES     numeric(18,8)        null
)
go

alter table AUCTION_IC_ALLOCATIONS
   add constraint AUCTION_IC_ALLOCATIONS_PK primary key (CONTRACTYEAR, QUARTER, VERSIONNO, INTERCONNECTORID, FROMREGIONID)
go

/*==============================================================*/
/* Index: AUCTION_IC_ALLOCATIONS_LCX                            */
/*==============================================================*/
create index AUCTION_IC_ALLOCATIONS_LCX on AUCTION_IC_ALLOCATIONS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: AUCTION_REVENUE_ESTIMATE                              */
/*==============================================================*/
create table AUCTION_REVENUE_ESTIMATE (
   CONTRACTYEAR         numeric(4,0)         not null,
   QUARTER              numeric(1,0)         not null,
   VALUATIONID          varchar(15)          not null,
   VERSIONNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   MONTHNO              numeric(1,0)         not null,
   STARTDATE            datetime             null,
   ENDDATE              datetime             null,
   REVENUE              numeric(17,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table AUCTION_REVENUE_ESTIMATE
   add constraint AUCTION_REVENUE_ESTIMATE_PK primary key (CONTRACTYEAR, QUARTER, VALUATIONID, VERSIONNO, INTERCONNECTORID, FROMREGIONID, MONTHNO)
go

/*==============================================================*/
/* Index: AUCTION_REVENUE_ESTIMATE_LCX                          */
/*==============================================================*/
create index AUCTION_REVENUE_ESTIMATE_LCX on AUCTION_REVENUE_ESTIMATE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: AUCTION_REVENUE_TRACK                                 */
/*==============================================================*/
create table AUCTION_REVENUE_TRACK (
   CONTRACTYEAR         numeric(4,0)         not null,
   QUARTER              numeric(1,0)         not null,
   VALUATIONID          varchar(15)          not null,
   VERSIONNO            numeric(3,0)         not null,
   EFFECTIVEDATE        datetime             null,
   STATUS               varchar(10)          null,
   DOCUMENTREF          varchar(30)          null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   LASTCHANGED          datetime             null
)
go

alter table AUCTION_REVENUE_TRACK
   add constraint AUCTION_REVENUE_TRACK_PK primary key (CONTRACTYEAR, QUARTER, VALUATIONID, VERSIONNO)
go

/*==============================================================*/
/* Index: AUCTIONREVTRK_NDX_LCHD                                */
/*==============================================================*/
create index AUCTIONREVTRK_NDX_LCHD on AUCTION_REVENUE_TRACK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: AUCTION_RP_ESTIMATE                                   */
/*==============================================================*/
create table AUCTION_RP_ESTIMATE (
   CONTRACTYEAR         numeric(4,0)         not null,
   QUARTER              numeric(1,0)         not null,
   VALUATIONID          varchar(15)          not null,
   VERSIONNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   RPESTIMATE           numeric(17,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table AUCTION_RP_ESTIMATE
   add constraint AUCTION_RP_ESTIMATE_PK primary key (CONTRACTYEAR, QUARTER, VALUATIONID, VERSIONNO, INTERCONNECTORID, FROMREGIONID)
go

/*==============================================================*/
/* Index: AUCTION_RP_ESTIMATE_LCX                               */
/*==============================================================*/
create index AUCTION_RP_ESTIMATE_LCX on AUCTION_RP_ESTIMATE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: AUCTION_TRANCHE                                       */
/*==============================================================*/
create table AUCTION_TRANCHE (
   CONTRACTYEAR         numeric(4,0)         not null,
   QUARTER              numeric(1,0)         not null,
   VERSIONNO            numeric(3,0)         not null,
   TRANCHE              numeric(2,0)         not null,
   AUCTIONDATE          datetime             null,
   NOTIFYDATE           datetime             null,
   UNITALLOCATION       numeric(18,8)        null,
   CHANGEDATE           datetime             null,
   CHANGEDBY            varchar(15)          null,
   LASTCHANGED          datetime             null
)
go

alter table AUCTION_TRANCHE
   add constraint AUCTION_TRANCHE_PK primary key (CONTRACTYEAR, QUARTER, VERSIONNO, TRANCHE)
go

/*==============================================================*/
/* Index: AUCTION_TRANCHE_LCX                                   */
/*==============================================================*/
create index AUCTION_TRANCHE_LCX on AUCTION_TRANCHE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BIDDAYOFFER                                           */
/*==============================================================*/
create table BIDDAYOFFER (
   DUID                 varchar(10)          not null,
   BIDTYPE              varchar(10)          not null,
   SETTLEMENTDATE       datetime             not null,
   OFFERDATE            datetime             not null,
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
   LASTCHANGED          datetime             null,
   MR_FACTOR            numeric(16,6)        null,
   ENTRYTYPE            varchar(20)          null
)
go

alter table BIDDAYOFFER
   add constraint BIDDAYOFFER_PK primary key (DUID, BIDTYPE, SETTLEMENTDATE, OFFERDATE)
go

/*==============================================================*/
/* Index: BIDDAYOFFER_LCHD_IDX                                  */
/*==============================================================*/
create index BIDDAYOFFER_LCHD_IDX on BIDDAYOFFER (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: BIDDAYOFFER_PART_IDX                                  */
/*==============================================================*/
create index BIDDAYOFFER_PART_IDX on BIDDAYOFFER (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Table: BIDDAYOFFER_D                                         */
/*==============================================================*/
create table BIDDAYOFFER_D (
   SETTLEMENTDATE       datetime             not null,
   DUID                 varchar(10)          not null,
   BIDTYPE              varchar(10)          not null,
   BIDSETTLEMENTDATE    datetime             null,
   OFFERDATE            datetime             null,
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
   LASTCHANGED          datetime             null,
   MR_FACTOR            numeric(16,6)        null,
   ENTRYTYPE            varchar(20)          null
)
go

alter table BIDDAYOFFER_D
   add constraint BIDDAYOFFER_D_PK primary key (SETTLEMENTDATE, DUID, BIDTYPE)
go

/*==============================================================*/
/* Index: BIDDAYOFFER_D_LCHD_IDX                                */
/*==============================================================*/
create index BIDDAYOFFER_D_LCHD_IDX on BIDDAYOFFER_D (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: BIDDAYOFFER_D_PART_IDX                                */
/*==============================================================*/
create index BIDDAYOFFER_D_PART_IDX on BIDDAYOFFER_D (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Table: BIDDUIDDETAILS                                        */
/*==============================================================*/
create table BIDDUIDDETAILS (
   DUID                 varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   BIDTYPE              varchar(10)          not null,
   MAXCAPACITY          numeric(22,0)        null,
   MINENABLEMENTLEVEL   numeric(22,0)        null,
   MAXENABLEMENTLEVEL   numeric(22,0)        null,
   MAXLOWERANGLE        numeric(3,0)         null,
   MAXUPPERANGLE        numeric(3,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table BIDDUIDDETAILS
   add constraint BIDDUIDDETAILS_PK primary key (DUID, EFFECTIVEDATE, VERSIONNO, BIDTYPE)
go

/*==============================================================*/
/* Index: BIDDUIDDETAILS_LCHD_IDX                               */
/*==============================================================*/
create index BIDDUIDDETAILS_LCHD_IDX on BIDDUIDDETAILS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BIDDUIDDETAILSTRK                                     */
/*==============================================================*/
create table BIDDUIDDETAILSTRK (
   DUID                 varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   LASTCHANGED          datetime             null
)
go

alter table BIDDUIDDETAILSTRK
   add constraint BIDDUIDDETAILSTRK_PK primary key (DUID, EFFECTIVEDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: BIDDUIDDETAILSTRK_LCHD_IDX                            */
/*==============================================================*/
create index BIDDUIDDETAILSTRK_LCHD_IDX on BIDDUIDDETAILSTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BIDOFFERFILETRK                                       */
/*==============================================================*/
create table BIDOFFERFILETRK (
   PARTICIPANTID        varchar(10)          not null,
   OFFERDATE            datetime             not null,
   FILENAME             varchar(80)          not null,
   STATUS               varchar(10)          null,
   LASTCHANGED          datetime             null,
   AUTHORISEDBY         varchar(20)          null,
   AUTHORISEDDATE       datetime             null
)
go

alter table BIDOFFERFILETRK
   add constraint BIDOFFERFILETRK_FILE_UK unique (FILENAME)
go

alter table BIDOFFERFILETRK
   add constraint BIDOFFERFILETRK_PK primary key (PARTICIPANTID, OFFERDATE)
go

/*==============================================================*/
/* Index: BIDOFFERFILETRK_LCHD_IDX                              */
/*==============================================================*/
create index BIDOFFERFILETRK_LCHD_IDX on BIDOFFERFILETRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BIDPEROFFER                                           */
/*==============================================================*/
create table BIDPEROFFER (
   DUID                 varchar(10)          not null,
   BIDTYPE              varchar(10)          not null,
   SETTLEMENTDATE       datetime             not null,
   OFFERDATE            datetime             not null,
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
   LASTCHANGED          datetime             null,
   PASAAVAILABILITY     numeric(12,0)        null,
   MR_CAPACITY          numeric(6,0)         null
)
go

alter table BIDPEROFFER
   add constraint BIDPEROFFER_PK primary key (DUID, BIDTYPE, SETTLEMENTDATE, OFFERDATE, PERIODID)
go

/*==============================================================*/
/* Index: BIDPEROFFER_LCHD_IDX                                  */
/*==============================================================*/
create index BIDPEROFFER_LCHD_IDX on BIDPEROFFER (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BIDPEROFFER_D                                         */
/*==============================================================*/
create table BIDPEROFFER_D (
   SETTLEMENTDATE       datetime             not null,
   DUID                 varchar(10)          not null,
   BIDTYPE              varchar(10)          not null,
   BIDSETTLEMENTDATE    datetime             null,
   OFFERDATE            datetime             null,
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
   LASTCHANGED          datetime             null,
   PASAAVAILABILITY     numeric(12,0)        null,
   INTERVAL_DATETIME    datetime             not null,
   MR_CAPACITY          numeric(6,0)         null
)
go

alter table BIDPEROFFER_D
   add constraint BIDPEROFFER_D_PK primary key (SETTLEMENTDATE, DUID, BIDTYPE, INTERVAL_DATETIME)
go

/*==============================================================*/
/* Index: BIDPEROFFER_D_LCHD_IDX                                */
/*==============================================================*/
create index BIDPEROFFER_D_LCHD_IDX on BIDPEROFFER_D (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BIDTYPES                                              */
/*==============================================================*/
create table BIDTYPES (
   BIDTYPE              varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   DESCRIPTION          varchar(64)          null,
   NUMBEROFBANDS        numeric(3,0)         null,
   NUMDAYSAHEADPRICELOCKED numeric(2,0)         null,
   VALIDATIONRULE       varchar(10)          null,
   LASTCHANGED          datetime             null,
   SPDALIAS             varchar(10)          null
)
go

alter table BIDTYPES
   add constraint BIDTYPES_PK primary key (BIDTYPE, EFFECTIVEDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: BIDTYPES_LCHD_IDX                                     */
/*==============================================================*/
create index BIDTYPES_LCHD_IDX on BIDTYPES (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BIDTYPESTRK                                           */
/*==============================================================*/
create table BIDTYPESTRK (
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   LASTCHANGED          datetime             null
)
go

alter table BIDTYPESTRK
   add constraint BIDTYPESTRK_PK primary key (EFFECTIVEDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: BIDTYPESTRK_LCHD_IDX                                  */
/*==============================================================*/
create index BIDTYPESTRK_LCHD_IDX on BIDTYPESTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLADJUSTMENTS                                       */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   LRS                  numeric(15,5)        null,
   PRS                  numeric(15,5)        null,
   OFS                  numeric(15,5)        null,
   IRN                  numeric(15,5)        null,
   IRP                  numeric(15,5)        null,
   INTERESTAMOUNT       numeric(15,5)        null
)
go

alter table BILLADJUSTMENTS
   add constraint BILLADJUSTMENTS_PK primary key (CONTRACTYEAR, WEEKNO, ADJCONTRACTYEAR, ADJWEEKNO, ADJBILLRUNNO, PARTICIPANTID)
go

/*==============================================================*/
/* Index: BILLADJUSTMENTS_NDX2                                  */
/*==============================================================*/
create index BILLADJUSTMENTS_NDX2 on BILLADJUSTMENTS (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: BILLADJUSTMENTS_LCX                                   */
/*==============================================================*/
create index BILLADJUSTMENTS_LCX on BILLADJUSTMENTS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGAPCCOMPENSATION                                */
/*==============================================================*/
create table BILLINGAPCCOMPENSATION (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   APCCOMPENSATION      numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLINGAPCCOMPENSATION
   add constraint BILLINGAPCCOMPENSATION_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID)
go

/*==============================================================*/
/* Index: BILLINGAPCCOMPENSATION_LCX                            */
/*==============================================================*/
create index BILLINGAPCCOMPENSATION_LCX on BILLINGAPCCOMPENSATION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGAPCRECOVERY                                    */
/*==============================================================*/
create table BILLINGAPCRECOVERY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   APCRECOVERY          numeric(15,0)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLINGAPCRECOVERY
   add constraint BILLINGAPCRECOVERY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID)
go

/*==============================================================*/
/* Index: BILLINGAPCRECOVERY_LCX                                */
/*==============================================================*/
create index BILLINGAPCRECOVERY_LCX on BILLINGAPCRECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGASPAYMENTS                                     */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   LOWER5MIN            numeric(15,5)        null,
   RAISE5MIN            numeric(15,5)        null,
   LOWERREG             numeric(15,5)        null,
   RAISEREG             numeric(15,5)        null,
   AVAILABILITY_REACTIVE numeric(18,8)        null,
   AVAILABILITY_REACTIVE_RBT numeric(18,8)        null
)
go

alter table BILLINGASPAYMENTS
   add constraint BILLINGASPAYMENTS_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, CONNECTIONPOINTID)
go

/*==============================================================*/
/* Index: BILLINGASPAYMENTS_LCX                                 */
/*==============================================================*/
create index BILLINGASPAYMENTS_LCX on BILLINGASPAYMENTS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGASRECOVERY                                     */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
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
)
go

alter table BILLINGASRECOVERY
   add constraint BILLINGASRECOVERY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID)
go

/*==============================================================*/
/* Index: BILLINGASRECOVERY_LCX                                 */
/*==============================================================*/
create index BILLINGASRECOVERY_LCX on BILLINGASRECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGCALENDAR                                       */
/*==============================================================*/
create table BILLINGCALENDAR (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   STARTDATE            datetime             null,
   ENDDATE              datetime             null,
   PRELIMINARYSTATEMENTDATE datetime             null,
   FINALSTATEMENTDATE   datetime             null,
   PAYMENTDATE          datetime             null,
   LASTCHANGED          datetime             null,
   REVISION1_STATEMENTDATE datetime             null,
   REVISION2_STATEMENTDATE datetime             null
)
go

alter table BILLINGCALENDAR
   add constraint BILLINGCALENDAR_PK primary key (CONTRACTYEAR, WEEKNO)
go

/*==============================================================*/
/* Index: BILLINGCALENDAR_LCX                                   */
/*==============================================================*/
create index BILLINGCALENDAR_LCX on BILLINGCALENDAR (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGCPDATA                                         */
/*==============================================================*/
create table BILLINGCPDATA (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONNECTIONPOINTID    varchar(10)          not null,
   AGGREGATEENERGY      numeric(16,6)        null,
   PURCHASES            numeric(16,6)        null,
   LASTCHANGED          datetime             null,
   MDA                  varchar(10)          not null
)
go

alter table BILLINGCPDATA
   add constraint BILLINGCPDATA_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, CONNECTIONPOINTID, MDA)
go

/*==============================================================*/
/* Index: BILLINGCPDATA_NDX2                                    */
/*==============================================================*/
create index BILLINGCPDATA_NDX2 on BILLINGCPDATA (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: BILLINGCPDATA_LCX                                     */
/*==============================================================*/
create index BILLINGCPDATA_LCX on BILLINGCPDATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGCPSUM                                          */
/*==============================================================*/
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
   LASTCHANGED          datetime             null
)
go

alter table BILLINGCPSUM
   add constraint BILLINGCPSUM_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, PARTICIPANTTYPE)
go

/*==============================================================*/
/* Index: BILLINGCPSUM_LCX                                      */
/*==============================================================*/
create index BILLINGCPSUM_LCX on BILLINGCPSUM (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: BILLINGCPSUM_NDX2                                     */
/*==============================================================*/
create index BILLINGCPSUM_NDX2 on BILLINGCPSUM (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Table: BILLINGCUSTEXCESSGEN                                  */
/*==============================================================*/
create table BILLINGCUSTEXCESSGEN (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   SETTLEMENTDATE       datetime             not null,
   PERIODID             numeric(3,0)         not null,
   EXCESSGENPAYMENT     numeric(16,6)        null,
   LASTCHANGED          datetime             null,
   REGIONID             varchar(10)          not null
)
go

alter table BILLINGCUSTEXCESSGEN
   add constraint BILLINGCUSTEXCESSGEN_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID, SETTLEMENTDATE, PERIODID)
go

/*==============================================================*/
/* Index: BILLINGCUSTEXCESSGEN_LCX                              */
/*==============================================================*/
create index BILLINGCUSTEXCESSGEN_LCX on BILLINGCUSTEXCESSGEN (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGDAYTRK                                         */
/*==============================================================*/
create table BILLINGDAYTRK (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table BILLINGDAYTRK
   add constraint BILLINGDAYTRK_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, SETTLEMENTDATE)
go

/*==============================================================*/
/* Index: BILLINGDAYTRK_LCX                                     */
/*==============================================================*/
create index BILLINGDAYTRK_LCX on BILLINGDAYTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGEXCESSGEN                                      */
/*==============================================================*/
create table BILLINGEXCESSGEN (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   SETTLEMENTDATE       datetime             not null,
   PERIODID             numeric(3,0)         not null,
   EXCESSENERGYCOST     numeric(15,5)        null,
   LASTCHANGED          datetime             null,
   REGIONID             varchar(10)          not null
)
go

alter table BILLINGEXCESSGEN
   add constraint BILLINGEXCESSGEN_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID, SETTLEMENTDATE, PERIODID)
go

/*==============================================================*/
/* Index: BILLINGEXCESSGEN_LCX                                  */
/*==============================================================*/
create index BILLINGEXCESSGEN_LCX on BILLINGEXCESSGEN (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: BILLINGEXCESSGEN_NDX2                                 */
/*==============================================================*/
create index BILLINGEXCESSGEN_NDX2 on BILLINGEXCESSGEN (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Table: BILLINGFEES                                           */
/*==============================================================*/
create table BILLINGFEES (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   MARKETFEEID          varchar(10)          not null,
   RATE                 numeric(15,5)        null,
   ENERGY               numeric(16,6)        null,
   VALUE                numeric(15,5)        null,
   LASTCHANGED          datetime             null,
   PARTICIPANTCATEGORYID varchar(10)          not null
)
go

alter table BILLINGFEES
   add constraint BILLINGFEES_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, MARKETFEEID, PARTICIPANTCATEGORYID)
go

/*==============================================================*/
/* Index: BILLINGFEES_LCX                                       */
/*==============================================================*/
create index BILLINGFEES_LCX on BILLINGFEES (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: BILLINGFEES_NDX2                                      */
/*==============================================================*/
create index BILLINGFEES_NDX2 on BILLINGFEES (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Table: BILLINGFINANCIALADJUSTMENTS                           */
/*==============================================================*/
create table BILLINGFINANCIALADJUSTMENTS (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   PARTICIPANTTYPE      varchar(10)          null,
   ADJUSTMENTITEM       varchar(64)          not null,
   AMOUNT               numeric(15,5)        null,
   VALUE                numeric(15,5)        null,
   LASTCHANGED          datetime             null,
   FINANCIALCODE        numeric(10,0)        null,
   BAS_CLASS            varchar(30)          null
)
go

alter table BILLINGFINANCIALADJUSTMENTS
   add constraint BILLINGFINANCIALADJUSTMENTS_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, ADJUSTMENTITEM)
go

/*==============================================================*/
/* Index: BILLINGFINANCIALADJUSTMEN_LCX                         */
/*==============================================================*/
create index BILLINGFINANCIALADJUSTMEN_LCX on BILLINGFINANCIALADJUSTMENTS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGGENDATA                                        */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   PURCHASEDENERGY      numeric(16,6)        null,
   MDA                  varchar(10)          null
)
go

alter table BILLINGGENDATA
   add constraint BILLINGGENDATA_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, CONNECTIONPOINTID)
go

/*==============================================================*/
/* Index: BILLINGGENDATA_LCX                                    */
/*==============================================================*/
create index BILLINGGENDATA_LCX on BILLINGGENDATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: BILLINGGENDATA_NDX2                                   */
/*==============================================================*/
create index BILLINGGENDATA_NDX2 on BILLINGGENDATA (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Table: BILLINGINTERRESIDUES                                  */
/*==============================================================*/
create table BILLINGINTERRESIDUES (
   ALLOCATION           numeric(6,3)         null,
   TOTALSURPLUS         numeric(15,5)        null,
   INTERCONNECTORID     varchar(10)          not null,
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   SURPLUSVALUE         numeric(15,6)        null,
   LASTCHANGED          datetime             null,
   REGIONID             varchar(10)          not null
)
go

alter table BILLINGINTERRESIDUES
   add constraint BILLINGINTERRESIDUES_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, INTERCONNECTORID, REGIONID)
go

/*==============================================================*/
/* Index: BILLINGINTERRESIDUES_LCX                              */
/*==============================================================*/
create index BILLINGINTERRESIDUES_LCX on BILLINGINTERRESIDUES (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGINTERVENTION                                   */
/*==============================================================*/
create table BILLINGINTERVENTION (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   MARKETINTERVENTION   numeric(15,5)        null,
   TOTALINTERVENTION    numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLINGINTERVENTION
   add constraint BILLINGINTERVENTION_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID)
go

/*==============================================================*/
/* Index: BILLINGINTERVENTION_LCX                               */
/*==============================================================*/
create index BILLINGINTERVENTION_LCX on BILLINGINTERVENTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGINTERVENTIONREGION                             */
/*==============================================================*/
create table BILLINGINTERVENTIONREGION (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   REGIONINTERVENTION   numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLINGINTERVENTIONREGION
   add constraint BILLINGINTERVENTIONREGION_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID)
go

/*==============================================================*/
/* Index: BILLINGINTERVENTIONREGION_LCX                         */
/*==============================================================*/
create index BILLINGINTERVENTIONREGION_LCX on BILLINGINTERVENTIONREGION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGINTRARESIDUES                                  */
/*==============================================================*/
create table BILLINGINTRARESIDUES (
   ALLOCATION           numeric(6,3)         null,
   TOTALSURPLUS         numeric(15,5)        null,
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   SURPLUSVALUE         numeric(15,6)        null,
   LASTCHANGED          datetime             null,
   REGIONID             varchar(10)          not null
)
go

alter table BILLINGINTRARESIDUES
   add constraint BILLINGINTRARESIDUES_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID)
go

/*==============================================================*/
/* Index: BILLINGINTRARESIDUES_LCX                              */
/*==============================================================*/
create index BILLINGINTRARESIDUES_LCX on BILLINGINTRARESIDUES (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGIRAUCSURPLUS                                   */
/*==============================================================*/
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
   LASTCHANGED          datetime             null
)
go

alter table BILLINGIRAUCSURPLUS
   add constraint BILLINGAUCSURPLUS_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, CONTRACTID, INTERCONNECTORID, FROMREGIONID, PARTICIPANTID)
go

/*==============================================================*/
/* Index: BILLINGIRAUCSURPLUS_IDX_LC                            */
/*==============================================================*/
create index BILLINGIRAUCSURPLUS_IDX_LC on BILLINGIRAUCSURPLUS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGIRAUCSURPLUSSUM                                */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   CSP_DEROGATION_AMOUNT numeric(18,8)        null,
   UNADJUSTED_IRSR      numeric(18,8)        null,
   NEGATIVE_RESIDUES    numeric(18,8)        null
)
go

alter table BILLINGIRAUCSURPLUSSUM
   add constraint BILLINGIRAUCSURPLUSSUM_PK primary key (CONTRACTYEAR, WEEKNO, RESIDUEYEAR, QUARTER, BILLRUNNO, INTERCONNECTORID, FROMREGIONID, PARTICIPANTID)
go

/*==============================================================*/
/* Index: BILLINGIRAUCSURPSUM_LCX                               */
/*==============================================================*/
create index BILLINGIRAUCSURPSUM_LCX on BILLINGIRAUCSURPLUSSUM (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGIRFM                                           */
/*==============================================================*/
create table BILLINGIRFM (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   IRFMPAYMENT          numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLINGIRFM
   add constraint BILLINGIRFM_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID)
go

/*==============================================================*/
/* Index: BILLINGIRFM_LCX                                       */
/*==============================================================*/
create index BILLINGIRFM_LCX on BILLINGIRFM (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGIRNSPSURPLUS                                   */
/*==============================================================*/
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
   LASTCHANGED          datetime             null
)
go

alter table BILLINGIRNSPSURPLUS
   add constraint BILLINGNSPSURPLUS_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, CONTRACTID, INTERCONNECTORID, FROMREGIONID, PARTICIPANTID)
go

/*==============================================================*/
/* Index: BILLINGIRNSPSURPLUS_LCX                               */
/*==============================================================*/
create index BILLINGIRNSPSURPLUS_LCX on BILLINGIRNSPSURPLUS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGIRNSPSURPLUSSUM                                */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   CSP_DEROGATION_AMOUNT numeric(18,8)        null,
   UNADJUSTED_IRSR      numeric(18,8)        null
)
go

alter table BILLINGIRNSPSURPLUSSUM
   add constraint BILLINGIRNSPSURPLUSSUM_PK primary key (CONTRACTYEAR, WEEKNO, RESIDUEYEAR, QUARTER, BILLRUNNO, INTERCONNECTORID, FROMREGIONID, PARTICIPANTID)
go

/*==============================================================*/
/* Index: BILLINGIRNSPSURPSUM_LCX                               */
/*==============================================================*/
create index BILLINGIRNSPSURPSUM_LCX on BILLINGIRNSPSURPLUSSUM (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGIRPARTSURPLUS                                  */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   ACTUALPAYMENT        numeric(15,5)        null
)
go

alter table BILLINGIRPARTSURPLUS
   add constraint BILLINGPARTSURPLUS_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, CONTRACTID, INTERCONNECTORID, FROMREGIONID, PARTICIPANTID)
go

/*==============================================================*/
/* Index: BILLINGIRPARTSURPLUS_LCX                              */
/*==============================================================*/
create index BILLINGIRPARTSURPLUS_LCX on BILLINGIRPARTSURPLUS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGIRPARTSURPLUSSUM                               */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   CSP_DEROGATION_AMOUNT numeric(18,8)        null,
   UNADJUSTED_IRSR      numeric(18,8)        null,
   AUCTIONFEES_TOTALGROSS_ADJ numeric(18,8)        null
)
go

alter table BILLINGIRPARTSURPLUSSUM
   add constraint BILLINGIRPARTSURPLUSSUM_PK primary key (CONTRACTYEAR, WEEKNO, RESIDUEYEAR, QUARTER, BILLRUNNO, INTERCONNECTORID, FROMREGIONID, PARTICIPANTID)
go

/*==============================================================*/
/* Index: BILLINGIRPARTSURPSUM_LCX                              */
/*==============================================================*/
create index BILLINGIRPARTSURPSUM_LCX on BILLINGIRPARTSURPLUSSUM (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: BILLINGIRPARTSURPLUSSUM_I01                           */
/*==============================================================*/
create index BILLINGIRPARTSURPLUSSUM_I01 on BILLINGIRPARTSURPLUSSUM (
RESIDUEYEAR ASC,
QUARTER ASC
)
go

/*==============================================================*/
/* Table: BILLINGPRIORADJUSTMENTS                               */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   IRSR_PREVAMOUNT      numeric(15,5)        null,
   IRSR_ADJAMOUNT       numeric(15,5)        null,
   IRSR_INTERESTAMOUNT  numeric(15,5)        null
)
go

alter table BILLINGPRIORADJUSTMENTS
   add constraint BILLINGPRIORADJUSTMENTS_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, ADJCONTRACTYEAR, ADJWEEKNO, ADJBILLRUNNO, PARTICIPANTID)
go

/*==============================================================*/
/* Index: BILLINGPRIORADJUSTMENTS_NDX2                          */
/*==============================================================*/
create index BILLINGPRIORADJUSTMENTS_NDX2 on BILLINGPRIORADJUSTMENTS (
PARTICIPANTID ASC,
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: BILLINGPRIORADJMNTS_NDX_LCHD                          */
/*==============================================================*/
create index BILLINGPRIORADJMNTS_NDX_LCHD on BILLINGPRIORADJUSTMENTS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGREALLOC                                        */
/*==============================================================*/
create table BILLINGREALLOC (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   COUNTERPARTY         varchar(10)          not null,
   VALUE                numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLINGREALLOC
   add constraint BILLINGREALLOC_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, COUNTERPARTY)
go

/*==============================================================*/
/* Index: BILLINGREALLOC_NDX2                                   */
/*==============================================================*/
create index BILLINGREALLOC_NDX2 on BILLINGREALLOC (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: BILLINGREALLOC_LCX                                    */
/*==============================================================*/
create index BILLINGREALLOC_LCX on BILLINGREALLOC (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGREALLOC_DETAIL                                 */
/*==============================================================*/
create table BILLINGREALLOC_DETAIL (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   COUNTERPARTY         varchar(10)          not null,
   REALLOCATIONID       varchar(20)          not null,
   VALUE                numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLINGREALLOC_DETAIL
   add constraint BILLINGREALLOC_DETAIL_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, COUNTERPARTY, REALLOCATIONID)
go

/*==============================================================*/
/* Index: BILLINGREALLOC_DETAIL_LCX                             */
/*==============================================================*/
create index BILLINGREALLOC_DETAIL_LCX on BILLINGREALLOC_DETAIL (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGREGIONEXPORTS                                  */
/*==============================================================*/
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
   LASTCHANGED          datetime             null
)
go

alter table BILLINGREGIONEXPORTS
   add constraint BILLINGREGIONEXPORTS_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, REGIONID, EXPORTTO)
go

/*==============================================================*/
/* Index: BILLINGREGIONEXPORTS_LCX                              */
/*==============================================================*/
create index BILLINGREGIONEXPORTS_LCX on BILLINGREGIONEXPORTS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGREGIONFIGURES                                  */
/*==============================================================*/
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
   LASTCHANGED          datetime             null
)
go

alter table BILLINGREGIONFIGURES
   add constraint BILLINGREGIONFIGURES_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, REGIONID)
go

/*==============================================================*/
/* Index: BILLINGREGIONFIGURES_LCX                              */
/*==============================================================*/
create index BILLINGREGIONFIGURES_LCX on BILLINGREGIONFIGURES (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGREGIONIMPORTS                                  */
/*==============================================================*/
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
   LASTCHANGED          datetime             null
)
go

alter table BILLINGREGIONIMPORTS
   add constraint BILLINGREGIONIMPORTS_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, REGIONID, IMPORTFROM)
go

/*==============================================================*/
/* Index: BILLINGREGIONIMPORTS_LCX                              */
/*==============================================================*/
create index BILLINGREGIONIMPORTS_LCX on BILLINGREGIONIMPORTS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGRESERVERECOVERY                                */
/*==============================================================*/
create table BILLINGRESERVERECOVERY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   MARKETRESERVE        numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLINGRESERVERECOVERY
   add constraint BILLRESERVERECOVERY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID)
go

/*==============================================================*/
/* Index: BILLINGRESERVERECOVERY_LCX                            */
/*==============================================================*/
create index BILLINGRESERVERECOVERY_LCX on BILLINGRESERVERECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGRESERVEREGIONRECOVERY                          */
/*==============================================================*/
create table BILLINGRESERVEREGIONRECOVERY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   REGIONRESERVE        numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLINGRESERVEREGIONRECOVERY
   add constraint BILLRESERVEREGIONRECOVERY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID)
go

/*==============================================================*/
/* Index: BILLINGRESERVEREGIONRECOV_LCX                         */
/*==============================================================*/
create index BILLINGRESERVEREGIONRECOV_LCX on BILLINGRESERVEREGIONRECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGRESERVETRADER                                  */
/*==============================================================*/
create table BILLINGRESERVETRADER (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   MARKETRESERVE        numeric(15,5)        null,
   TOTALRESERVE         numeric(15,5)        null,
   LASTCHANGED          datetime             null,
   TOTALCAPDIFFERENCE   numeric(15,5)        null
)
go

alter table BILLINGRESERVETRADER
   add constraint BILLINGRESERVETRADER_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID)
go

/*==============================================================*/
/* Index: BILLINGRESERVETRADER_LCX                              */
/*==============================================================*/
create index BILLINGRESERVETRADER_LCX on BILLINGRESERVETRADER (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGRESERVETRADERREGION                            */
/*==============================================================*/
create table BILLINGRESERVETRADERREGION (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   REGIONRESERVE        numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLINGRESERVETRADERREGION
   add constraint BILLINGRESERVETRADERREGION_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID)
go

/*==============================================================*/
/* Index: BILLINGRESERVETRADERREGIO_LCX                         */
/*==============================================================*/
create index BILLINGRESERVETRADERREGIO_LCX on BILLINGRESERVETRADERREGION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGRUNTRK                                         */
/*==============================================================*/
create table BILLINGRUNTRK (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   STATUS               varchar(6)           null,
   ADJ_CLEARED          varchar(1)           null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(10)          null,
   POSTDATE             datetime             null,
   POSTBY               varchar(10)          null,
   LASTCHANGED          datetime             null,
   RECEIPTPOSTDATE      datetime             null,
   RECEIPTPOSTBY        varchar(10)          null,
   PAYMENTPOSTDATE      datetime             null,
   PAYMENTPOSTBY        varchar(10)          null,
   SHORTFALL            numeric(16,6)        null,
   MAKEUP               numeric(15,5)        null
)
go

alter table BILLINGRUNTRK
   add constraint BILLINGRUNTRK_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO)
go

/*==============================================================*/
/* Index: BILLINGRUNTRK_LCX                                     */
/*==============================================================*/
create index BILLINGRUNTRK_LCX on BILLINGRUNTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINGSMELTERREDUCTION                               */
/*==============================================================*/
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
   LASTCHANGED          datetime             null
)
go

alter table BILLINGSMELTERREDUCTION
   add constraint BILLINGSMELTERREDUCTION_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID)
go

/*==============================================================*/
/* Index: BILLINGSMELTERREDUCT_NDX2                             */
/*==============================================================*/
create index BILLINGSMELTERREDUCT_NDX2 on BILLINGSMELTERREDUCTION (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: BILLINGSMELTERREDUCTION_LCX                           */
/*==============================================================*/
create index BILLINGSMELTERREDUCTION_LCX on BILLINGSMELTERREDUCTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLING_APC_COMPENSATION                              */
/*==============================================================*/
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
   LASTCHANGED          datetime             null
)
go

alter table BILLING_APC_COMPENSATION
   add constraint BILLING_APC_COMPENSATION_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, APEVENTID, CLAIMID)
go

/*==============================================================*/
/* Table: BILLING_APC_RECOVERY                                  */
/*==============================================================*/
create table BILLING_APC_RECOVERY (
   CONTRACTYEAR         numeric(4)           not null,
   WEEKNO               numeric(3)           not null,
   BILLRUNNO            numeric(3)           not null,
   APEVENTID            numeric(6)           not null,
   CLAIMID              numeric(6)           not null,
   PARTICIPANTID        varchar(20)          not null,
   REGIONID             varchar(20)          not null,
   RECOVERY_AMOUNT      numeric(18,8)        null,
   ELIGIBILITY_START_INTERVAL datetime             null,
   ELIGIBILITY_END_INTERVAL datetime             null,
   PARTICIPANT_DEMAND   numeric(18,8)        null,
   REGION_DEMAND        numeric(18,8)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLING_APC_RECOVERY
   add constraint BILLING_APC_RECOVERY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, APEVENTID, CLAIMID, PARTICIPANTID, REGIONID)
go

/*==============================================================*/
/* Table: BILLING_CO2E_PUBLICATION                              */
/*==============================================================*/
create table BILLING_CO2E_PUBLICATION (
   CONTRACTYEAR         numeric(4)           not null,
   WEEKNO               numeric(3)           not null,
   BILLRUNNO            numeric(3)           not null,
   SETTLEMENTDATE       datetime             not null,
   REGIONID             varchar(20)          not null,
   SENTOUTENERGY        numeric(18,8)        null,
   GENERATOREMISSIONS   numeric(18,8)        null,
   INTENSITYINDEX       numeric(18,8)        null
)
go

alter table BILLING_CO2E_PUBLICATION
   add constraint BILLING_CO2E_PUBLICATION_PK primary key (CONTRACTYEAR, WEEKNO, SETTLEMENTDATE, REGIONID)
go

/*==============================================================*/
/* Table: BILLING_CO2E_PUBLICATION_TRK                          */
/*==============================================================*/
create table BILLING_CO2E_PUBLICATION_TRK (
   CONTRACTYEAR         numeric(4)           not null,
   WEEKNO               numeric(3)           not null,
   BILLRUNNO            numeric(3)           null,
   LASTCHANGED          datetime             null
)
go

alter table BILLING_CO2E_PUBLICATION_TRK
   add constraint BILLING_CO2E_PUBLICATIO_TRK_PK primary key (CONTRACTYEAR, WEEKNO)
go

/*==============================================================*/
/* Table: BILLING_CSP_DEROGATION_AMOUNT                         */
/*==============================================================*/
create table BILLING_CSP_DEROGATION_AMOUNT (
   CONTRACTYEAR         numeric(4)           not null,
   WEEKNO               numeric(3)           not null,
   BILLRUNNO            numeric(3)           not null,
   PARTICIPANTID        varchar(10)          not null,
   AMOUNT_ID            varchar(20)          not null,
   DEROGATION_AMOUNT    numeric(18,8)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLING_CSP_DEROGATION_AMOUNT
   add constraint BILLING_CSP_DEROGATN_AMNT_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, AMOUNT_ID)
go

/*==============================================================*/
/* Index: BILLING_CSP_DEROGATN_AMNT_NDX1                        */
/*==============================================================*/
create index BILLING_CSP_DEROGATN_AMNT_NDX1 on BILLING_CSP_DEROGATION_AMOUNT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLING_DAILY_ENERGY_SUMMARY                          */
/*==============================================================*/
create table BILLING_DAILY_ENERGY_SUMMARY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   SETTLEMENTDATE       datetime             not null,
   PARTICIPANTID        varchar(20)          not null,
   REGIONID             varchar(20)          not null,
   CUSTOMER_ENERGY_PURCHASED numeric(18,8)        null,
   GENERATOR_ENERGY_SOLD numeric(18,8)        null,
   GENERATOR_ENERGY_PURCHASED numeric(18,8)        null
)
go

alter table BILLING_DAILY_ENERGY_SUMMARY
   add constraint BILLING_DAILY_ENRGY_SUMMARY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, SETTLEMENTDATE, PARTICIPANTID, REGIONID)
go

/*==============================================================*/
/* Table: BILLING_DIRECTION_RECONCILIATN                        */
/*==============================================================*/
create table BILLING_DIRECTION_RECONCILIATN (
   CONTRACTYEAR         numeric(4)           not null,
   WEEKNO               numeric(3)           not null,
   BILLRUNNO            numeric(3)           not null,
   DIRECTION_ID         varchar(20)          not null,
   DIRECTION_DESC       varchar(200)         null,
   DIRECTION_START_DATE datetime             null,
   DIRECTION_END_DATE   datetime             null,
   COMPENSATION_AMOUNT  numeric(16,6)        null,
   INDEPENDENT_EXPERT_FEE numeric(16,6)        null,
   INTEREST_AMOUNT      numeric(16,6)        null,
   CRA                  numeric(16,6)        null,
   NEM_FEE_ID           varchar(20)          null,
   NEM_FIXED_FEE_AMOUNT numeric(16,6)        null,
   MKT_CUSTOMER_PERC    numeric(16,6)        null,
   GENERATOR_PERC       numeric(16,6)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLING_DIRECTION_RECONCILIATN
   add constraint BILLING_DIRECTION_RCNCLTN_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, DIRECTION_ID)
go

/*==============================================================*/
/* Index: BILLING_DIRECTION_RCNCLTN_NDX1                        */
/*==============================================================*/
create index BILLING_DIRECTION_RCNCLTN_NDX1 on BILLING_DIRECTION_RECONCILIATN (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLING_DIRECTION_RECON_OTHER                         */
/*==============================================================*/
create table BILLING_DIRECTION_RECON_OTHER (
   CONTRACTYEAR         numeric(4)           not null,
   WEEKNO               numeric(3)           not null,
   BILLRUNNO            numeric(3)           not null,
   DIRECTION_ID         varchar(20)          not null,
   REGIONID             varchar(20)          not null,
   DIRECTION_DESC       varchar(200)         null,
   DIRECTION_TYPE_ID    varchar(20)          null,
   DIRECTION_START_DATE datetime             null,
   DIRECTION_END_DATE   datetime             null,
   DIRECTION_START_INTERVAL datetime             null,
   DIRECTION_END_INTERVAL datetime             null,
   COMPENSATION_AMOUNT  numeric(18,8)        null,
   INTEREST_AMOUNT      numeric(18,8)        null,
   INDEPENDENT_EXPERT_FEE numeric(18,8)        null,
   CRA                  numeric(18,8)        null,
   REGIONAL_CUSTOMER_ENERGY numeric(18,8)        null,
   REGIONAL_GENERATOR_ENERGY numeric(18,8)        null,
   REGIONAL_BENEFIT_FACTOR numeric(18,8)        null
)
go

alter table BILLING_DIRECTION_RECON_OTHER
   add constraint BILLING_DIRECTION_REC_OTHER_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, DIRECTION_ID, REGIONID)
go

/*==============================================================*/
/* Table: BILLING_EFTSHORTFALL_AMOUNT                           */
/*==============================================================*/
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
)
go

alter table BILLING_EFTSHORTFALL_AMOUNT
   add constraint BILLING_EFTSHORTFALL_AMT_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID)
go

/*==============================================================*/
/* Table: BILLING_EFTSHORTFALL_DETAIL                           */
/*==============================================================*/
create table BILLING_EFTSHORTFALL_DETAIL (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(20)          not null,
   TRANSACTION_TYPE     varchar(40)          not null,
   AMOUNT               numeric(18,8)        null
)
go

alter table BILLING_EFTSHORTFALL_DETAIL
   add constraint BILLING_EFTSHORTFALL_DETL_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, TRANSACTION_TYPE)
go

/*==============================================================*/
/* Table: BILLING_GST_DETAIL                                    */
/*==============================================================*/
create table BILLING_GST_DETAIL (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   BAS_CLASS            varchar(30)          not null,
   TRANSACTION_TYPE     varchar(30)          not null,
   GST_EXCLUSIVE_AMOUNT numeric(15,5)        null,
   GST_AMOUNT           numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLING_GST_DETAIL
   add constraint BILLING_GST_DETAIL_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, TRANSACTION_TYPE, BAS_CLASS)
go

/*==============================================================*/
/* Index: BILLING_GST_DETAIL_LCX                                */
/*==============================================================*/
create index BILLING_GST_DETAIL_LCX on BILLING_GST_DETAIL (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLING_GST_SUMMARY                                   */
/*==============================================================*/
create table BILLING_GST_SUMMARY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   BAS_CLASS            varchar(30)          not null,
   GST_EXCLUSIVE_AMOUNT numeric(15,5)        null,
   GST_AMOUNT           numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLING_GST_SUMMARY
   add constraint BILLING_GST_SUMMARY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, BAS_CLASS)
go

/*==============================================================*/
/* Index: BILLING_GST_SUMMARY_LCX                               */
/*==============================================================*/
create index BILLING_GST_SUMMARY_LCX on BILLING_GST_SUMMARY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLING_MR_PAYMENT                                    */
/*==============================================================*/
create table BILLING_MR_PAYMENT (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   MR_DATE              datetime             not null,
   REGIONID             varchar(10)          not null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          not null,
   MR_AMOUNT            numeric(16,6)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLING_MR_PAYMENT
   add constraint BILLING_MR_PAYMENT_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, MR_DATE, REGIONID, DUID)
go

/*==============================================================*/
/* Index: BILLING_MR_PAYMENT_LCX                                */
/*==============================================================*/
create index BILLING_MR_PAYMENT_LCX on BILLING_MR_PAYMENT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLING_MR_RECOVERY                                   */
/*==============================================================*/
create table BILLING_MR_RECOVERY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   MR_DATE              datetime             not null,
   REGIONID             varchar(10)          not null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          not null,
   MR_AMOUNT            numeric(16,6)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLING_MR_RECOVERY
   add constraint BILLING_MR_RECOVERY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, MR_DATE, REGIONID, DUID)
go

/*==============================================================*/
/* Index: BILLING_MR_RECOVERY_LCX                               */
/*==============================================================*/
create index BILLING_MR_RECOVERY_LCX on BILLING_MR_RECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLING_MR_SHORTFALL                                  */
/*==============================================================*/
create table BILLING_MR_SHORTFALL (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   MR_DATE              datetime             not null,
   REGIONID             varchar(10)          not null,
   PARTICIPANTID        varchar(10)          not null,
   AGE                  numeric(16,6)        null,
   RSA                  numeric(16,6)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLING_MR_SHORTFALL
   add constraint BILLING_MR_SHORTFALL_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, MR_DATE, REGIONID, PARTICIPANTID)
go

/*==============================================================*/
/* Index: BILLING_MR_SHORTFALL_LCX                              */
/*==============================================================*/
create index BILLING_MR_SHORTFALL_LCX on BILLING_MR_SHORTFALL (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLING_MR_SUMMARY                                    */
/*==============================================================*/
create table BILLING_MR_SUMMARY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   MR_DATE              datetime             not null,
   REGIONID             varchar(10)          not null,
   TOTAL_PAYMENTS       numeric(16,6)        null,
   TOTAL_RECOVERY       numeric(16,6)        null,
   TOTAL_RSA            numeric(16,6)        null,
   AAGE                 numeric(16,6)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLING_MR_SUMMARY
   add constraint BILLING_MR_SUMMARY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, MR_DATE, REGIONID)
go

/*==============================================================*/
/* Index: BILLING_MR_SUMMARY_LCX                                */
/*==============================================================*/
create index BILLING_MR_SUMMARY_LCX on BILLING_MR_SUMMARY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLING_NMAS_TST_PAYMENTS                             */
/*==============================================================*/
create table BILLING_NMAS_TST_PAYMENTS (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(20)          not null,
   SERVICE              varchar(10)          not null,
   CONTRACTID           varchar(10)          not null,
   PAYMENT_AMOUNT       numeric(18,8)        null
)
go

alter table BILLING_NMAS_TST_PAYMENTS
   add constraint PK_BILLING_NMAS_TST_PAYMENTS primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, SERVICE, CONTRACTID)
go

/*==============================================================*/
/* Table: BILLING_NMAS_TST_RECOVERY                             */
/*==============================================================*/
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
   RECOVERY_START_DATE  datetime             null,
   RECOVERY_END_DATE    datetime             null,
   PARTICIPANT_ENERGY   numeric(18,8)        null,
   REGION_ENERGY        numeric(18,8)        null,
   NEM_ENERGY           numeric(18,8)        null,
   CUSTOMER_PROPORTION  numeric(18,8)        null,
   GENERATOR_PROPORTION numeric(18,8)        null,
   PARTICIPANT_GENERATION numeric(18,8)        null,
   NEM_GENERATION       numeric(18,8)        null,
   RECOVERY_AMOUNT      numeric(18,8)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLING_NMAS_TST_RECOVERY
   add constraint PK_BILLING_NMAS_TST_RECOVERY primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, SERVICE, CONTRACTID, REGIONID)
go

/*==============================================================*/
/* Index: BILLING_NMAS_TST_RECOVERY_LCX                         */
/*==============================================================*/
create index BILLING_NMAS_TST_RECOVERY_LCX on BILLING_NMAS_TST_RECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLING_NMAS_TST_RECVRY_RBF                           */
/*==============================================================*/
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
   LASTCHANGED          datetime             null
)
go

alter table BILLING_NMAS_TST_RECVRY_RBF
   add constraint PK_BILLING_NMAS_TST_RECVRY_RBF primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, SERVICE, CONTRACTID, REGIONID)
go

/*==============================================================*/
/* Index: BILLING_NMAS_TST_RCVRY_RBF_LCX                        */
/*==============================================================*/
create index BILLING_NMAS_TST_RCVRY_RBF_LCX on BILLING_NMAS_TST_RECVRY_RBF (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLING_NMAS_TST_RECVRY_TRK                           */
/*==============================================================*/
create table BILLING_NMAS_TST_RECVRY_TRK (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   RECOVERY_CONTRACTYEAR numeric(4,0)         not null,
   RECOVERY_WEEKNO      numeric(3,0)         not null,
   RECOVERY_BILLRUNNO   numeric(3,0)         not null
)
go

alter table BILLING_NMAS_TST_RECVRY_TRK
   add constraint PK_BILLING_NMAS_TST_RECVRY_TRK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, RECOVERY_CONTRACTYEAR, RECOVERY_WEEKNO, RECOVERY_BILLRUNNO)
go

/*==============================================================*/
/* Table: BILLING_RES_TRADER_PAYMENT                            */
/*==============================================================*/
create table BILLING_RES_TRADER_PAYMENT (
   CONTRACTYEAR         numeric(4)           not null,
   WEEKNO               numeric(3)           not null,
   BILLRUNNO            numeric(3)           not null,
   CONTRACTID           varchar(20)          not null,
   PAYMENT_TYPE         varchar(40)          not null,
   PARTICIPANTID        varchar(20)          not null,
   PAYMENT_AMOUNT       numeric(18,8)        null
)
go

alter table BILLING_RES_TRADER_PAYMENT
   add constraint BILLING_RES_TRADER_PAYMENT_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, CONTRACTID, PAYMENT_TYPE, PARTICIPANTID)
go

/*==============================================================*/
/* Table: BILLING_RES_TRADER_RECOVERY                           */
/*==============================================================*/
create table BILLING_RES_TRADER_RECOVERY (
   CONTRACTYEAR         numeric(4)           not null,
   WEEKNO               numeric(3)           not null,
   BILLRUNNO            numeric(3)           not null,
   REGIONID             varchar(20)          not null,
   PARTICIPANTID        varchar(20)          not null,
   RECOVERY_AMOUNT      numeric(18,8)        null
)
go

alter table BILLING_RES_TRADER_RECOVERY
   add constraint BILLING_RES_TRADER_RECOVERY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, REGIONID, PARTICIPANTID)
go

/*==============================================================*/
/* Table: BILLING_SECDEPOSIT_APPLICATION                        */
/*==============================================================*/
create table BILLING_SECDEPOSIT_APPLICATION (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(20)          not null,
   APPLICATION_AMOUNT   numeric(18,8)        null
)
go

alter table BILLING_SECDEPOSIT_APPLICATION
   add constraint BILLING_SECDEPOSIT_APPL_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID)
go

/*==============================================================*/
/* Table: BILLING_SECDEP_INTEREST_PAY                           */
/*==============================================================*/
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
)
go

alter table BILLING_SECDEP_INTEREST_PAY
   add constraint BILLING_SECDEP_INTEREST_PAY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, SECURITY_DEPOSIT_ID, PARTICIPANTID)
go

/*==============================================================*/
/* Table: BILLING_SECDEP_INTEREST_RATE                          */
/*==============================================================*/
create table BILLING_SECDEP_INTEREST_RATE (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   INTEREST_ACCT_ID     varchar(20)          not null,
   EFFECTIVEDATE        datetime             not null,
   INTEREST_RATE        numeric(18,8)        null
)
go

alter table BILLING_SECDEP_INTEREST_RATE
   add constraint BILL_SECDEP_INTEREST_RATE_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, INTEREST_ACCT_ID, EFFECTIVEDATE)
go

/*==============================================================*/
/* Table: BILLINTERVENTIONRECOVERY                              */
/*==============================================================*/
create table BILLINTERVENTIONRECOVERY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   MARKETINTERVENTION   numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLINTERVENTIONRECOVERY
   add constraint BILLINTERVENTIONRECOVERY_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID)
go

/*==============================================================*/
/* Index: BILLINTERVENTIONRECOVERY_LCX                          */
/*==============================================================*/
create index BILLINTERVENTIONRECOVERY_LCX on BILLINTERVENTIONRECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLINTERVENTIONREGIONRECOVERY                        */
/*==============================================================*/
create table BILLINTERVENTIONREGIONRECOVERY (
   CONTRACTYEAR         numeric(4,0)         not null,
   WEEKNO               numeric(3,0)         not null,
   BILLRUNNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   REGIONINTERVENTION   numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table BILLINTERVENTIONREGIONRECOVERY
   add constraint BILLINTERVENTIONREGIONRECOV_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, REGIONID)
go

/*==============================================================*/
/* Index: BILLINTERVENTIONREGIONREC_LCX                         */
/*==============================================================*/
create index BILLINTERVENTIONREGIONREC_LCX on BILLINTERVENTIONREGIONRECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLSMELTERRATE                                       */
/*==============================================================*/
create table BILLSMELTERRATE (
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   CONTRACTYEAR         numeric(22,0)        not null,
   RAR1                 numeric(6,2)         null,
   RAR2                 numeric(6,2)         null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(10)          null,
   LASTCHANGED          datetime             null
)
go

alter table BILLSMELTERRATE
   add constraint BILLSMELTERRATE_PK primary key (EFFECTIVEDATE, VERSIONNO, CONTRACTYEAR)
go

/*==============================================================*/
/* Index: BILLSMELTERRATE_LCX                                   */
/*==============================================================*/
create index BILLSMELTERRATE_LCX on BILLSMELTERRATE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: BILLWHITEHOLE                                         */
/*==============================================================*/
create table BILLWHITEHOLE (
   CONTRACTYEAR         numeric(22,0)        not null,
   WEEKNO               numeric(22,0)        not null,
   BILLRUNNO            numeric(22,0)        not null,
   PARTICIPANTID        varchar(10)          not null,
   NL                   numeric(15,6)        null,
   PARTICIPANTDEMAND    numeric(15,6)        null,
   REGIONDEMAND         numeric(15,6)        null,
   WHITEHOLEPAYMENT     numeric(15,6)        null,
   LASTCHANGED          datetime             null,
   INTERCONNECTORID     varchar(10)          not null
)
go

alter table BILLWHITEHOLE
   add constraint BILLWHITEHOLE_PK primary key (CONTRACTYEAR, WEEKNO, BILLRUNNO, PARTICIPANTID, INTERCONNECTORID)
go

/*==============================================================*/
/* Index: BILLWHITEHOLE_LCX                                     */
/*==============================================================*/
create index BILLWHITEHOLE_LCX on BILLWHITEHOLE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: CONNECTIONPOINT                                       */
/*==============================================================*/
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
   LASTCHANGED          datetime             null
)
go

alter table CONNECTIONPOINT
   add constraint CONNECTIONPOINT_PK primary key (CONNECTIONPOINTID)
go

/*==============================================================*/
/* Index: CONNECTIONPOINT_LCX                                   */
/*==============================================================*/
create index CONNECTIONPOINT_LCX on CONNECTIONPOINT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: CONNECTIONPOINTDETAILS                                */
/*==============================================================*/
create table CONNECTIONPOINTDETAILS (
   EFFECTIVEDATE        datetime             not null,
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
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null,
   INUSE                varchar(1)           null,
   LNSP                 varchar(10)          null,
   MDA                  varchar(10)          null,
   ROLR                 varchar(10)          null,
   RP                   varchar(10)          null,
   AGGREGATEDDATA       varchar(1)           null,
   VALID_TODATE         datetime             null,
   LR                   varchar(10)          null
)
go

alter table CONNECTIONPOINTDETAILS
   add constraint CONNECTIONPOINTDETAILS_PK primary key (EFFECTIVEDATE, VERSIONNO, CONNECTIONPOINTID)
go

/*==============================================================*/
/* Index: CONNECTIONPOINTDETAILS_LCX                            */
/*==============================================================*/
create index CONNECTIONPOINTDETAILS_LCX on CONNECTIONPOINTDETAILS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: CONNECTIONPOINTDETAI_NDX2                             */
/*==============================================================*/
create index CONNECTIONPOINTDETAI_NDX2 on CONNECTIONPOINTDETAILS (
METERDATAPROVIDER ASC,
NETWORKSERVICEPROVIDER ASC,
FINRESPORGAN ASC
)
go

/*==============================================================*/
/* Index: CONNECTIONPOINTDETAI_NDX3                             */
/*==============================================================*/
create index CONNECTIONPOINTDETAI_NDX3 on CONNECTIONPOINTDETAILS (
CONNECTIONPOINTID ASC
)
go

/*==============================================================*/
/* Table: CONNECTIONPOINTOPERATINGSTA                           */
/*==============================================================*/
create table CONNECTIONPOINTOPERATINGSTA (
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   CONNECTIONPOINTID    varchar(10)          not null,
   OPERATINGSTATUS      varchar(16)          null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   LASTCHANGED          datetime             null
)
go

alter table CONNECTIONPOINTOPERATINGSTA
   add constraint CPOPSTATUS_PK primary key (EFFECTIVEDATE, VERSIONNO, CONNECTIONPOINTID)
go

/*==============================================================*/
/* Index: CONNECTIONPOINTOPERA_NDX2                             */
/*==============================================================*/
create index CONNECTIONPOINTOPERA_NDX2 on CONNECTIONPOINTOPERATINGSTA (
CONNECTIONPOINTID ASC
)
go

/*==============================================================*/
/* Index: CONNECTIONPOINTOPERATINGS_LCX                         */
/*==============================================================*/
create index CONNECTIONPOINTOPERATINGS_LCX on CONNECTIONPOINTOPERATINGSTA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: CONSTRAINTRELAXATION_OCD                              */
/*==============================================================*/
create table CONSTRAINTRELAXATION_OCD (
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3,0)         not null,
   CONSTRAINTID         varchar(20)          not null,
   RHS                  numeric(16,6)        null,
   LASTCHANGED          datetime             null,
   VERSIONNO            numeric(3,0)         not null default 1
)
go

alter table CONSTRAINTRELAXATION_OCD
   add constraint PK_CONSTRAINTRELAXATION_OCD primary key (SETTLEMENTDATE, RUNNO, CONSTRAINTID, VERSIONNO)
go

/*==============================================================*/
/* Index: CONSTRAINTRELAX_OCD_LCX                               */
/*==============================================================*/
create index CONSTRAINTRELAX_OCD_LCX on CONSTRAINTRELAXATION_OCD (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: CONTRACTAGC                                           */
/*==============================================================*/
create table CONTRACTAGC (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   STARTDATE            datetime             null,
   ENDDATE              datetime             null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          null,
   CRR                  numeric(4,0)         null,
   CRL                  numeric(4,0)         null,
   RLPRICE              numeric(10,2)        null,
   CCPRICE              numeric(10,2)        null,
   BS                   numeric(10,2)        null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table CONTRACTAGC
   add constraint CONTRACTAGC_PK primary key (CONTRACTID, VERSIONNO)
go

/*==============================================================*/
/* Index: CONTRACTAGC_NDX2                                      */
/*==============================================================*/
create index CONTRACTAGC_NDX2 on CONTRACTAGC (
PARTICIPANTID ASC,
CONTRACTID ASC
)
go

/*==============================================================*/
/* Index: CONTRACTAGC_LCX                                       */
/*==============================================================*/
create index CONTRACTAGC_LCX on CONTRACTAGC (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: CONTRACTGOVERNOR                                      */
/*==============================================================*/
create table CONTRACTGOVERNOR (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   STARTDATE            datetime             null,
   ENDDATE              datetime             null,
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
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table CONTRACTGOVERNOR
   add constraint CONTRACTGOVERNOR_PK primary key (CONTRACTID, VERSIONNO)
go

/*==============================================================*/
/* Index: CONTRACTGOVERNOR_NDX2                                 */
/*==============================================================*/
create index CONTRACTGOVERNOR_NDX2 on CONTRACTGOVERNOR (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: CONTRACTGOVERNOR_LCX                                  */
/*==============================================================*/
create index CONTRACTGOVERNOR_LCX on CONTRACTGOVERNOR (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: CONTRACTLOADSHED                                      */
/*==============================================================*/
create table CONTRACTLOADSHED (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   STARTDATE            datetime             null,
   ENDDATE              datetime             null,
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
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null,
   DEFAULT_TESTINGPAYMENT_AMOUNT numeric(18,8)        null,
   SERVICE_START_DATE   datetime             null
)
go

alter table CONTRACTLOADSHED
   add constraint CONTRACTLOADSHED_PK primary key (CONTRACTID, VERSIONNO)
go

/*==============================================================*/
/* Index: CONTRACTLOADSHED_NDX2                                 */
/*==============================================================*/
create index CONTRACTLOADSHED_NDX2 on CONTRACTLOADSHED (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: CONTRACTLOADSHED_LCX                                  */
/*==============================================================*/
create index CONTRACTLOADSHED_LCX on CONTRACTLOADSHED (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: CONTRACTREACTIVEPOWER                                 */
/*==============================================================*/
create table CONTRACTREACTIVEPOWER (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   STARTDATE            datetime             null,
   ENDDATE              datetime             null,
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
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null,
   DEFAULT_TESTINGPAYMENT_AMOUNT numeric(18,8)        null,
   SERVICE_START_DATE   datetime             null,
   AVAILABILITY_MWH_THRESHOLD numeric(18,8)        null,
   MVAR_THRESHOLD       numeric(18,8)        null,
   REBATE_CAP           numeric(18,8)        null,
   REBATE_AMOUNT_PER_MVAR numeric(18,8)        null,
   ISREBATEAPPLICABLE   numeric(1,0)         null
)
go

alter table CONTRACTREACTIVEPOWER
   add constraint CONTRACTREACTIVEPOWER_PK primary key (CONTRACTID, VERSIONNO)
go

/*==============================================================*/
/* Index: CONTRACTREACTIVEPOWE_NDX2                             */
/*==============================================================*/
create index CONTRACTREACTIVEPOWE_NDX2 on CONTRACTREACTIVEPOWER (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: CONTRACTREACTIVEPOWER_LCX                             */
/*==============================================================*/
create index CONTRACTREACTIVEPOWER_LCX on CONTRACTREACTIVEPOWER (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: CONTRACTRESERVEFLAG                                   */
/*==============================================================*/
create table CONTRACTRESERVEFLAG (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   RCF                  char(1)              null,
   LASTCHANGED          datetime             null
)
go

alter table CONTRACTRESERVEFLAG
   add constraint CONTRACTRESERVEFLAG_PK primary key (CONTRACTID, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: CONTRACTRESERVEFLAG_LCX                               */
/*==============================================================*/
create index CONTRACTRESERVEFLAG_LCX on CONTRACTRESERVEFLAG (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: CONTRACTRESERVETHRESHOLD                              */
/*==============================================================*/
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
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table CONTRACTRESERVETHRESHOLD
   add constraint CONTRACTRESERVETHRESHOLD_PK primary key (CONTRACTID, VERSIONNO)
go

/*==============================================================*/
/* Index: CONTRACTRESERVETHRESHOLD_LCX                          */
/*==============================================================*/
create index CONTRACTRESERVETHRESHOLD_LCX on CONTRACTRESERVETHRESHOLD (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: CONTRACTRESERVETRADER                                 */
/*==============================================================*/
create table CONTRACTRESERVETRADER (
   CONTRACTID           varchar(10)          not null,
   DUID                 varchar(10)          null,
   STARTDATE            datetime             null,
   ENDDATE              datetime             null,
   STARTPERIOD          numeric(3,0)         null,
   ENDPERIOD            numeric(3,0)         null,
   DEREGISTRATIONDATE   datetime             null,
   DEREGISTRATIONPERIOD numeric(3,0)         null,
   PARTICIPANTID        varchar(10)          null,
   LASTCHANGED          datetime             null,
   REGIONID             varchar(10)          null
)
go

alter table CONTRACTRESERVETRADER
   add constraint CONTRACTRESERVETRADER_PK primary key (CONTRACTID)
go

/*==============================================================*/
/* Index: CONTRACTRESERVETRADER_LCX                             */
/*==============================================================*/
create index CONTRACTRESERVETRADER_LCX on CONTRACTRESERVETRADER (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: CONTRACTRESTARTSERVICES                               */
/*==============================================================*/
create table CONTRACTRESTARTSERVICES (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   STARTDATE            datetime             null,
   ENDDATE              datetime             null,
   PARTICIPANTID        varchar(10)          null,
   RESTARTTYPE          numeric(1,0)         null,
   RCPRICE              numeric(6,2)         null,
   TRIPTOHOUSELEVEL     numeric(5,0)         null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null,
   DEFAULT_TESTINGPAYMENT_AMOUNT numeric(18,8)        null,
   SERVICE_START_DATE   datetime             null
)
go

alter table CONTRACTRESTARTSERVICES
   add constraint CONTRACTRESTARTSERVICES_PK primary key (CONTRACTID, VERSIONNO)
go

/*==============================================================*/
/* Index: CONTRACTRESTARTSERVI_NDX2                             */
/*==============================================================*/
create index CONTRACTRESTARTSERVI_NDX2 on CONTRACTRESTARTSERVICES (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: CONTRACTRESTARTSERVICES_LCX                           */
/*==============================================================*/
create index CONTRACTRESTARTSERVICES_LCX on CONTRACTRESTARTSERVICES (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: CONTRACTRESTARTUNITS                                  */
/*==============================================================*/
create table CONTRACTRESTARTUNITS (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   DUID                 varchar(10)          not null,
   LASTCHANGED          datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       datetime             null
)
go

alter table CONTRACTRESTARTUNITS
   add constraint CONTRACTRESTARTUNITS_PK primary key (CONTRACTID, VERSIONNO, DUID)
go

/*==============================================================*/
/* Index: CONTRACTRESTARTUNITS_NDX2                             */
/*==============================================================*/
create index CONTRACTRESTARTUNITS_NDX2 on CONTRACTRESTARTUNITS (
CONTRACTID ASC
)
go

/*==============================================================*/
/* Index: CONTRACTRESTARTUNITS_LCX                              */
/*==============================================================*/
create index CONTRACTRESTARTUNITS_LCX on CONTRACTRESTARTUNITS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: CONTRACTUNITLOADING                                   */
/*==============================================================*/
create table CONTRACTUNITLOADING (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   STARTDATE            datetime             null,
   ENDDATE              datetime             null,
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
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table CONTRACTUNITLOADING
   add constraint CONTRACTUNITLOADING_PK primary key (CONTRACTID, VERSIONNO)
go

/*==============================================================*/
/* Index: CONTRACTUNITLOADING_NDX2                              */
/*==============================================================*/
create index CONTRACTUNITLOADING_NDX2 on CONTRACTUNITLOADING (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: CONTRACTUNITLOADING_LCX                               */
/*==============================================================*/
create index CONTRACTUNITLOADING_LCX on CONTRACTUNITLOADING (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: CONTRACTUNITUNLOADING                                 */
/*==============================================================*/
create table CONTRACTUNITUNLOADING (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   STARTDATE            datetime             null,
   ENDDATE              datetime             null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          null,
   RPRICE               numeric(10,2)        null,
   SUPRICE              numeric(10,2)        null,
   CCPRICE              numeric(10,2)        null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table CONTRACTUNITUNLOADING
   add constraint CONTRACTUNITUNLOADING_PK primary key (CONTRACTID, VERSIONNO)
go

/*==============================================================*/
/* Index: CONTRACTUNITUNLOADIN_NDX2                             */
/*==============================================================*/
create index CONTRACTUNITUNLOADIN_NDX2 on CONTRACTUNITUNLOADING (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: CONTRACTUNITUNLOADING_LCX                             */
/*==============================================================*/
create index CONTRACTUNITUNLOADING_LCX on CONTRACTUNITUNLOADING (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DAYOFFER                                              */
/*==============================================================*/
create table DAYOFFER (
   SETTLEMENTDATE       datetime             not null,
   DUID                 varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   OFFERDATE            datetime             not null,
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
   LASTCHANGED          datetime             null,
   MR_FACTOR            numeric(16,6)        null
)
go

alter table DAYOFFER
   add constraint DAYOFFER_PK primary key (SETTLEMENTDATE, DUID, OFFERDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: DAYOFFER_NDX2                                         */
/*==============================================================*/
create index DAYOFFER_NDX2 on DAYOFFER (
DUID ASC,
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: DAYOFFER_LCX                                          */
/*==============================================================*/
create index DAYOFFER_LCX on DAYOFFER (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DAYOFFER_D                                            */
/*==============================================================*/
create table DAYOFFER_D (
   SETTLEMENTDATE       datetime             not null,
   DUID                 varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   OFFERDATE            datetime             not null,
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
   LASTCHANGED          datetime             null,
   MR_FACTOR            numeric(6,0)         null
)
go

alter table DAYOFFER_D
   add constraint DAYOFFER_D_PK primary key (SETTLEMENTDATE, DUID, OFFERDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: DAYOFFER_D_NDX2                                       */
/*==============================================================*/
create index DAYOFFER_D_NDX2 on DAYOFFER_D (
DUID ASC,
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: DAYOFFER_D_LCX                                        */
/*==============================================================*/
create index DAYOFFER_D_LCX on DAYOFFER_D (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DAYTRACK                                              */
/*==============================================================*/
create table DAYTRACK (
   SETTLEMENTDATE       datetime             not null,
   REGIONID             varchar(10)          null,
   EXANTERUNSTATUS      varchar(15)          null,
   EXANTERUNNO          numeric(3,0)         null,
   EXPOSTRUNSTATUS      varchar(15)          null,
   EXPOSTRUNNO          numeric(3,0)         not null,
   LASTCHANGED          datetime             null
)
go

alter table DAYTRACK
   add constraint DAYTRACK_PK primary key (SETTLEMENTDATE, EXPOSTRUNNO)
go

/*==============================================================*/
/* Index: DAYTRACK_LCX                                          */
/*==============================================================*/
create index DAYTRACK_LCX on DAYTRACK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DEFAULTDAYOFFER                                       */
/*==============================================================*/
create table DEFAULTDAYOFFER (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table DEFAULTDAYOFFER
   add constraint DEFDAYOFFER_PK primary key (SETTLEMENTDATE, DUID, VERSIONNO)
go

/*==============================================================*/
/* Index: DEFAULTDAYOFFER_LCX                                   */
/*==============================================================*/
create index DEFAULTDAYOFFER_LCX on DEFAULTDAYOFFER (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DEFAULTOFFERTRK                                       */
/*==============================================================*/
create table DEFAULTOFFERTRK (
   DUID                 varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   FILENAME             varchar(40)          null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table DEFAULTOFFERTRK
   add constraint DEFOFFERTRK_PK primary key (DUID, EFFECTIVEDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: DEFAULTOFFERTRK_LCX                                   */
/*==============================================================*/
create index DEFAULTOFFERTRK_LCX on DEFAULTOFFERTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DEFAULTPEROFFER                                       */
/*==============================================================*/
create table DEFAULTPEROFFER (
   SETTLEMENTDATE       datetime             not null,
   DUID                 varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   VERSIONNO            numeric(3,0)         not null,
   SELFDISPATCH         numeric(9,6)         null,
   MAXAVAIL             numeric(12,6)        null,
   FIXEDLOAD            numeric(9,6)         null,
   ROCUP                numeric(6,0)         null,
   ROCDOWN              numeric(6,0)         null,
   LASTCHANGED          datetime             null,
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
)
go

alter table DEFAULTPEROFFER
   add constraint DEFPEROFFER_PK primary key (DUID, SETTLEMENTDATE, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: DEFAULTPEROFFER_LCX                                   */
/*==============================================================*/
create index DEFAULTPEROFFER_LCX on DEFAULTPEROFFER (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DELTAMW                                               */
/*==============================================================*/
create table DELTAMW (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null,
   RAISEREG             numeric(6,0)         null,
   LOWERREG             numeric(6,0)         null
)
go

alter table DELTAMW
   add constraint DELTAMW_PK primary key (SETTLEMENTDATE, VERSIONNO, REGIONID, PERIODID)
go

/*==============================================================*/
/* Index: DELTAMW_LCX                                           */
/*==============================================================*/
create index DELTAMW_LCX on DELTAMW (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DEMANDOPERATIONALACTUAL                               */
/*==============================================================*/
create table DEMANDOPERATIONALACTUAL (
   INTERVAL_DATETIME    datetime             not null,
   REGIONID             varchar(20)          not null,
   OPERATIONAL_DEMAND   numeric(10,0)        null,
   LASTCHANGED          datetime             null
)
go

alter table DEMANDOPERATIONALACTUAL
   add constraint DEMANDOPERATIONALACTUAL_PK primary key (INTERVAL_DATETIME, REGIONID)
go

/*==============================================================*/
/* Table: DEMANDOPERATIONALFORECAST                             */
/*==============================================================*/
create table DEMANDOPERATIONALFORECAST (
   INTERVAL_DATETIME    datetime             not null,
   REGIONID             varchar(20)          not null,
   LOAD_DATE            datetime             null,
   OPERATIONAL_DEMAND_POE10 numeric(15,2)        null,
   OPERATIONAL_DEMAND_POE50 numeric(15,2)        null,
   OPERATIONAL_DEMAND_POE90 numeric(15,2)        null,
   LASTCHANGED          datetime             null
)
go

alter table DEMANDOPERATIONALFORECAST
   add constraint DEMANDOPERATIONALFORECAST_PK primary key (INTERVAL_DATETIME, REGIONID)
go

/*==============================================================*/
/* Table: DISPATCHABLEUNIT                                      */
/*==============================================================*/
create table DISPATCHABLEUNIT (
   DUID                 varchar(10)          not null,
   DUNAME               varchar(20)          null,
   UNITTYPE             varchar(20)          null,
   LASTCHANGED          datetime             null
)
go

alter table DISPATCHABLEUNIT
   add constraint DISPATCHABLEUNIT_PK primary key (DUID)
go

/*==============================================================*/
/* Index: DISPATCHABLEUNIT_LCX                                  */
/*==============================================================*/
create index DISPATCHABLEUNIT_LCX on DISPATCHABLEUNIT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCHBIDTRK                                        */
/*==============================================================*/
create table DISPATCHBIDTRK (
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3,0)         not null,
   OFFEREFFECTIVEDATE   datetime             not null,
   OFFERVERSIONNO       numeric(3,0)         not null,
   DUID                 varchar(10)          not null,
   BIDTYPE              varchar(10)          null,
   LASTCHANGED          datetime             null
)
go

alter table DISPATCHBIDTRK
   add constraint DISPATCHBIDTRK_PK primary key (SETTLEMENTDATE, RUNNO, OFFEREFFECTIVEDATE, OFFERVERSIONNO, DUID)
go

/*==============================================================*/
/* Index: DISPATCHBIDTRK_NDX2                                   */
/*==============================================================*/
create index DISPATCHBIDTRK_NDX2 on DISPATCHBIDTRK (
DUID ASC,
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: DISPATCHBIDTRK_LCX                                    */
/*==============================================================*/
create index DISPATCHBIDTRK_LCX on DISPATCHBIDTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCHBLOCKEDCONSTRAINT                             */
/*==============================================================*/
create table DISPATCHBLOCKEDCONSTRAINT (
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3,0)         not null,
   CONSTRAINTID         varchar(20)          not null
)
go

alter table DISPATCHBLOCKEDCONSTRAINT
   add constraint DISPATCHBLOCKEDCONSTRAINT_PK primary key (SETTLEMENTDATE, RUNNO, CONSTRAINTID)
go

/*==============================================================*/
/* Table: DISPATCHCASESOLUTION                                  */
/*==============================================================*/
create table DISPATCHCASESOLUTION (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null,
   SWITCHRUNINITIALSTATUS numeric(1,0)         null,
   SWITCHRUNBESTSTATUS  numeric(1,0)         null,
   SWITCHRUNBESTSTATUS_INT numeric(1,0)         null
)
go

alter table DISPATCHCASESOLUTION
   add constraint DISPATCHCASESOLUTION_PK primary key (SETTLEMENTDATE, RUNNO)
go

/*==============================================================*/
/* Index: DISPATCHCASESOLUTION_LCX                              */
/*==============================================================*/
create index DISPATCHCASESOLUTION_LCX on DISPATCHCASESOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCHCASESOLUTION_BNC                              */
/*==============================================================*/
create table DISPATCHCASESOLUTION_BNC (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table DISPATCHCASESOLUTION_BNC
   add constraint PK_DISPATCHCASESOLUTION_BNC primary key (SETTLEMENTDATE, RUNNO, INTERVENTION)
go

/*==============================================================*/
/* Index: DISPATCHCASESOLUTION_BNC_LCX                          */
/*==============================================================*/
create index DISPATCHCASESOLUTION_BNC_LCX on DISPATCHCASESOLUTION_BNC (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCHCASE_OCD                                      */
/*==============================================================*/
create table DISPATCHCASE_OCD (
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3,0)         not null,
   LASTCHANGED          datetime             null
)
go

alter table DISPATCHCASE_OCD
   add constraint DISPATCHCASE_OCD_PK primary key (SETTLEMENTDATE, RUNNO)
go

/*==============================================================*/
/* Index: DISPATCHCASE_OCD_LCX                                  */
/*==============================================================*/
create index DISPATCHCASE_OCD_LCX on DISPATCHCASE_OCD (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCHCONSTRAINT                                    */
/*==============================================================*/
create table DISPATCHCONSTRAINT (
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3,0)         not null,
   CONSTRAINTID         varchar(20)          not null,
   DISPATCHINTERVAL     numeric(22,0)        not null,
   INTERVENTION         numeric(2,0)         not null,
   RHS                  numeric(15,5)        null,
   MARGINALVALUE        numeric(15,5)        null,
   VIOLATIONDEGREE      numeric(15,5)        null,
   LASTCHANGED          datetime             null,
   DUID                 varchar(20)          null,
   GENCONID_EFFECTIVEDATE datetime             null,
   GENCONID_VERSIONNO   numeric(22,0)        null,
   LHS                  numeric(15,5)        null
)
go

alter table DISPATCHCONSTRAINT
   add constraint PK_DISPATCHCONSTRAINT primary key (SETTLEMENTDATE, RUNNO, CONSTRAINTID, DISPATCHINTERVAL, INTERVENTION)
go

/*==============================================================*/
/* Index: DISPATCHCONSTRAINT_NDX2                               */
/*==============================================================*/
create index DISPATCHCONSTRAINT_NDX2 on DISPATCHCONSTRAINT (
SETTLEMENTDATE ASC
)
go

/*==============================================================*/
/* Index: DISPATCHCONSTRAINT_LCX                                */
/*==============================================================*/
create index DISPATCHCONSTRAINT_LCX on DISPATCHCONSTRAINT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCHINTERCONNECTORRES                             */
/*==============================================================*/
create table DISPATCHINTERCONNECTORRES (
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   DISPATCHINTERVAL     numeric(22,0)        not null,
   INTERVENTION         numeric(2,0)         not null,
   METEREDMWFLOW        numeric(15,5)        null,
   MWFLOW               numeric(15,5)        null,
   MWLOSSES             numeric(15,5)        null,
   MARGINALVALUE        numeric(15,5)        null,
   VIOLATIONDEGREE      numeric(15,5)        null,
   LASTCHANGED          datetime             null,
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
)
go

alter table DISPATCHINTERCONNECTORRES
   add constraint PK_DISPATCHINTERCONNECTORRES primary key (SETTLEMENTDATE, RUNNO, INTERCONNECTORID, DISPATCHINTERVAL, INTERVENTION)
go

/*==============================================================*/
/* Index: DISPATCHINTERCONNECTORRES_LCX                         */
/*==============================================================*/
create index DISPATCHINTERCONNECTORRES_LCX on DISPATCHINTERCONNECTORRES (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCHLOAD                                          */
/*==============================================================*/
create table DISPATCHLOAD (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null,
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
)
go

alter table DISPATCHLOAD
   add constraint PK_DISPATCHLOAD primary key (SETTLEMENTDATE, RUNNO, DUID, INTERVENTION)
go

/*==============================================================*/
/* Index: DISPATCHLOAD_LCX                                      */
/*==============================================================*/
create index DISPATCHLOAD_LCX on DISPATCHLOAD (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: DISPATCHLOAD_NDX2                                     */
/*==============================================================*/
create index DISPATCHLOAD_NDX2 on DISPATCHLOAD (
DUID ASC,
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCHLOAD_BNC                                      */
/*==============================================================*/
create table DISPATCHLOAD_BNC (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table DISPATCHLOAD_BNC
   add constraint PK_DISPATCHLOAD_BNC primary key (SETTLEMENTDATE, RUNNO, DUID, INTERVENTION)
go

/*==============================================================*/
/* Index: DISPATCHLOAD_BNC_LCX                                  */
/*==============================================================*/
create index DISPATCHLOAD_BNC_LCX on DISPATCHLOAD_BNC (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: DISPATCHLOAD_BNC_NDX2                                 */
/*==============================================================*/
create index DISPATCHLOAD_BNC_NDX2 on DISPATCHLOAD_BNC (
DUID ASC,
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCHOFFERTRK                                      */
/*==============================================================*/
create table DISPATCHOFFERTRK (
   SETTLEMENTDATE       datetime             not null,
   DUID                 varchar(10)          not null,
   BIDTYPE              varchar(10)          not null,
   BIDSETTLEMENTDATE    datetime             null,
   BIDOFFERDATE         datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table DISPATCHOFFERTRK
   add constraint DISPATCHOFFERTRK_PK primary key (SETTLEMENTDATE, DUID, BIDTYPE)
go

/*==============================================================*/
/* Index: DISPATCHOFFERTRK_LCHD_IDX                             */
/*==============================================================*/
create index DISPATCHOFFERTRK_LCHD_IDX on DISPATCHOFFERTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: DISPATCHOFFERTRK_NDX2                                 */
/*==============================================================*/
create index DISPATCHOFFERTRK_NDX2 on DISPATCHOFFERTRK (
DUID ASC,
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCHPRICE                                         */
/*==============================================================*/
create table DISPATCHPRICE (
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   DISPATCHINTERVAL     varchar(22)          not null,
   INTERVENTION         numeric(2,0)         not null,
   RRP                  numeric(15,5)        null,
   EEP                  numeric(15,5)        null,
   ROP                  numeric(15,5)        null,
   APCFLAG              numeric(3,0)         null,
   MARKETSUSPENDEDFLAG  numeric(3,0)         null,
   LASTCHANGED          datetime             null,
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
)
go

alter table DISPATCHPRICE
   add constraint PK_DISPATCHPRICE primary key (SETTLEMENTDATE, RUNNO, REGIONID, DISPATCHINTERVAL, INTERVENTION)
go

/*==============================================================*/
/* Index: DISPATCHPRICE_LCX                                     */
/*==============================================================*/
create index DISPATCHPRICE_LCX on DISPATCHPRICE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCHREGIONSUM                                     */
/*==============================================================*/
create table DISPATCHREGIONSUM (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null,
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
)
go

alter table DISPATCHREGIONSUM
   add constraint PK_DISPATCHREGIONSUM primary key (SETTLEMENTDATE, RUNNO, REGIONID, DISPATCHINTERVAL, INTERVENTION)
go

/*==============================================================*/
/* Index: DISPATCHREGIONSUM_LCX                                 */
/*==============================================================*/
create index DISPATCHREGIONSUM_LCX on DISPATCHREGIONSUM (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCHTRK                                           */
/*==============================================================*/
create table DISPATCHTRK (
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3,0)         not null,
   REASON               varchar(64)          null,
   SPDRUNNO             numeric(3,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table DISPATCHTRK
   add constraint DISPATCHTRK_PK primary key (SETTLEMENTDATE, RUNNO)
go

/*==============================================================*/
/* Index: DISPATCHTRK_LCX                                       */
/*==============================================================*/
create index DISPATCHTRK_LCX on DISPATCHTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCH_CONSTRAINT_FCAS_OCD                          */
/*==============================================================*/
create table DISPATCH_CONSTRAINT_FCAS_OCD (
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3)           not null,
   INTERVENTION         numeric(2)           not null,
   CONSTRAINTID         varchar(20)          not null,
   VERSIONNO            numeric(3)           not null,
   LASTCHANGED          datetime             null,
   RHS                  numeric(15,5)        null,
   MARGINALVALUE        numeric(15,5)        null,
   VIOLATIONDEGREE      numeric(15,5)        null
)
go

alter table DISPATCH_CONSTRAINT_FCAS_OCD
   add constraint DISPATCH_CONSTRNT_FCAS_OCD_PK primary key (SETTLEMENTDATE, RUNNO, INTERVENTION, CONSTRAINTID, VERSIONNO)
go

/*==============================================================*/
/* Index: DISPATCH_CONSTRNT_FCASOCD_LCX                         */
/*==============================================================*/
create index DISPATCH_CONSTRNT_FCASOCD_LCX on DISPATCH_CONSTRAINT_FCAS_OCD (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCH_FCAS_REQ                                     */
/*==============================================================*/
create table DISPATCH_FCAS_REQ (
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3,0)         not null,
   INTERVENTION         numeric(2,0)         not null,
   GENCONID             varchar(20)          not null,
   REGIONID             varchar(10)          not null,
   BIDTYPE              varchar(10)          not null,
   GENCONEFFECTIVEDATE  datetime             null,
   GENCONVERSIONNO      numeric(3,0)         null,
   MARGINALVALUE        numeric(16,6)        null,
   LASTCHANGED          datetime             null,
   BASE_COST            numeric(18,8)        null,
   ADJUSTED_COST        numeric(18,8)        null,
   ESTIMATED_CMPF       numeric(18,8)        null,
   ESTIMATED_CRMPF      numeric(18,8)        null,
   RECOVERY_FACTOR_CMPF numeric(18,8)        null,
   RECOVERY_FACTOR_CRMPF numeric(18,8)        null
)
go

alter table DISPATCH_FCAS_REQ
   add constraint DISPATCH_FCAS_REQ_PK primary key (SETTLEMENTDATE, RUNNO, INTERVENTION, GENCONID, REGIONID, BIDTYPE)
go

/*==============================================================*/
/* Index: DISPATCH_FCAS_REQ_LCX                                 */
/*==============================================================*/
create index DISPATCH_FCAS_REQ_LCX on DISPATCH_FCAS_REQ (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCH_INTERCONNECTION                              */
/*==============================================================*/
create table DISPATCH_INTERCONNECTION (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table DISPATCH_INTERCONNECTION
   add constraint DISPATCH_INTERCONNECTION_PK primary key (SETTLEMENTDATE, RUNNO, FROM_REGIONID, TO_REGIONID, INTERVENTION)
go

/*==============================================================*/
/* Table: DISPATCH_LOCAL_PRICE                                  */
/*==============================================================*/
create table DISPATCH_LOCAL_PRICE (
   SETTLEMENTDATE       datetime             not null,
   DUID                 varchar(20)          not null,
   LOCAL_PRICE_ADJUSTMENT numeric(10,2)        null,
   LOCALLY_CONSTRAINED  numeric(1,0)         null
)
go

alter table DISPATCH_LOCAL_PRICE
   add constraint DISPATCH_LOCAL_PRICE_PK primary key (SETTLEMENTDATE, DUID)
go

/*==============================================================*/
/* Table: DISPATCH_MNSPBIDTRK                                   */
/*==============================================================*/
create table DISPATCH_MNSPBIDTRK (
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   LINKID               varchar(10)          not null,
   OFFERSETTLEMENTDATE  datetime             null,
   OFFEREFFECTIVEDATE   datetime             null,
   OFFERVERSIONNO       numeric(3,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table DISPATCH_MNSPBIDTRK
   add constraint DISPATCH_MNSPBIDTRK_PK primary key (SETTLEMENTDATE, RUNNO, PARTICIPANTID, LINKID)
go

/*==============================================================*/
/* Index: DISPATCH_MNSPBIDTRK_LCX                               */
/*==============================================================*/
create index DISPATCH_MNSPBIDTRK_LCX on DISPATCH_MNSPBIDTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCH_MR_SCHEDULE_TRK                              */
/*==============================================================*/
create table DISPATCH_MR_SCHEDULE_TRK (
   SETTLEMENTDATE       datetime             not null,
   REGIONID             varchar(10)          not null,
   MR_DATE              datetime             null,
   VERSION_DATETIME     datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table DISPATCH_MR_SCHEDULE_TRK
   add constraint DISPATCH_MR_SCHEDULE_TRK_PK primary key (SETTLEMENTDATE, REGIONID)
go

/*==============================================================*/
/* Index: DISPATCH_MR_SCHEDULE_TRK_LCX                          */
/*==============================================================*/
create index DISPATCH_MR_SCHEDULE_TRK_LCX on DISPATCH_MR_SCHEDULE_TRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCH_PRICE_REVISION                               */
/*==============================================================*/
create table DISPATCH_PRICE_REVISION (
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3,0)         not null,
   INTERVENTION         numeric(2,0)         not null,
   REGIONID             varchar(10)          not null,
   BIDTYPE              varchar(10)          not null,
   VERSIONNO            numeric(3)           not null,
   RRP_NEW              numeric(15,5)        null,
   RRP_OLD              numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table DISPATCH_PRICE_REVISION
   add constraint DISPATCH_PRICE_REVISION_PK primary key (SETTLEMENTDATE, RUNNO, INTERVENTION, REGIONID, BIDTYPE, VERSIONNO)
go

/*==============================================================*/
/* Index: DISPATCH_PRICE_REVISION_LCX                           */
/*==============================================================*/
create index DISPATCH_PRICE_REVISION_LCX on DISPATCH_PRICE_REVISION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCH_UNIT_CONFORMANCE                             */
/*==============================================================*/
create table DISPATCH_UNIT_CONFORMANCE (
   INTERVAL_DATETIME    datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table DISPATCH_UNIT_CONFORMANCE
   add constraint PK_DISPATCH_UNIT_CONFORMANCE primary key (INTERVAL_DATETIME, DUID)
go

/*==============================================================*/
/* Index: DISPATCH_UNIT_CONFORMANCE_LCX                         */
/*==============================================================*/
create index DISPATCH_UNIT_CONFORMANCE_LCX on DISPATCH_UNIT_CONFORMANCE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DISPATCH_UNIT_SCADA                                   */
/*==============================================================*/
create table DISPATCH_UNIT_SCADA (
   SETTLEMENTDATE       datetime             not null,
   DUID                 varchar(20)          not null,
   SCADAVALUE           numeric(16,6)        null
)
go

alter table DISPATCH_UNIT_SCADA
   add constraint DISPATCH_UNIT_SCADA_PK primary key (SETTLEMENTDATE, DUID)
go

/*==============================================================*/
/* Table: DUALLOC                                               */
/*==============================================================*/
create table DUALLOC (
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   DUID                 varchar(10)          not null,
   GENSETID             varchar(20)          not null,
   LASTCHANGED          datetime             null
)
go

alter table DUALLOC
   add constraint DUALLOC_PK primary key (DUID, EFFECTIVEDATE, VERSIONNO, GENSETID)
go

/*==============================================================*/
/* Index: DUALLOC_NDX2                                          */
/*==============================================================*/
create index DUALLOC_NDX2 on DUALLOC (
DUID ASC
)
go

/*==============================================================*/
/* Index: DUALLOC_LCX                                           */
/*==============================================================*/
create index DUALLOC_LCX on DUALLOC (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DUDETAIL                                              */
/*==============================================================*/
create table DUDETAIL (
   EFFECTIVEDATE        datetime             not null,
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
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null,
   INTERMITTENTFLAG     varchar(1)           null,
   SEMISCHEDULE_FLAG    varchar(1)           null,
   MAXRATEOFCHANGEUP    numeric(6,0)         null,
   MAXRATEOFCHANGEDOWN  numeric(6,0)         null
)
go

alter table DUDETAIL
   add constraint DUDETAIL_PK primary key (DUID, EFFECTIVEDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: DUDETAIL_LCX                                          */
/*==============================================================*/
create index DUDETAIL_LCX on DUDETAIL (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: DUDETAILSUMMARY                                       */
/*==============================================================*/
create table DUDETAILSUMMARY (
   DUID                 varchar(10)          not null,
   START_DATE           datetime             not null,
   END_DATE             datetime             not null,
   DISPATCHTYPE         varchar(10)          null,
   CONNECTIONPOINTID    varchar(10)          null,
   REGIONID             varchar(10)          null,
   STATIONID            varchar(10)          null,
   PARTICIPANTID        varchar(10)          null,
   LASTCHANGED          datetime             null,
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
)
go

alter table DUDETAILSUMMARY
   add constraint DUDETAILSUMMARY_PK primary key (DUID, START_DATE)
go

/*==============================================================*/
/* Index: DUDETAILSUMMARY_LCX                                   */
/*==============================================================*/
create index DUDETAILSUMMARY_LCX on DUDETAILSUMMARY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: EMSMASTER                                             */
/*==============================================================*/
create table EMSMASTER (
   SPD_ID               varchar(21)          not null,
   SPD_TYPE             varchar(1)           not null,
   DESCRIPTION          varchar(255)         null,
   GROUPING_ID          varchar(20)          null,
   LASTCHANGED          datetime             null
)
go

alter table EMSMASTER
   add constraint EMSMASTER_PK primary key (SPD_ID, SPD_TYPE)
go

/*==============================================================*/
/* Index: EMSMASTER_LCX                                         */
/*==============================================================*/
create index EMSMASTER_LCX on EMSMASTER (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: FORCEMAJEURE                                          */
/*==============================================================*/
create table FORCEMAJEURE (
   FMID                 varchar(10)          not null,
   STARTDATE            datetime             null,
   STARTPERIOD          numeric(3,0)         null,
   ENDDATE              datetime             null,
   ENDPERIOD            numeric(3,0)         null,
   APCSTARTDATE         datetime             null,
   STARTAUTHORISEDBY    varchar(15)          null,
   ENDAUTHORISEDBY      varchar(15)          null,
   LASTCHANGED          datetime             null
)
go

alter table FORCEMAJEURE
   add constraint FORCEMAJEURE_PK primary key (FMID)
go

/*==============================================================*/
/* Index: FORCEMAJEURE_LCX                                      */
/*==============================================================*/
create index FORCEMAJEURE_LCX on FORCEMAJEURE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: FORCEMAJEUREREGION                                    */
/*==============================================================*/
create table FORCEMAJEUREREGION (
   FMID                 varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   LASTCHANGED          datetime             null
)
go

alter table FORCEMAJEUREREGION
   add constraint FORCEMAJEUREREGION_PK primary key (FMID, REGIONID)
go

/*==============================================================*/
/* Index: FORCEMAJEUREREGION_LCX                                */
/*==============================================================*/
create index FORCEMAJEUREREGION_LCX on FORCEMAJEUREREGION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: GDINSTRUCT                                            */
/*==============================================================*/
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
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   PARTICIPANTID        varchar(10)          null,
   ISSUEDTIME           datetime             null,
   TARGETTIME           datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table GDINSTRUCT
   add constraint GDINSTRUCT_PK primary key (ID)
go

/*==============================================================*/
/* Index: GDINSTRUCT_LCX                                        */
/*==============================================================*/
create index GDINSTRUCT_LCX on GDINSTRUCT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: GDINSTRUCT_NDX2                                       */
/*==============================================================*/
create index GDINSTRUCT_NDX2 on GDINSTRUCT (
DUID ASC
)
go

/*==============================================================*/
/* Index: GDINSTRUCT_NDX3                                       */
/*==============================================================*/
create index GDINSTRUCT_NDX3 on GDINSTRUCT (
TARGETTIME ASC
)
go

/*==============================================================*/
/* Table: GENCONDATA                                            */
/*==============================================================*/
create table GENCONDATA (
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   GENCONID             varchar(20)          not null,
   CONSTRAINTTYPE       varchar(2)           null,
   CONSTRAINTVALUE      numeric(16,6)        null,
   DESCRIPTION          varchar(256)         null,
   STATUS               varchar(8)           null,
   GENERICCONSTRAINTWEIGHT numeric(16,6)        null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   DYNAMICRHS           numeric(15,5)        null,
   LASTCHANGED          datetime             null,
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
)
go

alter table GENCONDATA
   add constraint GENCONDATA_PK primary key (EFFECTIVEDATE, VERSIONNO, GENCONID)
go

/*==============================================================*/
/* Index: GENCONDATA_LCX                                        */
/*==============================================================*/
create index GENCONDATA_LCX on GENCONDATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: GENCONSET                                             */
/*==============================================================*/
create table GENCONSET (
   GENCONSETID          varchar(20)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   GENCONID             varchar(20)          not null,
   GENCONEFFDATE        datetime             null,
   GENCONVERSIONNO      numeric(3,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table GENCONSET
   add constraint GENCONSET_PK primary key (GENCONSETID, EFFECTIVEDATE, VERSIONNO, GENCONID)
go

/*==============================================================*/
/* Index: GENCONSET_LCX                                         */
/*==============================================================*/
create index GENCONSET_LCX on GENCONSET (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: GENCONSETINVOKE                                       */
/*==============================================================*/
create table GENCONSETINVOKE (
   INVOCATION_ID        numeric(9)           not null,
   STARTDATE            datetime             not null,
   STARTPERIOD          numeric(3,0)         not null,
   GENCONSETID          varchar(20)          not null,
   ENDDATE              datetime             null,
   ENDPERIOD            numeric(3,0)         null,
   STARTAUTHORISEDBY    varchar(15)          null,
   ENDAUTHORISEDBY      varchar(15)          null,
   INTERVENTION         varchar(1)           null,
   ASCONSTRAINTTYPE     varchar(10)          null,
   LASTCHANGED          datetime             null,
   STARTINTERVALDATETIME datetime             null,
   ENDINTERVALDATETIME  datetime             null,
   SYSTEMNORMAL         varchar(1)           null
)
go

alter table GENCONSETINVOKE
   add constraint GENCONSETINV_PK primary key (INVOCATION_ID)
go

/*==============================================================*/
/* Index: GENCONSETINVOKE_LCX                                   */
/*==============================================================*/
create index GENCONSETINVOKE_LCX on GENCONSETINVOKE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: GENCONSETTRK                                          */
/*==============================================================*/
create table GENCONSETTRK (
   GENCONSETID          varchar(20)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   DESCRIPTION          varchar(256)         null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null,
   COVERAGE             varchar(64)          null,
   MODIFICATIONS        varchar(256)         null,
   SYSTEMNORMAL         varchar(1)           null,
   OUTAGE               varchar(256)         null
)
go

alter table GENCONSETTRK
   add constraint GENCONSETTRK_PK primary key (GENCONSETID, EFFECTIVEDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: GENCONSETTRK_LCX                                      */
/*==============================================================*/
create index GENCONSETTRK_LCX on GENCONSETTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: GENERICCONSTRAINTRHS                                  */
/*==============================================================*/
create table GENERICCONSTRAINTRHS (
   GENCONID             varchar(20)          not null,
   EFFECTIVEDATE        datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table GENERICCONSTRAINTRHS
   add constraint GENERICCONSTRAINTRHS_PK primary key (GENCONID, EFFECTIVEDATE, VERSIONNO, SCOPE, TERMID)
go

/*==============================================================*/
/* Index: GENERICCONSTRAINTRHS_LCHD_IDX                         */
/*==============================================================*/
create index GENERICCONSTRAINTRHS_LCHD_IDX on GENERICCONSTRAINTRHS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: GENERICEQUATIONDESC                                   */
/*==============================================================*/
create table GENERICEQUATIONDESC (
   EQUATIONID           varchar(20)          not null,
   DESCRIPTION          varchar(256)         null,
   LASTCHANGED          datetime             null,
   IMPACT               varchar(64)          null,
   SOURCE               varchar(128)         null,
   LIMITTYPE            varchar(64)          null,
   REASON               varchar(256)         null,
   MODIFICATIONS        varchar(256)         null,
   ADDITIONALNOTES      varchar(256)         null
)
go

alter table GENERICEQUATIONDESC
   add constraint GENERICEQUATIONDESC_PK primary key (EQUATIONID)
go

/*==============================================================*/
/* Index: GENERICEQUATIONDS_LCHD_IDX                            */
/*==============================================================*/
create index GENERICEQUATIONDS_LCHD_IDX on GENERICEQUATIONDESC (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: GENERICEQUATIONRHS                                    */
/*==============================================================*/
create table GENERICEQUATIONRHS (
   EQUATIONID           varchar(20)          not null,
   EFFECTIVEDATE        datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table GENERICEQUATIONRHS
   add constraint GENERICEQUATIONRHS_PK primary key (EQUATIONID, EFFECTIVEDATE, VERSIONNO, TERMID)
go

/*==============================================================*/
/* Index: GENERICEQUATION_LCHD_IDX                              */
/*==============================================================*/
create index GENERICEQUATION_LCHD_IDX on GENERICEQUATIONRHS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: GENMETER                                              */
/*==============================================================*/
create table GENMETER (
   METERID              varchar(12)          not null,
   GENSETID             varchar(20)          null,
   CONNECTIONPOINTID    varchar(10)          null,
   STATIONID            varchar(10)          null,
   METERTYPE            varchar(20)          null,
   METERCLASS           varchar(10)          null,
   VOLTAGELEVEL         numeric(6,0)         null,
   APPLYDATE            datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDBY         varchar(10)          null,
   AUTHORISEDDATE       datetime             null,
   COMDATE              datetime             null,
   DECOMDATE            datetime             null,
   ENDDATE              datetime             null,
   STARTDATE            datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table GENMETER
   add constraint GENMETERS_PK primary key (METERID, APPLYDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: GENMETER_LCX                                          */
/*==============================================================*/
create index GENMETER_LCX on GENMETER (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: GENMETER_NDX2                                         */
/*==============================================================*/
create index GENMETER_NDX2 on GENMETER (
STATIONID ASC
)
go

/*==============================================================*/
/* Table: GENUNITMTRINPERIOD                                    */
/*==============================================================*/
create table GENUNITMTRINPERIOD (
   PARTICIPANTID        varchar(10)          not null,
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(6,0)         not null,
   CONNECTIONPOINTID    varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   GENUNITID            varchar(10)          null,
   STATIONID            varchar(10)          null,
   IMPORTENERGYVALUE    numeric(16,6)        null,
   EXPORTENERGYVALUE    numeric(16,6)        null,
   IMPORTREACTIVEVALUE  numeric(16,6)        null,
   EXPORTREACTIVEVALUE  numeric(16,6)        null,
   LASTCHANGED          datetime             null,
   MDA                  varchar(10)          not null,
   LOCAL_RETAILER       varchar(10)          not null default 'POOLNSW'
)
go

alter table GENUNITMTRINPERIOD
   add constraint GENUNITMTRINPERD_PK primary key (SETTLEMENTDATE, MDA, VERSIONNO, CONNECTIONPOINTID, PARTICIPANTID, LOCAL_RETAILER, PERIODID)
go

/*==============================================================*/
/* Index: GENUNITMTRINPERIOD_LCX                                */
/*==============================================================*/
create index GENUNITMTRINPERIOD_LCX on GENUNITMTRINPERIOD (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: GENUNITMTRINPERIOD_NDX2                               */
/*==============================================================*/
create index GENUNITMTRINPERIOD_NDX2 on GENUNITMTRINPERIOD (
STATIONID ASC
)
go

/*==============================================================*/
/* Table: GENUNITS                                              */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   CO2E_EMISSIONS_FACTOR numeric(18,8)        null,
   CO2E_ENERGY_SOURCE   varchar(100)         null,
   CO2E_DATA_SOURCE     varchar(20)          null
)
go

alter table GENUNITS
   add constraint GENUNIT_PK primary key (GENSETID)
go

/*==============================================================*/
/* Index: GENUNITS_LCX                                          */
/*==============================================================*/
create index GENUNITS_LCX on GENUNITS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: GENUNITS_UNIT                                         */
/*==============================================================*/
create table GENUNITS_UNIT (
   GENSETID             varchar(20)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(6,0)         not null,
   UNIT_GROUPING_LABEL  varchar(20)          not null,
   UNIT_COUNT           numeric(3,0)         null,
   UNIT_SIZE            numeric(8,3)         null,
   UNIT_MAX_SIZE        numeric(8,3)         null,
   AGGREGATION_FLAG     numeric(1,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table GENUNITS_UNIT
   add constraint GENUNITS_UNIT_PK primary key (GENSETID, EFFECTIVEDATE, VERSIONNO, UNIT_GROUPING_LABEL)
go

/*==============================================================*/
/* Table: GST_BAS_CLASS                                         */
/*==============================================================*/
create table GST_BAS_CLASS (
   BAS_CLASS            varchar(30)          not null,
   DESCRIPTION          varchar(100)         null,
   LASTCHANGED          datetime             null
)
go

alter table GST_BAS_CLASS
   add constraint GST_BAS_CLASS_PK primary key (BAS_CLASS)
go

/*==============================================================*/
/* Index: GST_BAS_CLASS_LCX                                     */
/*==============================================================*/
create index GST_BAS_CLASS_LCX on GST_BAS_CLASS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: GST_RATE                                              */
/*==============================================================*/
create table GST_RATE (
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   BAS_CLASS            varchar(30)          not null,
   GST_RATE             numeric(8,5)         null,
   LASTCHANGED          datetime             null
)
go

alter table GST_RATE
   add constraint GST_RATE_PK primary key (EFFECTIVEDATE, VERSIONNO, BAS_CLASS)
go

/*==============================================================*/
/* Index: GST_RATE_LCX                                          */
/*==============================================================*/
create index GST_RATE_LCX on GST_RATE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: GST_TRANSACTION_CLASS                                 */
/*==============================================================*/
create table GST_TRANSACTION_CLASS (
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   TRANSACTION_TYPE     varchar(30)          not null,
   BAS_CLASS            varchar(30)          not null,
   LASTCHANGED          datetime             null
)
go

alter table GST_TRANSACTION_CLASS
   add constraint GST_TRANS_CLASS_PK primary key (EFFECTIVEDATE, VERSIONNO, TRANSACTION_TYPE, BAS_CLASS)
go

/*==============================================================*/
/* Index: GST_TRAN_CLASS_LCX                                    */
/*==============================================================*/
create index GST_TRAN_CLASS_LCX on GST_TRANSACTION_CLASS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: GST_TRANSACTION_TYPE                                  */
/*==============================================================*/
create table GST_TRANSACTION_TYPE (
   TRANSACTION_TYPE     varchar(30)          not null,
   DESCRIPTION          varchar(100)         null,
   GL_FINANCIALCODE     varchar(10)          null,
   GL_TCODE             varchar(15)          null,
   LASTCHANGED          datetime             null
)
go

alter table GST_TRANSACTION_TYPE
   add constraint GST_TRANSACTION_TYPE_PK primary key (TRANSACTION_TYPE)
go

/*==============================================================*/
/* Index: GST_TRANSACTION_TYPE_LCX                              */
/*==============================================================*/
create index GST_TRANSACTION_TYPE_LCX on GST_TRANSACTION_TYPE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: INSTRUCTIONSUBTYPE                                    */
/*==============================================================*/
create table INSTRUCTIONSUBTYPE (
   INSTRUCTIONTYPEID    varchar(10)          not null,
   INSTRUCTIONSUBTYPEID varchar(10)          not null,
   DESCRIPTION          varchar(64)          null,
   LASTCHANGED          datetime             null
)
go

alter table INSTRUCTIONSUBTYPE
   add constraint INSTRUCTIONSUBTYPE_PK primary key (INSTRUCTIONTYPEID, INSTRUCTIONSUBTYPEID)
go

/*==============================================================*/
/* Index: INSTRUCTIONSUBTYPE_LCX                                */
/*==============================================================*/
create index INSTRUCTIONSUBTYPE_LCX on INSTRUCTIONSUBTYPE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: INSTRUCTIONTYPE                                       */
/*==============================================================*/
create table INSTRUCTIONTYPE (
   INSTRUCTIONTYPEID    varchar(10)          not null,
   DESCRIPTION          varchar(64)          null,
   REGIONID             varchar(10)          null,
   LASTCHANGED          datetime             null
)
go

alter table INSTRUCTIONTYPE
   add constraint INSTRUCTIONTYPE_PK primary key (INSTRUCTIONTYPEID)
go

/*==============================================================*/
/* Index: INSTRUCTIONTYPE_LCX                                   */
/*==============================================================*/
create index INSTRUCTIONTYPE_LCX on INSTRUCTIONTYPE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: INTCONTRACT                                           */
/*==============================================================*/
create table INTCONTRACT (
   CONTRACTID           varchar(10)          not null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          null,
   STARTDATE            datetime             null,
   ENDDATE              datetime             null,
   STARTPERIOD          numeric(3,0)         null,
   ENDPERIOD            numeric(3,0)         null,
   DEREGISTRATIONDATE   datetime             null,
   DEREGISTRATIONPERIOD numeric(3,0)         null,
   LASTCHANGED          datetime             null,
   REGIONID             varchar(10)          null
)
go

alter table INTCONTRACT
   add constraint INTCONTRACT_PK primary key (CONTRACTID)
go

/*==============================================================*/
/* Index: INTCONTRACT_LCX                                       */
/*==============================================================*/
create index INTCONTRACT_LCX on INTCONTRACT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: INTCONTRACTAMOUNT                                     */
/*==============================================================*/
create table INTCONTRACTAMOUNT (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   AMOUNT               numeric(16,6)        null,
   RCF                  char(1)              null,
   LASTCHANGED          datetime             not null
)
go

alter table INTCONTRACTAMOUNT
   add constraint INTCONTRACTAMOUNT_PK primary key (CONTRACTID, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: INTCONTRACTAMOUNT_LCX                                 */
/*==============================================================*/
create index INTCONTRACTAMOUNT_LCX on INTCONTRACTAMOUNT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: INTCONTRACTAMOUNTTRK                                  */
/*==============================================================*/
create table INTCONTRACTAMOUNTTRK (
   CONTRACTID           varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table INTCONTRACTAMOUNTTRK
   add constraint INTCONTRACTAMOUNTTRK_PK primary key (CONTRACTID, VERSIONNO)
go

/*==============================================================*/
/* Index: INTCONTRACTAMOUNTTRK_LCX                              */
/*==============================================================*/
create index INTCONTRACTAMOUNTTRK_LCX on INTCONTRACTAMOUNTTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: INTERCONNECTOR                                        */
/*==============================================================*/
create table INTERCONNECTOR (
   INTERCONNECTORID     varchar(10)          not null,
   REGIONFROM           varchar(10)          null,
   RSOID                varchar(10)          null,
   REGIONTO             varchar(10)          null,
   DESCRIPTION          varchar(64)          null,
   LASTCHANGED          datetime             null
)
go

alter table INTERCONNECTOR
   add constraint INTERCONNECTOR_PK primary key (INTERCONNECTORID)
go

/*==============================================================*/
/* Index: INTERCONNECTOR_LCX                                    */
/*==============================================================*/
create index INTERCONNECTOR_LCX on INTERCONNECTOR (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: INTERCONNECTORALLOC                                   */
/*==============================================================*/
create table INTERCONNECTORALLOC (
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(5,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   PARTICIPANTID        varchar(10)          not null,
   ALLOCATION           numeric(12,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table INTERCONNECTORALLOC
   add constraint INTERCONNECTORALLOC_PK primary key (EFFECTIVEDATE, VERSIONNO, INTERCONNECTORID, REGIONID, PARTICIPANTID)
go

/*==============================================================*/
/* Index: INTERCONNECTORALLOC_LCX                               */
/*==============================================================*/
create index INTERCONNECTORALLOC_LCX on INTERCONNECTORALLOC (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: INTERCONNECTORCONSTRAINT                              */
/*==============================================================*/
create table INTERCONNECTORCONSTRAINT (
   RESERVEOVERALLLOADFACTOR numeric(5,2)         null,
   FROMREGIONLOSSSHARE  numeric(5,2)         null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   MAXMWIN              numeric(15,5)        null,
   MAXMWOUT             numeric(15,5)        null,
   LOSSCONSTANT         numeric(15,6)        null,
   LOSSFLOWCOEFFICIENT  numeric(27,17)       null,
   EMSMEASURAND         varchar(40)          null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       datetime             null,
   DYNAMICRHS           varchar(1)           null,
   IMPORTLIMIT          numeric(6,0)         null,
   EXPORTLIMIT          numeric(6,0)         null,
   OUTAGEDERATIONFACTOR numeric(15,5)        null,
   NONPHYSICALLOSSFACTOR numeric(15,5)        null,
   OVERLOADFACTOR60SEC  numeric(15,5)        null,
   OVERLOADFACTOR6SEC   numeric(15,5)        null,
   LASTCHANGED          datetime             null,
   FCASSUPPORTUNAVAILABLE numeric(1,0)         null,
   ICTYPE               varchar(10)          null
)
go

alter table INTERCONNECTORCONSTRAINT
   add constraint INTCCONSTRAINT_PK primary key (EFFECTIVEDATE, VERSIONNO, INTERCONNECTORID)
go

/*==============================================================*/
/* Index: INTERCONNECTORCONSTRAINT_LCX                          */
/*==============================================================*/
create index INTERCONNECTORCONSTRAINT_LCX on INTERCONNECTORCONSTRAINT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: INTERCONNMWFLOW                                       */
/*==============================================================*/
create table INTERCONNMWFLOW (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(6,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   IMPORTENERGYVALUE    numeric(15,6)        null,
   EXPORTENERGYVALUE    numeric(15,6)        null,
   LASTCHANGED          datetime             null
)
go

alter table INTERCONNMWFLOW
   add constraint INTERCONNMWFLOW_PK primary key (SETTLEMENTDATE, VERSIONNO, INTERCONNECTORID, PERIODID)
go

/*==============================================================*/
/* Index: INTERCONNMWFLOW_LCIDX                                 */
/*==============================================================*/
create index INTERCONNMWFLOW_LCIDX on INTERCONNMWFLOW (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: INTERMITTENT_CLUSTER_AVAIL                            */
/*==============================================================*/
create table INTERMITTENT_CLUSTER_AVAIL (
   TRADINGDATE          datetime             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        datetime             not null,
   CLUSTERID            varchar(20)          not null,
   PERIODID             numeric(3,0)         not null,
   ELEMENTS_UNAVAILABLE numeric(3,0)         null
)
go

alter table INTERMITTENT_CLUSTER_AVAIL
   add constraint INTERMITTENT_CLUSTER_AVAIL_PK primary key (TRADINGDATE, DUID, OFFERDATETIME, CLUSTERID, PERIODID)
go

/*==============================================================*/
/* Table: INTERMITTENT_CLUSTER_AVAIL_DAY                        */
/*==============================================================*/
create table INTERMITTENT_CLUSTER_AVAIL_DAY (
   TRADINGDATE          datetime             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        datetime             not null,
   CLUSTERID            varchar(20)          not null
)
go

alter table INTERMITTENT_CLUSTER_AVAIL_DAY
   add constraint INTERMITTENT_CLUST_AVL_DAY_PK primary key (TRADINGDATE, DUID, OFFERDATETIME, CLUSTERID)
go

/*==============================================================*/
/* Table: INTERMITTENT_DS_PRED                                  */
/*==============================================================*/
create table INTERMITTENT_DS_PRED (
   RUN_DATETIME         datetime             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        datetime             not null,
   INTERVAL_DATETIME    datetime             not null,
   ORIGIN               varchar(20)          not null,
   FORECAST_PRIORITY    numeric(10,0)        not null,
   FORECAST_MEAN        numeric(18,8)        null,
   FORECAST_POE10       numeric(18,8)        null,
   FORECAST_POE50       numeric(18,8)        null,
   FORECAST_POE90       numeric(18,8)        null
)
go

alter table INTERMITTENT_DS_PRED
   add constraint INTERMITTENT_DS_PRED_PK primary key (RUN_DATETIME, DUID, OFFERDATETIME, INTERVAL_DATETIME, ORIGIN, FORECAST_PRIORITY)
go

/*==============================================================*/
/* Table: INTERMITTENT_DS_RUN                                   */
/*==============================================================*/
create table INTERMITTENT_DS_RUN (
   RUN_DATETIME         datetime             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        datetime             not null,
   ORIGIN               varchar(20)          not null,
   FORECAST_PRIORITY    numeric(10,0)        not null,
   AUTHORISEDBY         varchar(20)          null,
   COMMENTS             varchar(200)         null,
   LASTCHANGED          datetime             null,
   MODEL                varchar(30)          null,
   PARTICIPANT_TIMESTAMP datetime             null,
   SUPPRESSED_AEMO      numeric(1,0)         null,
   SUPPRESSED_PARTICIPANT numeric(1,0)         null,
   TRANSACTION_ID       varchar(100)         null
)
go

alter table INTERMITTENT_DS_RUN
   add constraint INTERMITTENT_DS_RUN_PK primary key (RUN_DATETIME, DUID, OFFERDATETIME, ORIGIN, FORECAST_PRIORITY)
go

/*==============================================================*/
/* Table: INTERMITTENT_FORECAST_TRK                             */
/*==============================================================*/
create table INTERMITTENT_FORECAST_TRK (
   SETTLEMENTDATE       datetime             not null,
   DUID                 varchar(20)          not null,
   ORIGIN               varchar(20)          null,
   FORECAST_PRIORITY    numeric(10,0)        null,
   OFFERDATETIME        datetime             null
)
go

alter table INTERMITTENT_FORECAST_TRK
   add constraint INTERMITTENT_FORECAST_TRK_PK primary key (SETTLEMENTDATE, DUID)
go

/*==============================================================*/
/* Table: INTERMITTENT_GEN_FCST                                 */
/*==============================================================*/
create table INTERMITTENT_GEN_FCST (
   RUN_DATETIME         datetime             not null,
   DUID                 varchar(20)          not null,
   START_INTERVAL_DATETIME datetime             not null,
   END_INTERVAL_DATETIME datetime             not null,
   VERSIONNO            numeric(10,0)        null,
   LASTCHANGED          datetime             null
)
go

alter table INTERMITTENT_GEN_FCST
   add constraint PK_INTERMITTENT_GEN_FCST primary key (RUN_DATETIME, DUID)
go

/*==============================================================*/
/* Table: INTERMITTENT_GEN_FCST_DATA                            */
/*==============================================================*/
create table INTERMITTENT_GEN_FCST_DATA (
   RUN_DATETIME         datetime             not null,
   DUID                 varchar(20)          not null,
   INTERVAL_DATETIME    datetime             not null,
   POWERMEAN            numeric(9,3)         null,
   POWERPOE50           numeric(9,3)         null,
   POWERPOELOW          numeric(9,3)         null,
   POWERPOEHIGH         numeric(9,3)         null,
   LASTCHANGED          datetime             null
)
go

alter table INTERMITTENT_GEN_FCST_DATA
   add constraint PK_INTERMITTENT_GEN_FCST_DATA primary key (RUN_DATETIME, DUID, INTERVAL_DATETIME)
go

/*==============================================================*/
/* Table: INTERMITTENT_GEN_LIMIT                                */
/*==============================================================*/
create table INTERMITTENT_GEN_LIMIT (
   TRADINGDATE          datetime             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        datetime             not null,
   PERIODID             numeric(3,0)         not null,
   UPPERMWLIMIT         numeric(6)           null
)
go

alter table INTERMITTENT_GEN_LIMIT
   add constraint INTERMITTENT_GEN_LIMIT_PK primary key (TRADINGDATE, DUID, OFFERDATETIME, PERIODID)
go

/*==============================================================*/
/* Table: INTERMITTENT_GEN_LIMIT_DAY                            */
/*==============================================================*/
create table INTERMITTENT_GEN_LIMIT_DAY (
   TRADINGDATE          datetime             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        datetime             not null,
   PARTICIPANTID        varchar(20)          null,
   LASTCHANGED          datetime             null,
   AUTHORISEDBYUSER     varchar(20)          null,
   AUTHORISEDBYPARTICIPANTID varchar(20)          null
)
go

alter table INTERMITTENT_GEN_LIMIT_DAY
   add constraint INTERMITTENT_GEN_LIMIT_DAY_PK primary key (TRADINGDATE, DUID, OFFERDATETIME)
go

/*==============================================================*/
/* Table: INTERMITTENT_P5_PRED                                  */
/*==============================================================*/
create table INTERMITTENT_P5_PRED (
   RUN_DATETIME         datetime             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        datetime             not null,
   INTERVAL_DATETIME    datetime             not null,
   ORIGIN               varchar(20)          not null,
   FORECAST_PRIORITY    numeric(10,0)        not null,
   FORECAST_MEAN        numeric(18,8)        null,
   FORECAST_POE10       numeric(18,8)        null,
   FORECAST_POE50       numeric(18,8)        null,
   FORECAST_POE90       numeric(18,8)        null
)
go

alter table INTERMITTENT_P5_PRED
   add constraint INTERMITTENT_P5_PRED_PK primary key (RUN_DATETIME, DUID, OFFERDATETIME, INTERVAL_DATETIME, ORIGIN, FORECAST_PRIORITY)
go

/*==============================================================*/
/* Table: INTERMITTENT_P5_RUN                                   */
/*==============================================================*/
create table INTERMITTENT_P5_RUN (
   RUN_DATETIME         datetime             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        datetime             not null,
   ORIGIN               varchar(20)          not null,
   FORECAST_PRIORITY    numeric(10,0)        not null,
   AUTHORISEDBY         varchar(20)          null,
   COMMENTS             varchar(200)         null,
   LASTCHANGED          datetime             null,
   MODEL                varchar(30)          null,
   PARTICIPANT_TIMESTAMP datetime             null,
   SUPPRESSED_AEMO      numeric(1,0)         null,
   SUPPRESSED_PARTICIPANT numeric(1,0)         null,
   TRANSACTION_ID       varchar(100)         null
)
go

alter table INTERMITTENT_P5_RUN
   add constraint INTERMITTENT_P5_RUN_PK primary key (RUN_DATETIME, DUID, OFFERDATETIME, ORIGIN, FORECAST_PRIORITY)
go

/*==============================================================*/
/* Table: INTRAREGIONALLOC                                      */
/*==============================================================*/
create table INTRAREGIONALLOC (
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(5,0)         not null,
   REGIONID             varchar(10)          not null,
   PARTICIPANTID        varchar(10)          not null,
   ALLOCATION           numeric(12,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table INTRAREGIONALLOC
   add constraint INTRAREGIONALLOC_PK primary key (EFFECTIVEDATE, VERSIONNO, REGIONID, PARTICIPANTID)
go

/*==============================================================*/
/* Index: INTRAREGIONALLOC_LCX                                  */
/*==============================================================*/
create index INTRAREGIONALLOC_LCX on INTRAREGIONALLOC (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: IRFMAMOUNT                                            */
/*==============================================================*/
create table IRFMAMOUNT (
   IRFMID               varchar(10)          not null,
   EFFECTIVEDATE        datetime             null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(4,0)         not null,
   AMOUNT               numeric(15,5)        null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table IRFMAMOUNT
   add constraint IRFMAMOUNT_PK primary key (IRFMID, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: IRFMAMOUNT_LCX                                        */
/*==============================================================*/
create index IRFMAMOUNT_LCX on IRFMAMOUNT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: IRFMEVENTS                                            */
/*==============================================================*/
create table IRFMEVENTS (
   IRFMID               varchar(10)          not null,
   STARTDATE            datetime             null,
   STARTPERIOD          numeric(3,0)         null,
   ENDDATE              datetime             null,
   ENDPERIOD            numeric(3,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table IRFMEVENTS
   add constraint IRFMEVENTS_PK primary key (IRFMID)
go

/*==============================================================*/
/* Index: IRFMEVENTS_LCX                                        */
/*==============================================================*/
create index IRFMEVENTS_LCX on IRFMEVENTS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: LOSSFACTORMODEL                                       */
/*==============================================================*/
create table LOSSFACTORMODEL (
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   DEMANDCOEFFICIENT    numeric(27,17)       null,
   LASTCHANGED          datetime             null
)
go

alter table LOSSFACTORMODEL
   add constraint LFMOD_PK primary key (EFFECTIVEDATE, VERSIONNO, INTERCONNECTORID, REGIONID)
go

/*==============================================================*/
/* Index: LOSSFACTORMODEL_LCX                                   */
/*==============================================================*/
create index LOSSFACTORMODEL_LCX on LOSSFACTORMODEL (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: LOSSMODEL                                             */
/*==============================================================*/
create table LOSSMODEL (
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   PERIODID             varchar(20)          null,
   LOSSSEGMENT          numeric(6,0)         not null,
   MWBREAKPOINT         numeric(6,0)         null,
   LOSSFACTOR           numeric(16,6)        null,
   LASTCHANGED          datetime             null
)
go

alter table LOSSMODEL
   add constraint LOSSMODEL_PK primary key (EFFECTIVEDATE, VERSIONNO, INTERCONNECTORID, LOSSSEGMENT)
go

/*==============================================================*/
/* Index: LOSSMODEL_LCX                                         */
/*==============================================================*/
create index LOSSMODEL_LCX on LOSSMODEL (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MARKETFEE                                             */
/*==============================================================*/
create table MARKETFEE (
   MARKETFEEID          varchar(10)          not null,
   MARKETFEEPERIOD      varchar(20)          null,
   MARKETFEETYPE        varchar(12)          null,
   DESCRIPTION          varchar(64)          null,
   LASTCHANGED          datetime             null,
   GL_TCODE             varchar(15)          null,
   GL_FINANCIALCODE     varchar(10)          null,
   FEE_CLASS            varchar(40)          null
)
go

alter table MARKETFEE
   add constraint MARKETFEE_PK primary key (MARKETFEEID)
go

/*==============================================================*/
/* Index: MARKETFEE_LCX                                         */
/*==============================================================*/
create index MARKETFEE_LCX on MARKETFEE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MARKETFEEDATA                                         */
/*==============================================================*/
create table MARKETFEEDATA (
   MARKETFEEID          varchar(10)          not null,
   MARKETFEEVERSIONNO   numeric(3,0)         not null,
   EFFECTIVEDATE        datetime             not null,
   MARKETFEEVALUE       numeric(22,8)        null,
   LASTCHANGED          datetime             null
)
go

alter table MARKETFEEDATA
   add constraint MARKETFEEDATA_PK primary key (MARKETFEEID, MARKETFEEVERSIONNO, EFFECTIVEDATE)
go

/*==============================================================*/
/* Index: MARKETFEEDATA_LCX                                     */
/*==============================================================*/
create index MARKETFEEDATA_LCX on MARKETFEEDATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MARKETFEETRK                                          */
/*==============================================================*/
create table MARKETFEETRK (
   MARKETFEEVERSIONNO   numeric(3,0)         not null,
   EFFECTIVEDATE        datetime             not null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table MARKETFEETRK
   add constraint MARKETFEETRK_PK primary key (MARKETFEEVERSIONNO, EFFECTIVEDATE)
go

/*==============================================================*/
/* Index: MARKETFEETRK_LCX                                      */
/*==============================================================*/
create index MARKETFEETRK_LCX on MARKETFEETRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MARKETNOTICEDATA                                      */
/*==============================================================*/
create table MARKETNOTICEDATA (
   NOTICEID             numeric(10,0)        not null,
   EFFECTIVEDATE        datetime             null,
   TYPEID               varchar(25)          null,
   NOTICETYPE           varchar(25)          null,
   LASTCHANGED          datetime             null,
   REASON               varchar(2000)        null,
   EXTERNALREFERENCE    varchar(255)         null
)
go

alter table MARKETNOTICEDATA
   add constraint MARKETNOTICEDATA_PK primary key (NOTICEID)
go

/*==============================================================*/
/* Index: MARKETNOTICEDATA_LCX                                  */
/*==============================================================*/
create index MARKETNOTICEDATA_LCX on MARKETNOTICEDATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MARKETNOTICETYPE                                      */
/*==============================================================*/
create table MARKETNOTICETYPE (
   TYPEID               varchar(25)          not null,
   DESCRIPTION          varchar(64)          null,
   RAISEDBY             varchar(10)          null,
   LASTCHANGED          datetime             null
)
go

alter table MARKETNOTICETYPE
   add constraint MARKETNOTICETYPE_PK primary key (TYPEID)
go

/*==============================================================*/
/* Index: MARKETNOTICETYPE_LCX                                  */
/*==============================================================*/
create index MARKETNOTICETYPE_LCX on MARKETNOTICETYPE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MARKETSUSPENSION                                      */
/*==============================================================*/
create table MARKETSUSPENSION (
   SUSPENSIONID         varchar(10)          not null,
   STARTDATE            datetime             null,
   STARTPERIOD          numeric(3,0)         null,
   ENDDATE              datetime             null,
   ENDPERIOD            numeric(3,0)         null,
   REASON               varchar(64)          null,
   STARTAUTHORISEDBY    varchar(15)          null,
   ENDAUTHORISEDBY      varchar(15)          null,
   LASTCHANGED          datetime             null
)
go

alter table MARKETSUSPENSION
   add constraint MARKETSUSPENSION_PK primary key (SUSPENSIONID)
go

/*==============================================================*/
/* Index: MARKETSUSPENSION_LCX                                  */
/*==============================================================*/
create index MARKETSUSPENSION_LCX on MARKETSUSPENSION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MARKETSUSREGION                                       */
/*==============================================================*/
create table MARKETSUSREGION (
   SUSPENSIONID         varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   LASTCHANGED          datetime             null
)
go

alter table MARKETSUSREGION
   add constraint MARKETSUSREGION_PK primary key (SUSPENSIONID, REGIONID)
go

/*==============================================================*/
/* Index: MARKETSUSREGION_LCX                                   */
/*==============================================================*/
create index MARKETSUSREGION_LCX on MARKETSUSREGION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MARKET_FEE_CAT_EXCL                                   */
/*==============================================================*/
create table MARKET_FEE_CAT_EXCL (
   MARKETFEEID          varchar(20)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSION_DATETIME     datetime             not null,
   PARTICIPANT_CATEGORYID varchar(20)          not null
)
go

alter table MARKET_FEE_CAT_EXCL
   add constraint PK_MARKET_FEE_CAT_EXCL primary key (MARKETFEEID, EFFECTIVEDATE, VERSION_DATETIME, PARTICIPANT_CATEGORYID)
go

/*==============================================================*/
/* Table: MARKET_FEE_CAT_EXCL_TRK                               */
/*==============================================================*/
create table MARKET_FEE_CAT_EXCL_TRK (
   MARKETFEEID          varchar(20)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSION_DATETIME     datetime             not null,
   LASTCHANGED          datetime             null
)
go

alter table MARKET_FEE_CAT_EXCL_TRK
   add constraint PK_MARKET_FEE_CAT_EXCL_TRK primary key (MARKETFEEID, EFFECTIVEDATE, VERSION_DATETIME)
go

/*==============================================================*/
/* Table: MARKET_FEE_EXCLUSION                                  */
/*==============================================================*/
create table MARKET_FEE_EXCLUSION (
   PARTICIPANTID        varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   MARKETFEEID          varchar(10)          not null,
   LASTCHANGED          datetime             null
)
go

alter table MARKET_FEE_EXCLUSION
   add constraint MARKET_FEE_EXCLUSION_PK primary key (PARTICIPANTID, EFFECTIVEDATE, VERSIONNO, MARKETFEEID)
go

/*==============================================================*/
/* Index: MARKET_FEE_EXCLUSION_LCX                              */
/*==============================================================*/
create index MARKET_FEE_EXCLUSION_LCX on MARKET_FEE_EXCLUSION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MARKET_FEE_EXCLUSIONTRK                               */
/*==============================================================*/
create table MARKET_FEE_EXCLUSIONTRK (
   PARTICIPANTID        varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table MARKET_FEE_EXCLUSIONTRK
   add constraint MARKET_FEE_EXCLUSIONTRK_PK primary key (PARTICIPANTID, EFFECTIVEDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: MARKET_FEE_EXCLUSIONTRK_LCX                           */
/*==============================================================*/
create index MARKET_FEE_EXCLUSIONTRK_LCX on MARKET_FEE_EXCLUSIONTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MARKET_PRICE_THRESHOLDS                               */
/*==============================================================*/
create table MARKET_PRICE_THRESHOLDS (
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(4,0)         not null,
   VOLL                 numeric(15,5)        null,
   MARKETPRICEFLOOR     numeric(15,5)        null,
   ADMINISTERED_PRICE_THRESHOLD numeric(15,5)        null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   LASTCHANGED          datetime             null
)
go

alter table MARKET_PRICE_THRESHOLDS
   add constraint MARKET_PRICE_THRESHOLDS_PK primary key (EFFECTIVEDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: MARKET_PRICE_THRESHOLDS_LCX                           */
/*==============================================================*/
create index MARKET_PRICE_THRESHOLDS_LCX on MARKET_PRICE_THRESHOLDS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MARKET_SUSPEND_REGIME_SUM                             */
/*==============================================================*/
create table MARKET_SUSPEND_REGIME_SUM (
   SUSPENSION_ID        varchar(20)          not null,
   REGIONID             varchar(20)          not null,
   START_INTERVAL       datetime             not null,
   END_INTERVAL         datetime             null,
   PRICING_REGIME       varchar(20)          null,
   LASTCHANGED          datetime             null
)
go

alter table MARKET_SUSPEND_REGIME_SUM
   add constraint MARKET_SUSPEND_REGIME_SUM_PK primary key (SUSPENSION_ID, REGIONID, START_INTERVAL)
go

/*==============================================================*/
/* Table: MARKET_SUSPEND_REGION_SUM                             */
/*==============================================================*/
create table MARKET_SUSPEND_REGION_SUM (
   SUSPENSION_ID        varchar(20)          not null,
   REGIONID             varchar(20)          not null,
   INITIAL_INTERVAL     datetime             null,
   END_REGION_INTERVAL  datetime             null,
   END_SUSPENSION_INTERVAL datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table MARKET_SUSPEND_REGION_SUM
   add constraint MARKET_SUSPEND_REGION_SUM_PK primary key (SUSPENSION_ID, REGIONID)
go

/*==============================================================*/
/* Table: MARKET_SUSPEND_SCHEDULE                               */
/*==============================================================*/
create table MARKET_SUSPEND_SCHEDULE (
   EFFECTIVEDATE        datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table MARKET_SUSPEND_SCHEDULE
   add constraint MARKET_SUSPEND_SCHEDULE_PK primary key (EFFECTIVEDATE, DAY_TYPE, REGIONID, PERIODID)
go

/*==============================================================*/
/* Table: MARKET_SUSPEND_SCHEDULE_TRK                           */
/*==============================================================*/
create table MARKET_SUSPEND_SCHEDULE_TRK (
   EFFECTIVEDATE        datetime             not null,
   SOURCE_START_DATE    datetime             null,
   SOURCE_END_DATE      datetime             null,
   COMMENTS             varchar(1000)        null,
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table MARKET_SUSPEND_SCHEDULE_TRK
   add constraint MARKET_SUSPEND_SCHEDULE_TRK_PK primary key (EFFECTIVEDATE)
go

/*==============================================================*/
/* Table: MAS_CP_CHANGE                                         */
/*==============================================================*/
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
   INITIAL_CHANGE_DATE  datetime             null,
   CURRENT_CHANGE_DATE  datetime             null,
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
   LASTCHANGED          datetime             null,
   NMI_CLASS            varchar(9)           null,
   METERING_TYPE        varchar(9)           null,
   JURISDICTION         varchar(3)           null,
   CREATE_DATE          datetime             null,
   EXPIRY_DATE          datetime             null,
   METER_READ_DATE      datetime             null
)
go

alter table MAS_CP_CHANGE
   add constraint PK_MAS_CP_CHANGE primary key (NMI)
go

/*==============================================================*/
/* Index: MAS_CP_CHANGE_LCX                                     */
/*==============================================================*/
create index MAS_CP_CHANGE_LCX on MAS_CP_CHANGE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MAS_CP_MASTER                                         */
/*==============================================================*/
create table MAS_CP_MASTER (
   NMI                  varchar(10)          not null,
   CP_SECURITY_CODE     varchar(4)           null,
   IN_USE               varchar(1)           null,
   VALID_FROM_DATE      datetime             not null,
   VALID_TO_DATE        datetime             not null,
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
   LASTCHANGED          datetime             null,
   NMI_CLASS            varchar(9)           null,
   METERING_TYPE        varchar(9)           null,
   JURISDICTION         varchar(3)           null
)
go

alter table MAS_CP_MASTER
   add constraint PK_MAS_CP_MASTER primary key (NMI, VALID_FROM_DATE)
go

alter table MAS_CP_MASTER
   add constraint UC_MAS_CP_MASTER unique (NMI, VALID_TO_DATE)
go

/*==============================================================*/
/* Index: MAS_CP_MASTER_LCX                                     */
/*==============================================================*/
create index MAS_CP_MASTER_LCX on MAS_CP_MASTER (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MCC_CASESOLUTION                                      */
/*==============================================================*/
create table MCC_CASESOLUTION (
   RUN_DATETIME         datetime             not null
)
go

alter table MCC_CASESOLUTION
   add constraint MCC_CASESOLUTION_PK primary key (RUN_DATETIME)
go

/*==============================================================*/
/* Table: MCC_CONSTRAINTSOLUTION                                */
/*==============================================================*/
create table MCC_CONSTRAINTSOLUTION (
   RUN_DATETIME         datetime             not null,
   CONSTRAINTID         varchar(20)          not null,
   RHS                  numeric(15,5)        null,
   MARGINALVALUE        numeric(15,5)        null
)
go

alter table MCC_CONSTRAINTSOLUTION
   add constraint MCC_CONSTRAINTSOLUTION_PK primary key (RUN_DATETIME, CONSTRAINTID)
go

/*==============================================================*/
/* Table: METERDATA                                             */
/*==============================================================*/
create table METERDATA (
   PARTICIPANTID        varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   SETTLEMENTDATE       datetime             not null,
   METERRUNNO           numeric(6,0)         not null,
   CONNECTIONPOINTID    varchar(10)          not null,
   IMPORTENERGYVALUE    numeric(9,6)         null,
   EXPORTENERGYVALUE    numeric(9,6)         null,
   IMPORTREACTIVEVALUE  numeric(9,6)         null,
   EXPORTREACTIVEVALUE  numeric(9,6)         null,
   HOSTDISTRIBUTOR      varchar(10)          not null,
   LASTCHANGED          datetime             null,
   MDA                  varchar(10)          not null
)
go

alter table METERDATA
   add constraint METERDATA_PK primary key (SETTLEMENTDATE, MDA, METERRUNNO, CONNECTIONPOINTID, PARTICIPANTID, HOSTDISTRIBUTOR, PERIODID)
go

/*==============================================================*/
/* Index: METERDATA_LCX                                         */
/*==============================================================*/
create index METERDATA_LCX on METERDATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: METERDATATRK                                          */
/*==============================================================*/
create table METERDATATRK (
   SETTLEMENTDATE       datetime             not null,
   METERRUNNO           numeric(6,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   FILENAME             varchar(40)          null,
   ACKFILENAME          varchar(40)          null,
   CONNECTIONPOINTID    varchar(10)          not null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   METERINGDATAAGENT    varchar(10)          not null,
   HOSTDISTRIBUTOR      varchar(10)          not null,
   LASTCHANGED          datetime             null
)
go

alter table METERDATATRK
   add constraint METERDATATRK_PK primary key (SETTLEMENTDATE, METERINGDATAAGENT, METERRUNNO, CONNECTIONPOINTID, PARTICIPANTID, HOSTDISTRIBUTOR)
go

/*==============================================================*/
/* Index: METERDATATRK_LCX                                      */
/*==============================================================*/
create index METERDATATRK_LCX on METERDATATRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: METERDATA_AGGREGATE_READS                             */
/*==============================================================*/
create table METERDATA_AGGREGATE_READS (
   CASE_ID              numeric(15,0)        not null,
   SETTLEMENTDATE       datetime             not null,
   CONNECTIONPOINTID    varchar(20)          not null,
   METER_TYPE           varchar(20)          not null,
   FRMP                 varchar(20)          not null,
   LR                   varchar(20)          not null,
   PERIODID             numeric(3,0)         not null,
   IMPORTVALUE          numeric(18,8)        not null,
   EXPORTVALUE          numeric(18,8)        not null,
   LASTCHANGED          datetime             null
)
go

alter table METERDATA_AGGREGATE_READS
   add constraint METERDATA_AGGREGATE_READS_PK primary key (CASE_ID, SETTLEMENTDATE, CONNECTIONPOINTID, METER_TYPE, FRMP, LR, PERIODID)
go

/*==============================================================*/
/* Table: METERDATA_GEN_DUID                                    */
/*==============================================================*/
create table METERDATA_GEN_DUID (
   INTERVAL_DATETIME    datetime             not null,
   DUID                 varchar(10)          not null,
   MWH_READING          numeric(18,8)        null,
   LASTCHANGED          datetime             null
)
go

alter table METERDATA_GEN_DUID
   add constraint METERDATA_GEN_DUID_PK primary key (INTERVAL_DATETIME, DUID)
go

/*==============================================================*/
/* Index: METERDATA_GEN_DUID_LCX                                */
/*==============================================================*/
create index METERDATA_GEN_DUID_LCX on METERDATA_GEN_DUID (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: METERDATA_INDIVIDUAL_READS                            */
/*==============================================================*/
create table METERDATA_INDIVIDUAL_READS (
   CASE_ID              numeric(15,0)        not null,
   SETTLEMENTDATE       datetime             not null,
   METER_ID             varchar(20)          not null,
   METER_ID_SUFFIX      varchar(20)          not null,
   FRMP                 varchar(20)          not null,
   LR                   varchar(20)          not null,
   PERIODID             numeric(3,0)         not null,
   CONNECTIONPOINTID    varchar(20)          not null,
   METER_TYPE           varchar(20)          not null,
   IMPORTVALUE          numeric(18,8)        not null,
   EXPORTVALUE          numeric(18,8)        not null,
   LASTCHANGED          datetime             null
)
go

alter table METERDATA_INDIVIDUAL_READS
   add constraint METERDATA_INDIVIDUAL_READS_PK primary key (CASE_ID, SETTLEMENTDATE, METER_ID, METER_ID_SUFFIX, PERIODID)
go

/*==============================================================*/
/* Table: METERDATA_INTERCONNECTOR                              */
/*==============================================================*/
create table METERDATA_INTERCONNECTOR (
   CASE_ID              numeric(15,0)        not null,
   SETTLEMENTDATE       datetime             not null,
   INTERCONNECTORID     varchar(20)          not null,
   PERIODID             numeric(3,0)         not null,
   IMPORTVALUE          numeric(18,8)        null,
   EXPORTVALUE          numeric(18,8)        null,
   LASTCHANGED          datetime             null
)
go

alter table METERDATA_INTERCONNECTOR
   add constraint METERDATA_INTERCONNECTOR_PK primary key (CASE_ID, SETTLEMENTDATE, INTERCONNECTORID, PERIODID)
go

/*==============================================================*/
/* Table: METERDATA_TRK                                         */
/*==============================================================*/
create table METERDATA_TRK (
   CASE_ID              numeric(15,0)        not null,
   AGGREGATE_READS_LOAD_DATETIME datetime             null,
   INDIVIDUAL_READS_LOAD_DATETIME datetime             null,
   STARTDATE            datetime             null,
   ENDDATE              datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table METERDATA_TRK
   add constraint METERDATA_TRK_PK primary key (CASE_ID)
go

/*==============================================================*/
/* Table: MMS_DATA_MODEL_AUDIT                                  */
/*==============================================================*/
create table MMS_DATA_MODEL_AUDIT (
   INSTALLATION_DATE    datetime             not null,
   MMSDM_VERSION        varchar(20)          not null,
   INSTALL_TYPE         varchar(10)          not null,
   SCRIPT_VERSION       varchar(20)          null,
   NEM_CHANGE_NOTICE    varchar(20)          null,
   PROJECT_TITLE        varchar(200)         null,
   USERNAME             varchar(40)          null,
   STATUS               varchar(10)          null
)
go

alter table MMS_DATA_MODEL_AUDIT
   add constraint MMS_DATA_MODEL_AUDIT_PK primary key (INSTALLATION_DATE, MMSDM_VERSION, INSTALL_TYPE)
go

/*==============================================================*/
/* Table: MNSP_DAYOFFER                                         */
/*==============================================================*/
create table MNSP_DAYOFFER (
   SETTLEMENTDATE       datetime             not null,
   OFFERDATE            datetime             not null,
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
   LASTCHANGED          datetime             null,
   MR_FACTOR            numeric(16,6)        null
)
go

alter table MNSP_DAYOFFER
   add constraint MNSP_DAYOFFER_PK primary key (SETTLEMENTDATE, OFFERDATE, VERSIONNO, PARTICIPANTID, LINKID)
go

/*==============================================================*/
/* Index: MNSP_DAYOFFER_LCX                                     */
/*==============================================================*/
create index MNSP_DAYOFFER_LCX on MNSP_DAYOFFER (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MNSP_FILETRK                                          */
/*==============================================================*/
create table MNSP_FILETRK (
   SETTLEMENTDATE       datetime             not null,
   OFFERDATE            datetime             not null,
   PARTICIPANTID        varchar(10)          not null,
   FILENAME             varchar(40)          not null,
   STATUS               varchar(10)          null,
   ACKFILENAME          varchar(40)          null,
   LASTCHANGED          datetime             null
)
go

alter table MNSP_FILETRK
   add constraint MNSP_FILETRK_PK primary key (SETTLEMENTDATE, OFFERDATE, PARTICIPANTID, FILENAME)
go

/*==============================================================*/
/* Index: MNSP_FILETRK_LCX                                      */
/*==============================================================*/
create index MNSP_FILETRK_LCX on MNSP_FILETRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MNSP_INTERCONNECTOR                                   */
/*==============================================================*/
create table MNSP_INTERCONNECTOR (
   LINKID               varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          null,
   FROMREGION           varchar(10)          null,
   TOREGION             varchar(10)          null,
   MAXCAPACITY          numeric(5,0)         null,
   TLF                  numeric(12,7)        null,
   LHSFACTOR            numeric(12,7)        null,
   METERFLOWCONSTANT    numeric(12,7)        null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   LASTCHANGED          datetime             null,
   FROM_REGION_TLF      numeric(12,7)        null,
   TO_REGION_TLF        numeric(12,7)        null
)
go

alter table MNSP_INTERCONNECTOR
   add constraint MNSP_INTERCONNECTOR_PK primary key (LINKID, EFFECTIVEDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: MNSP_INTERCONNECTOR_LCX                               */
/*==============================================================*/
create index MNSP_INTERCONNECTOR_LCX on MNSP_INTERCONNECTOR (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MNSP_OFFERTRK                                         */
/*==============================================================*/
create table MNSP_OFFERTRK (
   SETTLEMENTDATE       datetime             not null,
   OFFERDATE            datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   FILENAME             varchar(40)          not null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   LASTCHANGED          datetime             null
)
go

alter table MNSP_OFFERTRK
   add constraint MNSP_OFFERTRK_PK primary key (SETTLEMENTDATE, OFFERDATE, VERSIONNO, PARTICIPANTID, FILENAME)
go

/*==============================================================*/
/* Index: MNSP_OFFERTRK_LCX                                     */
/*==============================================================*/
create index MNSP_OFFERTRK_LCX on MNSP_OFFERTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MNSP_PARTICIPANT                                      */
/*==============================================================*/
create table MNSP_PARTICIPANT (
   INTERCONNECTORID     varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   LASTCHANGED          datetime             null
)
go

alter table MNSP_PARTICIPANT
   add constraint MNSP_PARTICIPANT_PK primary key (INTERCONNECTORID, EFFECTIVEDATE, VERSIONNO, PARTICIPANTID)
go

/*==============================================================*/
/* Index: MNSP_PARTICIPANT_LCX                                  */
/*==============================================================*/
create index MNSP_PARTICIPANT_LCX on MNSP_PARTICIPANT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MNSP_PEROFFER                                         */
/*==============================================================*/
create table MNSP_PEROFFER (
   SETTLEMENTDATE       datetime             not null,
   OFFERDATE            datetime             not null,
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
   LASTCHANGED          datetime             null,
   FIXEDLOAD            numeric(12,6)        null,
   RAMPUPRATE           numeric(6,0)         null,
   PASAAVAILABILITY     numeric(12,0)        null,
   MR_CAPACITY          numeric(6,0)         null
)
go

alter table MNSP_PEROFFER
   add constraint MNSP_PEROFFER_PK primary key (SETTLEMENTDATE, OFFERDATE, VERSIONNO, PARTICIPANTID, LINKID, PERIODID)
go

/*==============================================================*/
/* Index: MNSP_PEROFFER_LCX                                     */
/*==============================================================*/
create index MNSP_PEROFFER_LCX on MNSP_PEROFFER (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MR_DAYOFFER_STACK                                     */
/*==============================================================*/
create table MR_DAYOFFER_STACK (
   MR_DATE              datetime             not null,
   REGIONID             varchar(10)          not null,
   VERSION_DATETIME     datetime             not null,
   STACK_POSITION       numeric(3,0)         not null,
   DUID                 varchar(10)          null,
   AUTHORISED           numeric(1,0)         null,
   OFFER_SETTLEMENTDATE datetime             null,
   OFFER_OFFERDATE      datetime             null,
   OFFER_VERSIONNO      numeric(3,0)         null,
   OFFER_TYPE           varchar(20)          null,
   LAOF                 numeric(16,6)        null,
   LASTCHANGED          datetime             null
)
go

alter table MR_DAYOFFER_STACK
   add constraint MR_DAYOFFER_STACK_PK primary key (MR_DATE, REGIONID, VERSION_DATETIME, STACK_POSITION)
go

/*==============================================================*/
/* Index: MR_DAYOFFER_STACK_LCX                                 */
/*==============================================================*/
create index MR_DAYOFFER_STACK_LCX on MR_DAYOFFER_STACK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MR_EVENT                                              */
/*==============================================================*/
create table MR_EVENT (
   MR_DATE              datetime             not null,
   REGIONID             varchar(10)          not null,
   DESCRIPTION          varchar(200)         null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(20)          null,
   OFFER_CUT_OFF_TIME   datetime             null,
   SETTLEMENT_COMPLETE  numeric(1,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table MR_EVENT
   add constraint MR_EVENT_PK primary key (MR_DATE, REGIONID)
go

/*==============================================================*/
/* Index: MR_EVENT_LCX                                          */
/*==============================================================*/
create index MR_EVENT_LCX on MR_EVENT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MR_EVENT_SCHEDULE                                     */
/*==============================================================*/
create table MR_EVENT_SCHEDULE (
   MR_DATE              datetime             not null,
   REGIONID             varchar(10)          not null,
   VERSION_DATETIME     datetime             not null,
   DEMAND_EFFECTIVEDATE datetime             null,
   DEMAND_OFFERDATE     datetime             null,
   DEMAND_VERSIONNO     numeric(3,0)         null,
   AUTHORISEDBY         varchar(20)          null,
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table MR_EVENT_SCHEDULE
   add constraint MR_EVENT_SCHEDULE_PK primary key (MR_DATE, REGIONID, VERSION_DATETIME)
go

/*==============================================================*/
/* Index: MR_EVENT_SCHEDULE_LCX                                 */
/*==============================================================*/
create index MR_EVENT_SCHEDULE_LCX on MR_EVENT_SCHEDULE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MR_PEROFFER_STACK                                     */
/*==============================================================*/
create table MR_PEROFFER_STACK (
   MR_DATE              datetime             not null,
   REGIONID             varchar(10)          not null,
   VERSION_DATETIME     datetime             not null,
   STACK_POSITION       numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   DUID                 varchar(10)          null,
   ACCEPTED_CAPACITY    numeric(6,0)         null,
   DEDUCTED_CAPACITY    numeric(6,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table MR_PEROFFER_STACK
   add constraint MR_PEROFFER_STACK_PK primary key (MR_DATE, REGIONID, VERSION_DATETIME, STACK_POSITION, PERIODID)
go

/*==============================================================*/
/* Index: MR_PEROFFER_STACK_LCX                                 */
/*==============================================================*/
create index MR_PEROFFER_STACK_LCX on MR_PEROFFER_STACK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MTPASACONSTRAINTSOLUTION_D                            */
/*==============================================================*/
create table MTPASACONSTRAINTSOLUTION_D (
   DATETIME             datetime             not null,
   CONSTRAINT_ID        varchar(20)          not null,
   DEGREE_OF_VIOLATION  numeric(16,6)        null,
   LASTCHANGED          datetime             null,
   RUN_DATETIME         datetime             null
)
go

alter table MTPASACONSTRAINTSOLUTION_D
   add constraint MTPASACONSTRAINTSOLUTION_D_PK primary key (DATETIME, CONSTRAINT_ID)
go

/*==============================================================*/
/* Index: MTPASACONSOLUTION_D_LCX                               */
/*==============================================================*/
create index MTPASACONSOLUTION_D_LCX on MTPASACONSTRAINTSOLUTION_D (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MTPASAINTERCONNECTORSOLUTION_D                        */
/*==============================================================*/
create table MTPASAINTERCONNECTORSOLUTION_D (
   DATETIME             datetime             not null,
   INTERCONNECTOR_ID    varchar(12)          not null,
   POSITIVE_INTERCONNECTOR_FLOW numeric(16,6)        null,
   POSITIVE_TRANSFER_LIMITS numeric(16,6)        null,
   POSITIVE_BINDING     varchar(10)          null,
   NEGATIVE_INTERCONNECTOR_FLOW numeric(16,6)        null,
   NEGATIVE_TRANSFER_LIMITS numeric(16,6)        null,
   NEGATIVE_BINDING     varchar(10)          null,
   LASTCHANGED          datetime             null,
   RUN_DATETIME         datetime             null
)
go

alter table MTPASAINTERCONNECTORSOLUTION_D
   add constraint MTPASAINTERCONSOLUTION_D_PK primary key (DATETIME, INTERCONNECTOR_ID)
go

/*==============================================================*/
/* Index: MTPASAINTERCONSOLUTION_D_LCX                          */
/*==============================================================*/
create index MTPASAINTERCONSOLUTION_D_LCX on MTPASAINTERCONNECTORSOLUTION_D (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MTPASAREGIONSOLUTION_D                                */
/*==============================================================*/
create table MTPASAREGIONSOLUTION_D (
   DATETIME             datetime             not null,
   REGION_ID            varchar(12)          not null,
   RUN_DATETIME         datetime             null,
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
   LASTCHANGED          datetime             null
)
go

alter table MTPASAREGIONSOLUTION_D
   add constraint MTPASAREGIONSOLUTION_D_PK primary key (DATETIME, REGION_ID)
go

/*==============================================================*/
/* Index: MTPASAREGIONSOLUTION_D_LCX                            */
/*==============================================================*/
create index MTPASAREGIONSOLUTION_D_LCX on MTPASAREGIONSOLUTION_D (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MTPASA_CASERESULT                                     */
/*==============================================================*/
create table MTPASA_CASERESULT (
   RUN_DATETIME         datetime             not null,
   RUN_NO               numeric(4)           not null,
   PLEXOS_VERSION       varchar(20)          null,
   LASTCHANGED          datetime             null
)
go

alter table MTPASA_CASERESULT
   add constraint MTPASA_CASERESULT_PK primary key (RUN_DATETIME, RUN_NO)
go

/*==============================================================*/
/* Table: MTPASA_CASESOLUTION                                   */
/*==============================================================*/
create table MTPASA_CASESOLUTION (
   RUN_DATETIME         datetime             not null,
   RUN_NO               numeric(3,0)         not null,
   PASAVERSION          varchar(10)          null,
   RESERVECONDITION     numeric(1,0)         null,
   LORCONDITION         numeric(1,0)         null,
   CAPACITYOBJFUNCTION  numeric(12,3)        null,
   CAPACITYOPTION       numeric(12,3)        null,
   MAXSURPLUSRESERVEOPTION numeric(12,3)        null,
   MAXSPARECAPACITYOPTION numeric(12,3)        null,
   INTERCONNECTORFLOWPENALTY numeric(12,3)        null,
   LASTCHANGED          datetime             null,
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
)
go

alter table MTPASA_CASESOLUTION
   add constraint MTPASA_CASESOLUTION_PK primary key (RUN_DATETIME, RUN_NO)
go

/*==============================================================*/
/* Index: MTPASA_CASESOLUTION_LCX                               */
/*==============================================================*/
create index MTPASA_CASESOLUTION_LCX on MTPASA_CASESOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MTPASA_CASE_SET                                       */
/*==============================================================*/
create table MTPASA_CASE_SET (
   RUN_DATETIME         datetime             not null,
   RUN_NO               numeric(3,0)         not null,
   CASESETID            numeric(3,0)         null,
   RUNTYPEID            numeric(1,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table MTPASA_CASE_SET
   add constraint MTPASA_CASE_SET_PK primary key (RUN_DATETIME, RUN_NO)
go

/*==============================================================*/
/* Index: MTPASA_CASE_SET_LCX                                   */
/*==============================================================*/
create index MTPASA_CASE_SET_LCX on MTPASA_CASE_SET (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MTPASA_CONSTRAINTRESULT                               */
/*==============================================================*/
create table MTPASA_CONSTRAINTRESULT (
   RUN_DATETIME         datetime             not null,
   RUN_NO               numeric(4)           not null,
   RUNTYPE              varchar(20)          not null,
   DEMAND_POE_TYPE      varchar(20)          not null,
   DAY                  datetime             not null,
   CONSTRAINTID         varchar(20)          not null,
   EFFECTIVEDATE        datetime             null,
   VERSIONNO            numeric(3,0)         null,
   PERIODID             numeric(3,0)         null,
   PROBABILITYOFBINDING numeric(8,5)         null,
   PROBABILITYOFVIOLATION numeric(8,5)         null,
   CONSTRAINTVIOLATION90 numeric(12,2)        null,
   CONSTRAINTVIOLATION50 numeric(12,2)        null,
   CONSTRAINTVIOLATION10 numeric(12,2)        null,
   LASTCHANGED          datetime             null
)
go

alter table MTPASA_CONSTRAINTRESULT
   add constraint MTPASA_CONSTRAINTRESULT_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, DEMAND_POE_TYPE, DAY, CONSTRAINTID)
go

/*==============================================================*/
/* Table: MTPASA_CONSTRAINTSOLUTION                             */
/*==============================================================*/
create table MTPASA_CONSTRAINTSOLUTION (
   RUN_DATETIME         datetime             not null,
   RUN_NO               numeric(3,0)         not null,
   ENERGYBLOCK          datetime             not null,
   DAY                  datetime             not null,
   LDCBLOCK             numeric(3,0)         not null,
   CONSTRAINTID         varchar(20)          not null,
   CAPACITYRHS          numeric(12,2)        null,
   CAPACITYMARGINALVALUE numeric(12,2)        null,
   CAPACITYVIOLATIONDEGREE numeric(12,2)        null,
   LASTCHANGED          datetime             null,
   RUNTYPE              varchar(20)          not null default 'OUTAGE_LRC'
)
go

alter table MTPASA_CONSTRAINTSOLUTION
   add constraint MTPASA_CONSTRAINTSOLUTION_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, ENERGYBLOCK, DAY, LDCBLOCK, CONSTRAINTID)
go

/*==============================================================*/
/* Index: MTPASA_CONSTRAINTSOLUTION_NDX2                        */
/*==============================================================*/
create index MTPASA_CONSTRAINTSOLUTION_NDX2 on MTPASA_CONSTRAINTSOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MTPASA_CONSTRAINTSUMMARY                              */
/*==============================================================*/
create table MTPASA_CONSTRAINTSUMMARY (
   RUN_DATETIME         datetime             not null,
   RUN_NO               numeric(4)           not null,
   RUNTYPE              varchar(20)          not null,
   DEMAND_POE_TYPE      varchar(20)          not null,
   DAY                  datetime             not null,
   CONSTRAINTID         varchar(20)          not null,
   EFFECTIVEDATE        datetime             null,
   VERSIONNO            numeric(3,0)         null,
   AGGREGATION_PERIOD   varchar(20)          not null,
   CONSTRAINTHOURSBINDING numeric(12,2)        null,
   LASTCHANGED          datetime             null
)
go

alter table MTPASA_CONSTRAINTSUMMARY
   add constraint MTPASA_CONSTRAINTSUMMARY_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, DEMAND_POE_TYPE, DAY, CONSTRAINTID, AGGREGATION_PERIOD)
go

/*==============================================================*/
/* Table: MTPASA_INTERCONNECTORRESULT                           */
/*==============================================================*/
create table MTPASA_INTERCONNECTORRESULT (
   RUN_DATETIME         datetime             not null,
   RUN_NO               numeric(4)           not null,
   RUNTYPE              varchar(20)          not null,
   DEMAND_POE_TYPE      varchar(20)          not null,
   DAY                  datetime             not null,
   INTERCONNECTORID     varchar(20)          not null,
   PERIODID             numeric(3,0)         null,
   FLOW90               numeric(12,2)        null,
   FLOW50               numeric(12,2)        null,
   FLOW10               numeric(12,2)        null,
   PROBABILITYOFBINDINGEXPORT numeric(8,5)         null,
   PROBABILITYOFBINDINGIMPORT numeric(8,5)         null,
   CALCULATEDEXPORTLIMIT numeric(12,2)        null,
   CALCULATEDIMPORTLIMIT numeric(12,2)        null,
   LASTCHANGED          datetime             null
)
go

alter table MTPASA_INTERCONNECTORRESULT
   add constraint MTPASA_INTERCONNECTORRESULT_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, DEMAND_POE_TYPE, DAY, INTERCONNECTORID)
go

/*==============================================================*/
/* Table: MTPASA_INTERCONNECTORSOLUTION                         */
/*==============================================================*/
create table MTPASA_INTERCONNECTORSOLUTION (
   RUN_DATETIME         datetime             not null,
   RUN_NO               numeric(3,0)         not null,
   ENERGYBLOCK          datetime             not null,
   DAY                  datetime             not null,
   LDCBLOCK             numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   CAPACITYMWFLOW       numeric(12,2)        null,
   CAPACITYMARGINALVALUE numeric(12,2)        null,
   CAPACITYVIOLATIONDEGREE numeric(12,2)        null,
   CALCULATEDEXPORTLIMIT numeric(12,2)        null,
   CALCULATEDIMPORTLIMIT numeric(12,2)        null,
   LASTCHANGED          datetime             null,
   RUNTYPE              varchar(20)          not null default 'OUTAGE_LRC',
   EXPORTLIMITCONSTRAINTID varchar(20)          null,
   IMPORTLIMITCONSTRAINTID varchar(20)          null
)
go

alter table MTPASA_INTERCONNECTORSOLUTION
   add constraint MTPASA_INTERCONNECTORSOLN_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, ENERGYBLOCK, DAY, LDCBLOCK, INTERCONNECTORID)
go

/*==============================================================*/
/* Index: MTPASA_INTERCONNECTORSOLN_NDX2                        */
/*==============================================================*/
create index MTPASA_INTERCONNECTORSOLN_NDX2 on MTPASA_INTERCONNECTORSOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MTPASA_INTERMITTENT_AVAIL                             */
/*==============================================================*/
create table MTPASA_INTERMITTENT_AVAIL (
   TRADINGDATE          datetime             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        datetime             not null,
   CLUSTERID            varchar(20)          not null,
   LASTCHANGED          datetime             null,
   ELEMENTS_UNAVAILABLE numeric(3,0)         null
)
go

alter table MTPASA_INTERMITTENT_AVAIL
   add constraint MTPASA_INTERMITTENT_AVAIL_PK primary key (TRADINGDATE, DUID, OFFERDATETIME, CLUSTERID)
go

/*==============================================================*/
/* Table: MTPASA_INTERMITTENT_LIMIT                             */
/*==============================================================*/
create table MTPASA_INTERMITTENT_LIMIT (
   TRADINGDATE          datetime             not null,
   DUID                 varchar(20)          not null,
   OFFERDATETIME        datetime             not null,
   LASTCHANGED          datetime             null,
   UPPERMWLIMIT         numeric(6)           null,
   AUTHORISEDBYUSER     varchar(20)          null,
   AUTHORISEDBYPARTICIPANTID varchar(20)          null
)
go

alter table MTPASA_INTERMITTENT_LIMIT
   add constraint MTPASA_INTERMITTENT_LIMIT_PK primary key (TRADINGDATE, DUID, OFFERDATETIME)
go

/*==============================================================*/
/* Table: MTPASA_LOLPRESULT                                     */
/*==============================================================*/
create table MTPASA_LOLPRESULT (
   RUN_DATETIME         datetime             not null,
   RUN_NO               numeric(4)           not null,
   RUNTYPE              varchar(20)          not null,
   DAY                  datetime             not null,
   REGIONID             varchar(20)          not null,
   WORST_INTERVAL_PERIODID numeric(3,0)         null,
   WORST_INTERVAL_DEMAND numeric(12,2)        null,
   WORST_INTERVAL_INTGEN numeric(12,2)        null,
   WORST_INTERVAL_DSP   numeric(12,2)        null,
   LOSSOFLOADPROBABILITY numeric(8,5)         null,
   LOSSOFLOADMAGNITUDE  varchar(20)          null,
   LASTCHANGED          datetime             null
)
go

alter table MTPASA_LOLPRESULT
   add constraint MTPASA_LOLPRESULT_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, DAY, REGIONID)
go

/*==============================================================*/
/* Table: MTPASA_OFFERDATA                                      */
/*==============================================================*/
create table MTPASA_OFFERDATA (
   PARTICIPANTID        varchar(20)          not null,
   OFFERDATETIME        datetime             not null,
   UNITID               varchar(20)          not null,
   EFFECTIVEDATE        datetime             not null,
   ENERGY               numeric(9)           null,
   CAPACITY1            numeric(9)           null,
   CAPACITY2            numeric(9)           null,
   CAPACITY3            numeric(9)           null,
   CAPACITY4            numeric(9)           null,
   CAPACITY5            numeric(9)           null,
   CAPACITY6            numeric(9)           null,
   CAPACITY7            numeric(9)           null,
   LASTCHANGED          datetime             null
)
go

alter table MTPASA_OFFERDATA
   add constraint MTPASA_OFFERDATA_PK primary key (PARTICIPANTID, OFFERDATETIME, UNITID, EFFECTIVEDATE)
go

/*==============================================================*/
/* Index: MTPASA_OFFERDATA_LCX                                  */
/*==============================================================*/
create index MTPASA_OFFERDATA_LCX on MTPASA_OFFERDATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MTPASA_OFFERFILETRK                                   */
/*==============================================================*/
create table MTPASA_OFFERFILETRK (
   PARTICIPANTID        varchar(20)          not null,
   OFFERDATETIME        datetime             not null,
   FILENAME             varchar(200)         null
)
go

alter table MTPASA_OFFERFILETRK
   add constraint MTPASA_OFFERFILETRK_PK primary key (PARTICIPANTID, OFFERDATETIME)
go

/*==============================================================*/
/* Table: MTPASA_REGIONAVAILABILITY                             */
/*==============================================================*/
create table MTPASA_REGIONAVAILABILITY (
   PUBLISH_DATETIME     datetime             not null,
   DAY                  datetime             not null,
   REGIONID             varchar(20)          not null,
   PASAAVAILABILITY_SCHEDULED numeric(12,0)        null,
   LATEST_OFFER_DATETIME datetime             null,
   ENERGYUNCONSTRAINEDCAPACITY numeric(12,0)        null,
   ENERGYCONSTRAINEDCAPACITY numeric(12,0)        null,
   NONSCHEDULEDGENERATION numeric(12,2)        null,
   DEMAND10             numeric(12,2)        null,
   DEMAND50             numeric(12,2)        null,
   ENERGYREQDEMAND10    numeric(12,2)        null,
   ENERGYREQDEMAND50    numeric(12,2)        null,
   LASTCHANGED          datetime             null
)
go

alter table MTPASA_REGIONAVAILABILITY
   add constraint MTPASA_REGIONAVAILABILITY_PK primary key (PUBLISH_DATETIME, DAY, REGIONID)
go

/*==============================================================*/
/* Table: MTPASA_REGIONAVAIL_TRK                                */
/*==============================================================*/
create table MTPASA_REGIONAVAIL_TRK (
   PUBLISH_DATETIME     datetime             not null,
   STARTDATE            datetime             null,
   ENDDATE              datetime             null,
   LATEST_OFFER_DATETIME datetime             null
)
go

alter table MTPASA_REGIONAVAIL_TRK
   add constraint MTPASA_REGIONAVAIL_TRK_PK primary key (PUBLISH_DATETIME)
go

/*==============================================================*/
/* Table: MTPASA_REGIONITERATION                                */
/*==============================================================*/
create table MTPASA_REGIONITERATION (
   RUN_DATETIME         datetime             not null,
   RUN_NO               numeric(4)           not null,
   RUNTYPE              varchar(20)          not null,
   DEMAND_POE_TYPE      varchar(20)          not null,
   AGGREGATION_PERIOD   varchar(20)          not null,
   PERIOD_ENDING        datetime             not null,
   REGIONID             varchar(20)          not null,
   USE_ITERATION_ID     numeric(5)           not null,
   USE_ITERATION_EVENT_NUMBER numeric(12,2)        null,
   USE_ITERATION_EVENT_AVERAGE numeric(12,2)        null,
   LASTCHANGED          datetime             null
)
go

alter table MTPASA_REGIONITERATION
   add constraint MTPASA_REGIONITERATION_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, DEMAND_POE_TYPE, AGGREGATION_PERIOD, PERIOD_ENDING, REGIONID, USE_ITERATION_ID)
go

/*==============================================================*/
/* Table: MTPASA_REGIONRESULT                                   */
/*==============================================================*/
create table MTPASA_REGIONRESULT (
   RUN_DATETIME         datetime             not null,
   RUN_NO               numeric(4)           not null,
   RUNTYPE              varchar(20)          not null,
   DEMAND_POE_TYPE      varchar(20)          not null,
   DAY                  datetime             not null,
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
   LASTCHANGED          datetime             null,
   TOTALSEMISCHEDULEGEN90 numeric(12,2)        null,
   TOTALSEMISCHEDULEGEN50 numeric(12,2)        null,
   TOTALSEMISCHEDULEGEN10 numeric(12,2)        null
)
go

alter table MTPASA_REGIONRESULT
   add constraint MTPASA_REGIONRESULT_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, DEMAND_POE_TYPE, DAY, REGIONID)
go

/*==============================================================*/
/* Table: MTPASA_REGIONSOLUTION                                 */
/*==============================================================*/
create table MTPASA_REGIONSOLUTION (
   RUN_DATETIME         datetime             not null,
   RUN_NO               numeric(3,0)         not null,
   ENERGYBLOCK          datetime             not null,
   DAY                  datetime             not null,
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
   LASTCHANGED          datetime             null,
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
)
go

alter table MTPASA_REGIONSOLUTION
   add constraint MTPASA_REGIONSOLUTION_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, ENERGYBLOCK, DAY, LDCBLOCK, REGIONID)
go

/*==============================================================*/
/* Index: MTPASA_REGIONSOLUTION_NDX2                            */
/*==============================================================*/
create index MTPASA_REGIONSOLUTION_NDX2 on MTPASA_REGIONSOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: MTPASA_REGIONSUMMARY                                  */
/*==============================================================*/
create table MTPASA_REGIONSUMMARY (
   RUN_DATETIME         datetime             not null,
   RUN_NO               numeric(4)           not null,
   RUNTYPE              varchar(20)          not null,
   DEMAND_POE_TYPE      varchar(20)          not null,
   AGGREGATION_PERIOD   varchar(20)          not null,
   PERIOD_ENDING        datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table MTPASA_REGIONSUMMARY
   add constraint MTPASA_REGIONSUMMARY_PK primary key (RUN_DATETIME, RUN_NO, RUNTYPE, DEMAND_POE_TYPE, AGGREGATION_PERIOD, PERIOD_ENDING, REGIONID)
go

/*==============================================================*/
/* Table: MTPASA_RESERVELIMIT                                   */
/*==============================================================*/
create table MTPASA_RESERVELIMIT (
   EFFECTIVEDATE        datetime             not null,
   VERSION_DATETIME     datetime             not null,
   RESERVELIMITID       varchar(20)          not null,
   DESCRIPTION          varchar(200)         null,
   RHS                  numeric(16,6)        null,
   LASTCHANGED          datetime             null
)
go

alter table MTPASA_RESERVELIMIT
   add constraint PK_MTPASA_RESERVELIMIT primary key (EFFECTIVEDATE, VERSION_DATETIME, RESERVELIMITID)
go

/*==============================================================*/
/* Table: MTPASA_RESERVELIMITSOLUTION                           */
/*==============================================================*/
create table MTPASA_RESERVELIMITSOLUTION (
   RUN_DATETIME         datetime             not null,
   RUN_NO               numeric(3,0)         not null,
   RUNTYPE              varchar(20)          not null,
   ENERGYBLOCK          datetime             not null,
   DAY                  datetime             not null,
   LDCBLOCK             numeric(3,0)         not null,
   RESERVELIMITID       varchar(20)          not null,
   MARGINALVALUE        numeric(16,6)        null,
   LASTCHANGED          datetime             null
)
go

alter table MTPASA_RESERVELIMITSOLUTION
   add constraint PK_MTPASA_RESERVELIMITSOLUTION primary key (RUN_DATETIME, RUN_NO, RUNTYPE, ENERGYBLOCK, DAY, LDCBLOCK, RESERVELIMITID)
go

/*==============================================================*/
/* Table: MTPASA_RESERVELIMIT_REGION                            */
/*==============================================================*/
create table MTPASA_RESERVELIMIT_REGION (
   EFFECTIVEDATE        datetime             not null,
   VERSION_DATETIME     datetime             not null,
   RESERVELIMITID       varchar(20)          not null,
   REGIONID             varchar(20)          not null,
   COEF                 numeric(16,6)        null,
   LASTCHANGED          datetime             null
)
go

alter table MTPASA_RESERVELIMIT_REGION
   add constraint PK_MTPASA_RESERVELIMIT_REGION primary key (EFFECTIVEDATE, VERSION_DATETIME, RESERVELIMITID, REGIONID)
go

/*==============================================================*/
/* Table: MTPASA_RESERVELIMIT_SET                               */
/*==============================================================*/
create table MTPASA_RESERVELIMIT_SET (
   EFFECTIVEDATE        datetime             not null,
   VERSION_DATETIME     datetime             not null,
   RESERVELIMIT_SET_ID  varchar(20)          null,
   DESCRIPTION          varchar(200)         null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(20)          null,
   LASTCHANGED          datetime             null
)
go

alter table MTPASA_RESERVELIMIT_SET
   add constraint PK_MTPASA_RESERVELIMIT_SET primary key (EFFECTIVEDATE, VERSION_DATETIME)
go

/*==============================================================*/
/* Table: NEGATIVE_RESIDUE                                      */
/*==============================================================*/
create table NEGATIVE_RESIDUE (
   SETTLEMENTDATE       datetime             not null,
   NRM_DATETIME         datetime             not null,
   DIRECTIONAL_INTERCONNECTORID varchar(30)          not null,
   NRM_ACTIVATED_FLAG   numeric(1,0)         null,
   CUMUL_NEGRESIDUE_AMOUNT numeric(15,5)        null,
   CUMUL_NEGRESIDUE_PREV_TI numeric(15,5)        null,
   NEGRESIDUE_CURRENT_TI numeric(15,5)        null,
   NEGRESIDUE_PD_NEXT_TI numeric(15,5)        null,
   PRICE_REVISION       varchar(30)          null,
   PREDISPATCHSEQNO     varchar(20)          null,
   EVENT_ACTIVATED_DI   datetime             null,
   EVENT_DEACTIVATED_DI datetime             null,
   DI_NOTBINDING_COUNT  numeric(2,0)         null,
   DI_VIOLATED_COUNT    numeric(2,0)         null,
   NRMCONSTRAINT_BLOCKED_FLAG numeric(1,0)         null
)
go

alter table NEGATIVE_RESIDUE
   add constraint NEGATIVE_RESIDUE_PK primary key (SETTLEMENTDATE, NRM_DATETIME, DIRECTIONAL_INTERCONNECTORID)
go

/*==============================================================*/
/* Table: NETWORK_EQUIPMENTDETAIL                               */
/*==============================================================*/
create table NETWORK_EQUIPMENTDETAIL (
   SUBSTATIONID         varchar(30)          not null,
   EQUIPMENTTYPE        varchar(10)          not null,
   EQUIPMENTID          varchar(30)          not null,
   VALIDFROM            datetime             not null,
   VALIDTO              datetime             null,
   VOLTAGE              varchar(20)          null,
   DESCRIPTION          varchar(100)         null,
   LASTCHANGED          datetime             null
)
go

alter table NETWORK_EQUIPMENTDETAIL
   add constraint PK_NETWORK_EQUIPMENTDETAIL primary key (SUBSTATIONID, EQUIPMENTTYPE, EQUIPMENTID, VALIDFROM)
go

/*==============================================================*/
/* Index: NETWORK_EQUIPMENTDETAIL_LCX                           */
/*==============================================================*/
create index NETWORK_EQUIPMENTDETAIL_LCX on NETWORK_EQUIPMENTDETAIL (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: NETWORK_OUTAGECONSTRAINTSET                           */
/*==============================================================*/
create table NETWORK_OUTAGECONSTRAINTSET (
   OUTAGEID             numeric(15,0)        not null,
   GENCONSETID          varchar(50)          not null,
   STARTINTERVAL        datetime             null,
   ENDINTERVAL          datetime             null
)
go

alter table NETWORK_OUTAGECONSTRAINTSET
   add constraint PK_NETWORK_OUTAGECONSTRAINTSET primary key (OUTAGEID, GENCONSETID)
go

/*==============================================================*/
/* Table: NETWORK_OUTAGEDETAIL                                  */
/*==============================================================*/
create table NETWORK_OUTAGEDETAIL (
   OUTAGEID             numeric(15,0)        not null,
   SUBSTATIONID         varchar(30)          not null,
   EQUIPMENTTYPE        varchar(10)          not null,
   EQUIPMENTID          varchar(30)          not null,
   STARTTIME            datetime             not null,
   ENDTIME              datetime             null,
   SUBMITTEDDATE        datetime             null,
   OUTAGESTATUSCODE     varchar(10)          null,
   RESUBMITREASON       varchar(50)          null,
   RESUBMITOUTAGEID     numeric(15,0)        null,
   RECALLTIMEDAY        numeric(10,0)        null,
   RECALLTIMENIGHT      numeric(10,0)        null,
   LASTCHANGED          datetime             null,
   REASON               varchar(100)         null,
   ISSECONDARY          numeric(1,0)         null,
   ACTUAL_STARTTIME     datetime             null,
   ACTUAL_ENDTIME       datetime             null,
   COMPANYREFCODE       varchar(20)          null
)
go

alter table NETWORK_OUTAGEDETAIL
   add constraint PK_NETWORK_OUTAGEDETAIL primary key (OUTAGEID, SUBSTATIONID, EQUIPMENTTYPE, EQUIPMENTID, STARTTIME)
go

/*==============================================================*/
/* Index: NETWORK_OUTAGEDETAIL_LCX                              */
/*==============================================================*/
create index NETWORK_OUTAGEDETAIL_LCX on NETWORK_OUTAGEDETAIL (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: NETWORK_OUTAGESTATUSCODE                              */
/*==============================================================*/
create table NETWORK_OUTAGESTATUSCODE (
   OUTAGESTATUSCODE     varchar(10)          not null,
   DESCRIPTION          varchar(100)         null,
   LASTCHANGED          datetime             null
)
go

alter table NETWORK_OUTAGESTATUSCODE
   add constraint PK_NETWORK_OUTAGESTATUSCODE primary key (OUTAGESTATUSCODE)
go

/*==============================================================*/
/* Table: NETWORK_RATING                                        */
/*==============================================================*/
create table NETWORK_RATING (
   SPD_ID               varchar(21)          not null,
   VALIDFROM            datetime             not null,
   VALIDTO              datetime             null,
   REGIONID             varchar(10)          null,
   SUBSTATIONID         varchar(30)          null,
   EQUIPMENTTYPE        varchar(10)          null,
   EQUIPMENTID          varchar(30)          null,
   RATINGLEVEL          varchar(10)          null,
   ISDYNAMIC            numeric(1,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table NETWORK_RATING
   add constraint PK_NETWORK_RATING primary key (SPD_ID, VALIDFROM)
go

/*==============================================================*/
/* Index: NETWORK_RATING_LCX                                    */
/*==============================================================*/
create index NETWORK_RATING_LCX on NETWORK_RATING (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: NETWORK_REALTIMERATING                                */
/*==============================================================*/
create table NETWORK_REALTIMERATING (
   SETTLEMENTDATE       datetime             not null,
   SPD_ID               varchar(21)          not null,
   RATINGVALUE          numeric(16,6)        not null
)
go

alter table NETWORK_REALTIMERATING
   add constraint PK_NETWORK_REALTIMERATING primary key (SETTLEMENTDATE, SPD_ID)
go

/*==============================================================*/
/* Table: NETWORK_STATICRATING                                  */
/*==============================================================*/
create table NETWORK_STATICRATING (
   SUBSTATIONID         varchar(30)          not null,
   EQUIPMENTTYPE        varchar(10)          not null,
   EQUIPMENTID          varchar(30)          not null,
   RATINGLEVEL          varchar(10)          not null,
   APPLICATIONID        varchar(20)          not null,
   VALIDFROM            datetime             not null,
   VALIDTO              datetime             null,
   RATINGVALUE          numeric(16,6)        null,
   LASTCHANGED          datetime             null
)
go

alter table NETWORK_STATICRATING
   add constraint PK_NETWORK_STATICRATING primary key (SUBSTATIONID, EQUIPMENTTYPE, EQUIPMENTID, RATINGLEVEL, APPLICATIONID, VALIDFROM)
go

/*==============================================================*/
/* Index: NETWORK_STATICRATING_LCX                              */
/*==============================================================*/
create index NETWORK_STATICRATING_LCX on NETWORK_STATICRATING (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: NETWORK_SUBSTATIONDETAIL                              */
/*==============================================================*/
create table NETWORK_SUBSTATIONDETAIL (
   SUBSTATIONID         varchar(30)          not null,
   VALIDFROM            datetime             not null,
   VALIDTO              datetime             null,
   DESCRIPTION          varchar(100)         null,
   REGIONID             varchar(10)          null,
   OWNERID              varchar(30)          null,
   LASTCHANGED          datetime             null
)
go

alter table NETWORK_SUBSTATIONDETAIL
   add constraint PK_NETWORK_SUBSTATIONDETAIL primary key (SUBSTATIONID, VALIDFROM)
go

/*==============================================================*/
/* Index: NETWORK_SUBSTATIONDETAIL_LCX                          */
/*==============================================================*/
create index NETWORK_SUBSTATIONDETAIL_LCX on NETWORK_SUBSTATIONDETAIL (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: OARTRACK                                              */
/*==============================================================*/
create table OARTRACK (
   SETTLEMENTDATE       datetime             not null,
   OFFERDATE            datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   FILENAME             varchar(40)          null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(10)          null,
   LASTCHANGED          datetime             null
)
go

alter table OARTRACK
   add constraint OARTRACK_PK primary key (SETTLEMENTDATE, OFFERDATE, VERSIONNO, PARTICIPANTID)
go

/*==============================================================*/
/* Index: OARTRACK_NDX2                                         */
/*==============================================================*/
create index OARTRACK_NDX2 on OARTRACK (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: OARTRACK_LCX                                          */
/*==============================================================*/
create index OARTRACK_LCX on OARTRACK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: OFFERAGCDATA                                          */
/*==============================================================*/
create table OFFERAGCDATA (
   CONTRACTID           varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   AVAILABILITY         numeric(4,0)         null,
   UPPERLIMIT           numeric(4,0)         null,
   LOWERLIMIT           numeric(4,0)         null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   FILENAME             varchar(40)          null,
   LASTCHANGED          datetime             null,
   PERIODID             numeric(3,0)         not null,
   AGCUP                numeric(3,0)         null,
   AGCDOWN              numeric(3,0)         null
)
go

alter table OFFERAGCDATA
   add constraint OFFERAGCDATA_PK primary key (CONTRACTID, EFFECTIVEDATE, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: OFFERAGCDATA_NDX2                                     */
/*==============================================================*/
create index OFFERAGCDATA_NDX2 on OFFERAGCDATA (
CONTRACTID ASC
)
go

/*==============================================================*/
/* Index: OFFERAGCDATA_LCX                                      */
/*==============================================================*/
create index OFFERAGCDATA_LCX on OFFERAGCDATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: OFFERASTRK                                            */
/*==============================================================*/
create table OFFERASTRK (
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   FILENAME             varchar(40)          null,
   LASTCHANGED          datetime             null
)
go

alter table OFFERASTRK
   add constraint OFFERASTRK_PK primary key (EFFECTIVEDATE, VERSIONNO, PARTICIPANTID)
go

/*==============================================================*/
/* Index: OFFERASTRK_LCX                                        */
/*==============================================================*/
create index OFFERASTRK_LCX on OFFERASTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: OFFERFILETRK                                          */
/*==============================================================*/
create table OFFERFILETRK (
   OFFERDATE            datetime             not null,
   PARTICIPANTID        varchar(10)          not null,
   STATUS               varchar(10)          null,
   ACKFILENAME          varchar(40)          null,
   ENDDATE              datetime             null,
   FILENAME             varchar(40)          not null,
   LASTCHANGED          datetime             null
)
go

alter table OFFERFILETRK
   add constraint OFFERFILETRK_PK primary key (OFFERDATE, FILENAME, PARTICIPANTID)
go

/*==============================================================*/
/* Index: OFFERFILETRK_NDX2                                     */
/*==============================================================*/
create index OFFERFILETRK_NDX2 on OFFERFILETRK (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: OFFERFILETRK_LCX                                      */
/*==============================================================*/
create index OFFERFILETRK_LCX on OFFERFILETRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: OFFERGOVDATA                                          */
/*==============================================================*/
create table OFFERGOVDATA (
   CONTRACTID           varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   SEC6AVAILUP          numeric(6,0)         null,
   SEC6AVAILDOWN        numeric(6,0)         null,
   SEC60AVAILUP         numeric(6,0)         null,
   SEC60AVAILDOWN       numeric(6,0)         null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   FILENAME             varchar(40)          null,
   LASTCHANGED          datetime             null
)
go

alter table OFFERGOVDATA
   add constraint OFFERGOVDATA_PK primary key (CONTRACTID, EFFECTIVEDATE, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: OFFERGOVDATA_NDX2                                     */
/*==============================================================*/
create index OFFERGOVDATA_NDX2 on OFFERGOVDATA (
CONTRACTID ASC
)
go

/*==============================================================*/
/* Index: OFFERGOVDATA_LCX                                      */
/*==============================================================*/
create index OFFERGOVDATA_LCX on OFFERGOVDATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: OFFERLSHEDDATA                                        */
/*==============================================================*/
create table OFFERLSHEDDATA (
   CONTRACTID           varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   AVAILABLELOAD        numeric(4,0)         null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   FILENAME             varchar(40)          null,
   LASTCHANGED          datetime             null,
   PERIODID             numeric(3,0)         not null
)
go

alter table OFFERLSHEDDATA
   add constraint OFFERLSHEDDATA_PK primary key (CONTRACTID, EFFECTIVEDATE, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: OFFERLSHEDDATA_LCX                                    */
/*==============================================================*/
create index OFFERLSHEDDATA_LCX on OFFERLSHEDDATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: OFFERRESTARTDATA                                      */
/*==============================================================*/
create table OFFERRESTARTDATA (
   CONTRACTID           varchar(10)          not null,
   OFFERDATE            datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   AVAILABILITY         varchar(3)           null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   FILENAME             varchar(40)          null,
   LASTCHANGED          datetime             null,
   PERIODID             numeric(3,0)         not null
)
go

alter table OFFERRESTARTDATA
   add constraint OFFERRESTARTDATA_PK primary key (CONTRACTID, OFFERDATE, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: OFFERRESTARTDATA_LCX                                  */
/*==============================================================*/
create index OFFERRESTARTDATA_LCX on OFFERRESTARTDATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: OFFERRPOWERDATA                                       */
/*==============================================================*/
create table OFFERRPOWERDATA (
   CONTRACTID           varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   AVAILABILITY         numeric(3,0)         null,
   MTA                  numeric(6,0)         null,
   MTG                  numeric(6,0)         null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   FILENAME             varchar(40)          null,
   LASTCHANGED          datetime             null
)
go

alter table OFFERRPOWERDATA
   add constraint OFFERRPOWERDATA_PK primary key (CONTRACTID, EFFECTIVEDATE, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: OFFERRPOWERDATA_NDX2                                  */
/*==============================================================*/
create index OFFERRPOWERDATA_NDX2 on OFFERRPOWERDATA (
CONTRACTID ASC
)
go

/*==============================================================*/
/* Index: OFFERRPOWERDATA_LCX                                   */
/*==============================================================*/
create index OFFERRPOWERDATA_LCX on OFFERRPOWERDATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: OFFERULOADINGDATA                                     */
/*==============================================================*/
create table OFFERULOADINGDATA (
   CONTRACTID           varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   AVAILABLELOAD        numeric(4,0)         null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   FILENAME             varchar(40)          null,
   LASTCHANGED          datetime             null,
   PERIODID             numeric(3,0)         not null
)
go

alter table OFFERULOADINGDATA
   add constraint OFFERULOADINGDATA_PK primary key (CONTRACTID, EFFECTIVEDATE, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: OFFERULOADINGDATA_NDX2                                */
/*==============================================================*/
create index OFFERULOADINGDATA_NDX2 on OFFERULOADINGDATA (
CONTRACTID ASC
)
go

/*==============================================================*/
/* Index: OFFERULOADINGDATA_LCX                                 */
/*==============================================================*/
create index OFFERULOADINGDATA_LCX on OFFERULOADINGDATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: OFFERUNLOADINGDATA                                    */
/*==============================================================*/
create table OFFERUNLOADINGDATA (
   CONTRACTID           varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   AVAILABLELOAD        numeric(4,0)         null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   FILENAME             varchar(40)          null,
   LASTCHANGED          datetime             null,
   PERIODID             numeric(3,0)         not null
)
go

alter table OFFERUNLOADINGDATA
   add constraint OFFERUNLOADINGDATA_PK primary key (CONTRACTID, EFFECTIVEDATE, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: OFFERUNLOADINGDATA_NDX2                               */
/*==============================================================*/
create index OFFERUNLOADINGDATA_NDX2 on OFFERUNLOADINGDATA (
CONTRACTID ASC
)
go

/*==============================================================*/
/* Index: OFFERUNLOADINGDATA_LCX                                */
/*==============================================================*/
create index OFFERUNLOADINGDATA_LCX on OFFERUNLOADINGDATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: OVERRIDERRP                                           */
/*==============================================================*/
create table OVERRIDERRP (
   REGIONID             varchar(10)          not null,
   STARTDATE            datetime             not null,
   STARTPERIOD          numeric(3,0)         not null,
   ENDDATE              datetime             null,
   ENDPERIOD            numeric(3,0)         null,
   RRP                  numeric(15,0)        null,
   DESCRIPTION          varchar(128)         null,
   AUTHORISESTART       varchar(15)          null,
   AUTHORISEEND         varchar(15)          null,
   LASTCHANGED          datetime             null
)
go

alter table OVERRIDERRP
   add constraint OVERRIDERRP_PK primary key (STARTDATE, STARTPERIOD, REGIONID)
go

/*==============================================================*/
/* Index: OVERRIDERRP_LCX                                       */
/*==============================================================*/
create index OVERRIDERRP_LCX on OVERRIDERRP (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: P5MIN_BLOCKEDCONSTRAINT                               */
/*==============================================================*/
create table P5MIN_BLOCKEDCONSTRAINT (
   RUN_DATETIME         datetime             not null,
   CONSTRAINTID         varchar(20)          not null
)
go

alter table P5MIN_BLOCKEDCONSTRAINT
   add constraint P5MIN_BLOCKEDCONSTRAINT_PK primary key (RUN_DATETIME, CONSTRAINTID)
go

/*==============================================================*/
/* Table: P5MIN_CASESOLUTION                                    */
/*==============================================================*/
create table P5MIN_CASESOLUTION (
   RUN_DATETIME         datetime             not null,
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
   LASTCHANGED          datetime             null,
   INTERVENTION         numeric(2,0)         null
)
go

alter table P5MIN_CASESOLUTION
   add constraint P5MIN_CASESOLUTION_PK primary key (RUN_DATETIME)
go

/*==============================================================*/
/* Index: P5MIN_CASESOLUTION_LCX                                */
/*==============================================================*/
create index P5MIN_CASESOLUTION_LCX on P5MIN_CASESOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: P5MIN_CONSTRAINTSOLUTION                              */
/*==============================================================*/
create table P5MIN_CONSTRAINTSOLUTION (
   RUN_DATETIME         datetime             not null,
   INTERVAL_DATETIME    datetime             not null,
   CONSTRAINTID         varchar(20)          not null,
   RHS                  numeric(15,5)        null,
   MARGINALVALUE        numeric(15,5)        null,
   VIOLATIONDEGREE      numeric(15,5)        null,
   LASTCHANGED          datetime             null,
   DUID                 varchar(20)          null,
   GENCONID_EFFECTIVEDATE datetime             null,
   GENCONID_VERSIONNO   numeric(22,0)        null,
   LHS                  numeric(15,5)        null,
   INTERVENTION         numeric(2,0)         null
)
go

alter table P5MIN_CONSTRAINTSOLUTION
   add constraint P5MIN_CONSTRAINTSOLUTION_PK primary key (RUN_DATETIME, CONSTRAINTID, INTERVAL_DATETIME)
go

/*==============================================================*/
/* Index: P5MIN_CONSTRAINTSOLUTION_LCX                          */
/*==============================================================*/
create index P5MIN_CONSTRAINTSOLUTION_LCX on P5MIN_CONSTRAINTSOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: P5MIN_INTERCONNECTORSOLN                              */
/*==============================================================*/
create table P5MIN_INTERCONNECTORSOLN (
   RUN_DATETIME         datetime             not null,
   INTERCONNECTORID     varchar(10)          not null,
   INTERVAL_DATETIME    datetime             not null,
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
   LASTCHANGED          datetime             null,
   LOCAL_PRICE_ADJUSTMENT_EXPORT numeric(10,2)        null,
   LOCALLY_CONSTRAINED_EXPORT numeric(1,0)         null,
   LOCAL_PRICE_ADJUSTMENT_IMPORT numeric(10,2)        null,
   LOCALLY_CONSTRAINED_IMPORT numeric(1,0)         null,
   INTERVENTION         numeric(2,0)         null
)
go

alter table P5MIN_INTERCONNECTORSOLN
   add constraint P5MIN_INTERCONNECTORSOLN_PK primary key (RUN_DATETIME, INTERCONNECTORID, INTERVAL_DATETIME)
go

/*==============================================================*/
/* Index: P5MIN_INTERCONNECTORSOLN_LCX                          */
/*==============================================================*/
create index P5MIN_INTERCONNECTORSOLN_LCX on P5MIN_INTERCONNECTORSOLN (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: P5MIN_LOCAL_PRICE                                     */
/*==============================================================*/
create table P5MIN_LOCAL_PRICE (
   RUN_DATETIME         datetime             not null,
   INTERVAL_DATETIME    datetime             not null,
   DUID                 varchar(20)          not null,
   LOCAL_PRICE_ADJUSTMENT numeric(10,2)        null,
   LOCALLY_CONSTRAINED  numeric(1,0)         null
)
go

alter table P5MIN_LOCAL_PRICE
   add constraint P5MIN_LOCAL_PRICE_PK primary key (RUN_DATETIME, INTERVAL_DATETIME, DUID)
go

/*==============================================================*/
/* Table: P5MIN_REGIONSOLUTION                                  */
/*==============================================================*/
create table P5MIN_REGIONSOLUTION (
   RUN_DATETIME         datetime             not null,
   INTERVAL_DATETIME    datetime             not null,
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
   LASTCHANGED          datetime             null,
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
)
go

alter table P5MIN_REGIONSOLUTION
   add constraint P5MIN_REGIONSOLUTION_PK primary key (RUN_DATETIME, REGIONID, INTERVAL_DATETIME)
go

/*==============================================================*/
/* Index: P5MIN_REGIONSOLUTION_LCX                              */
/*==============================================================*/
create index P5MIN_REGIONSOLUTION_LCX on P5MIN_REGIONSOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: P5MIN_UNITSOLUTION                                    */
/*==============================================================*/
create table P5MIN_UNITSOLUTION (
   RUN_DATETIME         datetime             not null,
   INTERVAL_DATETIME    datetime             not null,
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
   LASTCHANGED          datetime             null,
   SEMIDISPATCHCAP      numeric(3,0)         null,
   INTERVENTION         numeric(2,0)         null
)
go

alter table P5MIN_UNITSOLUTION
   add constraint P5MIN_UNITSOLUTION_PK primary key (RUN_DATETIME, DUID, INTERVAL_DATETIME)
go

/*==============================================================*/
/* Index: P5MIN_UNITSOLUTION_LCX                                */
/*==============================================================*/
create index P5MIN_UNITSOLUTION_LCX on P5MIN_UNITSOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PARTICIPANT                                           */
/*==============================================================*/
create table PARTICIPANT (
   PARTICIPANTID        varchar(10)          not null,
   PARTICIPANTCLASSID   varchar(20)          null,
   NAME                 varchar(80)          null,
   DESCRIPTION          varchar(64)          null,
   ACN                  varchar(9)           null,
   PRIMARYBUSINESS      varchar(40)          null,
   LASTCHANGED          datetime             null
)
go

alter table PARTICIPANT
   add constraint PARTICIPANT_PK primary key (PARTICIPANTID)
go

/*==============================================================*/
/* Index: PARTICIPANT_LCX                                       */
/*==============================================================*/
create index PARTICIPANT_LCX on PARTICIPANT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PARTICIPANTACCOUNT                                    */
/*==============================================================*/
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
   AUTHORISEDDATE       datetime             null,
   EFFECTIVEDATE        datetime             null,
   LASTCHANGED          datetime             null,
   ABN                  varchar(20)          null
)
go

alter table PARTICIPANTACCOUNT
   add constraint PARTICIPANTACCOUNT_PK primary key (PARTICIPANTID)
go

/*==============================================================*/
/* Index: PARTICIPANTACCOUNT_LCX                                */
/*==============================================================*/
create index PARTICIPANTACCOUNT_LCX on PARTICIPANTACCOUNT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PARTICIPANTCATEGORY                                   */
/*==============================================================*/
create table PARTICIPANTCATEGORY (
   PARTICIPANTCATEGORYID varchar(10)          not null,
   DESCRIPTION          varchar(64)          null,
   LASTCHANGED          datetime             null
)
go

alter table PARTICIPANTCATEGORY
   add constraint PARTICIPANTCATEGORY_PK primary key (PARTICIPANTCATEGORYID)
go

/*==============================================================*/
/* Index: PARTICIPANTCATEGORY_LCX                               */
/*==============================================================*/
create index PARTICIPANTCATEGORY_LCX on PARTICIPANTCATEGORY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PARTICIPANTCATEGORYALLOC                              */
/*==============================================================*/
create table PARTICIPANTCATEGORYALLOC (
   PARTICIPANTCATEGORYID varchar(10)          not null,
   PARTICIPANTID        varchar(10)          not null,
   LASTCHANGED          datetime             null
)
go

alter table PARTICIPANTCATEGORYALLOC
   add constraint PARTICIPANTCATALLOC_PK primary key (PARTICIPANTCATEGORYID, PARTICIPANTID)
go

/*==============================================================*/
/* Index: PARTICIPANTCATEGORYALLOC_LCX                          */
/*==============================================================*/
create index PARTICIPANTCATEGORYALLOC_LCX on PARTICIPANTCATEGORYALLOC (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PARTICIPANTCLASS                                      */
/*==============================================================*/
create table PARTICIPANTCLASS (
   PARTICIPANTCLASSID   varchar(20)          not null,
   DESCRIPTION          varchar(64)          null,
   LASTCHANGED          datetime             null
)
go

alter table PARTICIPANTCLASS
   add constraint PARTCLASS_PK primary key (PARTICIPANTCLASSID)
go

/*==============================================================*/
/* Index: PARTICIPANTCLASS_LCX                                  */
/*==============================================================*/
create index PARTICIPANTCLASS_LCX on PARTICIPANTCLASS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PARTICIPANTCREDITDETAIL                               */
/*==============================================================*/
create table PARTICIPANTCREDITDETAIL (
   EFFECTIVEDATE        datetime             not null,
   PARTICIPANTID        varchar(10)          not null,
   CREDITLIMIT          numeric(10,0)        null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table PARTICIPANTCREDITDETAIL
   add constraint PARTCREDDET_PK primary key (EFFECTIVEDATE, PARTICIPANTID)
go

/*==============================================================*/
/* Index: PARTICIPANTCREDITDETAIL_LCX                           */
/*==============================================================*/
create index PARTICIPANTCREDITDETAIL_LCX on PARTICIPANTCREDITDETAIL (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: PARTICIPANTCREDITDET_NDX2                             */
/*==============================================================*/
create index PARTICIPANTCREDITDET_NDX2 on PARTICIPANTCREDITDETAIL (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Table: PARTICIPANTNOTICETRK                                  */
/*==============================================================*/
create table PARTICIPANTNOTICETRK (
   PARTICIPANTID        varchar(10)          not null,
   NOTICEID             numeric(10,0)        not null,
   LASTCHANGED          datetime             null
)
go

alter table PARTICIPANTNOTICETRK
   add constraint PARTICIPANTNOTICETRK_PK primary key (PARTICIPANTID, NOTICEID)
go

/*==============================================================*/
/* Index: PARTICIPANTNOTICETRK_NDX2                             */
/*==============================================================*/
create index PARTICIPANTNOTICETRK_NDX2 on PARTICIPANTNOTICETRK (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: PARTICIPANTNOTICETRK_LCX                              */
/*==============================================================*/
create index PARTICIPANTNOTICETRK_LCX on PARTICIPANTNOTICETRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PARTICIPANT_BANDFEE_ALLOC                             */
/*==============================================================*/
create table PARTICIPANT_BANDFEE_ALLOC (
   PARTICIPANTID        varchar(10)          not null,
   MARKETFEEID          varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTCATEGORYID varchar(10)          not null,
   MARKETFEEVALUE       numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table PARTICIPANT_BANDFEE_ALLOC
   add constraint PARTICIPANT_BANDFEE_ALLOC_PK primary key (PARTICIPANTID, MARKETFEEID, EFFECTIVEDATE, VERSIONNO, PARTICIPANTCATEGORYID)
go

/*==============================================================*/
/* Index: PARTICIPANT_BANDFEE_ALOC_LCX                          */
/*==============================================================*/
create index PARTICIPANT_BANDFEE_ALOC_LCX on PARTICIPANT_BANDFEE_ALLOC (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PASACASESOLUTION                                      */
/*==============================================================*/
create table PASACASESOLUTION (
   CASEID               varchar(20)          not null,
   SOLUTIONCOMPLETE     numeric(16,6)        null,
   PASAVERSION          numeric(27,10)       null,
   EXCESSGENERATION     numeric(16,6)        null,
   DEFICITCAPACITY      numeric(16,6)        null,
   LASTCHANGED          datetime             null,
   DATETIME             datetime             null
)
go

alter table PASACASESOLUTION
   add constraint PASACASESOLUTION_PK primary key (CASEID)
go

/*==============================================================*/
/* Index: PASACASESOLUTION_LCX                                  */
/*==============================================================*/
create index PASACASESOLUTION_LCX on PASACASESOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PASACONSTRAINTSOLUTION                                */
/*==============================================================*/
create table PASACONSTRAINTSOLUTION (
   CASEID               varchar(20)          not null,
   CONSTRAINTID         varchar(20)          not null,
   PERIODID             varchar(20)          not null,
   CAPACITYMARGINALVALUE numeric(16,6)        null,
   CAPACITYVIOLATIONDEGREE numeric(16,6)        null,
   EXCESSGENMARGINALVALUE numeric(16,6)        null,
   EXCESSGENVIOLATIONDEGREE numeric(16,6)        null,
   LASTCHANGED          datetime             null,
   DATETIME             datetime             null
)
go

alter table PASACONSTRAINTSOLUTION
   add constraint PASACONSTRAINTSOLUTION_PK primary key (PERIODID, CONSTRAINTID)
go

/*==============================================================*/
/* Index: PASACONSTRAINTSOLUTION_LCX                            */
/*==============================================================*/
create index PASACONSTRAINTSOLUTION_LCX on PASACONSTRAINTSOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PASAINTERCONNECTORSOLUTION                            */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   IMPORTLIMIT          numeric(15,5)        null,
   EXPORTLIMIT          numeric(15,5)        null,
   DATETIME             datetime             null
)
go

alter table PASAINTERCONNECTORSOLUTION
   add constraint PASAINTERCONNECTORSOLUTION_PK primary key (PERIODID, INTERCONNECTORID)
go

/*==============================================================*/
/* Index: PASAINTERCONNECTORSOLUTIO_LCX                         */
/*==============================================================*/
create index PASAINTERCONNECTORSOLUTIO_LCX on PASAINTERCONNECTORSOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PASAREGIONSOLUTION                                    */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   EXCESSGENERATION     numeric(22,0)        null,
   ENERGYREQUIRED       numeric(15,5)        null,
   CAPACITYREQUIRED     numeric(15,5)        null,
   DATETIME             datetime             null
)
go

alter table PASAREGIONSOLUTION
   add constraint PASAREGIONSOLUTION_PK primary key (PERIODID, REGIONID)
go

/*==============================================================*/
/* Index: PASAREGIONSOLUTION_LCX                                */
/*==============================================================*/
create index PASAREGIONSOLUTION_LCX on PASAREGIONSOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PDPASA_CASESOLUTION                                   */
/*==============================================================*/
create table PDPASA_CASESOLUTION (
   RUN_DATETIME         datetime             not null,
   PASAVERSION          varchar(10)          null,
   RESERVECONDITION     numeric(1,0)         null,
   LORCONDITION         numeric(1,0)         null,
   CAPACITYOBJFUNCTION  numeric(12,3)        null,
   CAPACITYOPTION       numeric(12,3)        null,
   MAXSURPLUSRESERVEOPTION numeric(12,3)        null,
   MAXSPARECAPACITYOPTION numeric(12,3)        null,
   INTERCONNECTORFLOWPENALTY numeric(12,3)        null,
   LASTCHANGED          datetime             null,
   RELIABILITYLRCDEMANDOPTION numeric(12,3)        null,
   OUTAGELRCDEMANDOPTION numeric(12,3)        null,
   LORDEMANDOPTION      numeric(12,3)        null,
   RELIABILITYLRCCAPACITYOPTION varchar(10)          null,
   OUTAGELRCCAPACITYOPTION varchar(10)          null,
   LORCAPACITYOPTION    varchar(10)          null,
   LORUIGFOPTION        numeric(3,0)         null,
   RELIABILITYLRCUIGFOPTION numeric(3,0)         null,
   OUTAGELRCUIGFOPTION  numeric(3,0)         null
)
go

alter table PDPASA_CASESOLUTION
   add constraint PDPASA_CASESOLUTION_PK primary key (RUN_DATETIME)
go

/*==============================================================*/
/* Index: PDPASA_CASESOLUTION_LCX                               */
/*==============================================================*/
create index PDPASA_CASESOLUTION_LCX on PDPASA_CASESOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PDPASA_REGIONSOLUTION                                 */
/*==============================================================*/
create table PDPASA_REGIONSOLUTION (
   RUN_DATETIME         datetime             not null,
   INTERVAL_DATETIME    datetime             not null,
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
   LASTCHANGED          datetime             null,
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
)
go

alter table PDPASA_REGIONSOLUTION
   add constraint PDPASA_REGIONSOLUTION_PK primary key (RUN_DATETIME, RUNTYPE, INTERVAL_DATETIME, REGIONID)
go

/*==============================================================*/
/* Index: PDPASA_REGIONSOLUTION_LCX                             */
/*==============================================================*/
create index PDPASA_REGIONSOLUTION_LCX on PDPASA_REGIONSOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PERDEMAND                                             */
/*==============================================================*/
create table PERDEMAND (
   EFFECTIVEDATE        datetime             null,
   SETTLEMENTDATE       datetime             not null,
   REGIONID             varchar(10)          not null,
   OFFERDATE            datetime             not null,
   PERIODID             numeric(3,0)         not null,
   VERSIONNO            numeric(3,0)         not null,
   RESDEMAND            numeric(10,0)        null,
   DEMAND90PROBABILITY  numeric(10,0)        null,
   DEMAND10PROBABILITY  numeric(10,0)        null,
   LASTCHANGED          datetime             null,
   MR_SCHEDULE          numeric(6,0)         null
)
go

alter table PERDEMAND
   add constraint PERDEMAND_PK primary key (SETTLEMENTDATE, REGIONID, OFFERDATE, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: PERDEMAND_LCX                                         */
/*==============================================================*/
create index PERDEMAND_LCX on PERDEMAND (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PEROFFER                                              */
/*==============================================================*/
create table PEROFFER (
   SETTLEMENTDATE       datetime             not null,
   DUID                 varchar(10)          not null,
   OFFERDATE            datetime             not null,
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
   LASTCHANGED          datetime             null,
   PASAAVAILABILITY     numeric(12,0)        null,
   MR_CAPACITY          numeric(6,0)         null
)
go

alter table PEROFFER
   add constraint PEROFFER_PK primary key (SETTLEMENTDATE, DUID, OFFERDATE, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: PEROFFER_NDX2                                         */
/*==============================================================*/
create index PEROFFER_NDX2 on PEROFFER (
DUID ASC,
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: PEROFFER_LCX                                          */
/*==============================================================*/
create index PEROFFER_LCX on PEROFFER (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PEROFFER_D                                            */
/*==============================================================*/
create table PEROFFER_D (
   SETTLEMENTDATE       datetime             not null,
   DUID                 varchar(10)          not null,
   OFFERDATE            datetime             not null,
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
   LASTCHANGED          datetime             null,
   PASAAVAILABILITY     numeric(12,0)        null,
   MR_CAPACITY          numeric(6,0)         null
)
go

alter table PEROFFER_D
   add constraint PEROFFER_D_PK primary key (SETTLEMENTDATE, DUID, OFFERDATE, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: PEROFFER_D_NDX2                                       */
/*==============================================================*/
create index PEROFFER_D_NDX2 on PEROFFER_D (
DUID ASC,
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: PEROFFER_D_LCX                                        */
/*==============================================================*/
create index PEROFFER_D_LCX on PEROFFER_D (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PREDISPATCHBIDTRK                                     */
/*==============================================================*/
create table PREDISPATCHBIDTRK (
   PREDISPATCHSEQNO     varchar(20)          not null,
   DUID                 varchar(10)          not null,
   PERIODID             varchar(20)          not null,
   BIDTYPE              varchar(10)          null,
   OFFERDATE            datetime             null,
   VERSIONNO            numeric(3,0)         null,
   LASTCHANGED          datetime             null,
   SETTLEMENTDATE       datetime             null,
   DATETIME             datetime             null
)
go

alter table PREDISPATCHBIDTRK
   add constraint PREDISPATCHBIDTRK_PK primary key (PREDISPATCHSEQNO, DUID, PERIODID)
go

/*==============================================================*/
/* Index: PREDISPATCHBIDTRK_LCX                                 */
/*==============================================================*/
create index PREDISPATCHBIDTRK_LCX on PREDISPATCHBIDTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: PREDISPATCHBIDTRK_NDX2                                */
/*==============================================================*/
create index PREDISPATCHBIDTRK_NDX2 on PREDISPATCHBIDTRK (
DUID ASC,
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: PREDISPATCHBIDTRK_NDX3                                */
/*==============================================================*/
create index PREDISPATCHBIDTRK_NDX3 on PREDISPATCHBIDTRK (
DUID ASC,
SETTLEMENTDATE ASC
)
go

/*==============================================================*/
/* Table: PREDISPATCHBLOCKEDCONSTRAINT                          */
/*==============================================================*/
create table PREDISPATCHBLOCKEDCONSTRAINT (
   PREDISPATCHSEQNO     varchar(20)          not null,
   CONSTRAINTID         varchar(20)          not null
)
go

alter table PREDISPATCHBLOCKEDCONSTRAINT
   add constraint PK_PREDISPATCHBLOCKEDCONSTR primary key (PREDISPATCHSEQNO, CONSTRAINTID)
go

/*==============================================================*/
/* Table: PREDISPATCHCASESOLUTION                               */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   INTERVENTION         numeric(2,0)         null
)
go

alter table PREDISPATCHCASESOLUTION
   add constraint PREDISPATCHCASESOLUTION_PK primary key (PREDISPATCHSEQNO, RUNNO)
go

/*==============================================================*/
/* Index: PREDISPATCHCASESOL_NDX_LCHD                           */
/*==============================================================*/
create index PREDISPATCHCASESOL_NDX_LCHD on PREDISPATCHCASESOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PREDISPATCHCONSTRAINT                                 */
/*==============================================================*/
create table PREDISPATCHCONSTRAINT (
   PREDISPATCHSEQNO     varchar(20)          null,
   RUNNO                numeric(3,0)         null,
   CONSTRAINTID         varchar(20)          not null,
   PERIODID             varchar(20)          null,
   INTERVENTION         numeric(2,0)         null,
   RHS                  numeric(15,5)        null,
   MARGINALVALUE        numeric(15,5)        null,
   VIOLATIONDEGREE      numeric(15,5)        null,
   LASTCHANGED          datetime             null,
   DATETIME             datetime             not null,
   DUID                 varchar(20)          null,
   GENCONID_EFFECTIVEDATE datetime             null,
   GENCONID_VERSIONNO   numeric(22,0)        null,
   LHS                  numeric(15,5)        null
)
go

alter table PREDISPATCHCONSTRAINT
   add constraint PK_PREDISPATCHCONSTRAINT primary key (DATETIME, CONSTRAINTID)
go

/*==============================================================*/
/* Index: PREDISPATCHCONSTRAIN_NDX2                             */
/*==============================================================*/
create index PREDISPATCHCONSTRAIN_NDX2 on PREDISPATCHCONSTRAINT (
PREDISPATCHSEQNO ASC
)
go

/*==============================================================*/
/* Index: PREDISPATCHCONSTRAINT_LCX                             */
/*==============================================================*/
create index PREDISPATCHCONSTRAINT_LCX on PREDISPATCHCONSTRAINT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PREDISPATCHINTERCONNECTORRES                          */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   DATETIME             datetime             not null,
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
)
go

alter table PREDISPATCHINTERCONNECTORRES
   add constraint PK_PREDISPATCHINTCONRES primary key (DATETIME, INTERCONNECTORID)
go

/*==============================================================*/
/* Index: PREDISPATCHINTERCONNECTOR_LCX                         */
/*==============================================================*/
create index PREDISPATCHINTERCONNECTOR_LCX on PREDISPATCHINTERCONNECTORRES (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: PREDISPATCHINTCONRES_NDX3                             */
/*==============================================================*/
create index PREDISPATCHINTCONRES_NDX3 on PREDISPATCHINTERCONNECTORRES (
PREDISPATCHSEQNO ASC
)
go

/*==============================================================*/
/* Table: PREDISPATCHINTERSENSITIVITIES                         */
/*==============================================================*/
create table PREDISPATCHINTERSENSITIVITIES (
   PREDISPATCHSEQNO     varchar(20)          null,
   RUNNO                numeric(3,0)         null,
   INTERCONNECTORID     varchar(10)          not null,
   PERIODID             varchar(20)          null,
   INTERVENTION         numeric(2,0)         null,
   DATETIME             datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table PREDISPATCHINTERSENSITIVITIES
   add constraint PREDISPATCHINTERSENSITIVIT_PK primary key (INTERCONNECTORID, DATETIME)
go

/*==============================================================*/
/* Index: PREDISPATCHINTERSENSITIVIT_LCX                        */
/*==============================================================*/
create index PREDISPATCHINTERSENSITIVIT_LCX on PREDISPATCHINTERSENSITIVITIES (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PREDISPATCHLOAD                                       */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   DATETIME             datetime             not null,
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
)
go

alter table PREDISPATCHLOAD
   add constraint PK_PREDISPATCHLOAD primary key (DATETIME, DUID)
go

/*==============================================================*/
/* Index: PREDISPATCHLOAD_NDX2                                  */
/*==============================================================*/
create index PREDISPATCHLOAD_NDX2 on PREDISPATCHLOAD (
DUID ASC,
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: PREDISPATCHLOAD_NDX3                                  */
/*==============================================================*/
create index PREDISPATCHLOAD_NDX3 on PREDISPATCHLOAD (
PREDISPATCHSEQNO ASC
)
go

/*==============================================================*/
/* Index: PREDISPATCHLOAD_LCX                                   */
/*==============================================================*/
create index PREDISPATCHLOAD_LCX on PREDISPATCHLOAD (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PREDISPATCHOFFERTRK                                   */
/*==============================================================*/
create table PREDISPATCHOFFERTRK (
   PREDISPATCHSEQNO     varchar(20)          not null,
   DUID                 varchar(10)          not null,
   BIDTYPE              varchar(20)          not null,
   PERIODID             varchar(20)          not null,
   BIDSETTLEMENTDATE    datetime             null,
   BIDOFFERDATE         datetime             null,
   DATETIME             datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table PREDISPATCHOFFERTRK
   add constraint PREDISPATCHOFFERTRK_PK primary key (PREDISPATCHSEQNO, DUID, BIDTYPE, PERIODID)
go

/*==============================================================*/
/* Index: PREDISPATCHOFFERTRK_LCHD_IDX                          */
/*==============================================================*/
create index PREDISPATCHOFFERTRK_LCHD_IDX on PREDISPATCHOFFERTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PREDISPATCHPRICE                                      */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   DATETIME             datetime             not null,
   RAISE6SECRRP         numeric(15,5)        null,
   RAISE60SECRRP        numeric(15,5)        null,
   RAISE5MINRRP         numeric(15,5)        null,
   RAISEREGRRP          numeric(15,5)        null,
   LOWER6SECRRP         numeric(15,5)        null,
   LOWER60SECRRP        numeric(15,5)        null,
   LOWER5MINRRP         numeric(15,5)        null,
   LOWERREGRRP          numeric(15,5)        null
)
go

alter table PREDISPATCHPRICE
   add constraint PK_PREDISPATCHPRICE primary key (DATETIME, REGIONID)
go

/*==============================================================*/
/* Index: PREDISPATCHPRICE_NDX3                                 */
/*==============================================================*/
create index PREDISPATCHPRICE_NDX3 on PREDISPATCHPRICE (
PREDISPATCHSEQNO ASC
)
go

/*==============================================================*/
/* Index: PREDISPATCHPRICE_LCX                                  */
/*==============================================================*/
create index PREDISPATCHPRICE_LCX on PREDISPATCHPRICE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PREDISPATCHPRICESENSITIVITIES                         */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   DATETIME             datetime             not null,
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
)
go

alter table PREDISPATCHPRICESENSITIVITIES
   add constraint PREDISPATCHPRICESENS_PK primary key (DATETIME, REGIONID)
go

/*==============================================================*/
/* Index: PREDISPATCHPRCESENS_NDX3                              */
/*==============================================================*/
create index PREDISPATCHPRCESENS_NDX3 on PREDISPATCHPRICESENSITIVITIES (
PREDISPATCHSEQNO ASC
)
go

/*==============================================================*/
/* Index: PREDISPATCHPRICESENSITIVI_LCX                         */
/*==============================================================*/
create index PREDISPATCHPRICESENSITIVI_LCX on PREDISPATCHPRICESENSITIVITIES (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PREDISPATCHREGIONSUM                                  */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   DATETIME             datetime             not null,
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
)
go

alter table PREDISPATCHREGIONSUM
   add constraint PK_PREDISPATCHREGIONSUM primary key (DATETIME, REGIONID)
go

/*==============================================================*/
/* Index: PREDISPATCHRGNSUM_NDX3                                */
/*==============================================================*/
create index PREDISPATCHRGNSUM_NDX3 on PREDISPATCHREGIONSUM (
PREDISPATCHSEQNO ASC
)
go

/*==============================================================*/
/* Index: PREDISPATCHREGIONSUM_LCX                              */
/*==============================================================*/
create index PREDISPATCHREGIONSUM_LCX on PREDISPATCHREGIONSUM (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PREDISPATCHSCENARIODEMAND                             */
/*==============================================================*/
create table PREDISPATCHSCENARIODEMAND (
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3)           not null,
   SCENARIO             numeric(2)           not null,
   REGIONID             varchar(20)          not null,
   DELTAMW              numeric(4)           null
)
go

alter table PREDISPATCHSCENARIODEMAND
   add constraint PREDISPATCHSCENARIODEMAND_PK primary key (EFFECTIVEDATE, VERSIONNO, SCENARIO, REGIONID)
go

/*==============================================================*/
/* Table: PREDISPATCHSCENARIODEMANDTRK                          */
/*==============================================================*/
create table PREDISPATCHSCENARIODEMANDTRK (
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3)           not null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table PREDISPATCHSCENARIODEMANDTRK
   add constraint PREDISPATCHSCENARIODMNDTRK_PK primary key (EFFECTIVEDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: PREDISPATCHSCENARIODMNDTRK_LCX                        */
/*==============================================================*/
create index PREDISPATCHSCENARIODMNDTRK_LCX on PREDISPATCHSCENARIODEMANDTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PREDISPATCH_FCAS_REQ                                  */
/*==============================================================*/
create table PREDISPATCH_FCAS_REQ (
   PREDISPATCHSEQNO     varchar(20)          null,
   RUNNO                numeric(3,0)         null,
   INTERVENTION         numeric(2,0)         null,
   PERIODID             varchar(20)          null,
   GENCONID             varchar(20)          not null,
   REGIONID             varchar(10)          not null,
   BIDTYPE              varchar(10)          not null,
   GENCONEFFECTIVEDATE  datetime             null,
   GENCONVERSIONNO      numeric(3,0)         null,
   MARGINALVALUE        numeric(16,6)        null,
   DATETIME             datetime             not null,
   LASTCHANGED          datetime             null,
   BASE_COST            numeric(18,8)        null,
   ADJUSTED_COST        numeric(18,8)        null,
   ESTIMATED_CMPF       numeric(18,8)        null,
   ESTIMATED_CRMPF      numeric(18,8)        null,
   RECOVERY_FACTOR_CMPF numeric(18,8)        null,
   RECOVERY_FACTOR_CRMPF numeric(18,8)        null
)
go

alter table PREDISPATCH_FCAS_REQ
   add constraint PREDISPATCH_FCAS_REQ_PK primary key (DATETIME, GENCONID, REGIONID, BIDTYPE)
go

/*==============================================================*/
/* Index: PREDISPATCH_FCAS_REQ_LCX                              */
/*==============================================================*/
create index PREDISPATCH_FCAS_REQ_LCX on PREDISPATCH_FCAS_REQ (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PREDISPATCH_LOCAL_PRICE                               */
/*==============================================================*/
create table PREDISPATCH_LOCAL_PRICE (
   PREDISPATCHSEQNO     varchar(20)          not null,
   DATETIME             datetime             not null,
   DUID                 varchar(20)          not null,
   PERIODID             varchar(20)          null,
   LOCAL_PRICE_ADJUSTMENT numeric(10,2)        null,
   LOCALLY_CONSTRAINED  numeric(1,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table PREDISPATCH_LOCAL_PRICE
   add constraint PREDISPATCH_LOCAL_PRICE_PK primary key (DATETIME, DUID)
go

/*==============================================================*/
/* Table: PREDISPATCH_MNSPBIDTRK                                */
/*==============================================================*/
create table PREDISPATCH_MNSPBIDTRK (
   PREDISPATCHSEQNO     varchar(20)          not null,
   LINKID               varchar(10)          not null,
   PERIODID             varchar(20)          not null,
   PARTICIPANTID        varchar(10)          null,
   SETTLEMENTDATE       datetime             null,
   OFFERDATE            datetime             null,
   VERSIONNO            numeric(3,0)         null,
   DATETIME             datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table PREDISPATCH_MNSPBIDTRK
   add constraint PREDISPATCH_MNSPBIDTRK_PK primary key (PREDISPATCHSEQNO, LINKID, PERIODID)
go

/*==============================================================*/
/* Index: PREDISPATCH_MNSPBIDTRK_LCX                            */
/*==============================================================*/
create index PREDISPATCH_MNSPBIDTRK_LCX on PREDISPATCH_MNSPBIDTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PRUDENTIALCOMPANYPOSITION                             */
/*==============================================================*/
create table PRUDENTIALCOMPANYPOSITION (
   PRUDENTIAL_DATE      datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table PRUDENTIALCOMPANYPOSITION
   add constraint PRUDENTIALCOMPANYPOSITION_PK primary key (PRUDENTIAL_DATE, RUNNO, COMPANY_ID)
go

/*==============================================================*/
/* Index: PRUDENTIALCOMPANYPOSITION_LCX                         */
/*==============================================================*/
create index PRUDENTIALCOMPANYPOSITION_LCX on PRUDENTIALCOMPANYPOSITION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: PRUDENTIALRUNTRK                                      */
/*==============================================================*/
create table PRUDENTIALRUNTRK (
   PRUDENTIAL_DATE      datetime             not null,
   RUNNO                numeric(3)           not null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table PRUDENTIALRUNTRK
   add constraint PRUDENTIALRUNTRK_PK primary key (PRUDENTIAL_DATE, RUNNO)
go

/*==============================================================*/
/* Index: PRUDENTIALRUNTRK_LCX                                  */
/*==============================================================*/
create index PRUDENTIALRUNTRK_LCX on PRUDENTIALRUNTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: REALLOCATION                                          */
/*==============================================================*/
create table REALLOCATION (
   REALLOCATIONID       varchar(20)          not null,
   CREDITPARTICIPANTID  varchar(10)          null,
   DEBITPARTICIPANTID   varchar(10)          null,
   REGIONID             varchar(10)          null,
   AGREEMENTTYPE        varchar(10)          null,
   CREDITREFERENCE      varchar(400)         null,
   DEBITREFERENCE       varchar(400)         null,
   LASTCHANGED          datetime             null,
   STARTDATE            datetime             null,
   ENDDATE              datetime             null,
   CURRENT_STEPID       varchar(20)          null,
   DAYTYPE              varchar(20)          null,
   REALLOCATION_TYPE    varchar(1)           null,
   CALENDARID           varchar(30)          null,
   INTERVALLENGTH       numeric(3,0)         null
)
go

alter table REALLOCATION
   add constraint REALLOCATION_PK primary key (REALLOCATIONID)
go

/*==============================================================*/
/* Index: REALLOCATION_LCX                                      */
/*==============================================================*/
create index REALLOCATION_LCX on REALLOCATION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: REALLOCATIONDETAILS                                   */
/*==============================================================*/
create table REALLOCATIONDETAILS (
   REALLOCATIONID       varchar(20)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(10)          null,
   LASTCHANGED          datetime             null
)
go

alter table REALLOCATIONDETAILS
   add constraint REALLOCATIONDETAILS_PK primary key (REALLOCATIONID, EFFECTIVEDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: REALLOCATIONDETAILS_LCX                               */
/*==============================================================*/
create index REALLOCATIONDETAILS_LCX on REALLOCATIONDETAILS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: REALLOCATIONINTERVAL                                  */
/*==============================================================*/
create table REALLOCATIONINTERVAL (
   REALLOCATIONID       varchar(20)          not null,
   PERIODID             numeric(3)           not null,
   VALUE                numeric(15,5)        null,
   LASTCHANGED          datetime             null,
   NRP                  numeric(15,5)        null
)
go

alter table REALLOCATIONINTERVAL
   add constraint REALLOCATIONINTERVAL_PK primary key (REALLOCATIONID, PERIODID)
go

/*==============================================================*/
/* Index: REALLOCATIONINTERVAL_LCX                              */
/*==============================================================*/
create index REALLOCATIONINTERVAL_LCX on REALLOCATIONINTERVAL (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: REALLOCATIONINTERVALS                                 */
/*==============================================================*/
create table REALLOCATIONINTERVALS (
   REALLOCATIONID       varchar(20)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   REALLOCATIONVALUE    numeric(6,2)         null,
   LASTCHANGED          datetime             null
)
go

alter table REALLOCATIONINTERVALS
   add constraint REALLOCATIONINTERVALS_PK primary key (REALLOCATIONID, EFFECTIVEDATE, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: REALLOCATIONINTERVALS_LCX                             */
/*==============================================================*/
create index REALLOCATIONINTERVALS_LCX on REALLOCATIONINTERVALS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: REALLOCATIONS                                         */
/*==============================================================*/
create table REALLOCATIONS (
   REALLOCATIONID       varchar(20)          not null,
   STARTDATE            datetime             null,
   STARTPERIOD          numeric(3,0)         null,
   ENDDATE              datetime             null,
   ENDPERIOD            numeric(3,0)         null,
   PARTICIPANTTOID      varchar(10)          null,
   PARTICIPANTFROMID    varchar(10)          null,
   AGREEMENTTYPE        varchar(10)          null,
   DEREGISTRATIONDATE   datetime             null,
   DEREGISTRATIONPERIOD numeric(3,0)         null,
   REGIONID             varchar(10)          null,
   LASTCHANGED          datetime             null
)
go

alter table REALLOCATIONS
   add constraint REALLOCATIONS_PK primary key (REALLOCATIONID)
go

/*==============================================================*/
/* Index: REALLOCATIONS_LCX                                     */
/*==============================================================*/
create index REALLOCATIONS_LCX on REALLOCATIONS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: REGION                                                */
/*==============================================================*/
create table REGION (
   REGIONID             varchar(10)          not null,
   DESCRIPTION          varchar(64)          null,
   REGIONSTATUS         varchar(8)           null,
   LASTCHANGED          datetime             null
)
go

alter table REGION
   add constraint REGION_PK primary key (REGIONID)
go

/*==============================================================*/
/* Index: REGION_LCX                                            */
/*==============================================================*/
create index REGION_LCX on REGION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: REGIONAPC                                             */
/*==============================================================*/
create table REGIONAPC (
   REGIONID             varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(10)          null,
   LASTCHANGED          datetime             null
)
go

alter table REGIONAPC
   add constraint REGIONAPC_PK primary key (REGIONID, EFFECTIVEDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: REGIONAPC_LCX                                         */
/*==============================================================*/
create index REGIONAPC_LCX on REGIONAPC (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: REGIONAPCINTERVALS                                    */
/*==============================================================*/
create table REGIONAPCINTERVALS (
   REGIONID             varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   APCVALUE             numeric(16,6)        null,
   LASTCHANGED          datetime             null,
   APCTYPE              numeric(3,0)         null,
   FCASAPCVALUE         numeric(16,6)        null,
   APFVALUE             numeric(16,6)        null
)
go

alter table REGIONAPCINTERVALS
   add constraint REGIONAPCINTERVALS_PK primary key (REGIONID, EFFECTIVEDATE, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: REGIONAPCINTERVALS_LCX                                */
/*==============================================================*/
create index REGIONAPCINTERVALS_LCX on REGIONAPCINTERVALS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: REGIONFCASRELAXATION_OCD                              */
/*==============================================================*/
create table REGIONFCASRELAXATION_OCD (
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   SERVICETYPE          varchar(10)          not null,
   GLOBAL               numeric(1,0)         not null,
   REQUIREMENT          numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table REGIONFCASRELAXATION_OCD
   add constraint PK_REGIONFCASRELAXATION_OCD primary key (SETTLEMENTDATE, RUNNO, REGIONID, SERVICETYPE, GLOBAL)
go

/*==============================================================*/
/* Index: REGIONFCASRELAXATION_OCD_LCX                          */
/*==============================================================*/
create index REGIONFCASRELAXATION_OCD_LCX on REGIONFCASRELAXATION_OCD (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: REGIONSTANDINGDATA                                    */
/*==============================================================*/
create table REGIONSTANDINGDATA (
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   RSOID                varchar(10)          null,
   REGIONALREFERENCEPOINTID varchar(10)          null,
   PEAKTRADINGPERIOD    numeric(3,0)         null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   SCALINGFACTOR        numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table REGIONSTANDINGDATA
   add constraint REGIONSTANDINGDATA_PK primary key (EFFECTIVEDATE, VERSIONNO, REGIONID)
go

/*==============================================================*/
/* Index: REGIONSTANDINGDATA_LCX                                */
/*==============================================================*/
create index REGIONSTANDINGDATA_LCX on REGIONSTANDINGDATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: RESDEMANDTRK                                          */
/*==============================================================*/
create table RESDEMANDTRK (
   EFFECTIVEDATE        datetime             not null,
   REGIONID             varchar(10)          not null,
   OFFERDATE            datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   FILENAME             varchar(40)          null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(10)          null,
   LASTCHANGED          datetime             null
)
go

alter table RESDEMANDTRK
   add constraint RESDEMANDTRK_PK primary key (REGIONID, EFFECTIVEDATE, OFFERDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: RESDEMANDTRK_LCX                                      */
/*==============================================================*/
create index RESDEMANDTRK_LCX on RESDEMANDTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: RESERVE                                               */
/*==============================================================*/
create table RESERVE (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   REGIONID             varchar(12)          not null,
   PERIODID             numeric(2,0)         not null,
   LOWER5MIN            numeric(6,0)         null,
   LOWER60SEC           numeric(6,0)         null,
   LOWER6SEC            numeric(6,0)         null,
   RAISE5MIN            numeric(6,0)         null,
   RAISE60SEC           numeric(6,0)         null,
   RAISE6SEC            numeric(6,0)         null,
   LASTCHANGED          datetime             null,
   PASARESERVE          numeric(6,0)         null,
   LOADREJECTIONRESERVEREQ numeric(10,0)        null,
   RAISEREG             numeric(6,0)         null,
   LOWERREG             numeric(6,0)         null,
   LOR1LEVEL            numeric(6,0)         null,
   LOR2LEVEL            numeric(6,0)         null
)
go

alter table RESERVE
   add constraint RESERVE_PK primary key (SETTLEMENTDATE, REGIONID, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: RESERVE_LCX                                           */
/*==============================================================*/
create index RESERVE_LCX on RESERVE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: RESIDUECONTRACTPAYMENTS                               */
/*==============================================================*/
create table RESIDUECONTRACTPAYMENTS (
   CONTRACTID           varchar(30)          not null,
   PARTICIPANTID        varchar(10)          not null,
   LASTCHANGED          datetime             null
)
go

alter table RESIDUECONTRACTPAYMENTS
   add constraint RESIDUECONTRACTPAYMENTS_PK primary key (CONTRACTID, PARTICIPANTID)
go

/*==============================================================*/
/* Index: RESIDUECONTRACTPAYMENTS_LCX                           */
/*==============================================================*/
create index RESIDUECONTRACTPAYMENTS_LCX on RESIDUECONTRACTPAYMENTS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: RESIDUEFILETRK                                        */
/*==============================================================*/
create table RESIDUEFILETRK (
   CONTRACTID           varchar(30)          null,
   PARTICIPANTID        varchar(10)          not null,
   LOADDATE             datetime             not null,
   FILENAME             varchar(40)          null,
   ACKFILENAME          varchar(40)          null,
   STATUS               varchar(10)          null,
   LASTCHANGED          datetime             null,
   AUCTIONID            varchar(30)          not null
)
go

alter table RESIDUEFILETRK
   add constraint RESIDUEFILETRK_PK primary key (AUCTIONID, PARTICIPANTID, LOADDATE)
go

/*==============================================================*/
/* Index: RESIDUEFILETRK_NDX_LCHD                               */
/*==============================================================*/
create index RESIDUEFILETRK_NDX_LCHD on RESIDUEFILETRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: RESIDUE_BID_TRK                                       */
/*==============================================================*/
create table RESIDUE_BID_TRK (
   CONTRACTID           varchar(30)          null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   BIDLOADDATE          datetime             null,
   LASTCHANGED          datetime             null,
   AUCTIONID            varchar(30)          not null
)
go

alter table RESIDUE_BID_TRK
   add constraint RESIDUE_BID_TRK_PK primary key (AUCTIONID, VERSIONNO, PARTICIPANTID)
go

/*==============================================================*/
/* Index: RESIDUEBID_NDX_LCHD                                   */
/*==============================================================*/
create index RESIDUEBID_NDX_LCHD on RESIDUE_BID_TRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: RESIDUE_CONTRACTS                                     */
/*==============================================================*/
create table RESIDUE_CONTRACTS (
   CONTRACTYEAR         numeric(4,0)         not null,
   QUARTER              numeric(1,0)         not null,
   TRANCHE              numeric(2,0)         not null,
   CONTRACTID           varchar(30)          null,
   STARTDATE            datetime             null,
   ENDDATE              datetime             null,
   NOTIFYDATE           datetime             null,
   AUCTIONDATE          datetime             null,
   CALCMETHOD           varchar(20)          null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   NOTIFYPOSTDATE       datetime             null,
   NOTIFYBY             varchar(15)          null,
   POSTDATE             datetime             null,
   POSTEDBY             varchar(15)          null,
   LASTCHANGED          datetime             null,
   DESCRIPTION          varchar(80)          null,
   AUCTIONID            varchar(30)          null
)
go

alter table RESIDUE_CONTRACTS
   add constraint RESIDUE_CONTRACTS_PK primary key (CONTRACTYEAR, QUARTER, TRANCHE)
go

/*==============================================================*/
/* Index: RESIDUE_CONTRACTS_LCX                                 */
/*==============================================================*/
create index RESIDUE_CONTRACTS_LCX on RESIDUE_CONTRACTS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: RESIDUE_CON_DATA                                      */
/*==============================================================*/
create table RESIDUE_CON_DATA (
   CONTRACTID           varchar(30)          not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   UNITSPURCHASED       numeric(17,5)        null,
   LINKPAYMENT          numeric(17,5)        null,
   LASTCHANGED          datetime             null,
   SECONDARY_UNITS_SOLD numeric(18,8)        null
)
go

alter table RESIDUE_CON_DATA
   add constraint RESIDUE_CON_DATA_PK primary key (CONTRACTID, VERSIONNO, PARTICIPANTID, INTERCONNECTORID, FROMREGIONID)
go

/*==============================================================*/
/* Index: RESIDUE_CON_DATA_LCX                                  */
/*==============================================================*/
create index RESIDUE_CON_DATA_LCX on RESIDUE_CON_DATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: RESIDUE_CON_ESTIMATES_TRK                             */
/*==============================================================*/
create table RESIDUE_CON_ESTIMATES_TRK (
   CONTRACTID           varchar(30)          not null,
   CONTRACTYEAR         numeric(4,0)         not null,
   QUARTER              numeric(1,0)         not null,
   VALUATIONID          varchar(15)          not null,
   VERSIONNO            numeric(3,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table RESIDUE_CON_ESTIMATES_TRK
   add constraint RESIDUE_CON_ESTIMATES_TRK_PK primary key (CONTRACTID, CONTRACTYEAR, QUARTER, VALUATIONID)
go

/*==============================================================*/
/* Index: REVCONESTIMATESTRK_NDX_LCHD                           */
/*==============================================================*/
create index REVCONESTIMATESTRK_NDX_LCHD on RESIDUE_CON_ESTIMATES_TRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: RESIDUE_CON_FUNDS                                     */
/*==============================================================*/
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
   LASTCHANGED          datetime             null
)
go

alter table RESIDUE_CON_FUNDS
   add constraint RESIDUE_CON_FUNDS_PK primary key (CONTRACTID, INTERCONNECTORID, FROMREGIONID)
go

/*==============================================================*/
/* Index: RESIDUE_CON_FUNDS_LCX                                 */
/*==============================================================*/
create index RESIDUE_CON_FUNDS_LCX on RESIDUE_CON_FUNDS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: RESIDUE_FUNDS_BID                                     */
/*==============================================================*/
create table RESIDUE_FUNDS_BID (
   CONTRACTID           varchar(30)          not null,
   PARTICIPANTID        varchar(10)          not null,
   LOADDATE             datetime             not null,
   OPTIONID             numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   UNITS                numeric(5,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table RESIDUE_FUNDS_BID
   add constraint RESIDUE_FUNDS_BID_PK primary key (CONTRACTID, PARTICIPANTID, LOADDATE, OPTIONID, INTERCONNECTORID, FROMREGIONID)
go

/*==============================================================*/
/* Index: RESIDUE_FUNDS_BID_LCX                                 */
/*==============================================================*/
create index RESIDUE_FUNDS_BID_LCX on RESIDUE_FUNDS_BID (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: RESIDUE_PRICE_BID                                     */
/*==============================================================*/
create table RESIDUE_PRICE_BID (
   CONTRACTID           varchar(30)          null,
   PARTICIPANTID        varchar(10)          not null,
   LOADDATE             datetime             not null,
   OPTIONID             numeric(3,0)         not null,
   BIDPRICE             numeric(17,5)        null,
   LASTCHANGED          datetime             null,
   AUCTIONID            varchar(30)          not null
)
go

alter table RESIDUE_PRICE_BID
   add constraint RESIDUE_PRICE_BID_PK primary key (AUCTIONID, PARTICIPANTID, LOADDATE, OPTIONID)
go

/*==============================================================*/
/* Index: RESIDUE_PRICE_BID_LCX                                 */
/*==============================================================*/
create index RESIDUE_PRICE_BID_LCX on RESIDUE_PRICE_BID (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: RESIDUE_PRICE_FUNDS_BID                               */
/*==============================================================*/
create table RESIDUE_PRICE_FUNDS_BID (
   CONTRACTID           varchar(30)          not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   UNITS                numeric(5,0)         null,
   BIDPRICE             numeric(17,5)        null,
   LINKEDBIDFLAG        numeric(6,0)         not null,
   AUCTIONID            varchar(30)          not null,
   LASTCHANGED          datetime             null
)
go

alter table RESIDUE_PRICE_FUNDS_BID
   add constraint RESIDUE_PRICE_FUNDS_BID_PK primary key (AUCTIONID, CONTRACTID, INTERCONNECTORID, FROMREGIONID, LINKEDBIDFLAG)
go

/*==============================================================*/
/* Index: RESIDUE_PRICE_FUNDS_BID_LCX                           */
/*==============================================================*/
create index RESIDUE_PRICE_FUNDS_BID_LCX on RESIDUE_PRICE_FUNDS_BID (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: RESIDUE_PUBLIC_DATA                                   */
/*==============================================================*/
create table RESIDUE_PUBLIC_DATA (
   CONTRACTID           varchar(30)          not null,
   VERSIONNO            numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   UNITSOFFERED         numeric(5,0)         null,
   UNITSSOLD            numeric(16,6)        null,
   CLEARINGPRICE        numeric(17,5)        null,
   RESERVEPRICE         numeric(17,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table RESIDUE_PUBLIC_DATA
   add constraint RESIDUE_PUBLIC_DATA_PK primary key (CONTRACTID, VERSIONNO, INTERCONNECTORID, FROMREGIONID)
go

/*==============================================================*/
/* Index: RESIDUE_PUBLIC_DATA_LCX                               */
/*==============================================================*/
create index RESIDUE_PUBLIC_DATA_LCX on RESIDUE_PUBLIC_DATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: RESIDUE_TRK                                           */
/*==============================================================*/
create table RESIDUE_TRK (
   CONTRACTID           varchar(30)          null,
   VERSIONNO            numeric(3,0)         not null,
   RUNDATE              datetime             null,
   AUTHORISEDDATE       datetime             null,
   AUTHORISEDBY         varchar(15)          null,
   POSTDATE             datetime             null,
   POSTEDBY             varchar(15)          null,
   LASTCHANGED          datetime             null,
   STATUS               varchar(15)          null,
   AUCTIONID            varchar(30)          not null
)
go

alter table RESIDUE_TRK
   add constraint RESIDUE_TRK_PK primary key (AUCTIONID, VERSIONNO)
go

/*==============================================================*/
/* Index: RESIDUETRK_NDX_LCHD                                   */
/*==============================================================*/
create index RESIDUETRK_NDX_LCHD on RESIDUE_TRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: ROOFTOP_PV_ACTUAL                                     */
/*==============================================================*/
create table ROOFTOP_PV_ACTUAL (
   INTERVAL_DATETIME    datetime             not null,
   TYPE                 varchar(20)          not null,
   REGIONID             varchar(20)          not null,
   POWER                numeric(12,3)        null,
   QI                   numeric(2,1)         null,
   LASTCHANGED          datetime             null
)
go

alter table ROOFTOP_PV_ACTUAL
   add constraint ROOFTOP_PV_ACTUAL_PK primary key (INTERVAL_DATETIME, TYPE, REGIONID)
go

/*==============================================================*/
/* Table: ROOFTOP_PV_FORECAST                                   */
/*==============================================================*/
create table ROOFTOP_PV_FORECAST (
   VERSION_DATETIME     datetime             not null,
   REGIONID             varchar(20)          not null,
   INTERVAL_DATETIME    datetime             not null,
   POWERMEAN            numeric(12,3)        null,
   POWERPOE50           numeric(12,3)        null,
   POWERPOELOW          numeric(12,3)        null,
   POWERPOEHIGH         numeric(12,3)        null,
   LASTCHANGED          datetime             null
)
go

alter table ROOFTOP_PV_FORECAST
   add constraint ROOFTOP_PV_FORECAST_PK primary key (VERSION_DATETIME, INTERVAL_DATETIME, REGIONID)
go

/*==============================================================*/
/* Table: SECDEPOSIT_INTEREST_RATE                              */
/*==============================================================*/
create table SECDEPOSIT_INTEREST_RATE (
   INTEREST_ACCT_ID     varchar(20)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSION_DATETIME     datetime             not null,
   INTEREST_RATE        numeric(18,8)        null
)
go

alter table SECDEPOSIT_INTEREST_RATE
   add constraint SECDEPOSIT_INTEREST_RATE_PK primary key (INTEREST_ACCT_ID, EFFECTIVEDATE, VERSION_DATETIME)
go

/*==============================================================*/
/* Table: SECDEPOSIT_PROVISION                                  */
/*==============================================================*/
create table SECDEPOSIT_PROVISION (
   SECURITY_DEPOSIT_ID  varchar(20)          not null,
   PARTICIPANTID        varchar(20)          not null,
   TRANSACTION_DATE     datetime             null,
   MATURITY_CONTRACTYEAR numeric(4,0)         null,
   MATURITY_WEEKNO      numeric(3,0)         null,
   AMOUNT               numeric(18,8)        null,
   INTEREST_RATE        numeric(18,8)        null,
   INTEREST_CALC_TYPE   varchar(20)          null,
   INTEREST_ACCT_ID     varchar(20)          null
)
go

alter table SECDEPOSIT_PROVISION
   add constraint SECDEPOSIT_PROVISION_PK primary key (SECURITY_DEPOSIT_ID, PARTICIPANTID)
go

/*==============================================================*/
/* Table: SETAGCPAYMENT                                         */
/*==============================================================*/
create table SETAGCPAYMENT (
   SETTLEMENTDATE       datetime             not null,
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
   OFFERDATE            datetime             null,
   OFFERVERSIONNO       numeric(3,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table SETAGCPAYMENT
   add constraint SETAGCPAYMENT_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, CONTRACTID, PERIODID)
go

/*==============================================================*/
/* Index: SETAGCPAYMENT_NDX2                                    */
/*==============================================================*/
create index SETAGCPAYMENT_NDX2 on SETAGCPAYMENT (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: SETAGCPAYMENT_LCX                                     */
/*==============================================================*/
create index SETAGCPAYMENT_LCX on SETAGCPAYMENT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETAGCRECOVERY                                        */
/*==============================================================*/
create table SETAGCRECOVERY (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONTRACTID           varchar(10)          null,
   PERIODID             numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   ENABLINGPAYMENT      numeric(15,5)        null,
   PARTICIPANTDEMAND    numeric(15,5)        null,
   REGIONDEMAND         numeric(15,5)        null,
   ENABLINGRECOVERY     numeric(15,5)        null,
   LASTCHANGED          datetime             null,
   ENABLINGRECOVERY_GEN numeric(15,5)        null,
   PARTICIPANTDEMAND_GEN numeric(15,5)        null,
   REGIONDEMAND_GEN     numeric(15,5)        null
)
go

alter table SETAGCRECOVERY
   add constraint SETAGCRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, PERIODID, REGIONID)
go

/*==============================================================*/
/* Index: SETAGCRECOVERY_LCX                                    */
/*==============================================================*/
create index SETAGCRECOVERY_LCX on SETAGCRECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETAPCCOMPENSATION                                    */
/*==============================================================*/
create table SETAPCCOMPENSATION (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   APCCOMPENSATION      numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table SETAPCCOMPENSATION
   add constraint SETAPCCOMPENSATION_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, REGIONID, PERIODID)
go

/*==============================================================*/
/* Index: SETAPCCOMPENSATION_LCX                                */
/*==============================================================*/
create index SETAPCCOMPENSATION_LCX on SETAPCCOMPENSATION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETAPCRECOVERY                                        */
/*==============================================================*/
create table SETAPCRECOVERY (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   TOTALCOMPENSATION    numeric(15,5)        null,
   PARTICIPANTDEMAND    numeric(15,5)        null,
   REGIONDEMAND         numeric(15,5)        null,
   APCRECOVERY          numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table SETAPCRECOVERY
   add constraint SETAPCRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, REGIONID, PERIODID)
go

/*==============================================================*/
/* Index: SETAPCRECOVERY_LCX                                    */
/*==============================================================*/
create index SETAPCRECOVERY_LCX on SETAPCRECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETCFG_PARTICIPANT_MPF                                */
/*==============================================================*/
create table SETCFG_PARTICIPANT_MPF (
   PARTICIPANTID        varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTCATEGORYID varchar(10)          not null,
   CONNECTIONPOINTID    varchar(10)          not null,
   MPF                  numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table SETCFG_PARTICIPANT_MPF
   add constraint SETCFG_PARTICIPANT_MPF_PK primary key (PARTICIPANTID, EFFECTIVEDATE, VERSIONNO, PARTICIPANTCATEGORYID, CONNECTIONPOINTID)
go

/*==============================================================*/
/* Index: SETCFG_PARTI_MPF_LCHD_IDX                             */
/*==============================================================*/
create index SETCFG_PARTI_MPF_LCHD_IDX on SETCFG_PARTICIPANT_MPF (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETCFG_PARTICIPANT_MPFTRK                             */
/*==============================================================*/
create table SETCFG_PARTICIPANT_MPFTRK (
   PARTICIPANTID        varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table SETCFG_PARTICIPANT_MPFTRK
   add constraint SETCFG_PARTICIPANT_MPFTRK_PK primary key (PARTICIPANTID, EFFECTIVEDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: SETCFG_PARTI_MPFTRK_LCHD_IDX                          */
/*==============================================================*/
create index SETCFG_PARTI_MPFTRK_LCHD_IDX on SETCFG_PARTICIPANT_MPFTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETCPDATA                                             */
/*==============================================================*/
create table SETCPDATA (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null,
   HOSTDISTRIBUTOR      varchar(10)          null,
   MDA                  varchar(10)          not null
)
go

alter table SETCPDATA
   add constraint SETCPDATA_PK primary key (SETTLEMENTDATE, VERSIONNO, PERIODID, PARTICIPANTID, TCPID, MDA)
go

/*==============================================================*/
/* Index: SETCPDATA_NDX2                                        */
/*==============================================================*/
create index SETCPDATA_NDX2 on SETCPDATA (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: SETCPDATA_LCX                                         */
/*==============================================================*/
create index SETCPDATA_LCX on SETCPDATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETCPDATAREGION                                       */
/*==============================================================*/
create table SETCPDATAREGION (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(22,10)       not null,
   PERIODID             numeric(22,10)       not null,
   REGIONID             varchar(10)          not null,
   SUMIGENERGY          numeric(27,5)        null,
   SUMXGENERGY          numeric(27,5)        null,
   SUMINENERGY          numeric(27,5)        null,
   SUMXNENERGY          numeric(27,5)        null,
   SUMIPOWER            numeric(22,0)        null,
   SUMXPOWER            numeric(22,0)        null,
   LASTCHANGED          datetime             null,
   SUMEP                numeric(15,5)        null
)
go

alter table SETCPDATAREGION
   add constraint SETCPDATAREGION_PK primary key (SETTLEMENTDATE, VERSIONNO, PERIODID, REGIONID)
go

/*==============================================================*/
/* Index: SETCPDATAREGION_LCX                                   */
/*==============================================================*/
create index SETCPDATAREGION_LCX on SETCPDATAREGION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETFCASCOMP                                           */
/*==============================================================*/
create table SETFCASCOMP (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table SETFCASCOMP
   add constraint SETFCASCOMP_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, DUID, PERIODID)
go

/*==============================================================*/
/* Index: SETFCASCOMP_LCX                                       */
/*==============================================================*/
create index SETFCASCOMP_LCX on SETFCASCOMP (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETFCASRECOVERY                                       */
/*==============================================================*/
create table SETFCASRECOVERY (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   DUID                 varchar(10)          null,
   PARTICIPANTID        varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   FCASCOMP             numeric(15,5)        null,
   PARTICIPANTDEMAND    numeric(15,5)        null,
   REGIONDEMAND         numeric(15,5)        null,
   FCASRECOVERY         numeric(15,5)        null,
   LASTCHANGED          datetime             null,
   FCASRECOVERY_GEN     numeric(15,5)        null,
   PARTICIPANTDEMAND_GEN numeric(15,5)        null,
   REGIONDEMAND_GEN     numeric(15,5)        null
)
go

alter table SETFCASRECOVERY
   add constraint SETFCASRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, REGIONID, PERIODID)
go

/*==============================================================*/
/* Index: SETFCASRECOVERY_LCX                                   */
/*==============================================================*/
create index SETFCASRECOVERY_LCX on SETFCASRECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETFCASREGIONRECOVERY                                 */
/*==============================================================*/
create table SETFCASREGIONRECOVERY (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   BIDTYPE              varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   GENERATORREGIONENERGY numeric(16,6)        null,
   CUSTOMERREGIONENERGY numeric(16,6)        null,
   REGIONRECOVERY       numeric(18,8)        null,
   LASTCHANGED          datetime             null
)
go

alter table SETFCASREGIONRECOVERY
   add constraint SETFCASREGIONRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, BIDTYPE, REGIONID, PERIODID)
go

/*==============================================================*/
/* Index: SETFCASREGIONRECOVERY_NDX_LCHD                        */
/*==============================================================*/
create index SETFCASREGIONRECOVERY_NDX_LCHD on SETFCASREGIONRECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETGENDATA                                            */
/*==============================================================*/
create table SETGENDATA (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null,
   EXPENERGY            numeric(15,6)        null,
   EXPENERGYCOST        numeric(15,6)        null,
   METERRUNNO           numeric(6,0)         null,
   MDA                  varchar(10)          null,
   SECONDARY_TLF        numeric(7,5)         null
)
go

alter table SETGENDATA
   add constraint SETGENDATA_PK primary key (SETTLEMENTDATE, VERSIONNO, REGIONID, STATIONID, DUID, GENSETID, PERIODID)
go

/*==============================================================*/
/* Index: SETGENDATA_NDX2                                       */
/*==============================================================*/
create index SETGENDATA_NDX2 on SETGENDATA (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: SETGENDATA_LCX                                        */
/*==============================================================*/
create index SETGENDATA_LCX on SETGENDATA (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETGENDATAREGION                                      */
/*==============================================================*/
create table SETGENDATAREGION (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table SETGENDATAREGION
   add constraint SETGENDATAREGION_PK primary key (SETTLEMENTDATE, VERSIONNO, PERIODID, REGIONID)
go

/*==============================================================*/
/* Index: SETGENDATAREGION_LCX                                  */
/*==============================================================*/
create index SETGENDATAREGION_LCX on SETGENDATAREGION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETGOVPAYMENT                                         */
/*==============================================================*/
create table SETGOVPAYMENT (
   SETTLEMENTDATE       datetime             not null,
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
   OFFERDATE            datetime             null,
   OFFERVERSIONNO       numeric(3,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table SETGOVPAYMENT
   add constraint SETGOVPAYMENT_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, CONTRACTID, PERIODID)
go

/*==============================================================*/
/* Index: SETGOVPAYMENT_NDX2                                    */
/*==============================================================*/
create index SETGOVPAYMENT_NDX2 on SETGOVPAYMENT (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: SETGOVPAYMENT_LCX                                     */
/*==============================================================*/
create index SETGOVPAYMENT_LCX on SETGOVPAYMENT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETGOVRECOVERY                                        */
/*==============================================================*/
create table SETGOVRECOVERY (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null,
   ENABLING6LRECOVERY_GEN numeric(15,5)        null,
   ENABLING6RRECOVERY_GEN numeric(15,5)        null,
   ENABLING60LRECOVERY_GEN numeric(15,5)        null,
   ENABLING60RRECOVERY_GEN numeric(15,5)        null,
   PARTICIPANTDEMAND_GEN numeric(15,5)        null,
   REGIONDEMAND_GEN     numeric(15,5)        null
)
go

alter table SETGOVRECOVERY
   add constraint SETGOVRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, PERIODID, REGIONID)
go

/*==============================================================*/
/* Index: SETGOVRECOVERY_LCX                                    */
/*==============================================================*/
create index SETGOVRECOVERY_LCX on SETGOVRECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETINTERVENTION                                       */
/*==============================================================*/
create table SETINTERVENTION (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   CONTRACTID           varchar(10)          null,
   CONTRACTVERSION      numeric(3,0)         null,
   PARTICIPANTID        varchar(10)          null,
   REGIONID             varchar(10)          null,
   DUID                 varchar(10)          not null,
   RCF                  char(1)              null,
   INTERVENTIONPAYMENT  numeric(12,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table SETINTERVENTION
   add constraint SETINTERVENTION_PK primary key (SETTLEMENTDATE, VERSIONNO, DUID, PERIODID)
go

/*==============================================================*/
/* Index: SETINTERVENTION_LCX                                   */
/*==============================================================*/
create index SETINTERVENTION_LCX on SETINTERVENTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETINTERVENTIONRECOVERY                               */
/*==============================================================*/
create table SETINTERVENTIONRECOVERY (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   CONTRACTID           varchar(10)          not null,
   RCF                  char(1)              null,
   PARTICIPANTID        varchar(10)          not null,
   PARTICIPANTDEMAND    numeric(12,5)        null,
   TOTALDEMAND          numeric(12,5)        null,
   INTERVENTIONPAYMENT  numeric(12,5)        null,
   INTERVENTIONAMOUNT   numeric(12,5)        null,
   LASTCHANGED          datetime             null,
   REGIONID             varchar(10)          null
)
go

alter table SETINTERVENTIONRECOVERY
   add constraint SETINTERVENTIONRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, CONTRACTID, PARTICIPANTID, PERIODID)
go

/*==============================================================*/
/* Index: SETINTERVENTIONRECOVERY_LCX                           */
/*==============================================================*/
create index SETINTERVENTIONRECOVERY_LCX on SETINTERVENTIONRECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETINTRAREGIONRESIDUES                                */
/*==============================================================*/
create table SETINTRAREGIONRESIDUES (
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3)           not null,
   PERIODID             numeric(3)           not null,
   REGIONID             varchar(10)          not null,
   EP                   numeric(15,5)        null,
   EC                   numeric(15,5)        null,
   RRP                  numeric(15,5)        null,
   EXP                  numeric(15,5)        null,
   IRSS                 numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table SETINTRAREGIONRESIDUES
   add constraint PK_SETINTRAREGIONRESIDUES primary key (SETTLEMENTDATE, RUNNO, PERIODID, REGIONID)
go

/*==============================================================*/
/* Index: SETINTRAREGIONRESIDUES_LCX                            */
/*==============================================================*/
create index SETINTRAREGIONRESIDUES_LCX on SETINTRAREGIONRESIDUES (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETIRAUCSURPLUS                                       */
/*==============================================================*/
create table SETIRAUCSURPLUS (
   SETTLEMENTDATE       datetime             not null,
   SETTLEMENTRUNNO      numeric(3,0)         not null,
   CONTRACTID           varchar(10)          not null,
   PERIODID             numeric(2,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   TOTALSURPLUS         numeric(15,5)        null,
   CONTRACTALLOCATION   numeric(8,5)         null,
   SURPLUSVALUE         numeric(15,5)        null,
   LASTCHANGED          datetime             null,
   CSP_DEROGATION_AMOUNT numeric(18,8)        null,
   UNADJUSTED_IRSR      numeric(18,8)        null
)
go

alter table SETIRAUCSURPLUS
   add constraint SETIRAUCSURPLUS_PK primary key (SETTLEMENTDATE, SETTLEMENTRUNNO, CONTRACTID, INTERCONNECTORID, FROMREGIONID, PARTICIPANTID, PERIODID)
go

/*==============================================================*/
/* Index: SETIRAUCSURPLUS_LCX                                   */
/*==============================================================*/
create index SETIRAUCSURPLUS_LCX on SETIRAUCSURPLUS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETIRFMRECOVERY                                       */
/*==============================================================*/
create table SETIRFMRECOVERY (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table SETIRFMRECOVERY
   add constraint SETIRFMRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, IRFMID, PARTICIPANTID, PERIODID)
go

/*==============================================================*/
/* Index: SETIRFMRECOVERY_LCX                                   */
/*==============================================================*/
create index SETIRFMRECOVERY_LCX on SETIRFMRECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETIRNSPSURPLUS                                       */
/*==============================================================*/
create table SETIRNSPSURPLUS (
   SETTLEMENTDATE       datetime             not null,
   SETTLEMENTRUNNO      numeric(3,0)         not null,
   CONTRACTID           varchar(10)          not null,
   PERIODID             numeric(2,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   TOTALSURPLUS         numeric(15,5)        null,
   CONTRACTALLOCATION   numeric(8,5)         null,
   SURPLUSVALUE         numeric(15,5)        null,
   LASTCHANGED          datetime             null,
   CSP_DEROGATION_AMOUNT numeric(18,8)        null,
   UNADJUSTED_IRSR      numeric(18,8)        null
)
go

alter table SETIRNSPSURPLUS
   add constraint SETIRNSPSURPLUS_PK primary key (SETTLEMENTDATE, SETTLEMENTRUNNO, CONTRACTID, INTERCONNECTORID, FROMREGIONID, PARTICIPANTID, PERIODID)
go

/*==============================================================*/
/* Index: SETIRNSPSURPLUS_LCX                                   */
/*==============================================================*/
create index SETIRNSPSURPLUS_LCX on SETIRNSPSURPLUS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETIRPARTSURPLUS                                      */
/*==============================================================*/
create table SETIRPARTSURPLUS (
   SETTLEMENTDATE       datetime             not null,
   SETTLEMENTRUNNO      numeric(3,0)         not null,
   CONTRACTID           varchar(10)          not null,
   PERIODID             numeric(2,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   TOTALSURPLUS         numeric(15,5)        null,
   CONTRACTALLOCATION   numeric(8,5)         null,
   SURPLUSVALUE         numeric(15,5)        null,
   LASTCHANGED          datetime             null,
   CSP_DEROGATION_AMOUNT numeric(18,8)        null,
   UNADJUSTED_IRSR      numeric(18,8)        null
)
go

alter table SETIRPARTSURPLUS
   add constraint SETIRPARTSURPLUS_PK primary key (SETTLEMENTDATE, SETTLEMENTRUNNO, CONTRACTID, INTERCONNECTORID, FROMREGIONID, PARTICIPANTID, PERIODID)
go

/*==============================================================*/
/* Index: SETIRPARTSURPLUS_LCX                                  */
/*==============================================================*/
create index SETIRPARTSURPLUS_LCX on SETIRPARTSURPLUS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETIRSURPLUS                                          */
/*==============================================================*/
create table SETIRSURPLUS (
   SETTLEMENTDATE       datetime             not null,
   SETTLEMENTRUNNO      numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   REGIONID             varchar(10)          not null,
   MWFLOW               numeric(15,6)        null,
   LOSSFACTOR           numeric(15,5)        null,
   SURPLUSVALUE         numeric(15,5)        null,
   LASTCHANGED          datetime             null,
   CSP_DEROGATION_AMOUNT numeric(18,8)        null,
   UNADJUSTED_IRSR      numeric(18,8)        null
)
go

alter table SETIRSURPLUS
   add constraint SETIRSURPLUS_PK primary key (SETTLEMENTDATE, SETTLEMENTRUNNO, PERIODID, INTERCONNECTORID, REGIONID)
go

/*==============================================================*/
/* Index: SETIRSURPLUS_LCX                                      */
/*==============================================================*/
create index SETIRSURPLUS_LCX on SETIRSURPLUS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETLSHEDPAYMENT                                       */
/*==============================================================*/
create table SETLSHEDPAYMENT (
   SETTLEMENTDATE       datetime             not null,
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
   OFFERDATE            datetime             null,
   OFFERVERSIONNO       numeric(3,0)         null,
   LASTCHANGED          datetime             null,
   AVAILABILITYPAYMENT  numeric(16,6)        null
)
go

alter table SETLSHEDPAYMENT
   add constraint SETLSHEDPAYMENT_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, CONTRACTID, PERIODID)
go

/*==============================================================*/
/* Index: SETLSHEDPAYMENT_NDX2                                  */
/*==============================================================*/
create index SETLSHEDPAYMENT_NDX2 on SETLSHEDPAYMENT (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: SETLSHEDPAYMENT_LCX                                   */
/*==============================================================*/
create index SETLSHEDPAYMENT_LCX on SETLSHEDPAYMENT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETLSHEDRECOVERY                                      */
/*==============================================================*/
create table SETLSHEDRECOVERY (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null,
   LSERECOVERY_GEN      numeric(15,5)        null,
   CCRECOVERY_GEN       numeric(15,5)        null,
   PARTICIPANTDEMAND_GEN numeric(15,5)        null,
   REGIONDEMAND_GEN     numeric(15,5)        null,
   AVAILABILITYRECOVERY numeric(16,6)        null,
   AVAILABILITYRECOVERY_GEN numeric(16,6)        null
)
go

alter table SETLSHEDRECOVERY
   add constraint SETLSHEDRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, PERIODID, REGIONID)
go

/*==============================================================*/
/* Index: SETLSHEDRECOVERY_LCX                                  */
/*==============================================================*/
create index SETLSHEDRECOVERY_LCX on SETLSHEDRECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETLULOADPAYMENT                                      */
/*==============================================================*/
create table SETLULOADPAYMENT (
   SETTLEMENTDATE       datetime             not null,
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
   OFFERDATE            datetime             null,
   OFFERVERSIONNO       numeric(3,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table SETLULOADPAYMENT
   add constraint SETLULOADPAYMENT_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, CONTRACTID, PERIODID)
go

/*==============================================================*/
/* Index: SETLULOADPAYMENT_NDX2                                 */
/*==============================================================*/
create index SETLULOADPAYMENT_NDX2 on SETLULOADPAYMENT (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: SETLULOADPAYMENT_LCX                                  */
/*==============================================================*/
create index SETLULOADPAYMENT_LCX on SETLULOADPAYMENT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETLULOADRECOVERY                                     */
/*==============================================================*/
create table SETLULOADRECOVERY (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null,
   ENABLINGRECOVERY_GEN numeric(15,5)        null,
   USAGERECOVERY_GEN    numeric(15,5)        null,
   COMPENSATIONRECOVERY_GEN numeric(15,5)        null,
   PARTICIPANTDEMAND_GEN numeric(15,5)        null,
   REGIONDEMAND_GEN     numeric(15,5)        null
)
go

alter table SETLULOADRECOVERY
   add constraint SETLULOADRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, PERIODID, REGIONID)
go

/*==============================================================*/
/* Index: SETLULOADRECOVERY_LCX                                 */
/*==============================================================*/
create index SETLULOADRECOVERY_LCX on SETLULOADRECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETLUNLOADPAYMENT                                     */
/*==============================================================*/
create table SETLUNLOADPAYMENT (
   SETTLEMENTDATE       datetime             not null,
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
   OFFERDATE            datetime             null,
   OFFERVERSIONNO       numeric(3,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table SETLUNLOADPAYMENT
   add constraint SETLUNLOADPAYMENT_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, CONTRACTID, PERIODID)
go

/*==============================================================*/
/* Index: SETLUNLOADPAYMENT_NDX2                                */
/*==============================================================*/
create index SETLUNLOADPAYMENT_NDX2 on SETLUNLOADPAYMENT (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: SETLUNLOADPAYMENT_LCX                                 */
/*==============================================================*/
create index SETLUNLOADPAYMENT_LCX on SETLUNLOADPAYMENT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETLUNLOADRECOVERY                                    */
/*==============================================================*/
create table SETLUNLOADRECOVERY (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null,
   ENABLINGRECOVERY_GEN numeric(15,5)        null,
   USAGERECOVERY_GEN    numeric(15,5)        null,
   COMPENSATIONRECOVERY_GEN numeric(15,5)        null,
   PARTICIPANTDEMAND_GEN numeric(15,5)        null,
   REGIONDEMAND_GEN     numeric(15,5)        null
)
go

alter table SETLUNLOADRECOVERY
   add constraint SETLUNLOADRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, PERIODID, REGIONID)
go

/*==============================================================*/
/* Index: SETLUNLOADRECOVERY_LCX                                */
/*==============================================================*/
create index SETLUNLOADRECOVERY_LCX on SETLUNLOADRECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETMARKETFEES                                         */
/*==============================================================*/
create table SETMARKETFEES (
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   MARKETFEEID          varchar(10)          not null,
   MARKETFEEVALUE       numeric(15,5)        null,
   ENERGY               numeric(16,6)        null,
   LASTCHANGED          datetime             null,
   PARTICIPANTCATEGORYID varchar(10)          not null
)
go

alter table SETMARKETFEES
   add constraint SETMARKETFEES_PK primary key (SETTLEMENTDATE, RUNNO, PARTICIPANTID, MARKETFEEID, PARTICIPANTCATEGORYID, PERIODID)
go

/*==============================================================*/
/* Index: SETMARKETFEES_LCX                                     */
/*==============================================================*/
create index SETMARKETFEES_LCX on SETMARKETFEES (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETREALLOCATIONS                                      */
/*==============================================================*/
create table SETREALLOCATIONS (
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   REALLOCATIONID       varchar(20)          not null,
   REALLOCATIONVALUE    numeric(15,5)        null,
   ENERGY               numeric(15,5)        null,
   RRP                  numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table SETREALLOCATIONS
   add constraint SETREALLOCATIONS_PK primary key (SETTLEMENTDATE, RUNNO, PERIODID, PARTICIPANTID, REALLOCATIONID)
go

/*==============================================================*/
/* Index: SETREALLOCATIONS_LCX                                  */
/*==============================================================*/
create index SETREALLOCATIONS_LCX on SETREALLOCATIONS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETRESERVERECOVERY                                    */
/*==============================================================*/
create table SETRESERVERECOVERY (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null,
   REGIONID             varchar(10)          null
)
go

alter table SETRESERVERECOVERY
   add constraint SETRESERVERECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, CONTRACTID, PARTICIPANTID, PERIODID)
go

/*==============================================================*/
/* Index: SETRESERVERECOVERY_LCX                                */
/*==============================================================*/
create index SETRESERVERECOVERY_LCX on SETRESERVERECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETRESERVETRADER                                      */
/*==============================================================*/
create table SETRESERVETRADER (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table SETRESERVETRADER
   add constraint SETRESERVETRADER_PK primary key (SETTLEMENTDATE, VERSIONNO, DUID, PERIODID)
go

/*==============================================================*/
/* Index: SETRESERVETRADER_LCX                                  */
/*==============================================================*/
create index SETRESERVETRADER_LCX on SETRESERVETRADER (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETRESTARTPAYMENT                                     */
/*==============================================================*/
create table SETRESTARTPAYMENT (
   SETTLEMENTDATE       datetime             not null,
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
   OFFERDATE            datetime             null,
   OFFERVERSIONNO       numeric(3,0)         null,
   LASTCHANGED          datetime             null,
   ENABLINGPAYMENT      numeric(18,8)        null
)
go

alter table SETRESTARTPAYMENT
   add constraint SETRESTARTPAYMENT_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, CONTRACTID, PERIODID)
go

/*==============================================================*/
/* Index: SETRESTARTPAYMENT_NDX2                                */
/*==============================================================*/
create index SETRESTARTPAYMENT_NDX2 on SETRESTARTPAYMENT (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Index: SETRESTARTPAYMENT_LCX                                 */
/*==============================================================*/
create index SETRESTARTPAYMENT_LCX on SETRESTARTPAYMENT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETRESTARTRECOVERY                                    */
/*==============================================================*/
create table SETRESTARTRECOVERY (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   CONTRACTID           varchar(10)          null,
   PERIODID             numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   AVAILABILITYPAYMENT  numeric(15,5)        null,
   PARTICIPANTDEMAND    numeric(15,5)        null,
   REGIONDEMAND         numeric(15,5)        null,
   AVAILABILITYRECOVERY numeric(15,5)        null,
   LASTCHANGED          datetime             null,
   AVAILABILITYRECOVERY_GEN numeric(15,5)        null,
   PARTICIPANTDEMAND_GEN numeric(15,5)        null,
   REGIONDEMAND_GEN     numeric(15,5)        null,
   ENABLINGPAYMENT      numeric(18,8)        null,
   ENABLINGRECOVERY     numeric(18,8)        null,
   ENABLINGRECOVERY_GEN numeric(18,8)        null
)
go

alter table SETRESTARTRECOVERY
   add constraint SETRESTARTRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, PERIODID, REGIONID)
go

/*==============================================================*/
/* Index: SETRESTARTRECOVERY_LCX                                */
/*==============================================================*/
create index SETRESTARTRECOVERY_LCX on SETRESTARTRECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETRPOWERPAYMENT                                      */
/*==============================================================*/
create table SETRPOWERPAYMENT (
   SETTLEMENTDATE       datetime             not null,
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
   OFFERDATE            datetime             null,
   OFFERVERSIONNO       numeric(3,0)         null,
   LASTCHANGED          datetime             null,
   AVAILABILITYPAYMENT_REBATE numeric(18,8)        null
)
go

alter table SETRPOWERPAYMENT
   add constraint SETRPOWERPAYMENT_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, CONTRACTID, PERIODID)
go

/*==============================================================*/
/* Index: SETRPOWERPAYMENT_LCX                                  */
/*==============================================================*/
create index SETRPOWERPAYMENT_LCX on SETRPOWERPAYMENT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETRPOWERRECOVERY                                     */
/*==============================================================*/
create table SETRPOWERRECOVERY (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null,
   AVAILABILITYRECOVERY_GEN numeric(15,5)        null,
   ENABLINGRECOVERY_GEN numeric(15,5)        null,
   CCRECOVERY_GEN       numeric(15,5)        null,
   PARTICIPANTDEMAND_GEN numeric(15,5)        null,
   REGIONDEMAND_GEN     numeric(15,5)        null
)
go

alter table SETRPOWERRECOVERY
   add constraint SETRPOWERRECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, PERIODID, REGIONID)
go

/*==============================================================*/
/* Index: SETRPOWERRECOVERY_LCX                                 */
/*==============================================================*/
create index SETRPOWERRECOVERY_LCX on SETRPOWERRECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETSMALLGENDATA                                       */
/*==============================================================*/
create table SETSMALLGENDATA (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table SETSMALLGENDATA
   add constraint PK_SETSMALLGENDATA primary key (SETTLEMENTDATE, VERSIONNO, CONNECTIONPOINTID, PERIODID, PARTICIPANTID)
go

/*==============================================================*/
/* Table: SETVICBOUNDARYENERGY                                  */
/*==============================================================*/
create table SETVICBOUNDARYENERGY (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PARTICIPANTID        varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   BOUNDARYENERGY       numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table SETVICBOUNDARYENERGY
   add constraint SETVICBOUNDARYENERGY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, PERIODID)
go

/*==============================================================*/
/* Index: SETVICBOUNDARYENERGY_LCX                              */
/*==============================================================*/
create index SETVICBOUNDARYENERGY_LCX on SETVICBOUNDARYENERGY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETVICENERGYFIGURES                                   */
/*==============================================================*/
create table SETVICENERGYFIGURES (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   TOTALGENOUTPUT       numeric(15,5)        null,
   TOTALPCSD            numeric(15,5)        null,
   LASTCHANGED          datetime             null,
   TLR                  numeric(15,6)        null,
   MLF                  numeric(15,6)        null
)
go

alter table SETVICENERGYFIGURES
   add constraint SETVICENERGYFIGURES_PK primary key (SETTLEMENTDATE, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: SETVICENERGYFIGURES_LCX                               */
/*==============================================================*/
create index SETVICENERGYFIGURES_LCX on SETVICENERGYFIGURES (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SETVICENERGYFLOW                                      */
/*==============================================================*/
create table SETVICENERGYFLOW (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   NETFLOW              numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table SETVICENERGYFLOW
   add constraint SETVICENERGYFLOW_PK primary key (SETTLEMENTDATE, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: SETVICENERGYFLOW_LCX                                  */
/*==============================================================*/
create index SETVICENERGYFLOW_LCX on SETVICENERGYFLOW (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SET_ANCILLARY_SUMMARY                                 */
/*==============================================================*/
create table SET_ANCILLARY_SUMMARY (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   SERVICE              varchar(20)          not null,
   PAYMENTTYPE          varchar(20)          not null,
   REGIONID             varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   PAYMENTAMOUNT        numeric(18,8)        null,
   LASTCHANGED          datetime             null
)
go

alter table SET_ANCILLARY_SUMMARY
   add constraint SET_ANCILLARY_SUMMARY_PK primary key (SETTLEMENTDATE, VERSIONNO, SERVICE, PAYMENTTYPE, REGIONID, PERIODID)
go

/*==============================================================*/
/* Index: SET_ANCILLARY_SUMMARY_LCHD_IDX                        */
/*==============================================================*/
create index SET_ANCILLARY_SUMMARY_LCHD_IDX on SET_ANCILLARY_SUMMARY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SET_APC_COMPENSATION                                  */
/*==============================================================*/
create table SET_APC_COMPENSATION (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3)           not null,
   APEVENTID            numeric(6)           not null,
   CLAIMID              numeric(6)           not null,
   PARTICIPANTID        varchar(20)          not null,
   PERIODID             numeric(3)           not null,
   COMPENSATION_AMOUNT  numeric(18,8)        null
)
go

alter table SET_APC_COMPENSATION
   add constraint SET_APC_COMPENSATION_PK primary key (SETTLEMENTDATE, VERSIONNO, APEVENTID, CLAIMID, PARTICIPANTID, PERIODID)
go

/*==============================================================*/
/* Table: SET_APC_RECOVERY                                      */
/*==============================================================*/
create table SET_APC_RECOVERY (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3)           not null,
   APEVENTID            numeric(6)           not null,
   CLAIMID              numeric(6)           not null,
   PARTICIPANTID        varchar(20)          not null,
   PERIODID             numeric(3)           not null,
   REGIONID             varchar(20)          not null,
   RECOVERY_AMOUNT      numeric(18,8)        null,
   REGION_RECOVERY_AMOUNT numeric(18,8)        null
)
go

alter table SET_APC_RECOVERY
   add constraint SET_APC_RECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, APEVENTID, CLAIMID, PARTICIPANTID, PERIODID, REGIONID)
go

/*==============================================================*/
/* Table: SET_CSP_DEROGATION_AMOUNT                             */
/*==============================================================*/
create table SET_CSP_DEROGATION_AMOUNT (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3)           not null,
   PERIODID             numeric(3)           not null,
   PARTICIPANTID        varchar(10)          not null,
   AMOUNT_ID            varchar(20)          not null,
   DEROGATION_AMOUNT    numeric(18,8)        null,
   LASTCHANGED          datetime             null
)
go

alter table SET_CSP_DEROGATION_AMOUNT
   add constraint SET_CSP_DEROGATION_AMOUNT_PK primary key (SETTLEMENTDATE, VERSIONNO, PERIODID, PARTICIPANTID, AMOUNT_ID)
go

/*==============================================================*/
/* Index: SET_CSP_DEROGATION_AMOUNT_NDX1                        */
/*==============================================================*/
create index SET_CSP_DEROGATION_AMOUNT_NDX1 on SET_CSP_DEROGATION_AMOUNT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SET_CSP_SUPPORTDATA_CONSTRAINT                        */
/*==============================================================*/
create table SET_CSP_SUPPORTDATA_CONSTRAINT (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3)           not null,
   INTERVAL_DATETIME    datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table SET_CSP_SUPPORTDATA_CONSTRAINT
   add constraint SET_CSP_SUPPORTDATA_CNSTR_PK primary key (SETTLEMENTDATE, VERSIONNO, INTERVAL_DATETIME, CONSTRAINTID, PERIODID)
go

/*==============================================================*/
/* Index: SET_CSP_SUPPORTDATA_CNSTR_NDX1                        */
/*==============================================================*/
create index SET_CSP_SUPPORTDATA_CNSTR_NDX1 on SET_CSP_SUPPORTDATA_CONSTRAINT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SET_CSP_SUPPORTDATA_ENERGYDIFF                        */
/*==============================================================*/
create table SET_CSP_SUPPORTDATA_ENERGYDIFF (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table SET_CSP_SUPPORTDATA_ENERGYDIFF
   add constraint SET_CSP_SUPPDATA_ENERGYDF_PK primary key (SETTLEMENTDATE, VERSIONNO, PERIODID)
go

/*==============================================================*/
/* Index: SET_CSP_SUPPDATA_ENERGYDF_NDX1                        */
/*==============================================================*/
create index SET_CSP_SUPPDATA_ENERGYDF_NDX1 on SET_CSP_SUPPORTDATA_ENERGYDIFF (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SET_CSP_SUPPORTDATA_SUBPRICE                          */
/*==============================================================*/
create table SET_CSP_SUPPORTDATA_SUBPRICE (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3)           not null,
   INTERVAL_DATETIME    datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table SET_CSP_SUPPORTDATA_SUBPRICE
   add constraint SET_CSP_SUPPDATA_SUBPRCE_PK primary key (SETTLEMENTDATE, VERSIONNO, INTERVAL_DATETIME)
go

/*==============================================================*/
/* Index: SET_CSP_SUPPDATA_SUBPRCE_NDX1                         */
/*==============================================================*/
create index SET_CSP_SUPPDATA_SUBPRCE_NDX1 on SET_CSP_SUPPORTDATA_SUBPRICE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SET_FCAS_PAYMENT                                      */
/*==============================================================*/
create table SET_FCAS_PAYMENT (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null
)
go

alter table SET_FCAS_PAYMENT
   add constraint SET_FCAS_PAYMENT_PK primary key (SETTLEMENTDATE, VERSIONNO, DUID, PERIODID)
go

/*==============================================================*/
/* Index: SET_FCAS_PAYMENT_LCHD_IDX                             */
/*==============================================================*/
create index SET_FCAS_PAYMENT_LCHD_IDX on SET_FCAS_PAYMENT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SET_FCAS_RECOVERY                                     */
/*==============================================================*/
create table SET_FCAS_RECOVERY (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null,
   LOWER6SEC_RECOVERY_GEN numeric(18,8)        null,
   RAISE6SEC_RECOVERY_GEN numeric(18,8)        null,
   LOWER60SEC_RECOVERY_GEN numeric(18,8)        null,
   RAISE60SEC_RECOVERY_GEN numeric(18,8)        null,
   LOWER5MIN_RECOVERY_GEN numeric(18,8)        null,
   RAISE5MIN_RECOVERY_GEN numeric(18,8)        null,
   LOWERREG_RECOVERY_GEN numeric(18,8)        null,
   RAISEREG_RECOVERY_GEN numeric(18,8)        null
)
go

alter table SET_FCAS_RECOVERY
   add constraint SET_FCAS_RECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, PARTICIPANTID, REGIONID, PERIODID)
go

/*==============================================================*/
/* Index: SET_FCAS_RECOVERY_LCHD_IDX                            */
/*==============================================================*/
create index SET_FCAS_RECOVERY_LCHD_IDX on SET_FCAS_RECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SET_FCAS_REGULATION_TRK                               */
/*==============================================================*/
create table SET_FCAS_REGULATION_TRK (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   INTERVAL_DATETIME    datetime             not null,
   CONSTRAINTID         varchar(20)          not null,
   CMPF                 numeric(18,8)        null,
   CRMPF                numeric(18,8)        null,
   RECOVERY_FACTOR_CMPF numeric(18,8)        null,
   RECOVERY_FACTOR_CRMPF numeric(18,8)        null,
   LASTCHANGED          datetime             null
)
go

alter table SET_FCAS_REGULATION_TRK
   add constraint SET_FCAS_REGULATION_TRK_PK primary key (SETTLEMENTDATE, VERSIONNO, INTERVAL_DATETIME, CONSTRAINTID)
go

/*==============================================================*/
/* Index: SET_FCAS_REGUL_TRK_LCHD_IDX                           */
/*==============================================================*/
create index SET_FCAS_REGUL_TRK_LCHD_IDX on SET_FCAS_REGULATION_TRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SET_MR_PAYMENT                                        */
/*==============================================================*/
create table SET_MR_PAYMENT (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   MR_CAPACITY          numeric(16,6)        null,
   UNCAPPED_PAYMENT     numeric(16,6)        null,
   CAPPED_PAYMENT       numeric(16,6)        null,
   LASTCHANGED          datetime             null
)
go

alter table SET_MR_PAYMENT
   add constraint SET_MR_PAYMENT_PK primary key (SETTLEMENTDATE, VERSIONNO, REGIONID, DUID, PERIODID)
go

/*==============================================================*/
/* Index: SET_MR_PAYMENT_LCX                                    */
/*==============================================================*/
create index SET_MR_PAYMENT_LCX on SET_MR_PAYMENT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SET_MR_RECOVERY                                       */
/*==============================================================*/
create table SET_MR_RECOVERY (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   PARTICIPANTID        varchar(10)          null,
   DUID                 varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   ARODEF               numeric(16,6)        null,
   NTA                  numeric(16,6)        null,
   LASTCHANGED          datetime             null
)
go

alter table SET_MR_RECOVERY
   add constraint SET_MR_RECOVERY_PK primary key (SETTLEMENTDATE, VERSIONNO, REGIONID, DUID, PERIODID)
go

/*==============================================================*/
/* Index: SET_MR_RECOVERY_LCX                                   */
/*==============================================================*/
create index SET_MR_RECOVERY_LCX on SET_MR_RECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SET_NMAS_RECOVERY                                     */
/*==============================================================*/
create table SET_NMAS_RECOVERY (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null,
   PARTICIPANT_GENERATION numeric(18,8)        null,
   REGION_GENERATION    numeric(18,8)        null,
   RECOVERY_AMOUNT_CUSTOMER numeric(18,8)        null,
   RECOVERY_AMOUNT_GENERATOR numeric(18,8)        null
)
go

alter table SET_NMAS_RECOVERY
   add constraint PK_SET_NMAS_RECOVERY primary key (SETTLEMENTDATE, VERSIONNO, PERIODID, PARTICIPANTID, SERVICE, CONTRACTID, PAYMENTTYPE, REGIONID)
go

/*==============================================================*/
/* Index: SET_NMAS_RECOVERY_LCX                                 */
/*==============================================================*/
create index SET_NMAS_RECOVERY_LCX on SET_NMAS_RECOVERY (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SET_NMAS_RECOVERY_RBF                                 */
/*==============================================================*/
create table SET_NMAS_RECOVERY_RBF (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   PERIODID             numeric(3,0)         not null,
   SERVICE              varchar(10)          not null,
   CONTRACTID           varchar(10)          not null,
   PAYMENTTYPE          varchar(20)          not null,
   REGIONID             varchar(10)          not null,
   RBF                  numeric(18,8)        null,
   PAYMENT_AMOUNT       numeric(18,8)        null,
   RECOVERY_AMOUNT      numeric(18,8)        null,
   LASTCHANGED          datetime             null
)
go

alter table SET_NMAS_RECOVERY_RBF
   add constraint PK_SET_NMAS_RECOVERY_RBF primary key (SETTLEMENTDATE, VERSIONNO, PERIODID, SERVICE, CONTRACTID, PAYMENTTYPE, REGIONID)
go

/*==============================================================*/
/* Index: SET_NMAS_RECOVERY_RBF_LCX                             */
/*==============================================================*/
create index SET_NMAS_RECOVERY_RBF_LCX on SET_NMAS_RECOVERY_RBF (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SET_RUN_PARAMETER                                     */
/*==============================================================*/
create table SET_RUN_PARAMETER (
   SETTLEMENTDATE       datetime             not null,
   VERSIONNO            numeric(3)           not null,
   PARAMETERID          varchar(20)          not null,
   NUMVALUE             numeric(18,8)        null,
   LASTCHANGED          datetime             null
)
go

alter table SET_RUN_PARAMETER
   add constraint PK_SET_RUN_PARAMETER primary key (SETTLEMENTDATE, VERSIONNO, PARAMETERID)
go

/*==============================================================*/
/* Index: SET_RUN_PARAMETER_LCX                                 */
/*==============================================================*/
create index SET_RUN_PARAMETER_LCX on SET_RUN_PARAMETER (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SPDCONNECTIONPOINTCONSTRAINT                          */
/*==============================================================*/
create table SPDCONNECTIONPOINTCONSTRAINT (
   CONNECTIONPOINTID    varchar(12)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   GENCONID             varchar(20)          not null,
   FACTOR               numeric(16,6)        null,
   LASTCHANGED          datetime             null,
   BIDTYPE              varchar(12)          not null
)
go

alter table SPDCONNECTIONPOINTCONSTRAINT
   add constraint SPDCONNECTIONPTCONSTRAINT_PK primary key (GENCONID, EFFECTIVEDATE, VERSIONNO, BIDTYPE, CONNECTIONPOINTID)
go

/*==============================================================*/
/* Index: SPDCONNECTIONPOINTCONSTRA_LCX                         */
/*==============================================================*/
create index SPDCONNECTIONPOINTCONSTRA_LCX on SPDCONNECTIONPOINTCONSTRAINT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SPDINTERCONNECTORCONSTRAINT                           */
/*==============================================================*/
create table SPDINTERCONNECTORCONSTRAINT (
   INTERCONNECTORID     varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   GENCONID             varchar(20)          not null,
   FACTOR               numeric(16,6)        null,
   LASTCHANGED          datetime             null
)
go

alter table SPDINTERCONNECTORCONSTRAINT
   add constraint SPDINTERCONNECTORCONSTRAINT_PK primary key (GENCONID, EFFECTIVEDATE, VERSIONNO, INTERCONNECTORID)
go

/*==============================================================*/
/* Index: SPDINTERCONNECTORCONSTRAI_LCX                         */
/*==============================================================*/
create index SPDINTERCONNECTORCONSTRAI_LCX on SPDINTERCONNECTORCONSTRAINT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SPDREGIONCONSTRAINT                                   */
/*==============================================================*/
create table SPDREGIONCONSTRAINT (
   REGIONID             varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(3,0)         not null,
   GENCONID             varchar(20)          not null,
   FACTOR               numeric(16,6)        null,
   LASTCHANGED          datetime             null,
   BIDTYPE              varchar(10)          not null
)
go

alter table SPDREGIONCONSTRAINT
   add constraint SPDREGIONCONSTRAINT_PK primary key (GENCONID, EFFECTIVEDATE, VERSIONNO, REGIONID, BIDTYPE)
go

/*==============================================================*/
/* Index: SPDREGIONCONSTRAINT_LCX                               */
/*==============================================================*/
create index SPDREGIONCONSTRAINT_LCX on SPDREGIONCONSTRAINT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: SRA_CASH_SECURITY                                     */
/*==============================================================*/
create table SRA_CASH_SECURITY (
   CASH_SECURITY_ID     varchar(36)          not null,
   PARTICIPANTID        varchar(10)          null,
   PROVISION_DATE       datetime             null,
   CASH_AMOUNT          numeric(18,8)        null,
   INTEREST_ACCT_ID     varchar(20)          null,
   AUTHORISEDDATE       datetime             null,
   FINALRETURNDATE      datetime             null,
   CASH_SECURITY_RETURNED numeric(18,8)        null,
   DELETIONDATE         datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table SRA_CASH_SECURITY
   add constraint SRA_CASH_SECURITY_PK primary key (CASH_SECURITY_ID)
go

/*==============================================================*/
/* Table: SRA_FINANCIAL_AUCPAY_DETAIL                           */
/*==============================================================*/
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
   LASTCHANGED          datetime             null
)
go

alter table SRA_FINANCIAL_AUCPAY_DETAIL
   add constraint SRA_FINANCIAL_AUCPAY_DETAIL_PK primary key (SRA_YEAR, SRA_QUARTER, SRA_RUNNO, PARTICIPANTID, INTERCONNECTORID, FROMREGIONID, CONTRACTID)
go

/*==============================================================*/
/* Table: SRA_FINANCIAL_AUCPAY_SUM                              */
/*==============================================================*/
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
   LASTCHANGED          datetime             null
)
go

alter table SRA_FINANCIAL_AUCPAY_SUM
   add constraint SRA_FINANCIAL_AUCPAY_SUM_PK primary key (SRA_YEAR, SRA_QUARTER, SRA_RUNNO, PARTICIPANTID)
go

/*==============================================================*/
/* Table: SRA_FINANCIAL_AUC_MARDETAIL                           */
/*==============================================================*/
create table SRA_FINANCIAL_AUC_MARDETAIL (
   SRA_YEAR             numeric(4)           not null,
   SRA_QUARTER          numeric(3)           not null,
   SRA_RUNNO            numeric(3)           not null,
   PARTICIPANTID        varchar(10)          not null,
   CASH_SECURITY_ID     varchar(36)          not null,
   RETURNED_AMOUNT      numeric(18,8)        null,
   RETURNED_INTEREST    numeric(18,8)        null
)
go

alter table SRA_FINANCIAL_AUC_MARDETAIL
   add constraint SRA_FINANCIAL_AUC_MARDETAIL_PK primary key (SRA_YEAR, SRA_QUARTER, SRA_RUNNO, PARTICIPANTID, CASH_SECURITY_ID)
go

/*==============================================================*/
/* Table: SRA_FINANCIAL_AUC_MARGIN                              */
/*==============================================================*/
create table SRA_FINANCIAL_AUC_MARGIN (
   SRA_YEAR             numeric(4)           not null,
   SRA_QUARTER          numeric(3)           not null,
   SRA_RUNNO            numeric(3)           not null,
   PARTICIPANTID        varchar(10)          not null,
   TOTAL_CASH_SECURITY  numeric(18,8)        null,
   REQUIRED_MARGIN      numeric(18,8)        null,
   RETURNED_MARGIN      numeric(18,8)        null,
   RETURNED_MARGIN_INTEREST numeric(18,8)        null
)
go

alter table SRA_FINANCIAL_AUC_MARGIN
   add constraint SRA_FINANCIAL_AUC_MARGIN_PK primary key (SRA_YEAR, SRA_QUARTER, SRA_RUNNO, PARTICIPANTID)
go

/*==============================================================*/
/* Table: SRA_FINANCIAL_AUC_RECEIPTS                            */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   PROCEEDS_AMOUNT      numeric(18,8)        null,
   UNITS_SOLD           numeric(18,8)        null
)
go

alter table SRA_FINANCIAL_AUC_RECEIPTS
   add constraint SRA_FINANCIAL_AUC_RECEIPTS_PK primary key (SRA_YEAR, SRA_QUARTER, SRA_RUNNO, PARTICIPANTID, INTERCONNECTORID, FROMREGIONID, CONTRACTID)
go

/*==============================================================*/
/* Table: SRA_FINANCIAL_RUNTRK                                  */
/*==============================================================*/
create table SRA_FINANCIAL_RUNTRK (
   SRA_YEAR             numeric(4)           not null,
   SRA_QUARTER          numeric(3)           not null,
   SRA_RUNNO            numeric(3)           not null,
   RUNTYPE              varchar(20)          null,
   RUNDATE              datetime             null,
   POSTEDDATE           datetime             null,
   INTEREST_VERSIONNO   numeric(3)           null,
   MAKEUP_VERSIONNO     numeric(3)           null,
   LASTCHANGED          datetime             null
)
go

alter table SRA_FINANCIAL_RUNTRK
   add constraint SRA_FINANCIAL_RUNTRK_PK primary key (SRA_YEAR, SRA_QUARTER, SRA_RUNNO)
go

/*==============================================================*/
/* Table: SRA_OFFER_PRODUCT                                     */
/*==============================================================*/
create table SRA_OFFER_PRODUCT (
   AUCTIONID            varchar(30)          not null,
   PARTICIPANTID        varchar(10)          not null,
   LOADDATE             datetime             not null,
   OPTIONID             numeric(4)           not null,
   INTERCONNECTORID     varchar(10)          null,
   FROMREGIONID         varchar(10)          null,
   OFFER_QUANTITY       numeric(5)           null,
   OFFER_PRICE          numeric(18,8)        null,
   TRANCHEID            varchar(30)          null,
   LASTCHANGED          datetime             null
)
go

alter table SRA_OFFER_PRODUCT
   add constraint SRA_OFFER_PRODUCT_PK primary key (AUCTIONID, PARTICIPANTID, LOADDATE, OPTIONID)
go

/*==============================================================*/
/* Table: SRA_OFFER_PROFILE                                     */
/*==============================================================*/
create table SRA_OFFER_PROFILE (
   AUCTIONID            varchar(30)          not null,
   PARTICIPANTID        varchar(10)          not null,
   LOADDATE             datetime             not null,
   FILENAME             varchar(40)          null,
   ACKFILENAME          varchar(40)          null,
   TRANSACTIONID        varchar(100)         null,
   LASTCHANGED          datetime             null
)
go

alter table SRA_OFFER_PROFILE
   add constraint SRA_OFFER_PROFILE_PK primary key (AUCTIONID, PARTICIPANTID, LOADDATE)
go

/*==============================================================*/
/* Table: SRA_PRUDENTIAL_CASH_SECURITY                          */
/*==============================================================*/
create table SRA_PRUDENTIAL_CASH_SECURITY (
   PRUDENTIAL_DATE      datetime             not null,
   PRUDENTIAL_RUNNO     numeric(8)           not null,
   PARTICIPANTID        varchar(10)          not null,
   CASH_SECURITY_ID     varchar(36)          not null,
   CASH_SECURITY_AMOUNT numeric(18,8)        null
)
go

alter table SRA_PRUDENTIAL_CASH_SECURITY
   add constraint SRA_PRUDENTIAL_CASH_SEC_PK primary key (PRUDENTIAL_DATE, PRUDENTIAL_RUNNO, PARTICIPANTID, CASH_SECURITY_ID)
go

/*==============================================================*/
/* Table: SRA_PRUDENTIAL_COMP_POSITION                          */
/*==============================================================*/
create table SRA_PRUDENTIAL_COMP_POSITION (
   PRUDENTIAL_DATE      datetime             not null,
   PRUDENTIAL_RUNNO     numeric(8)           not null,
   PARTICIPANTID        varchar(10)          not null,
   TRADING_LIMIT        numeric(18,8)        null,
   PRUDENTIAL_EXPOSURE_AMOUNT numeric(18,8)        null,
   TRADING_MARGIN       numeric(18,8)        null
)
go

alter table SRA_PRUDENTIAL_COMP_POSITION
   add constraint SRA_PRUDENTIAL_COMP_PK primary key (PRUDENTIAL_DATE, PRUDENTIAL_RUNNO, PARTICIPANTID)
go

/*==============================================================*/
/* Table: SRA_PRUDENTIAL_EXPOSURE                               */
/*==============================================================*/
create table SRA_PRUDENTIAL_EXPOSURE (
   PRUDENTIAL_DATE      datetime             not null,
   PRUDENTIAL_RUNNO     numeric(8)           not null,
   PARTICIPANTID        varchar(10)          not null,
   SRA_YEAR             numeric(4)           not null,
   SRA_QUARTER          numeric(3)           not null,
   INTERCONNECTORID     varchar(10)          not null,
   FROMREGIONID         varchar(10)          not null,
   MAX_TRANCHE          numeric(2)           null,
   AUCTIONID            varchar(30)          null,
   OFFER_SUBMISSIONTIME datetime             null,
   AVERAGE_PURCHASE_PRICE numeric(18,8)        null,
   AVERAGE_CANCELLATION_PRICE numeric(18,8)        null,
   CANCELLATION_VOLUME  numeric(18,8)        null,
   TRADING_POSITION     numeric(18,8)        null
)
go

alter table SRA_PRUDENTIAL_EXPOSURE
   add constraint SRA_PRUDENTIAL_EXPOSURE_PK primary key (PRUDENTIAL_DATE, PRUDENTIAL_RUNNO, PARTICIPANTID, SRA_YEAR, SRA_QUARTER, INTERCONNECTORID, FROMREGIONID)
go

/*==============================================================*/
/* Table: SRA_PRUDENTIAL_RUN                                    */
/*==============================================================*/
create table SRA_PRUDENTIAL_RUN (
   PRUDENTIAL_DATE      datetime             not null,
   PRUDENTIAL_RUNNO     numeric(8)           not null
)
go

alter table SRA_PRUDENTIAL_RUN
   add constraint SRA_PRUDENTIAL_RUN_PK primary key (PRUDENTIAL_DATE, PRUDENTIAL_RUNNO)
go

/*==============================================================*/
/* Table: STADUALLOC                                            */
/*==============================================================*/
create table STADUALLOC (
   DUID                 varchar(10)          not null,
   EFFECTIVEDATE        datetime             not null,
   STATIONID            varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   LASTCHANGED          datetime             null
)
go

alter table STADUALLOC
   add constraint STADULLOC_PK primary key (STATIONID, EFFECTIVEDATE, VERSIONNO, DUID)
go

/*==============================================================*/
/* Index: STADUALLOC_LCX                                        */
/*==============================================================*/
create index STADUALLOC_LCX on STADUALLOC (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: STADUALLOC_NDX2                                       */
/*==============================================================*/
create index STADUALLOC_NDX2 on STADUALLOC (
STATIONID ASC,
EFFECTIVEDATE ASC,
VERSIONNO ASC
)
go

/*==============================================================*/
/* Index: STADUALLOC_NDX3                                       */
/*==============================================================*/
create index STADUALLOC_NDX3 on STADUALLOC (
DUID ASC
)
go

/*==============================================================*/
/* Table: STATION                                               */
/*==============================================================*/
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
   LASTCHANGED          datetime             null,
   CONNECTIONPOINTID    varchar(10)          null
)
go

alter table STATION
   add constraint STATION_PK primary key (STATIONID)
go

/*==============================================================*/
/* Index: STATION_LCX                                           */
/*==============================================================*/
create index STATION_LCX on STATION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: STATIONOPERATINGSTATUS                                */
/*==============================================================*/
create table STATIONOPERATINGSTATUS (
   EFFECTIVEDATE        datetime             not null,
   STATIONID            varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   STATUS               varchar(20)          null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table STATIONOPERATINGSTATUS
   add constraint STATIONOPERATINGSTATUS_PK primary key (EFFECTIVEDATE, STATIONID, VERSIONNO)
go

/*==============================================================*/
/* Index: STATIONOPERATINGSTATUS_LCX                            */
/*==============================================================*/
create index STATIONOPERATINGSTATUS_LCX on STATIONOPERATINGSTATUS (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: STATIONOWNER                                          */
/*==============================================================*/
create table STATIONOWNER (
   EFFECTIVEDATE        datetime             not null,
   PARTICIPANTID        varchar(10)          not null,
   STATIONID            varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   LASTCHANGED          datetime             null
)
go

alter table STATIONOWNER
   add constraint STATIONOWNER_PK primary key (PARTICIPANTID, EFFECTIVEDATE, VERSIONNO, STATIONID)
go

/*==============================================================*/
/* Index: STATIONOWNER_LCX                                      */
/*==============================================================*/
create index STATIONOWNER_LCX on STATIONOWNER (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: STATIONOWNER_NDX2                                     */
/*==============================================================*/
create index STATIONOWNER_NDX2 on STATIONOWNER (
STATIONID ASC,
EFFECTIVEDATE ASC,
VERSIONNO ASC
)
go

/*==============================================================*/
/* Index: STATIONOWNER_NDX3                                     */
/*==============================================================*/
create index STATIONOWNER_NDX3 on STATIONOWNER (
PARTICIPANTID ASC
)
go

/*==============================================================*/
/* Table: STATIONOWNERTRK                                       */
/*==============================================================*/
create table STATIONOWNERTRK (
   EFFECTIVEDATE        datetime             not null,
   PARTICIPANTID        varchar(10)          not null,
   VERSIONNO            numeric(3,0)         not null,
   AUTHORISEDBY         varchar(15)          null,
   AUTHORISEDDATE       datetime             null,
   LASTCHANGED          datetime             null
)
go

alter table STATIONOWNERTRK
   add constraint STATIONOWNERTRK_PK primary key (PARTICIPANTID, EFFECTIVEDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: STATIONOWNERTRK_LCX                                   */
/*==============================================================*/
create index STATIONOWNERTRK_LCX on STATIONOWNERTRK (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: STPASA_CASESOLUTION                                   */
/*==============================================================*/
create table STPASA_CASESOLUTION (
   RUN_DATETIME         datetime             not null,
   PASAVERSION          varchar(10)          null,
   RESERVECONDITION     numeric(1,0)         null,
   LORCONDITION         numeric(1,0)         null,
   CAPACITYOBJFUNCTION  numeric(12,3)        null,
   CAPACITYOPTION       numeric(12,3)        null,
   MAXSURPLUSRESERVEOPTION numeric(12,3)        null,
   MAXSPARECAPACITYOPTION numeric(12,3)        null,
   INTERCONNECTORFLOWPENALTY numeric(12,3)        null,
   LASTCHANGED          datetime             null,
   RELIABILITYLRCDEMANDOPTION numeric(12,3)        null,
   OUTAGELRCDEMANDOPTION numeric(12,3)        null,
   LORDEMANDOPTION      numeric(12,3)        null,
   RELIABILITYLRCCAPACITYOPTION varchar(10)          null,
   OUTAGELRCCAPACITYOPTION varchar(10)          null,
   LORCAPACITYOPTION    varchar(10)          null,
   LORUIGFOPTION        numeric(3,0)         null,
   RELIABILITYLRCUIGFOPTION numeric(3,0)         null,
   OUTAGELRCUIGFOPTION  numeric(3,0)         null
)
go

alter table STPASA_CASESOLUTION
   add constraint CASESOLUTION_PK primary key (RUN_DATETIME)
go

/*==============================================================*/
/* Index: STPASA_CASESOLUTION_LCX                               */
/*==============================================================*/
create index STPASA_CASESOLUTION_LCX on STPASA_CASESOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: STPASA_CONSTRAINTSOLUTION                             */
/*==============================================================*/
create table STPASA_CONSTRAINTSOLUTION (
   RUN_DATETIME         datetime             not null,
   INTERVAL_DATETIME    datetime             not null,
   CONSTRAINTID         varchar(20)          not null,
   CAPACITYRHS          numeric(12,2)        null,
   CAPACITYMARGINALVALUE numeric(12,2)        null,
   CAPACITYVIOLATIONDEGREE numeric(12,2)        null,
   LASTCHANGED          datetime             null,
   RUNTYPE              varchar(20)          not null default 'OUTAGE_LRC'
)
go

alter table STPASA_CONSTRAINTSOLUTION
   add constraint CONSTRAINTSOLUTION_PK primary key (RUN_DATETIME, RUNTYPE, INTERVAL_DATETIME, CONSTRAINTID)
go

/*==============================================================*/
/* Index: STPASA_CONSTRAINTSOLUTION_LCX                         */
/*==============================================================*/
create index STPASA_CONSTRAINTSOLUTION_LCX on STPASA_CONSTRAINTSOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: STPASA_INTERCONNECTORSOLN                             */
/*==============================================================*/
create table STPASA_INTERCONNECTORSOLN (
   RUN_DATETIME         datetime             not null,
   INTERVAL_DATETIME    datetime             not null,
   INTERCONNECTORID     varchar(10)          not null,
   CAPACITYMWFLOW       numeric(12,2)        null,
   CAPACITYMARGINALVALUE numeric(12,2)        null,
   CAPACITYVIOLATIONDEGREE numeric(12,2)        null,
   CALCULATEDEXPORTLIMIT numeric(12,2)        null,
   CALCULATEDIMPORTLIMIT numeric(12,2)        null,
   LASTCHANGED          datetime             null,
   RUNTYPE              varchar(20)          not null default 'OUTAGE_LRC',
   EXPORTLIMITCONSTRAINTID varchar(20)          null,
   IMPORTLIMITCONSTRAINTID varchar(20)          null
)
go

alter table STPASA_INTERCONNECTORSOLN
   add constraint INTERCONNECTORSOLUTION_PK primary key (RUN_DATETIME, RUNTYPE, INTERVAL_DATETIME, INTERCONNECTORID)
go

/*==============================================================*/
/* Index: STPASA_INTERCONNECTORSOLN_LCX                         */
/*==============================================================*/
create index STPASA_INTERCONNECTORSOLN_LCX on STPASA_INTERCONNECTORSOLN (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: STPASA_REGIONSOLUTION                                 */
/*==============================================================*/
create table STPASA_REGIONSOLUTION (
   RUN_DATETIME         datetime             not null,
   INTERVAL_DATETIME    datetime             not null,
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
   LASTCHANGED          datetime             null,
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
)
go

alter table STPASA_REGIONSOLUTION
   add constraint REGIONSOLUTION_PK primary key (RUN_DATETIME, RUNTYPE, INTERVAL_DATETIME, REGIONID)
go

/*==============================================================*/
/* Index: STPASA_REGIONSOLUTION_LCX                             */
/*==============================================================*/
create index STPASA_REGIONSOLUTION_LCX on STPASA_REGIONSOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: STPASA_SYSTEMSOLUTION                                 */
/*==============================================================*/
create table STPASA_SYSTEMSOLUTION (
   RUN_DATETIME         datetime             not null,
   INTERVAL_DATETIME    datetime             not null,
   SYSTEMDEMAND50       numeric(12,2)        null,
   RESERVEREQ           numeric(12,2)        null,
   UNCONSTRAINEDCAPACITY numeric(12,2)        null,
   CONSTRAINEDCAPACITY  numeric(12,2)        null,
   SURPLUSCAPACITY      numeric(12,2)        null,
   SURPLUSRESERVE       numeric(12,2)        null,
   RESERVECONDITION     numeric(1,0)         null,
   LASTCHANGED          datetime             null
)
go

alter table STPASA_SYSTEMSOLUTION
   add constraint SYSTEMSOLUTION_PK primary key (INTERVAL_DATETIME)
go

/*==============================================================*/
/* Index: STPASA_SYSTEMSOLUTION_LCX                             */
/*==============================================================*/
create index STPASA_SYSTEMSOLUTION_LCX on STPASA_SYSTEMSOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: STPASA_SYSTEMSOLUTION_NDX1                            */
/*==============================================================*/
create index STPASA_SYSTEMSOLUTION_NDX1 on STPASA_SYSTEMSOLUTION (
RUN_DATETIME ASC
)
go

/*==============================================================*/
/* Table: STPASA_UNITSOLUTION                                   */
/*==============================================================*/
create table STPASA_UNITSOLUTION (
   RUN_DATETIME         datetime             not null,
   INTERVAL_DATETIME    datetime             not null,
   DUID                 varchar(10)          not null,
   CONNECTIONPOINTID    varchar(10)          null,
   EXPECTEDMAXCAPACITY  numeric(12,2)        null,
   CAPACITYMARGINALVALUE numeric(12,2)        null,
   CAPACITYVIOLATIONDEGREE numeric(12,2)        null,
   CAPACITYAVAILABLE    numeric(12,2)        null,
   ENERGYCONSTRAINED    numeric(1,0)         null,
   ENERGYAVAILABLE      numeric(10,0)        null,
   LASTCHANGED          datetime             null,
   PASAAVAILABILITY     numeric(12,0)        null,
   RUNTYPE              varchar(20)          not null default 'OUTAGE_LRC'
)
go

alter table STPASA_UNITSOLUTION
   add constraint UNITSOLUTION_PK primary key (RUN_DATETIME, RUNTYPE, INTERVAL_DATETIME, DUID)
go

/*==============================================================*/
/* Index: STPASA_UNITSOLUTION_LCX                               */
/*==============================================================*/
create index STPASA_UNITSOLUTION_LCX on STPASA_UNITSOLUTION (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: TRADINGINTERCONNECT                                   */
/*==============================================================*/
create table TRADINGINTERCONNECT (
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3,0)         not null,
   INTERCONNECTORID     varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   METEREDMWFLOW        numeric(15,5)        null,
   MWFLOW               numeric(15,5)        null,
   MWLOSSES             numeric(15,5)        null,
   LASTCHANGED          datetime             null
)
go

alter table TRADINGINTERCONNECT
   add constraint PK_TRADINGINTERCONNECT primary key (SETTLEMENTDATE, RUNNO, INTERCONNECTORID, PERIODID)
go

/*==============================================================*/
/* Index: TRADINGINTERCONNECT_LCX                               */
/*==============================================================*/
create index TRADINGINTERCONNECT_LCX on TRADINGINTERCONNECT (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: TRADINGLOAD                                           */
/*==============================================================*/
create table TRADINGLOAD (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null,
   LOWERREG             numeric(15,5)        null,
   RAISEREG             numeric(15,5)        null,
   AVAILABILITY         numeric(15,5)        null,
   SEMIDISPATCHCAP      numeric(3,0)         null
)
go

alter table TRADINGLOAD
   add constraint PK_TRADINGLOAD primary key (SETTLEMENTDATE, RUNNO, DUID, TRADETYPE, PERIODID)
go

/*==============================================================*/
/* Index: TRADINGLOAD_NDX2                                      */
/*==============================================================*/
create index TRADINGLOAD_NDX2 on TRADINGLOAD (
DUID ASC,
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Index: TRADINGLOAD_LCX                                       */
/*==============================================================*/
create index TRADINGLOAD_LCX on TRADINGLOAD (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: TRADINGPRICE                                          */
/*==============================================================*/
create table TRADINGPRICE (
   SETTLEMENTDATE       datetime             not null,
   RUNNO                numeric(3,0)         not null,
   REGIONID             varchar(10)          not null,
   PERIODID             numeric(3,0)         not null,
   RRP                  numeric(15,5)        null,
   EEP                  numeric(15,5)        null,
   INVALIDFLAG          varchar(1)           null,
   LASTCHANGED          datetime             null,
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
)
go

alter table TRADINGPRICE
   add constraint PK_TRADINGPRICE primary key (SETTLEMENTDATE, RUNNO, REGIONID, PERIODID)
go

/*==============================================================*/
/* Index: TRADINGPRICE_LCX                                      */
/*==============================================================*/
create index TRADINGPRICE_LCX on TRADINGPRICE (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: TRADINGREGIONSUM                                      */
/*==============================================================*/
create table TRADINGREGIONSUM (
   SETTLEMENTDATE       datetime             not null,
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
   LASTCHANGED          datetime             null,
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
)
go

alter table TRADINGREGIONSUM
   add constraint PK_TRADNGREGIONSUM primary key (SETTLEMENTDATE, RUNNO, REGIONID, PERIODID)
go

/*==============================================================*/
/* Index: TRADINGREGIONSUM_LCX                                  */
/*==============================================================*/
create index TRADINGREGIONSUM_LCX on TRADINGREGIONSUM (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: TRANSMISSIONLOSSFACTOR                                */
/*==============================================================*/
create table TRANSMISSIONLOSSFACTOR (
   TRANSMISSIONLOSSFACTOR numeric(15,5)        not null,
   EFFECTIVEDATE        datetime             not null,
   VERSIONNO            numeric(22,0)        not null,
   CONNECTIONPOINTID    varchar(10)          not null,
   REGIONID             varchar(10)          null,
   LASTCHANGED          datetime             null,
   SECONDARY_TLF        numeric(18,8)        null
)
go

alter table TRANSMISSIONLOSSFACTOR
   add constraint TRANSMISSIONLOSSFACTOR_PK primary key (CONNECTIONPOINTID, EFFECTIVEDATE, VERSIONNO)
go

/*==============================================================*/
/* Index: TRANSMISSIONLOSSFACTOR_LCX                            */
/*==============================================================*/
create index TRANSMISSIONLOSSFACTOR_LCX on TRANSMISSIONLOSSFACTOR (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: VALUATIONID                                           */
/*==============================================================*/
create table VALUATIONID (
   VALUATIONID          varchar(15)          not null,
   DESCRIPTION          varchar(80)          null,
   LASTCHANGED          datetime             null
)
go

alter table VALUATIONID
   add constraint VALUATIONID_PK primary key (VALUATIONID)
go

/*==============================================================*/
/* Index: VALUATIONID_NDX_LCHD                                  */
/*==============================================================*/
create index VALUATIONID_NDX_LCHD on VALUATIONID (
LASTCHANGED ASC
)
go

/*==============================================================*/
/* Table: VOLTAGE_INSTRUCTION                                   */
/*==============================================================*/
create table VOLTAGE_INSTRUCTION (
   RUN_DATETIME         datetime             not null,
   EMS_ID               varchar(60)          not null,
   PARTICIPANTID        varchar(20)          null,
   STATION_ID           varchar(60)          null,
   DEVICE_ID            varchar(60)          null,
   DEVICE_TYPE          varchar(20)          null,
   CONTROL_TYPE         varchar(20)          null,
   TARGET               numeric(15,0)        null,
   CONFORMING           numeric(1,0)         null,
   INSTRUCTION_SUMMARY  varchar(400)         null,
   VERSION_DATETIME     datetime             not null,
   INSTRUCTION_SEQUENCE numeric(4,0)         null,
   ADDITIONAL_NOTES     varchar(60)          null
)
go

alter table VOLTAGE_INSTRUCTION
   add constraint VOLTAGE_INSTRUCTION_PK primary key (RUN_DATETIME, VERSION_DATETIME, EMS_ID)
go

/*==============================================================*/
/* Table: VOLTAGE_INSTRUCTION_TRK                               */
/*==============================================================*/
create table VOLTAGE_INSTRUCTION_TRK (
   RUN_DATETIME         datetime             not null,
   FILE_TYPE            varchar(20)          null,
   VERSION_DATETIME     datetime             not null,
   SE_DATETIME          datetime             null,
   SOLUTION_CATEGORY    varchar(60)          null,
   SOLUTION_STATUS      varchar(60)          null,
   OPERATING_MODE       varchar(60)          null,
   OPERATING_STATUS     varchar(100)         null,
   EST_EXPIRY           datetime             null,
   EST_NEXT_INSTRUCTION datetime             null
)
go

alter table VOLTAGE_INSTRUCTION_TRK
   add constraint VOLTAGE_INSTRUCTION_TRK_PK primary key (RUN_DATETIME, VERSION_DATETIME)
go

