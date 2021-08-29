# coding: utf-8
from sqlalchemy import CHAR, Column, Index, Numeric, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class AncillaryRecoverySplit(Base):
    __tablename__ = "ancillary_recovery_split"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    service = Column(String(10), primary_key=True, nullable=False)
    paymenttype = Column(String(20), primary_key=True, nullable=False)
    customer_portion = Column(Numeric(8, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Apccomp(Base):
    __tablename__ = "apccomp"
    __table_args__ = {"schema": "mms"}

    apcid = Column(String(10), primary_key=True)
    regionid = Column(String(10))
    startdate = Column(TIMESTAMP(precision=3))
    startperiod = Column(Numeric(3, 0))
    enddate = Column(TIMESTAMP(precision=3))
    endperiod = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Apccompamount(Base):
    __tablename__ = "apccompamount"
    __table_args__ = {"schema": "mms"}

    apcid = Column(String(10), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(6, 0), primary_key=True, nullable=False)
    amount = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Apccompamounttrk(Base):
    __tablename__ = "apccompamounttrk"
    __table_args__ = {"schema": "mms"}

    apcid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    authorisedby = Column(String(10))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Apevent(Base):
    __tablename__ = "apevent"
    __table_args__ = {"schema": "mms"}

    apeventid = Column(Numeric(22, 0), primary_key=True)
    effectivefrominterval = Column(TIMESTAMP(precision=3))
    effectivetointerval = Column(TIMESTAMP(precision=3))
    reason = Column(String(2000))
    startauthorisedby = Column(String(15))
    startauthoriseddate = Column(TIMESTAMP(precision=3))
    endauthorisedby = Column(String(15))
    endauthoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Apeventregion(Base):
    __tablename__ = "apeventregion"
    __table_args__ = {"schema": "mms"}

    apeventid = Column(Numeric(22, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    energyapflag = Column(Numeric(1, 0))
    raise6secapflag = Column(Numeric(1, 0))
    raise60secapflag = Column(Numeric(1, 0))
    raise5minapflag = Column(Numeric(1, 0))
    raiseregapflag = Column(Numeric(1, 0))
    lower6secapflag = Column(Numeric(1, 0))
    lower60secapflag = Column(Numeric(1, 0))
    lower5minapflag = Column(Numeric(1, 0))
    lowerregapflag = Column(Numeric(1, 0))


class Auction(Base):
    __tablename__ = "auction"
    __table_args__ = {"schema": "mms"}

    auctionid = Column(String(30), primary_key=True)
    auctiondate = Column(TIMESTAMP(precision=3))
    notifydate = Column(TIMESTAMP(precision=3))
    startdate = Column(TIMESTAMP(precision=3))
    enddate = Column(TIMESTAMP(precision=3))
    description = Column(String(100))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(30))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class AuctionCalendar(Base):
    __tablename__ = "auction_calendar"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    quarter = Column(Numeric(1, 0), primary_key=True, nullable=False)
    startdate = Column(TIMESTAMP(precision=3))
    enddate = Column(TIMESTAMP(precision=3))
    notifydate = Column(TIMESTAMP(precision=3))
    paymentdate = Column(TIMESTAMP(precision=3))
    reconciliationdate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    prelimpurchasestmtdate = Column(TIMESTAMP(precision=3))
    prelimproceedsstmtdate = Column(TIMESTAMP(precision=3))
    finalpurchasestmtdate = Column(TIMESTAMP(precision=3))
    finalproceedsstmtdate = Column(TIMESTAMP(precision=3))


class AuctionIcAllocation(Base):
    __tablename__ = "auction_ic_allocations"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    quarter = Column(Numeric(1, 0), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    maximumunits = Column(Numeric(5, 0))
    proportion = Column(Numeric(8, 5))
    auctionfee = Column(Numeric(17, 5))
    changedate = Column(TIMESTAMP(precision=3))
    changedby = Column(String(15))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    auctionfee_sales = Column(Numeric(18, 8))


class AuctionRevenueEstimate(Base):
    __tablename__ = "auction_revenue_estimate"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    quarter = Column(Numeric(1, 0), primary_key=True, nullable=False)
    valuationid = Column(String(15), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    monthno = Column(Numeric(1, 0), primary_key=True, nullable=False)
    startdate = Column(TIMESTAMP(precision=3))
    enddate = Column(TIMESTAMP(precision=3))
    revenue = Column(Numeric(17, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class AuctionRevenueTrack(Base):
    __tablename__ = "auction_revenue_track"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    quarter = Column(Numeric(1, 0), primary_key=True, nullable=False)
    valuationid = Column(String(15), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3))
    status = Column(String(10))
    documentref = Column(String(30))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class AuctionRpEstimate(Base):
    __tablename__ = "auction_rp_estimate"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    quarter = Column(Numeric(1, 0), primary_key=True, nullable=False)
    valuationid = Column(String(15), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    rpestimate = Column(Numeric(17, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class AuctionTranche(Base):
    __tablename__ = "auction_tranche"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    quarter = Column(Numeric(1, 0), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    tranche = Column(Numeric(2, 0), primary_key=True, nullable=False)
    auctiondate = Column(TIMESTAMP(precision=3))
    notifydate = Column(TIMESTAMP(precision=3))
    unitallocation = Column(Numeric(18, 8))
    changedate = Column(TIMESTAMP(precision=3))
    changedby = Column(String(15))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Biddayoffer(Base):
    __tablename__ = "biddayoffer"
    __table_args__ = {"schema": "mms"}

    duid = Column(String(10), primary_key=True, nullable=False)
    bidtype = Column(String(10), primary_key=True, nullable=False)
    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    offerdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(22, 0))
    participantid = Column(String(10), index=True)
    dailyenergyconstraint = Column(Numeric(12, 6))
    rebidexplanation = Column(String(500))
    priceband1 = Column(Numeric(9, 2))
    priceband2 = Column(Numeric(9, 2))
    priceband3 = Column(Numeric(9, 2))
    priceband4 = Column(Numeric(9, 2))
    priceband5 = Column(Numeric(9, 2))
    priceband6 = Column(Numeric(9, 2))
    priceband7 = Column(Numeric(9, 2))
    priceband8 = Column(Numeric(9, 2))
    priceband9 = Column(Numeric(9, 2))
    priceband10 = Column(Numeric(9, 2))
    minimumload = Column(Numeric(22, 0))
    t1 = Column(Numeric(22, 0))
    t2 = Column(Numeric(22, 0))
    t3 = Column(Numeric(22, 0))
    t4 = Column(Numeric(22, 0))
    normalstatus = Column(String(3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    mr_factor = Column(Numeric(16, 6))
    entrytype = Column(String(20))


class BiddayofferD(Base):
    __tablename__ = "biddayoffer_d"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    bidtype = Column(String(10), primary_key=True, nullable=False)
    bidsettlementdate = Column(TIMESTAMP(precision=3))
    offerdate = Column(TIMESTAMP(precision=3))
    versionno = Column(Numeric(22, 0))
    participantid = Column(String(10), index=True)
    dailyenergyconstraint = Column(Numeric(12, 6))
    rebidexplanation = Column(String(500))
    priceband1 = Column(Numeric(9, 2))
    priceband2 = Column(Numeric(9, 2))
    priceband3 = Column(Numeric(9, 2))
    priceband4 = Column(Numeric(9, 2))
    priceband5 = Column(Numeric(9, 2))
    priceband6 = Column(Numeric(9, 2))
    priceband7 = Column(Numeric(9, 2))
    priceband8 = Column(Numeric(9, 2))
    priceband9 = Column(Numeric(9, 2))
    priceband10 = Column(Numeric(9, 2))
    minimumload = Column(Numeric(22, 0))
    t1 = Column(Numeric(22, 0))
    t2 = Column(Numeric(22, 0))
    t3 = Column(Numeric(22, 0))
    t4 = Column(Numeric(22, 0))
    normalstatus = Column(String(3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    mr_factor = Column(Numeric(16, 6))
    entrytype = Column(String(20))


class Bidduiddetail(Base):
    __tablename__ = "bidduiddetails"
    __table_args__ = {"schema": "mms"}

    duid = Column(String(10), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    bidtype = Column(String(10), primary_key=True, nullable=False)
    maxcapacity = Column(Numeric(22, 0))
    minenablementlevel = Column(Numeric(22, 0))
    maxenablementlevel = Column(Numeric(22, 0))
    maxlowerangle = Column(Numeric(3, 0))
    maxupperangle = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Bidduiddetailstrk(Base):
    __tablename__ = "bidduiddetailstrk"
    __table_args__ = {"schema": "mms"}

    duid = Column(String(10), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Bidofferfiletrk(Base):
    __tablename__ = "bidofferfiletrk"
    __table_args__ = {"schema": "mms"}

    participantid = Column(String(10), primary_key=True, nullable=False)
    offerdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    filename = Column(String(80), nullable=False, unique=True)
    status = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    authorisedby = Column(String(20))
    authoriseddate = Column(TIMESTAMP(precision=3))


class Bidperoffer(Base):
    __tablename__ = "bidperoffer"
    __table_args__ = {"schema": "mms"}

    duid = Column(String(10), primary_key=True, nullable=False)
    bidtype = Column(String(10), primary_key=True, nullable=False)
    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    offerdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    periodid = Column(Numeric(22, 0), primary_key=True, nullable=False)
    versionno = Column(Numeric(22, 0))
    maxavail = Column(Numeric(12, 6))
    fixedload = Column(Numeric(12, 6))
    rocup = Column(Numeric(6, 0))
    rocdown = Column(Numeric(6, 0))
    enablementmin = Column(Numeric(6, 0))
    enablementmax = Column(Numeric(6, 0))
    lowbreakpoint = Column(Numeric(6, 0))
    highbreakpoint = Column(Numeric(6, 0))
    bandavail1 = Column(Numeric(22, 0))
    bandavail2 = Column(Numeric(22, 0))
    bandavail3 = Column(Numeric(22, 0))
    bandavail4 = Column(Numeric(22, 0))
    bandavail5 = Column(Numeric(22, 0))
    bandavail6 = Column(Numeric(22, 0))
    bandavail7 = Column(Numeric(22, 0))
    bandavail8 = Column(Numeric(22, 0))
    bandavail9 = Column(Numeric(22, 0))
    bandavail10 = Column(Numeric(22, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    pasaavailability = Column(Numeric(12, 0))
    mr_capacity = Column(Numeric(6, 0))


class BidperofferD(Base):
    __tablename__ = "bidperoffer_d"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    bidtype = Column(String(10), primary_key=True, nullable=False)
    bidsettlementdate = Column(TIMESTAMP(precision=3))
    offerdate = Column(TIMESTAMP(precision=3))
    periodid = Column(Numeric(22, 0))
    versionno = Column(Numeric(22, 0))
    maxavail = Column(Numeric(12, 6))
    fixedload = Column(Numeric(12, 6))
    rocup = Column(Numeric(6, 0))
    rocdown = Column(Numeric(6, 0))
    enablementmin = Column(Numeric(6, 0))
    enablementmax = Column(Numeric(6, 0))
    lowbreakpoint = Column(Numeric(6, 0))
    highbreakpoint = Column(Numeric(6, 0))
    bandavail1 = Column(Numeric(22, 0))
    bandavail2 = Column(Numeric(22, 0))
    bandavail3 = Column(Numeric(22, 0))
    bandavail4 = Column(Numeric(22, 0))
    bandavail5 = Column(Numeric(22, 0))
    bandavail6 = Column(Numeric(22, 0))
    bandavail7 = Column(Numeric(22, 0))
    bandavail8 = Column(Numeric(22, 0))
    bandavail9 = Column(Numeric(22, 0))
    bandavail10 = Column(Numeric(22, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    pasaavailability = Column(Numeric(12, 0))
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    mr_capacity = Column(Numeric(6, 0))


class Bidtype(Base):
    __tablename__ = "bidtypes"
    __table_args__ = {"schema": "mms"}

    bidtype = Column(String(10), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    description = Column(String(64))
    numberofbands = Column(Numeric(3, 0))
    numdaysaheadpricelocked = Column(Numeric(2, 0))
    validationrule = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    spdalias = Column(String(10))


class Bidtypestrk(Base):
    __tablename__ = "bidtypestrk"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billadjustment(Base):
    __tablename__ = "billadjustments"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0))
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    participanttype = Column(String(10))
    adjcontractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    adjweekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    adjbillrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    prevamount = Column(Numeric(16, 6))
    adjamount = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    lrs = Column(Numeric(15, 5))
    prs = Column(Numeric(15, 5))
    ofs = Column(Numeric(15, 5))
    irn = Column(Numeric(15, 5))
    irp = Column(Numeric(15, 5))
    interestamount = Column(Numeric(15, 5))


class BillingApcCompensation(Base):
    __tablename__ = "billing_apc_compensation"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    apeventid = Column(Numeric(6, 0), primary_key=True, nullable=False)
    claimid = Column(Numeric(6, 0), primary_key=True, nullable=False)
    participantid = Column(String(20))
    compensation_amount = Column(Numeric(18, 8))
    event_type = Column(String(20))
    compensation_type = Column(String(20))
    lastchanged = Column(TIMESTAMP(precision=3))


class BillingApcRecovery(Base):
    __tablename__ = "billing_apc_recovery"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    apeventid = Column(Numeric(6, 0), primary_key=True, nullable=False)
    claimid = Column(Numeric(6, 0), primary_key=True, nullable=False)
    participantid = Column(String(20), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    recovery_amount = Column(Numeric(18, 8))
    eligibility_start_interval = Column(TIMESTAMP(precision=3))
    eligibility_end_interval = Column(TIMESTAMP(precision=3))
    participant_demand = Column(Numeric(18, 8))
    region_demand = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3))


class BillingCo2ePublication(Base):
    __tablename__ = "billing_co2e_publication"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), nullable=False)
    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    sentoutenergy = Column(Numeric(18, 8))
    generatoremissions = Column(Numeric(18, 8))
    intensityindex = Column(Numeric(18, 8))


class BillingCo2ePublicationTrk(Base):
    __tablename__ = "billing_co2e_publication_trk"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3))


class BillingCspDerogationAmount(Base):
    __tablename__ = "billing_csp_derogation_amount"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    amount_id = Column(String(20), primary_key=True, nullable=False)
    derogation_amount = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class BillingDailyEnergySummary(Base):
    __tablename__ = "billing_daily_energy_summary"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    participantid = Column(String(20), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    customer_energy_purchased = Column(Numeric(18, 8))
    generator_energy_sold = Column(Numeric(18, 8))
    generator_energy_purchased = Column(Numeric(18, 8))


class BillingDirectionReconOther(Base):
    __tablename__ = "billing_direction_recon_other"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    direction_id = Column(String(20), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    direction_desc = Column(String(200))
    direction_type_id = Column(String(20))
    direction_start_date = Column(TIMESTAMP(precision=3))
    direction_end_date = Column(TIMESTAMP(precision=3))
    direction_start_interval = Column(TIMESTAMP(precision=3))
    direction_end_interval = Column(TIMESTAMP(precision=3))
    compensation_amount = Column(Numeric(18, 8))
    interest_amount = Column(Numeric(18, 8))
    independent_expert_fee = Column(Numeric(18, 8))
    cra = Column(Numeric(18, 8))
    regional_customer_energy = Column(Numeric(18, 8))
    regional_generator_energy = Column(Numeric(18, 8))
    regional_benefit_factor = Column(Numeric(18, 8))


class BillingDirectionReconciliatn(Base):
    __tablename__ = "billing_direction_reconciliatn"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    direction_id = Column(String(20), primary_key=True, nullable=False)
    direction_desc = Column(String(200))
    direction_start_date = Column(TIMESTAMP(precision=3))
    direction_end_date = Column(TIMESTAMP(precision=3))
    compensation_amount = Column(Numeric(16, 6))
    independent_expert_fee = Column(Numeric(16, 6))
    interest_amount = Column(Numeric(16, 6))
    cra = Column(Numeric(16, 6))
    nem_fee_id = Column(String(20))
    nem_fixed_fee_amount = Column(Numeric(16, 6))
    mkt_customer_perc = Column(Numeric(16, 6))
    generator_perc = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class BillingEftshortfallAmount(Base):
    __tablename__ = "billing_eftshortfall_amount"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(20), primary_key=True, nullable=False)
    shortfall_amount = Column(Numeric(18, 8))
    shortfall = Column(Numeric(18, 8))
    shortfall_company_id = Column(String(20))
    company_shortfall_amount = Column(Numeric(18, 8))
    participant_net_energy = Column(Numeric(18, 8))
    company_net_energy = Column(Numeric(18, 8))


class BillingEftshortfallDetail(Base):
    __tablename__ = "billing_eftshortfall_detail"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(20), primary_key=True, nullable=False)
    transaction_type = Column(String(40), primary_key=True, nullable=False)
    amount = Column(Numeric(18, 8))


class BillingGstDetail(Base):
    __tablename__ = "billing_gst_detail"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    bas_class = Column(String(30), primary_key=True, nullable=False)
    transaction_type = Column(String(30), primary_key=True, nullable=False)
    gst_exclusive_amount = Column(Numeric(15, 5))
    gst_amount = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class BillingGstSummary(Base):
    __tablename__ = "billing_gst_summary"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    bas_class = Column(String(30), primary_key=True, nullable=False)
    gst_exclusive_amount = Column(Numeric(15, 5))
    gst_amount = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class BillingMrPayment(Base):
    __tablename__ = "billing_mr_payment"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    mr_date = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    participantid = Column(String(10))
    duid = Column(String(10), primary_key=True, nullable=False)
    mr_amount = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class BillingMrRecovery(Base):
    __tablename__ = "billing_mr_recovery"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    mr_date = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    participantid = Column(String(10))
    duid = Column(String(10), primary_key=True, nullable=False)
    mr_amount = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class BillingMrShortfall(Base):
    __tablename__ = "billing_mr_shortfall"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    mr_date = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    age = Column(Numeric(16, 6))
    rsa = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class BillingMrSummary(Base):
    __tablename__ = "billing_mr_summary"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    mr_date = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    total_payments = Column(Numeric(16, 6))
    total_recovery = Column(Numeric(16, 6))
    total_rsa = Column(Numeric(16, 6))
    aage = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class BillingNmasTstPayment(Base):
    __tablename__ = "billing_nmas_tst_payments"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(20), primary_key=True, nullable=False)
    service = Column(String(10), primary_key=True, nullable=False)
    contractid = Column(String(10), primary_key=True, nullable=False)
    payment_amount = Column(Numeric(18, 8))


class BillingNmasTstRecovery(Base):
    __tablename__ = "billing_nmas_tst_recovery"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(20), primary_key=True, nullable=False)
    service = Column(String(10), primary_key=True, nullable=False)
    contractid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    rbf = Column(Numeric(18, 8))
    test_payment = Column(Numeric(18, 8))
    recovery_start_date = Column(TIMESTAMP(precision=3))
    recovery_end_date = Column(TIMESTAMP(precision=3))
    participant_energy = Column(Numeric(18, 8))
    region_energy = Column(Numeric(18, 8))
    nem_energy = Column(Numeric(18, 8))
    customer_proportion = Column(Numeric(18, 8))
    generator_proportion = Column(Numeric(18, 8))
    participant_generation = Column(Numeric(18, 8))
    nem_generation = Column(Numeric(18, 8))
    recovery_amount = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class BillingNmasTstRecvryRbf(Base):
    __tablename__ = "billing_nmas_tst_recvry_rbf"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    service = Column(String(10), primary_key=True, nullable=False)
    contractid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    rbf = Column(Numeric(18, 8))
    payment_amount = Column(Numeric(18, 8))
    recovery_amount = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class BillingNmasTstRecvryTrk(Base):
    __tablename__ = "billing_nmas_tst_recvry_trk"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    recovery_contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    recovery_weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    recovery_billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)


class BillingResTraderPayment(Base):
    __tablename__ = "billing_res_trader_payment"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    contractid = Column(String(20), primary_key=True, nullable=False)
    payment_type = Column(String(40), primary_key=True, nullable=False)
    participantid = Column(String(20), primary_key=True, nullable=False)
    payment_amount = Column(Numeric(18, 8))


class BillingResTraderRecovery(Base):
    __tablename__ = "billing_res_trader_recovery"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    participantid = Column(String(20), primary_key=True, nullable=False)
    recovery_amount = Column(Numeric(18, 8))


class BillingSecdepInterestPay(Base):
    __tablename__ = "billing_secdep_interest_pay"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    security_deposit_id = Column(String(20), primary_key=True, nullable=False)
    participantid = Column(String(20), primary_key=True, nullable=False)
    interest_amount = Column(Numeric(18, 8))
    interest_calc_type = Column(String(20))
    interest_acct_id = Column(String(20))
    interest_rate = Column(Numeric(18, 8))


class BillingSecdepInterestRate(Base):
    __tablename__ = "billing_secdep_interest_rate"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interest_acct_id = Column(String(20), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    interest_rate = Column(Numeric(18, 8))


class BillingSecdepositApplication(Base):
    __tablename__ = "billing_secdeposit_application"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(20), primary_key=True, nullable=False)
    application_amount = Column(Numeric(18, 8))


class Billingapccompensation(Base):
    __tablename__ = "billingapccompensation"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    apccompensation = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billingapcrecovery(Base):
    __tablename__ = "billingapcrecovery"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    apcrecovery = Column(Numeric(15, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billingaspayment(Base):
    __tablename__ = "billingaspayments"
    __table_args__ = {"schema": "mms"}

    regionid = Column(String(10))
    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    connectionpointid = Column(String(10), primary_key=True, nullable=False)
    raise6sec = Column(Numeric(15, 5))
    lower6sec = Column(Numeric(15, 5))
    raise60sec = Column(Numeric(15, 5))
    lower60sec = Column(Numeric(15, 5))
    agc = Column(Numeric(15, 5))
    fcascomp = Column(Numeric(15, 5))
    loadshed = Column(Numeric(15, 5))
    rgul = Column(Numeric(15, 5))
    rguu = Column(Numeric(15, 5))
    reactivepower = Column(Numeric(15, 5))
    systemrestart = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    lower5min = Column(Numeric(15, 5))
    raise5min = Column(Numeric(15, 5))
    lowerreg = Column(Numeric(15, 5))
    raisereg = Column(Numeric(15, 5))
    availability_reactive = Column(Numeric(18, 8))
    availability_reactive_rbt = Column(Numeric(18, 8))


class Billingasrecovery(Base):
    __tablename__ = "billingasrecovery"
    __table_args__ = {"schema": "mms"}

    regionid = Column(String(10), primary_key=True, nullable=False)
    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    raise6sec = Column(Numeric(15, 5))
    lower6sec = Column(Numeric(15, 5))
    raise60sec = Column(Numeric(15, 5))
    lower60sec = Column(Numeric(15, 5))
    agc = Column(Numeric(15, 5))
    fcascomp = Column(Numeric(15, 5))
    loadshed = Column(Numeric(15, 5))
    rgul = Column(Numeric(15, 5))
    rguu = Column(Numeric(15, 5))
    reactivepower = Column(Numeric(15, 5))
    systemrestart = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    raise6sec_gen = Column(Numeric(15, 5))
    lower6sec_gen = Column(Numeric(15, 5))
    raise60sec_gen = Column(Numeric(15, 5))
    lower60sec_gen = Column(Numeric(15, 5))
    agc_gen = Column(Numeric(15, 5))
    fcascomp_gen = Column(Numeric(15, 5))
    loadshed_gen = Column(Numeric(15, 5))
    rgul_gen = Column(Numeric(15, 5))
    rguu_gen = Column(Numeric(15, 5))
    reactivepower_gen = Column(Numeric(15, 5))
    systemrestart_gen = Column(Numeric(15, 5))
    lower5min = Column(Numeric(15, 5))
    raise5min = Column(Numeric(15, 5))
    lowerreg = Column(Numeric(15, 5))
    raisereg = Column(Numeric(15, 5))
    lower5min_gen = Column(Numeric(16, 6))
    raise5min_gen = Column(Numeric(16, 6))
    lowerreg_gen = Column(Numeric(16, 6))
    raisereg_gen = Column(Numeric(16, 6))
    availability_reactive = Column(Numeric(18, 8))
    availability_reactive_rbt = Column(Numeric(18, 8))
    availability_reactive_gen = Column(Numeric(18, 8))
    availability_reactive_rbt_gen = Column(Numeric(18, 8))


class Billingcalendar(Base):
    __tablename__ = "billingcalendar"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    startdate = Column(TIMESTAMP(precision=3))
    enddate = Column(TIMESTAMP(precision=3))
    preliminarystatementdate = Column(TIMESTAMP(precision=3))
    finalstatementdate = Column(TIMESTAMP(precision=3))
    paymentdate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    revision1_statementdate = Column(TIMESTAMP(precision=3))
    revision2_statementdate = Column(TIMESTAMP(precision=3))


class Billingcpdatum(Base):
    __tablename__ = "billingcpdata"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    connectionpointid = Column(String(10), primary_key=True, nullable=False)
    aggregateenergy = Column(Numeric(16, 6))
    purchases = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    mda = Column(String(10), primary_key=True, nullable=False)


class Billingcpsum(Base):
    __tablename__ = "billingcpsum"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    participanttype = Column(String(10), primary_key=True, nullable=False)
    previousamount = Column(Numeric(16, 6))
    adjustedamount = Column(Numeric(16, 6))
    adjustmentweekno = Column(Numeric(3, 0))
    adjustmentrunno = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billingcustexcessgen(Base):
    __tablename__ = "billingcustexcessgen"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    excessgenpayment = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    regionid = Column(String(10), primary_key=True, nullable=False)


class Billingdaytrk(Base):
    __tablename__ = "billingdaytrk"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billingexcessgen(Base):
    __tablename__ = "billingexcessgen"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    excessenergycost = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    regionid = Column(String(10), primary_key=True, nullable=False)


class Billingfee(Base):
    __tablename__ = "billingfees"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    marketfeeid = Column(String(10), primary_key=True, nullable=False)
    rate = Column(Numeric(15, 5))
    energy = Column(Numeric(16, 6))
    value = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    participantcategoryid = Column(String(10), primary_key=True, nullable=False)


class Billingfinancialadjustment(Base):
    __tablename__ = "billingfinancialadjustments"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    participanttype = Column(String(10))
    adjustmentitem = Column(String(64), primary_key=True, nullable=False)
    amount = Column(Numeric(15, 5))
    value = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    financialcode = Column(Numeric(10, 0))
    bas_class = Column(String(30))


class Billinggendatum(Base):
    __tablename__ = "billinggendata"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    connectionpointid = Column(String(10), primary_key=True, nullable=False)
    stationid = Column(String(10))
    duid = Column(String(10))
    aggregateenergy = Column(Numeric(16, 6))
    sales = Column(Numeric(16, 6))
    purchases = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    purchasedenergy = Column(Numeric(16, 6))
    mda = Column(String(10))


class Billinginterresidue(Base):
    __tablename__ = "billinginterresidues"
    __table_args__ = {"schema": "mms"}

    allocation = Column(Numeric(6, 3))
    totalsurplus = Column(Numeric(15, 5))
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    surplusvalue = Column(Numeric(15, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    regionid = Column(String(10), primary_key=True, nullable=False)


class Billingintervention(Base):
    __tablename__ = "billingintervention"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    marketintervention = Column(Numeric(15, 5))
    totalintervention = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billinginterventionregion(Base):
    __tablename__ = "billinginterventionregion"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    regionintervention = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billingintraresidue(Base):
    __tablename__ = "billingintraresidues"
    __table_args__ = {"schema": "mms"}

    allocation = Column(Numeric(6, 3))
    totalsurplus = Column(Numeric(15, 5))
    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    surplusvalue = Column(Numeric(15, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    regionid = Column(String(10), primary_key=True, nullable=False)


class Billingiraucsurplu(Base):
    __tablename__ = "billingiraucsurplus"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(2, 0), primary_key=True, nullable=False)
    residueyear = Column(Numeric(4, 0))
    quarter = Column(Numeric(2, 0))
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    contractid = Column(String(30), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    totalresidues = Column(Numeric(15, 5))
    adjustment = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billingiraucsurplussum(Base):
    __tablename__ = "billingiraucsurplussum"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    residueyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    quarter = Column(Numeric(2, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    totalsurplus = Column(Numeric(15, 5))
    auctionfees = Column(Numeric(15, 5))
    actualpayment = Column(Numeric(15, 5))
    auctionfees_gst = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    csp_derogation_amount = Column(Numeric(18, 8))
    unadjusted_irsr = Column(Numeric(18, 8))
    negative_residues = Column(Numeric(18, 8))


class Billingirfm(Base):
    __tablename__ = "billingirfm"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    irfmpayment = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billingirnspsurplu(Base):
    __tablename__ = "billingirnspsurplus"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(2, 0), primary_key=True, nullable=False)
    residueyear = Column(Numeric(4, 0))
    quarter = Column(Numeric(2, 0))
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    contractid = Column(String(30), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    totalresidues = Column(Numeric(15, 5))
    adjustment = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billingirnspsurplussum(Base):
    __tablename__ = "billingirnspsurplussum"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    residueyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    quarter = Column(Numeric(2, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    totalsurplus = Column(Numeric(15, 5))
    auctionfees = Column(Numeric(15, 5))
    auctionfees_gst = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    csp_derogation_amount = Column(Numeric(18, 8))
    unadjusted_irsr = Column(Numeric(18, 8))


class Billingirpartsurplu(Base):
    __tablename__ = "billingirpartsurplus"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(2, 0), primary_key=True, nullable=False)
    residueyear = Column(Numeric(4, 0))
    quarter = Column(Numeric(2, 0))
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    contractid = Column(String(30), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    totalresidues = Column(Numeric(15, 5))
    adjustment = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    actualpayment = Column(Numeric(15, 5))


class Billingirpartsurplussum(Base):
    __tablename__ = "billingirpartsurplussum"
    __table_args__ = (
        Index("billingirpartsurplussum_i01", "residueyear", "quarter"),
        {"schema": "mms"},
    )

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    residueyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    quarter = Column(Numeric(2, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    totalsurplus = Column(Numeric(15, 5))
    auctionfees = Column(Numeric(15, 5))
    actualpayment = Column(Numeric(15, 5))
    auctionfees_gst = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    csp_derogation_amount = Column(Numeric(18, 8))
    unadjusted_irsr = Column(Numeric(18, 8))
    auctionfees_totalgross_adj = Column(Numeric(18, 8))


class Billingprioradjustment(Base):
    __tablename__ = "billingprioradjustments"
    __table_args__ = (
        Index("billingprioradjustments_ndx2", "participantid", "lastchanged"),
        {"schema": "mms"},
    )

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    adjcontractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    adjweekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    adjbillrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    prevamount = Column(Numeric(15, 5))
    adjamount = Column(Numeric(15, 5))
    irn = Column(Numeric(15, 5))
    irp = Column(Numeric(15, 5))
    interestamount = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    irsr_prevamount = Column(Numeric(15, 5))
    irsr_adjamount = Column(Numeric(15, 5))
    irsr_interestamount = Column(Numeric(15, 5))


class Billingrealloc(Base):
    __tablename__ = "billingrealloc"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    counterparty = Column(String(10), primary_key=True, nullable=False)
    value = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class BillingreallocDetail(Base):
    __tablename__ = "billingrealloc_detail"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    counterparty = Column(String(10), primary_key=True, nullable=False)
    reallocationid = Column(String(20), primary_key=True, nullable=False)
    value = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billingregionexport(Base):
    __tablename__ = "billingregionexports"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    exportto = Column(String(10), primary_key=True, nullable=False)
    energy = Column(Numeric(16, 6))
    value = Column(Numeric(15, 5))
    surplusenergy = Column(Numeric(16, 6))
    surplusvalue = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billingregionfigure(Base):
    __tablename__ = "billingregionfigures"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    energyout = Column(Numeric(16, 6))
    valueout = Column(Numeric(16, 6))
    energypurchased = Column(Numeric(16, 6))
    valuepurchased = Column(Numeric(16, 6))
    excessgen = Column(Numeric(16, 6))
    reservetrading = Column(Numeric(16, 6))
    intcompo = Column(Numeric(16, 6))
    adminpricecompo = Column(Numeric(16, 6))
    settsurplus = Column(Numeric(16, 6))
    aspayment = Column(Numeric(16, 6))
    poolfees = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billingregionimport(Base):
    __tablename__ = "billingregionimports"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    importfrom = Column(String(10), primary_key=True, nullable=False)
    energy = Column(Numeric(16, 6))
    value = Column(Numeric(15, 5))
    surplusenergy = Column(Numeric(16, 6))
    surplusvalue = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billingreserverecovery(Base):
    __tablename__ = "billingreserverecovery"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    marketreserve = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billingreserveregionrecovery(Base):
    __tablename__ = "billingreserveregionrecovery"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    regionreserve = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billingreservetrader(Base):
    __tablename__ = "billingreservetrader"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    marketreserve = Column(Numeric(15, 5))
    totalreserve = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    totalcapdifference = Column(Numeric(15, 5))


class Billingreservetraderregion(Base):
    __tablename__ = "billingreservetraderregion"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    regionreserve = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billingruntrk(Base):
    __tablename__ = "billingruntrk"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    status = Column(String(6))
    adj_cleared = Column(String(1))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(10))
    postdate = Column(TIMESTAMP(precision=3))
    postby = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    receiptpostdate = Column(TIMESTAMP(precision=3))
    receiptpostby = Column(String(10))
    paymentpostdate = Column(TIMESTAMP(precision=3))
    paymentpostby = Column(String(10))
    shortfall = Column(Numeric(16, 6))
    makeup = Column(Numeric(15, 5))


class Billingsmelterreduction(Base):
    __tablename__ = "billingsmelterreduction"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(22, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(22, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(22, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    rate1 = Column(Numeric(15, 6))
    ra1 = Column(Numeric(15, 6))
    rate2 = Column(Numeric(15, 6))
    ra2 = Column(Numeric(15, 6))
    te = Column(Numeric(15, 6))
    pcsd = Column(Numeric(15, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billinterventionrecovery(Base):
    __tablename__ = "billinterventionrecovery"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    marketintervention = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billinterventionregionrecovery(Base):
    __tablename__ = "billinterventionregionrecovery"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    regionintervention = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billsmelterrate(Base):
    __tablename__ = "billsmelterrate"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    contractyear = Column(Numeric(22, 0), primary_key=True, nullable=False)
    rar1 = Column(Numeric(6, 2))
    rar2 = Column(Numeric(6, 2))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Billwhitehole(Base):
    __tablename__ = "billwhitehole"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(22, 0), primary_key=True, nullable=False)
    weekno = Column(Numeric(22, 0), primary_key=True, nullable=False)
    billrunno = Column(Numeric(22, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    nl = Column(Numeric(15, 6))
    participantdemand = Column(Numeric(15, 6))
    regiondemand = Column(Numeric(15, 6))
    whiteholepayment = Column(Numeric(15, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)


class Connectionpoint(Base):
    __tablename__ = "connectionpoint"
    __table_args__ = {"schema": "mms"}

    connectionpointid = Column(String(10), primary_key=True)
    connectionpointname = Column(String(80))
    connectionpointtype = Column(String(20))
    address1 = Column(String(80))
    address2 = Column(String(80))
    address3 = Column(String(80))
    address4 = Column(String(80))
    city = Column(String(40))
    state = Column(String(10))
    postcode = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Connectionpointdetail(Base):
    __tablename__ = "connectionpointdetails"
    __table_args__ = (
        Index(
            "connectionpointdetai_ndx2",
            "meterdataprovider",
            "networkserviceprovider",
            "finresporgan",
        ),
        {"schema": "mms"},
    )

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    connectionpointid = Column(String(10), primary_key=True, nullable=False, index=True)
    regionid = Column(String(10))
    transmissioncptid = Column(String(10))
    meterdataprovider = Column(String(10))
    transmissionlossfactor = Column(Numeric(7, 5))
    distributionlossfactor = Column(Numeric(7, 5))
    networkserviceprovider = Column(String(10))
    finresporgan = Column(String(10))
    nationalmeterinstallid = Column(Numeric(7, 5))
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    inuse = Column(String(1))
    lnsp = Column(String(10))
    mda = Column(String(10))
    rolr = Column(String(10))
    rp = Column(String(10))
    aggregateddata = Column(String(1))
    valid_todate = Column(TIMESTAMP(precision=3))
    lr = Column(String(10))


class Connectionpointoperatingsta(Base):
    __tablename__ = "connectionpointoperatingsta"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    connectionpointid = Column(String(10), primary_key=True, nullable=False, index=True)
    operatingstatus = Column(String(16))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class ConstraintrelaxationOcd(Base):
    __tablename__ = "constraintrelaxation_ocd"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    constraintid = Column(String(20), primary_key=True, nullable=False)
    rhs = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False, server_default=text("1"))


class Contractagc(Base):
    __tablename__ = "contractagc"
    __table_args__ = (Index("contractagc_ndx2", "participantid", "contractid"), {"schema": "mms"})

    contractid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    startdate = Column(TIMESTAMP(precision=3))
    enddate = Column(TIMESTAMP(precision=3))
    participantid = Column(String(10))
    duid = Column(String(10))
    crr = Column(Numeric(4, 0))
    crl = Column(Numeric(4, 0))
    rlprice = Column(Numeric(10, 2))
    ccprice = Column(Numeric(10, 2))
    bs = Column(Numeric(10, 2))
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Contractgovernor(Base):
    __tablename__ = "contractgovernor"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    startdate = Column(TIMESTAMP(precision=3))
    enddate = Column(TIMESTAMP(precision=3))
    participantid = Column(String(10), index=True)
    duid = Column(String(10))
    ccprice = Column(Numeric(10, 2))
    lower60secbreakpoint = Column(Numeric(9, 6))
    lower60secmax = Column(Numeric(9, 6))
    lower6secbreakpoint = Column(Numeric(9, 6))
    lower6secmax = Column(Numeric(9, 6))
    raise60secbreakpoint = Column(Numeric(9, 6))
    raise60seccapacity = Column(Numeric(9, 6))
    raise60secmax = Column(Numeric(9, 6))
    raise6secbreakpoint = Column(Numeric(9, 6))
    raise6seccapacity = Column(Numeric(9, 6))
    raise6secmax = Column(Numeric(9, 6))
    price6secraisemandatory = Column(Numeric(16, 6))
    quant6secraisemandatory = Column(Numeric(16, 6))
    price6secraisecontract = Column(Numeric(16, 6))
    quant6secraisecontract = Column(Numeric(16, 6))
    price60secraisemandatory = Column(Numeric(16, 6))
    quant60secraisemandatory = Column(Numeric(16, 6))
    price60secraisecontract = Column(Numeric(16, 6))
    quant60secraisecontract = Column(Numeric(16, 6))
    price6seclowermandatory = Column(Numeric(16, 6))
    quant6seclowermandatory = Column(Numeric(16, 6))
    price6seclowercontract = Column(Numeric(16, 6))
    quant6seclowercontract = Column(Numeric(16, 6))
    price60seclowermandatory = Column(Numeric(16, 6))
    quant60seclowermandatory = Column(Numeric(16, 6))
    price60seclowercontract = Column(Numeric(16, 6))
    quant60seclowercontract = Column(Numeric(16, 6))
    deadbandup = Column(Numeric(4, 2))
    deadbanddown = Column(Numeric(4, 2))
    droop6secraisebreakpoint = Column(Numeric(9, 6))
    droop6secraisecapacity = Column(Numeric(9, 6))
    droop6secraisemax = Column(Numeric(9, 6))
    droop60secraisebreakpoint = Column(Numeric(9, 6))
    droop60secraisecapacity = Column(Numeric(9, 6))
    droop60secraisemax = Column(Numeric(9, 6))
    droop6seclowerbreakpoint = Column(Numeric(9, 6))
    droop6seclowermax = Column(Numeric(9, 6))
    droop60seclowerbreakpoint = Column(Numeric(9, 6))
    droop60seclowermax = Column(Numeric(9, 6))
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Contractloadshed(Base):
    __tablename__ = "contractloadshed"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    startdate = Column(TIMESTAMP(precision=3))
    enddate = Column(TIMESTAMP(precision=3))
    participantid = Column(String(10), index=True)
    duid = Column(String(10))
    lseprice = Column(Numeric(6, 2))
    mcpprice = Column(Numeric(12, 2))
    tenderedprice = Column(Numeric(6, 2))
    lscr = Column(Numeric(6, 2))
    ilscalingfactor = Column(Numeric(15, 5))
    lower60secbreakpoint = Column(Numeric(9, 6))
    lower60secmax = Column(Numeric(9, 6))
    lower6secbreakpoint = Column(Numeric(9, 6))
    lower6secmax = Column(Numeric(9, 6))
    raise60secbreakpoint = Column(Numeric(9, 6))
    raise60seccapacity = Column(Numeric(9, 6))
    raise60secmax = Column(Numeric(9, 6))
    raise6secbreakpoint = Column(Numeric(9, 6))
    raise6seccapacity = Column(Numeric(9, 6))
    raise6secmax = Column(Numeric(9, 6))
    price6secraisemandatory = Column(Numeric(16, 6))
    quant6secraisemandatory = Column(Numeric(9, 6))
    price6secraisecontract = Column(Numeric(16, 6))
    quant6secraisecontract = Column(Numeric(9, 6))
    price60secraisemandatory = Column(Numeric(16, 6))
    quant60secraisemandatory = Column(Numeric(9, 6))
    price60secraisecontract = Column(Numeric(16, 6))
    quant60secraisecontract = Column(Numeric(9, 6))
    price6seclowermandatory = Column(Numeric(16, 6))
    quant6seclowermandatory = Column(Numeric(9, 6))
    price6seclowercontract = Column(Numeric(16, 6))
    quant6seclowercontract = Column(Numeric(9, 6))
    price60seclowermandatory = Column(Numeric(16, 6))
    quant60seclowermandatory = Column(Numeric(9, 6))
    price60seclowercontract = Column(Numeric(16, 6))
    quant60seclowercontract = Column(Numeric(9, 6))
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    default_testingpayment_amount = Column(Numeric(18, 8))
    service_start_date = Column(TIMESTAMP(precision=3))


class Contractreactivepower(Base):
    __tablename__ = "contractreactivepower"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    startdate = Column(TIMESTAMP(precision=3))
    enddate = Column(TIMESTAMP(precision=3))
    participantid = Column(String(10), index=True)
    duid = Column(String(10))
    synccompensation = Column(String(1))
    mvaraprice = Column(Numeric(10, 2))
    mvareprice = Column(Numeric(10, 2))
    mvargprice = Column(Numeric(10, 2))
    ccprice = Column(Numeric(10, 2))
    mta = Column(Numeric(10, 2))
    mtg = Column(Numeric(10, 2))
    mmca = Column(Numeric(10, 2))
    mmcg = Column(Numeric(10, 2))
    eu = Column(Numeric(10, 2))
    pp = Column(Numeric(10, 2))
    bs = Column(Numeric(10, 2))
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    default_testingpayment_amount = Column(Numeric(18, 8))
    service_start_date = Column(TIMESTAMP(precision=3))
    availability_mwh_threshold = Column(Numeric(18, 8))
    mvar_threshold = Column(Numeric(18, 8))
    rebate_cap = Column(Numeric(18, 8))
    rebate_amount_per_mvar = Column(Numeric(18, 8))
    isrebateapplicable = Column(Numeric(1, 0))


class Contractreserveflag(Base):
    __tablename__ = "contractreserveflag"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    rcf = Column(CHAR(1))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Contractreservethreshold(Base):
    __tablename__ = "contractreservethreshold"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    cra = Column(Numeric(16, 6))
    cre = Column(Numeric(16, 6))
    cru = Column(Numeric(16, 6))
    cta = Column(Numeric(16, 6))
    cte = Column(Numeric(16, 6))
    ctu = Column(Numeric(16, 6))
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Contractreservetrader(Base):
    __tablename__ = "contractreservetrader"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True)
    duid = Column(String(10))
    startdate = Column(TIMESTAMP(precision=3))
    enddate = Column(TIMESTAMP(precision=3))
    startperiod = Column(Numeric(3, 0))
    endperiod = Column(Numeric(3, 0))
    deregistrationdate = Column(TIMESTAMP(precision=3))
    deregistrationperiod = Column(Numeric(3, 0))
    participantid = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    regionid = Column(String(10))


class Contractrestartservice(Base):
    __tablename__ = "contractrestartservices"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    startdate = Column(TIMESTAMP(precision=3))
    enddate = Column(TIMESTAMP(precision=3))
    participantid = Column(String(10), index=True)
    restarttype = Column(Numeric(1, 0))
    rcprice = Column(Numeric(6, 2))
    triptohouselevel = Column(Numeric(5, 0))
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    default_testingpayment_amount = Column(Numeric(18, 8))
    service_start_date = Column(TIMESTAMP(precision=3))


class Contractrestartunit(Base):
    __tablename__ = "contractrestartunits"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True, nullable=False, index=True)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))


class Contractunitloading(Base):
    __tablename__ = "contractunitloading"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    startdate = Column(TIMESTAMP(precision=3))
    enddate = Column(TIMESTAMP(precision=3))
    participantid = Column(String(10), index=True)
    duid = Column(String(10))
    rprice = Column(Numeric(10, 2))
    suprice = Column(Numeric(10, 2))
    ccprice = Column(Numeric(10, 2))
    acr = Column(Numeric(10, 2))
    bs = Column(Numeric(10, 2))
    pp = Column(Numeric(10, 2))
    eu = Column(Numeric(10, 2))
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Contractunitunloading(Base):
    __tablename__ = "contractunitunloading"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    startdate = Column(TIMESTAMP(precision=3))
    enddate = Column(TIMESTAMP(precision=3))
    participantid = Column(String(10), index=True)
    duid = Column(String(10))
    rprice = Column(Numeric(10, 2))
    suprice = Column(Numeric(10, 2))
    ccprice = Column(Numeric(10, 2))
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Dayoffer(Base):
    __tablename__ = "dayoffer"
    __table_args__ = (Index("dayoffer_ndx2", "duid", "lastchanged"), {"schema": "mms"})

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    offerdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    selfcommitflag = Column(String(1))
    dailyenergyconstraint = Column(Numeric(12, 6))
    entrytype = Column(String(20))
    contingencyprice = Column(Numeric(9, 2))
    rebidexplanation = Column(String(64))
    bandquantisationid = Column(Numeric(2, 0))
    priceband1 = Column(Numeric(9, 2))
    priceband2 = Column(Numeric(9, 2))
    priceband3 = Column(Numeric(9, 2))
    priceband4 = Column(Numeric(9, 2))
    priceband5 = Column(Numeric(9, 2))
    priceband6 = Column(Numeric(9, 2))
    priceband7 = Column(Numeric(9, 2))
    priceband8 = Column(Numeric(9, 2))
    priceband9 = Column(Numeric(9, 2))
    priceband10 = Column(Numeric(9, 2))
    maxrampup = Column(Numeric(9, 2))
    maxrampdown = Column(Numeric(9, 2))
    minimumload = Column(Numeric(6, 0))
    t1 = Column(Numeric(6, 0))
    t2 = Column(Numeric(6, 0))
    t3 = Column(Numeric(6, 0))
    t4 = Column(Numeric(6, 0))
    normalstatus = Column(String(3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    mr_factor = Column(Numeric(16, 6))


class DayofferD(Base):
    __tablename__ = "dayoffer_d"
    __table_args__ = (Index("dayoffer_d_ndx2", "duid", "lastchanged"), {"schema": "mms"})

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    offerdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    selfcommitflag = Column(String(1))
    dailyenergyconstraint = Column(Numeric(12, 6))
    entrytype = Column(String(20))
    contingencyprice = Column(Numeric(9, 2))
    rebidexplanation = Column(String(64))
    bandquantisationid = Column(Numeric(2, 0))
    priceband1 = Column(Numeric(9, 2))
    priceband2 = Column(Numeric(9, 2))
    priceband3 = Column(Numeric(9, 2))
    priceband4 = Column(Numeric(9, 2))
    priceband5 = Column(Numeric(9, 2))
    priceband6 = Column(Numeric(9, 2))
    priceband7 = Column(Numeric(9, 2))
    priceband8 = Column(Numeric(9, 2))
    priceband9 = Column(Numeric(9, 2))
    priceband10 = Column(Numeric(9, 2))
    maxrampup = Column(Numeric(9, 2))
    maxrampdown = Column(Numeric(9, 2))
    minimumload = Column(Numeric(6, 0))
    t1 = Column(Numeric(6, 0))
    t2 = Column(Numeric(6, 0))
    t3 = Column(Numeric(6, 0))
    t4 = Column(Numeric(6, 0))
    normalstatus = Column(String(3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    mr_factor = Column(Numeric(6, 0))


class Daytrack(Base):
    __tablename__ = "daytrack"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(10))
    exanterunstatus = Column(String(15))
    exanterunno = Column(Numeric(3, 0))
    expostrunstatus = Column(String(15))
    expostrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Defaultdayoffer(Base):
    __tablename__ = "defaultdayoffer"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    selfcommitflag = Column(String(1))
    dailyenergyconstraint = Column(Numeric(12, 6))
    entrytype = Column(String(20))
    contingencyprice = Column(Numeric(9, 2))
    rebidexplanation = Column(String(64))
    bandquantisationid = Column(Numeric(2, 0))
    priceband1 = Column(Numeric(9, 2))
    priceband2 = Column(Numeric(9, 2))
    priceband3 = Column(Numeric(9, 2))
    priceband4 = Column(Numeric(9, 2))
    priceband5 = Column(Numeric(9, 2))
    priceband6 = Column(Numeric(9, 2))
    priceband7 = Column(Numeric(9, 2))
    priceband8 = Column(Numeric(9, 2))
    priceband9 = Column(Numeric(9, 2))
    priceband10 = Column(Numeric(9, 2))
    maxrampup = Column(Numeric(9, 2))
    maxrampdown = Column(Numeric(9, 2))
    minimumload = Column(Numeric(6, 0))
    t1 = Column(Numeric(6, 0))
    t2 = Column(Numeric(6, 0))
    t3 = Column(Numeric(6, 0))
    t4 = Column(Numeric(6, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Defaultoffertrk(Base):
    __tablename__ = "defaultoffertrk"
    __table_args__ = {"schema": "mms"}

    duid = Column(String(10), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    filename = Column(String(40))
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Defaultperoffer(Base):
    __tablename__ = "defaultperoffer"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    selfdispatch = Column(Numeric(9, 6))
    maxavail = Column(Numeric(12, 6))
    fixedload = Column(Numeric(9, 6))
    rocup = Column(Numeric(6, 0))
    rocdown = Column(Numeric(6, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    bandavail1 = Column(Numeric(6, 0))
    bandavail2 = Column(Numeric(6, 0))
    bandavail3 = Column(Numeric(6, 0))
    bandavail4 = Column(Numeric(6, 0))
    bandavail5 = Column(Numeric(6, 0))
    bandavail6 = Column(Numeric(6, 0))
    bandavail7 = Column(Numeric(6, 0))
    bandavail8 = Column(Numeric(6, 0))
    bandavail9 = Column(Numeric(6, 0))
    bandavail10 = Column(Numeric(6, 0))
    pasaavailability = Column(Numeric(12, 0))


class Deltamw(Base):
    __tablename__ = "deltamw"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(2, 0), primary_key=True, nullable=False)
    deltamw = Column(Numeric(6, 0))
    lower5min = Column(Numeric(6, 0))
    lower60sec = Column(Numeric(6, 0))
    lower6sec = Column(Numeric(6, 0))
    raise5min = Column(Numeric(6, 0))
    raise60sec = Column(Numeric(6, 0))
    raise6sec = Column(Numeric(6, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    raisereg = Column(Numeric(6, 0))
    lowerreg = Column(Numeric(6, 0))


class Demandoperationalactual(Base):
    __tablename__ = "demandoperationalactual"
    __table_args__ = {"schema": "mms"}

    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    operational_demand = Column(Numeric(10, 0))
    lastchanged = Column(TIMESTAMP(precision=3))


class Demandoperationalforecast(Base):
    __tablename__ = "demandoperationalforecast"
    __table_args__ = {"schema": "mms"}

    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    load_date = Column(TIMESTAMP(precision=3))
    operational_demand_poe10 = Column(Numeric(15, 2))
    operational_demand_poe50 = Column(Numeric(15, 2))
    operational_demand_poe90 = Column(Numeric(15, 2))
    lastchanged = Column(TIMESTAMP(precision=3))


class DispatchConstraintFcasOcd(Base):
    __tablename__ = "dispatch_constraint_fcas_ocd"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    intervention = Column(Numeric(2, 0), primary_key=True, nullable=False)
    constraintid = Column(String(20), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    rhs = Column(Numeric(15, 5))
    marginalvalue = Column(Numeric(15, 5))
    violationdegree = Column(Numeric(15, 5))


class DispatchFcasReq(Base):
    __tablename__ = "dispatch_fcas_req"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    intervention = Column(Numeric(2, 0), primary_key=True, nullable=False)
    genconid = Column(String(20), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    bidtype = Column(String(10), primary_key=True, nullable=False)
    genconeffectivedate = Column(TIMESTAMP(precision=3))
    genconversionno = Column(Numeric(3, 0))
    marginalvalue = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    base_cost = Column(Numeric(18, 8))
    adjusted_cost = Column(Numeric(18, 8))
    estimated_cmpf = Column(Numeric(18, 8))
    estimated_crmpf = Column(Numeric(18, 8))
    recovery_factor_cmpf = Column(Numeric(18, 8))
    recovery_factor_crmpf = Column(Numeric(18, 8))


class DispatchInterconnection(Base):
    __tablename__ = "dispatch_interconnection"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    intervention = Column(Numeric(2, 0), primary_key=True, nullable=False)
    from_regionid = Column(String(20), primary_key=True, nullable=False)
    to_regionid = Column(String(20), primary_key=True, nullable=False)
    dispatchinterval = Column(Numeric(22, 0))
    irlf = Column(Numeric(15, 5))
    mwflow = Column(Numeric(16, 6))
    meteredmwflow = Column(Numeric(16, 6))
    from_region_mw_losses = Column(Numeric(16, 6))
    to_region_mw_losses = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3))


class DispatchLocalPrice(Base):
    __tablename__ = "dispatch_local_price"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20), primary_key=True, nullable=False)
    local_price_adjustment = Column(Numeric(10, 2))
    locally_constrained = Column(Numeric(1, 0))


class DispatchMnspbidtrk(Base):
    __tablename__ = "dispatch_mnspbidtrk"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    linkid = Column(String(10), primary_key=True, nullable=False)
    offersettlementdate = Column(TIMESTAMP(precision=3))
    offereffectivedate = Column(TIMESTAMP(precision=3))
    offerversionno = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class DispatchMrScheduleTrk(Base):
    __tablename__ = "dispatch_mr_schedule_trk"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    mr_date = Column(TIMESTAMP(precision=3))
    version_datetime = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class DispatchPriceRevision(Base):
    __tablename__ = "dispatch_price_revision"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    intervention = Column(Numeric(2, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    bidtype = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    rrp_new = Column(Numeric(15, 5))
    rrp_old = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class DispatchUnitConformance(Base):
    __tablename__ = "dispatch_unit_conformance"
    __table_args__ = {"schema": "mms"}

    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20), primary_key=True, nullable=False)
    totalcleared = Column(Numeric(16, 6))
    actualmw = Column(Numeric(16, 6))
    roc = Column(Numeric(16, 6))
    availability = Column(Numeric(16, 6))
    lowerreg = Column(Numeric(16, 6))
    raisereg = Column(Numeric(16, 6))
    striglm = Column(Numeric(16, 6))
    ltriglm = Column(Numeric(16, 6))
    mwerror = Column(Numeric(16, 6))
    max_mwerror = Column(Numeric(16, 6))
    lecount = Column(Numeric(6, 0))
    secount = Column(Numeric(6, 0))
    status = Column(String(20))
    participant_status_action = Column(String(100))
    operating_mode = Column(String(20))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class DispatchUnitScada(Base):
    __tablename__ = "dispatch_unit_scada"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20), primary_key=True, nullable=False)
    scadavalue = Column(Numeric(16, 6))


class Dispatchableunit(Base):
    __tablename__ = "dispatchableunit"
    __table_args__ = {"schema": "mms"}

    duid = Column(String(10), primary_key=True)
    duname = Column(String(20))
    unittype = Column(String(20))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Dispatchbidtrk(Base):
    __tablename__ = "dispatchbidtrk"
    __table_args__ = (Index("dispatchbidtrk_ndx2", "duid", "lastchanged"), {"schema": "mms"})

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    offereffectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    offerversionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    bidtype = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Dispatchblockedconstraint(Base):
    __tablename__ = "dispatchblockedconstraint"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    constraintid = Column(String(20), primary_key=True, nullable=False)


class DispatchcaseOcd(Base):
    __tablename__ = "dispatchcase_ocd"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Dispatchcasesolution(Base):
    __tablename__ = "dispatchcasesolution"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    intervention = Column(Numeric(2, 0), nullable=False)
    casesubtype = Column(String(3))
    solutionstatus = Column(Numeric(2, 0))
    spdversion = Column(String(20))
    nonphysicallosses = Column(Numeric(1, 0))
    totalobjective = Column(Numeric(27, 10))
    totalareagenviolation = Column(Numeric(15, 5))
    totalinterconnectorviolation = Column(Numeric(15, 5))
    totalgenericviolation = Column(Numeric(15, 5))
    totalramprateviolation = Column(Numeric(15, 5))
    totalunitmwcapacityviolation = Column(Numeric(15, 5))
    total5minviolation = Column(Numeric(15, 5))
    totalregviolation = Column(Numeric(15, 5))
    total6secviolation = Column(Numeric(15, 5))
    total60secviolation = Column(Numeric(15, 5))
    totalasprofileviolation = Column(Numeric(15, 5))
    totalfaststartviolation = Column(Numeric(15, 5))
    totalenergyofferviolation = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    switchruninitialstatus = Column(Numeric(1, 0))
    switchrunbeststatus = Column(Numeric(1, 0))
    switchrunbeststatus_int = Column(Numeric(1, 0))


class DispatchcasesolutionBnc(Base):
    __tablename__ = "dispatchcasesolution_bnc"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    intervention = Column(Numeric(2, 0), primary_key=True, nullable=False)
    casesubtype = Column(String(3))
    solutionstatus = Column(Numeric(2, 0))
    spdversion = Column(Numeric(10, 3))
    startperiod = Column(String(20))
    nonphysicallosses = Column(Numeric(1, 0))
    totalobjective = Column(Numeric(27, 10))
    totalareagenviolation = Column(Numeric(15, 5))
    totalinterconnectorviolation = Column(Numeric(15, 5))
    totalgenericviolation = Column(Numeric(15, 5))
    totalramprateviolation = Column(Numeric(15, 5))
    totalunitmwcapacityviolation = Column(Numeric(15, 5))
    total5minviolation = Column(Numeric(15, 5))
    totalregviolation = Column(Numeric(15, 5))
    total6secviolation = Column(Numeric(15, 5))
    total60secviolation = Column(Numeric(15, 5))
    totalenergyconstrviolation = Column(Numeric(15, 5))
    totalenergyofferviolation = Column(Numeric(15, 5))
    totalasprofileviolation = Column(Numeric(15, 5))
    totalfaststartviolation = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Dispatchconstraint(Base):
    __tablename__ = "dispatchconstraint"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False, index=True)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    constraintid = Column(String(20), primary_key=True, nullable=False)
    dispatchinterval = Column(Numeric(22, 0), primary_key=True, nullable=False)
    intervention = Column(Numeric(2, 0), primary_key=True, nullable=False)
    rhs = Column(Numeric(15, 5))
    marginalvalue = Column(Numeric(15, 5))
    violationdegree = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    duid = Column(String(20))
    genconid_effectivedate = Column(TIMESTAMP(precision=3))
    genconid_versionno = Column(Numeric(22, 0))
    lhs = Column(Numeric(15, 5))


class Dispatchinterconnectorre(Base):
    __tablename__ = "dispatchinterconnectorres"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    dispatchinterval = Column(Numeric(22, 0), primary_key=True, nullable=False)
    intervention = Column(Numeric(2, 0), primary_key=True, nullable=False)
    meteredmwflow = Column(Numeric(15, 5))
    mwflow = Column(Numeric(15, 5))
    mwlosses = Column(Numeric(15, 5))
    marginalvalue = Column(Numeric(15, 5))
    violationdegree = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    exportlimit = Column(Numeric(15, 5))
    importlimit = Column(Numeric(15, 5))
    marginalloss = Column(Numeric(15, 5))
    exportgenconid = Column(String(20))
    importgenconid = Column(String(20))
    fcasexportlimit = Column(Numeric(15, 5))
    fcasimportlimit = Column(Numeric(15, 5))
    local_price_adjustment_export = Column(Numeric(10, 2))
    locally_constrained_export = Column(Numeric(1, 0))
    local_price_adjustment_import = Column(Numeric(10, 2))
    locally_constrained_import = Column(Numeric(1, 0))


class Dispatchload(Base):
    __tablename__ = "dispatchload"
    __table_args__ = (Index("dispatchload_ndx2", "duid", "lastchanged"), {"schema": "mms"})

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    tradetype = Column(Numeric(2, 0))
    dispatchinterval = Column(Numeric(22, 0))
    intervention = Column(Numeric(2, 0), primary_key=True, nullable=False)
    connectionpointid = Column(String(12))
    dispatchmode = Column(Numeric(2, 0))
    agcstatus = Column(Numeric(2, 0))
    initialmw = Column(Numeric(15, 5))
    totalcleared = Column(Numeric(15, 5))
    rampdownrate = Column(Numeric(15, 5))
    rampuprate = Column(Numeric(15, 5))
    lower5min = Column(Numeric(15, 5))
    lower60sec = Column(Numeric(15, 5))
    lower6sec = Column(Numeric(15, 5))
    raise5min = Column(Numeric(15, 5))
    raise60sec = Column(Numeric(15, 5))
    raise6sec = Column(Numeric(15, 5))
    downepf = Column(Numeric(15, 5))
    upepf = Column(Numeric(15, 5))
    marginal5minvalue = Column(Numeric(15, 5))
    marginal60secvalue = Column(Numeric(15, 5))
    marginal6secvalue = Column(Numeric(15, 5))
    marginalvalue = Column(Numeric(15, 5))
    violation5mindegree = Column(Numeric(15, 5))
    violation60secdegree = Column(Numeric(15, 5))
    violation6secdegree = Column(Numeric(15, 5))
    violationdegree = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    lowerreg = Column(Numeric(15, 5))
    raisereg = Column(Numeric(15, 5))
    availability = Column(Numeric(15, 5))
    raise6secflags = Column(Numeric(3, 0))
    raise60secflags = Column(Numeric(3, 0))
    raise5minflags = Column(Numeric(3, 0))
    raiseregflags = Column(Numeric(3, 0))
    lower6secflags = Column(Numeric(3, 0))
    lower60secflags = Column(Numeric(3, 0))
    lower5minflags = Column(Numeric(3, 0))
    lowerregflags = Column(Numeric(3, 0))
    raiseregavailability = Column(Numeric(15, 5))
    raiseregenablementmax = Column(Numeric(15, 5))
    raiseregenablementmin = Column(Numeric(15, 5))
    lowerregavailability = Column(Numeric(15, 5))
    lowerregenablementmax = Column(Numeric(15, 5))
    lowerregenablementmin = Column(Numeric(15, 5))
    raise6secactualavailability = Column(Numeric(16, 6))
    raise60secactualavailability = Column(Numeric(16, 6))
    raise5minactualavailability = Column(Numeric(16, 6))
    raiseregactualavailability = Column(Numeric(16, 6))
    lower6secactualavailability = Column(Numeric(16, 6))
    lower60secactualavailability = Column(Numeric(16, 6))
    lower5minactualavailability = Column(Numeric(16, 6))
    lowerregactualavailability = Column(Numeric(16, 6))
    semidispatchcap = Column(Numeric(3, 0))


class DispatchloadBnc(Base):
    __tablename__ = "dispatchload_bnc"
    __table_args__ = (Index("dispatchload_bnc_ndx2", "duid", "lastchanged"), {"schema": "mms"})

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    intervention = Column(Numeric(2, 0), primary_key=True, nullable=False)
    connectionpointid = Column(String(12))
    dispatchmode = Column(Numeric(2, 0))
    totalcleared = Column(Numeric(15, 5))
    raisereg = Column(Numeric(15, 5))
    raise5min = Column(Numeric(15, 5))
    raise60sec = Column(Numeric(15, 5))
    raise6sec = Column(Numeric(15, 5))
    lowerreg = Column(Numeric(15, 5))
    lower5min = Column(Numeric(15, 5))
    lower60sec = Column(Numeric(15, 5))
    lower6sec = Column(Numeric(15, 5))
    raiseregflags = Column(Numeric(3, 0))
    raise5minflags = Column(Numeric(3, 0))
    raise60secflags = Column(Numeric(3, 0))
    raise6secflags = Column(Numeric(3, 0))
    lowerregflags = Column(Numeric(3, 0))
    lower5minflags = Column(Numeric(3, 0))
    lower60secflags = Column(Numeric(3, 0))
    lower6secflags = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Dispatchoffertrk(Base):
    __tablename__ = "dispatchoffertrk"
    __table_args__ = (Index("dispatchoffertrk_ndx2", "duid", "lastchanged"), {"schema": "mms"})

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    bidtype = Column(String(10), primary_key=True, nullable=False)
    bidsettlementdate = Column(TIMESTAMP(precision=3))
    bidofferdate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Dispatchprice(Base):
    __tablename__ = "dispatchprice"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    dispatchinterval = Column(String(22), primary_key=True, nullable=False)
    intervention = Column(Numeric(2, 0), primary_key=True, nullable=False)
    rrp = Column(Numeric(15, 5))
    eep = Column(Numeric(15, 5))
    rop = Column(Numeric(15, 5))
    apcflag = Column(Numeric(3, 0))
    marketsuspendedflag = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    raise6secrrp = Column(Numeric(15, 5))
    raise6secrop = Column(Numeric(15, 5))
    raise6secapcflag = Column(Numeric(3, 0))
    raise60secrrp = Column(Numeric(15, 5))
    raise60secrop = Column(Numeric(15, 5))
    raise60secapcflag = Column(Numeric(3, 0))
    raise5minrrp = Column(Numeric(15, 5))
    raise5minrop = Column(Numeric(15, 5))
    raise5minapcflag = Column(Numeric(3, 0))
    raiseregrrp = Column(Numeric(15, 5))
    raiseregrop = Column(Numeric(15, 5))
    raiseregapcflag = Column(Numeric(3, 0))
    lower6secrrp = Column(Numeric(15, 5))
    lower6secrop = Column(Numeric(15, 5))
    lower6secapcflag = Column(Numeric(3, 0))
    lower60secrrp = Column(Numeric(15, 5))
    lower60secrop = Column(Numeric(15, 5))
    lower60secapcflag = Column(Numeric(3, 0))
    lower5minrrp = Column(Numeric(15, 5))
    lower5minrop = Column(Numeric(15, 5))
    lower5minapcflag = Column(Numeric(3, 0))
    lowerregrrp = Column(Numeric(15, 5))
    lowerregrop = Column(Numeric(15, 5))
    lowerregapcflag = Column(Numeric(3, 0))
    price_status = Column(String(20))
    pre_ap_energy_price = Column(Numeric(15, 5))
    pre_ap_raise6_price = Column(Numeric(15, 5))
    pre_ap_raise60_price = Column(Numeric(15, 5))
    pre_ap_raise5min_price = Column(Numeric(15, 5))
    pre_ap_raisereg_price = Column(Numeric(15, 5))
    pre_ap_lower6_price = Column(Numeric(15, 5))
    pre_ap_lower60_price = Column(Numeric(15, 5))
    pre_ap_lower5min_price = Column(Numeric(15, 5))
    pre_ap_lowerreg_price = Column(Numeric(15, 5))
    cumul_pre_ap_energy_price = Column(Numeric(15, 5))
    cumul_pre_ap_raise6_price = Column(Numeric(15, 5))
    cumul_pre_ap_raise60_price = Column(Numeric(15, 5))
    cumul_pre_ap_raise5min_price = Column(Numeric(15, 5))
    cumul_pre_ap_raisereg_price = Column(Numeric(15, 5))
    cumul_pre_ap_lower6_price = Column(Numeric(15, 5))
    cumul_pre_ap_lower60_price = Column(Numeric(15, 5))
    cumul_pre_ap_lower5min_price = Column(Numeric(15, 5))
    cumul_pre_ap_lowerreg_price = Column(Numeric(15, 5))
    ocd_status = Column(String(14))
    mii_status = Column(String(21))


class Dispatchregionsum(Base):
    __tablename__ = "dispatchregionsum"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    dispatchinterval = Column(Numeric(22, 0), primary_key=True, nullable=False)
    intervention = Column(Numeric(2, 0), primary_key=True, nullable=False)
    totaldemand = Column(Numeric(15, 5))
    availablegeneration = Column(Numeric(15, 5))
    availableload = Column(Numeric(15, 5))
    demandforecast = Column(Numeric(15, 5))
    dispatchablegeneration = Column(Numeric(15, 5))
    dispatchableload = Column(Numeric(15, 5))
    netinterchange = Column(Numeric(15, 5))
    excessgeneration = Column(Numeric(15, 5))
    lower5mindispatch = Column(Numeric(15, 5))
    lower5minimport = Column(Numeric(15, 5))
    lower5minlocaldispatch = Column(Numeric(15, 5))
    lower5minlocalprice = Column(Numeric(15, 5))
    lower5minlocalreq = Column(Numeric(15, 5))
    lower5minprice = Column(Numeric(15, 5))
    lower5minreq = Column(Numeric(15, 5))
    lower5minsupplyprice = Column(Numeric(15, 5))
    lower60secdispatch = Column(Numeric(15, 5))
    lower60secimport = Column(Numeric(15, 5))
    lower60seclocaldispatch = Column(Numeric(15, 5))
    lower60seclocalprice = Column(Numeric(15, 5))
    lower60seclocalreq = Column(Numeric(15, 5))
    lower60secprice = Column(Numeric(15, 5))
    lower60secreq = Column(Numeric(15, 5))
    lower60secsupplyprice = Column(Numeric(15, 5))
    lower6secdispatch = Column(Numeric(15, 5))
    lower6secimport = Column(Numeric(15, 5))
    lower6seclocaldispatch = Column(Numeric(15, 5))
    lower6seclocalprice = Column(Numeric(15, 5))
    lower6seclocalreq = Column(Numeric(15, 5))
    lower6secprice = Column(Numeric(15, 5))
    lower6secreq = Column(Numeric(15, 5))
    lower6secsupplyprice = Column(Numeric(15, 5))
    raise5mindispatch = Column(Numeric(15, 5))
    raise5minimport = Column(Numeric(15, 5))
    raise5minlocaldispatch = Column(Numeric(15, 5))
    raise5minlocalprice = Column(Numeric(15, 5))
    raise5minlocalreq = Column(Numeric(15, 5))
    raise5minprice = Column(Numeric(15, 5))
    raise5minreq = Column(Numeric(15, 5))
    raise5minsupplyprice = Column(Numeric(15, 5))
    raise60secdispatch = Column(Numeric(15, 5))
    raise60secimport = Column(Numeric(15, 5))
    raise60seclocaldispatch = Column(Numeric(15, 5))
    raise60seclocalprice = Column(Numeric(15, 5))
    raise60seclocalreq = Column(Numeric(15, 5))
    raise60secprice = Column(Numeric(15, 5))
    raise60secreq = Column(Numeric(15, 5))
    raise60secsupplyprice = Column(Numeric(15, 5))
    raise6secdispatch = Column(Numeric(15, 5))
    raise6secimport = Column(Numeric(15, 5))
    raise6seclocaldispatch = Column(Numeric(15, 5))
    raise6seclocalprice = Column(Numeric(15, 5))
    raise6seclocalreq = Column(Numeric(15, 5))
    raise6secprice = Column(Numeric(15, 5))
    raise6secreq = Column(Numeric(15, 5))
    raise6secsupplyprice = Column(Numeric(15, 5))
    aggegatedispatcherror = Column(Numeric(15, 5))
    aggregatedispatcherror = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    initialsupply = Column(Numeric(15, 5))
    clearedsupply = Column(Numeric(15, 5))
    lowerregimport = Column(Numeric(15, 5))
    lowerreglocaldispatch = Column(Numeric(15, 5))
    lowerreglocalreq = Column(Numeric(15, 5))
    lowerregreq = Column(Numeric(15, 5))
    raiseregimport = Column(Numeric(15, 5))
    raisereglocaldispatch = Column(Numeric(15, 5))
    raisereglocalreq = Column(Numeric(15, 5))
    raiseregreq = Column(Numeric(15, 5))
    raise5minlocalviolation = Column(Numeric(15, 5))
    raisereglocalviolation = Column(Numeric(15, 5))
    raise60seclocalviolation = Column(Numeric(15, 5))
    raise6seclocalviolation = Column(Numeric(15, 5))
    lower5minlocalviolation = Column(Numeric(15, 5))
    lowerreglocalviolation = Column(Numeric(15, 5))
    lower60seclocalviolation = Column(Numeric(15, 5))
    lower6seclocalviolation = Column(Numeric(15, 5))
    raise5minviolation = Column(Numeric(15, 5))
    raiseregviolation = Column(Numeric(15, 5))
    raise60secviolation = Column(Numeric(15, 5))
    raise6secviolation = Column(Numeric(15, 5))
    lower5minviolation = Column(Numeric(15, 5))
    lowerregviolation = Column(Numeric(15, 5))
    lower60secviolation = Column(Numeric(15, 5))
    lower6secviolation = Column(Numeric(15, 5))
    raise6secactualavailability = Column(Numeric(16, 6))
    raise60secactualavailability = Column(Numeric(16, 6))
    raise5minactualavailability = Column(Numeric(16, 6))
    raiseregactualavailability = Column(Numeric(16, 6))
    lower6secactualavailability = Column(Numeric(16, 6))
    lower60secactualavailability = Column(Numeric(16, 6))
    lower5minactualavailability = Column(Numeric(16, 6))
    lowerregactualavailability = Column(Numeric(16, 6))
    lorsurplus = Column(Numeric(16, 6))
    lrcsurplus = Column(Numeric(16, 6))
    totalintermittentgeneration = Column(Numeric(15, 5))
    demand_and_nonschedgen = Column(Numeric(15, 5))
    uigf = Column(Numeric(15, 5))
    semischedule_clearedmw = Column(Numeric(15, 5))
    semischedule_compliancemw = Column(Numeric(15, 5))
    ss_solar_uigf = Column(Numeric(15, 5))
    ss_wind_uigf = Column(Numeric(15, 5))
    ss_solar_clearedmw = Column(Numeric(15, 5))
    ss_wind_clearedmw = Column(Numeric(15, 5))
    ss_solar_compliancemw = Column(Numeric(15, 5))
    ss_wind_compliancemw = Column(Numeric(15, 5))


class Dispatchtrk(Base):
    __tablename__ = "dispatchtrk"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    reason = Column(String(64))
    spdrunno = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Dualloc(Base):
    __tablename__ = "dualloc"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False, index=True)
    gensetid = Column(String(20), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Dudetail(Base):
    __tablename__ = "dudetail"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    connectionpointid = Column(String(10))
    voltlevel = Column(String(10))
    registeredcapacity = Column(Numeric(6, 0))
    agccapability = Column(String(1))
    dispatchtype = Column(String(10))
    maxcapacity = Column(Numeric(6, 0))
    starttype = Column(String(20))
    normallyonflag = Column(String(1))
    physicaldetailsflag = Column(String(1))
    spinningreserveflag = Column(String(1))
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    intermittentflag = Column(String(1))
    semischedule_flag = Column(String(1))
    maxrateofchangeup = Column(Numeric(6, 0), nullable=True)
    maxrateofchangedown = Column(Numeric(6, 0), nullable=True)


class Dudetailsummary(Base):
    __tablename__ = "dudetailsummary"
    __table_args__ = {"schema": "mms"}

    duid = Column(String(10), primary_key=True, nullable=False)
    start_date = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    end_date = Column(TIMESTAMP(precision=3), nullable=False)
    dispatchtype = Column(String(10))
    connectionpointid = Column(String(10))
    regionid = Column(String(10))
    stationid = Column(String(10))
    participantid = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    transmissionlossfactor = Column(Numeric(15, 5))
    starttype = Column(String(20))
    distributionlossfactor = Column(Numeric(15, 5))
    minimum_energy_price = Column(Numeric(9, 2))
    maximum_energy_price = Column(Numeric(9, 2))
    schedule_type = Column(String(20))
    min_ramp_rate_up = Column(Numeric(6, 0))
    min_ramp_rate_down = Column(Numeric(6, 0))
    max_ramp_rate_up = Column(Numeric(6, 0))
    max_ramp_rate_down = Column(Numeric(6, 0))
    is_aggregated = Column(Numeric(1, 0))


class Emsmaster(Base):
    __tablename__ = "emsmaster"
    __table_args__ = {"schema": "mms"}

    spd_id = Column(String(21), primary_key=True, nullable=False)
    spd_type = Column(String(1), primary_key=True, nullable=False)
    description = Column(String(255))
    grouping_id = Column(String(20))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Forcemajeure(Base):
    __tablename__ = "forcemajeure"
    __table_args__ = {"schema": "mms"}

    fmid = Column(String(10), primary_key=True)
    startdate = Column(TIMESTAMP(precision=3))
    startperiod = Column(Numeric(3, 0))
    enddate = Column(TIMESTAMP(precision=3))
    endperiod = Column(Numeric(3, 0))
    apcstartdate = Column(TIMESTAMP(precision=3))
    startauthorisedby = Column(String(15))
    endauthorisedby = Column(String(15))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Forcemajeureregion(Base):
    __tablename__ = "forcemajeureregion"
    __table_args__ = {"schema": "mms"}

    fmid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Gdinstruct(Base):
    __tablename__ = "gdinstruct"
    __table_args__ = {"schema": "mms"}

    duid = Column(String(10), index=True)
    stationid = Column(String(10))
    regionid = Column(String(10))
    id = Column(Numeric(22, 0), primary_key=True)
    instructiontypeid = Column(String(10))
    instructionsubtypeid = Column(String(10))
    instructionclassid = Column(String(10))
    reason = Column(String(64))
    instlevel = Column(Numeric(6, 0))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    participantid = Column(String(10))
    issuedtime = Column(TIMESTAMP(precision=3))
    targettime = Column(TIMESTAMP(precision=3), index=True)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Gencondatum(Base):
    __tablename__ = "gencondata"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    genconid = Column(String(20), primary_key=True, nullable=False)
    constrainttype = Column(String(2))
    constraintvalue = Column(Numeric(16, 6))
    description = Column(String(256))
    status = Column(String(8))
    genericconstraintweight = Column(Numeric(16, 6))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    dynamicrhs = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    dispatch = Column(String(1))
    predispatch = Column(String(1))
    stpasa = Column(String(1))
    mtpasa = Column(String(1))
    impact = Column(String(64))
    source = Column(String(128))
    limittype = Column(String(64))
    reason = Column(String(256))
    modifications = Column(String(256))
    additionalnotes = Column(String(256))
    p5min_scope_override = Column(String(2))
    lrc = Column(String(1))
    lor = Column(String(1))
    force_scada = Column(Numeric(1, 0))


class Genconset(Base):
    __tablename__ = "genconset"
    __table_args__ = {"schema": "mms"}

    genconsetid = Column(String(20), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    genconid = Column(String(20), primary_key=True, nullable=False)
    genconeffdate = Column(TIMESTAMP(precision=3))
    genconversionno = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Genconsetinvoke(Base):
    __tablename__ = "genconsetinvoke"
    __table_args__ = {"schema": "mms"}

    invocation_id = Column(Numeric(9, 0), primary_key=True)
    startdate = Column(TIMESTAMP(precision=3), nullable=False)
    startperiod = Column(Numeric(3, 0), nullable=False)
    genconsetid = Column(String(20), nullable=False)
    enddate = Column(TIMESTAMP(precision=3))
    endperiod = Column(Numeric(3, 0))
    startauthorisedby = Column(String(15))
    endauthorisedby = Column(String(15))
    intervention = Column(String(1))
    asconstrainttype = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    startintervaldatetime = Column(TIMESTAMP(precision=3))
    endintervaldatetime = Column(TIMESTAMP(precision=3))
    systemnormal = Column(String(1))


class Genconsettrk(Base):
    __tablename__ = "genconsettrk"
    __table_args__ = {"schema": "mms"}

    genconsetid = Column(String(20), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    description = Column(String(256))
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    coverage = Column(String(64))
    modifications = Column(String(256))
    systemnormal = Column(String(1))
    outage = Column(String(256))


class Genericconstraintrh(Base):
    __tablename__ = "genericconstraintrhs"
    __table_args__ = {"schema": "mms"}

    genconid = Column(String(20), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(22, 0), primary_key=True, nullable=False)
    scope = Column(String(2), primary_key=True, nullable=False)
    termid = Column(Numeric(4, 0), primary_key=True, nullable=False)
    groupid = Column(Numeric(3, 0))
    spd_id = Column(String(21))
    spd_type = Column(String(1))
    factor = Column(Numeric(16, 6))
    operation = Column(String(10))
    defaultvalue = Column(Numeric(16, 6))
    parameterterm1 = Column(String(12))
    parameterterm2 = Column(String(12))
    parameterterm3 = Column(String(12))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Genericequationdesc(Base):
    __tablename__ = "genericequationdesc"
    __table_args__ = {"schema": "mms"}

    equationid = Column(String(20), primary_key=True)
    description = Column(String(256))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    impact = Column(String(64))
    source = Column(String(128))
    limittype = Column(String(64))
    reason = Column(String(256))
    modifications = Column(String(256))
    additionalnotes = Column(String(256))


class Genericequationrh(Base):
    __tablename__ = "genericequationrhs"
    __table_args__ = {"schema": "mms"}

    equationid = Column(String(20), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    termid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    groupid = Column(Numeric(3, 0))
    spd_id = Column(String(21))
    spd_type = Column(String(1))
    factor = Column(Numeric(16, 6))
    operation = Column(String(10))
    defaultvalue = Column(Numeric(16, 6))
    parameterterm1 = Column(String(12))
    parameterterm2 = Column(String(12))
    parameterterm3 = Column(String(12))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Genmeter(Base):
    __tablename__ = "genmeter"
    __table_args__ = {"schema": "mms"}

    meterid = Column(String(12), primary_key=True, nullable=False)
    gensetid = Column(String(20))
    connectionpointid = Column(String(10))
    stationid = Column(String(10), index=True)
    metertype = Column(String(20))
    meterclass = Column(String(10))
    voltagelevel = Column(Numeric(6, 0))
    applydate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    authorisedby = Column(String(10))
    authoriseddate = Column(TIMESTAMP(precision=3))
    comdate = Column(TIMESTAMP(precision=3))
    decomdate = Column(TIMESTAMP(precision=3))
    enddate = Column(TIMESTAMP(precision=3))
    startdate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Genunitmtrinperiod(Base):
    __tablename__ = "genunitmtrinperiod"
    __table_args__ = {"schema": "mms"}

    participantid = Column(String(10), primary_key=True, nullable=False)
    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(6, 0), primary_key=True, nullable=False)
    connectionpointid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    genunitid = Column(String(10))
    stationid = Column(String(10), index=True)
    importenergyvalue = Column(Numeric(16, 6))
    exportenergyvalue = Column(Numeric(16, 6))
    importreactivevalue = Column(Numeric(16, 6))
    exportreactivevalue = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    mda = Column(String(10), primary_key=True, nullable=False)
    local_retailer = Column(
        String(10),
        primary_key=True,
        nullable=False,
        server_default=text("'POOLNSW'::character varying"),
    )


class Genunit(Base):
    __tablename__ = "genunits"
    __table_args__ = {"schema": "mms"}

    gensetid = Column(String(20), primary_key=True)
    stationid = Column(String(10))
    setlossfactor = Column(Numeric(16, 6))
    cdindicator = Column(String(10))
    agcflag = Column(String(2))
    spinningflag = Column(String(2))
    voltlevel = Column(Numeric(6, 0))
    registeredcapacity = Column(Numeric(6, 0))
    dispatchtype = Column(String(10))
    starttype = Column(String(20))
    mktgeneratorind = Column(String(10))
    normalstatus = Column(String(10))
    maxcapacity = Column(Numeric(6, 0))
    gensettype = Column(String(15))
    gensetname = Column(String(40))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    co2e_emissions_factor = Column(Numeric(18, 8))
    co2e_energy_source = Column(String(100))
    co2e_data_source = Column(String(20))


class GenunitsUnit(Base):
    __tablename__ = "genunits_unit"
    __table_args__ = {"schema": "mms"}

    gensetid = Column(String(20), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(6, 0), primary_key=True, nullable=False)
    unit_grouping_label = Column(String(20), primary_key=True, nullable=False)
    unit_count = Column(Numeric(3, 0))
    unit_size = Column(Numeric(8, 3))
    unit_max_size = Column(Numeric(8, 3))
    aggregation_flag = Column(Numeric(1, 0))
    lastchanged = Column(TIMESTAMP(precision=3))


class GstBasClas(Base):
    __tablename__ = "gst_bas_class"
    __table_args__ = {"schema": "mms"}

    bas_class = Column(String(30), primary_key=True)
    description = Column(String(100))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class GstRate(Base):
    __tablename__ = "gst_rate"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    bas_class = Column(String(30), primary_key=True, nullable=False)
    gst_rate = Column(Numeric(8, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class GstTransactionClas(Base):
    __tablename__ = "gst_transaction_class"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    transaction_type = Column(String(30), primary_key=True, nullable=False)
    bas_class = Column(String(30), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class GstTransactionType(Base):
    __tablename__ = "gst_transaction_type"
    __table_args__ = {"schema": "mms"}

    transaction_type = Column(String(30), primary_key=True)
    description = Column(String(100))
    gl_financialcode = Column(String(10))
    gl_tcode = Column(String(15))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Instructionsubtype(Base):
    __tablename__ = "instructionsubtype"
    __table_args__ = {"schema": "mms"}

    instructiontypeid = Column(String(10), primary_key=True, nullable=False)
    instructionsubtypeid = Column(String(10), primary_key=True, nullable=False)
    description = Column(String(64))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Instructiontype(Base):
    __tablename__ = "instructiontype"
    __table_args__ = {"schema": "mms"}

    instructiontypeid = Column(String(10), primary_key=True)
    description = Column(String(64))
    regionid = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Intcontract(Base):
    __tablename__ = "intcontract"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True)
    participantid = Column(String(10))
    duid = Column(String(10))
    startdate = Column(TIMESTAMP(precision=3))
    enddate = Column(TIMESTAMP(precision=3))
    startperiod = Column(Numeric(3, 0))
    endperiod = Column(Numeric(3, 0))
    deregistrationdate = Column(TIMESTAMP(precision=3))
    deregistrationperiod = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    regionid = Column(String(10))


class Intcontractamount(Base):
    __tablename__ = "intcontractamount"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    amount = Column(Numeric(16, 6))
    rcf = Column(CHAR(1))
    lastchanged = Column(TIMESTAMP(precision=3), nullable=False, index=True)


class Intcontractamounttrk(Base):
    __tablename__ = "intcontractamounttrk"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Interconnector(Base):
    __tablename__ = "interconnector"
    __table_args__ = {"schema": "mms"}

    interconnectorid = Column(String(10), primary_key=True)
    regionfrom = Column(String(10))
    rsoid = Column(String(10))
    regionto = Column(String(10))
    description = Column(String(64))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Interconnectoralloc(Base):
    __tablename__ = "interconnectoralloc"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(5, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    allocation = Column(Numeric(12, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Interconnectorconstraint(Base):
    __tablename__ = "interconnectorconstraint"
    __table_args__ = {"schema": "mms"}

    reserveoverallloadfactor = Column(Numeric(5, 2))
    fromregionlossshare = Column(Numeric(5, 2))
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    maxmwin = Column(Numeric(15, 5))
    maxmwout = Column(Numeric(15, 5))
    lossconstant = Column(Numeric(15, 6))
    lossflowcoefficient = Column(Numeric(27, 17))
    emsmeasurand = Column(String(40))
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    dynamicrhs = Column(String(1))
    importlimit = Column(Numeric(6, 0))
    exportlimit = Column(Numeric(6, 0))
    outagederationfactor = Column(Numeric(15, 5))
    nonphysicallossfactor = Column(Numeric(15, 5))
    overloadfactor60sec = Column(Numeric(15, 5))
    overloadfactor6sec = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    fcassupportunavailable = Column(Numeric(1, 0))
    ictype = Column(String(10))


class Interconnmwflow(Base):
    __tablename__ = "interconnmwflow"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(6, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    importenergyvalue = Column(Numeric(15, 6))
    exportenergyvalue = Column(Numeric(15, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class IntermittentClusterAvail(Base):
    __tablename__ = "intermittent_cluster_avail"
    __table_args__ = {"schema": "mms"}

    tradingdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20), primary_key=True, nullable=False)
    offerdatetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    clusterid = Column(String(20), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    elements_unavailable = Column(Numeric(3, 0))


class IntermittentClusterAvailDay(Base):
    __tablename__ = "intermittent_cluster_avail_day"
    __table_args__ = {"schema": "mms"}

    tradingdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20), primary_key=True, nullable=False)
    offerdatetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    clusterid = Column(String(20), primary_key=True, nullable=False)


class IntermittentDsPred(Base):
    __tablename__ = "intermittent_ds_pred"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20), primary_key=True, nullable=False)
    offerdatetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    origin = Column(String(20), primary_key=True, nullable=False)
    forecast_priority = Column(Numeric(10, 0), primary_key=True, nullable=False)
    forecast_mean = Column(Numeric(18, 8))
    forecast_poe10 = Column(Numeric(18, 8))
    forecast_poe50 = Column(Numeric(18, 8))
    forecast_poe90 = Column(Numeric(18, 8))


class IntermittentDsRun(Base):
    __tablename__ = "intermittent_ds_run"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20), primary_key=True, nullable=False)
    offerdatetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    origin = Column(String(20), primary_key=True, nullable=False)
    forecast_priority = Column(Numeric(10, 0), primary_key=True, nullable=False)
    authorisedby = Column(String(20))
    comments = Column(String(200))
    lastchanged = Column(TIMESTAMP(precision=3))
    model = Column(String(30))
    participant_timestamp = Column(TIMESTAMP(precision=3))
    suppressed_aemo = Column(Numeric(1, 0))
    suppressed_participant = Column(Numeric(1, 0))
    transaction_id = Column(String(100))


class IntermittentForecastTrk(Base):
    __tablename__ = "intermittent_forecast_trk"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20), primary_key=True, nullable=False)
    origin = Column(String(20))
    forecast_priority = Column(Numeric(10, 0))
    offerdatetime = Column(TIMESTAMP(precision=3))


class IntermittentGenFcst(Base):
    __tablename__ = "intermittent_gen_fcst"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20), primary_key=True, nullable=False)
    start_interval_datetime = Column(TIMESTAMP(precision=3), nullable=False)
    end_interval_datetime = Column(TIMESTAMP(precision=3), nullable=False)
    versionno = Column(Numeric(10, 0))
    lastchanged = Column(TIMESTAMP(precision=3))


class IntermittentGenFcstDatum(Base):
    __tablename__ = "intermittent_gen_fcst_data"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20), primary_key=True, nullable=False)
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    powermean = Column(Numeric(9, 3))
    powerpoe50 = Column(Numeric(9, 3))
    powerpoelow = Column(Numeric(9, 3))
    powerpoehigh = Column(Numeric(9, 3))
    lastchanged = Column(TIMESTAMP(precision=3))


class IntermittentGenLimit(Base):
    __tablename__ = "intermittent_gen_limit"
    __table_args__ = {"schema": "mms"}

    tradingdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20), primary_key=True, nullable=False)
    offerdatetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    uppermwlimit = Column(Numeric(6, 0))


class IntermittentGenLimitDay(Base):
    __tablename__ = "intermittent_gen_limit_day"
    __table_args__ = {"schema": "mms"}

    tradingdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20), primary_key=True, nullable=False)
    offerdatetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    participantid = Column(String(20))
    lastchanged = Column(TIMESTAMP(precision=3))
    authorisedbyuser = Column(String(20))
    authorisedbyparticipantid = Column(String(20))


class IntermittentP5Pred(Base):
    __tablename__ = "intermittent_p5_pred"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20), primary_key=True, nullable=False)
    offerdatetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    origin = Column(String(20), primary_key=True, nullable=False)
    forecast_priority = Column(Numeric(10, 0), primary_key=True, nullable=False)
    forecast_mean = Column(Numeric(18, 8))
    forecast_poe10 = Column(Numeric(18, 8))
    forecast_poe50 = Column(Numeric(18, 8))
    forecast_poe90 = Column(Numeric(18, 8))


class IntermittentP5Run(Base):
    __tablename__ = "intermittent_p5_run"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20), primary_key=True, nullable=False)
    offerdatetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    origin = Column(String(20), primary_key=True, nullable=False)
    forecast_priority = Column(Numeric(10, 0), primary_key=True, nullable=False)
    authorisedby = Column(String(20))
    comments = Column(String(200))
    lastchanged = Column(TIMESTAMP(precision=3))
    model = Column(String(30))
    participant_timestamp = Column(TIMESTAMP(precision=3))
    suppressed_aemo = Column(Numeric(1, 0))
    suppressed_participant = Column(Numeric(1, 0))
    transaction_id = Column(String(100))


class Intraregionalloc(Base):
    __tablename__ = "intraregionalloc"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(5, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    allocation = Column(Numeric(12, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Irfmamount(Base):
    __tablename__ = "irfmamount"
    __table_args__ = {"schema": "mms"}

    irfmid = Column(String(10), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3))
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(4, 0), primary_key=True, nullable=False)
    amount = Column(Numeric(15, 5))
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Irfmevent(Base):
    __tablename__ = "irfmevents"
    __table_args__ = {"schema": "mms"}

    irfmid = Column(String(10), primary_key=True)
    startdate = Column(TIMESTAMP(precision=3))
    startperiod = Column(Numeric(3, 0))
    enddate = Column(TIMESTAMP(precision=3))
    endperiod = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Lossfactormodel(Base):
    __tablename__ = "lossfactormodel"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    demandcoefficient = Column(Numeric(27, 17))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Lossmodel(Base):
    __tablename__ = "lossmodel"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(String(20))
    losssegment = Column(Numeric(6, 0), primary_key=True, nullable=False)
    mwbreakpoint = Column(Numeric(6, 0))
    lossfactor = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class MarketFeeCatExcl(Base):
    __tablename__ = "market_fee_cat_excl"
    __table_args__ = {"schema": "mms"}

    marketfeeid = Column(String(20), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    version_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    participant_categoryid = Column(String(20), primary_key=True, nullable=False)


class MarketFeeCatExclTrk(Base):
    __tablename__ = "market_fee_cat_excl_trk"
    __table_args__ = {"schema": "mms"}

    marketfeeid = Column(String(20), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    version_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3))


class MarketFeeExclusion(Base):
    __tablename__ = "market_fee_exclusion"
    __table_args__ = {"schema": "mms"}

    participantid = Column(String(10), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    marketfeeid = Column(String(10), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class MarketFeeExclusiontrk(Base):
    __tablename__ = "market_fee_exclusiontrk"
    __table_args__ = {"schema": "mms"}

    participantid = Column(String(10), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class MarketPriceThreshold(Base):
    __tablename__ = "market_price_thresholds"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(4, 0), primary_key=True, nullable=False)
    voll = Column(Numeric(15, 5))
    marketpricefloor = Column(Numeric(15, 5))
    administered_price_threshold = Column(Numeric(15, 5))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class MarketSuspendRegimeSum(Base):
    __tablename__ = "market_suspend_regime_sum"
    __table_args__ = {"schema": "mms"}

    suspension_id = Column(String(20), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    start_interval = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    end_interval = Column(TIMESTAMP(precision=3))
    pricing_regime = Column(String(20))
    lastchanged = Column(TIMESTAMP(precision=3))


class MarketSuspendRegionSum(Base):
    __tablename__ = "market_suspend_region_sum"
    __table_args__ = {"schema": "mms"}

    suspension_id = Column(String(20), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    initial_interval = Column(TIMESTAMP(precision=3))
    end_region_interval = Column(TIMESTAMP(precision=3))
    end_suspension_interval = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3))


class MarketSuspendSchedule(Base):
    __tablename__ = "market_suspend_schedule"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    day_type = Column(String(20), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    energy_rrp = Column(Numeric(15, 5))
    r6_rrp = Column(Numeric(15, 5))
    r60_rrp = Column(Numeric(15, 5))
    r5_rrp = Column(Numeric(15, 5))
    rreg_rrp = Column(Numeric(15, 5))
    l6_rrp = Column(Numeric(15, 5))
    l60_rrp = Column(Numeric(15, 5))
    l5_rrp = Column(Numeric(15, 5))
    lreg_rrp = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3))


class MarketSuspendScheduleTrk(Base):
    __tablename__ = "market_suspend_schedule_trk"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True)
    source_start_date = Column(TIMESTAMP(precision=3))
    source_end_date = Column(TIMESTAMP(precision=3))
    comments = Column(String(1000))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3))


class Marketfee(Base):
    __tablename__ = "marketfee"
    __table_args__ = {"schema": "mms"}

    marketfeeid = Column(String(10), primary_key=True)
    marketfeeperiod = Column(String(20))
    marketfeetype = Column(String(12))
    description = Column(String(64))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    gl_tcode = Column(String(15))
    gl_financialcode = Column(String(10))
    fee_class = Column(String(40))


class Marketfeedatum(Base):
    __tablename__ = "marketfeedata"
    __table_args__ = {"schema": "mms"}

    marketfeeid = Column(String(10), primary_key=True, nullable=False)
    marketfeeversionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    marketfeevalue = Column(Numeric(22, 8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Marketfeetrk(Base):
    __tablename__ = "marketfeetrk"
    __table_args__ = {"schema": "mms"}

    marketfeeversionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Marketnoticedatum(Base):
    __tablename__ = "marketnoticedata"
    __table_args__ = {"schema": "mms"}

    noticeid = Column(Numeric(10, 0), primary_key=True)
    effectivedate = Column(TIMESTAMP(precision=3))
    typeid = Column(String(25))
    noticetype = Column(String(25))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    reason = Column(String(2000))
    externalreference = Column(String(255))


class Marketnoticetype(Base):
    __tablename__ = "marketnoticetype"
    __table_args__ = {"schema": "mms"}

    typeid = Column(String(25), primary_key=True)
    description = Column(String(64))
    raisedby = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Marketsuspension(Base):
    __tablename__ = "marketsuspension"
    __table_args__ = {"schema": "mms"}

    suspensionid = Column(String(10), primary_key=True)
    startdate = Column(TIMESTAMP(precision=3))
    startperiod = Column(Numeric(3, 0))
    enddate = Column(TIMESTAMP(precision=3))
    endperiod = Column(Numeric(3, 0))
    reason = Column(String(64))
    startauthorisedby = Column(String(15))
    endauthorisedby = Column(String(15))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Marketsusregion(Base):
    __tablename__ = "marketsusregion"
    __table_args__ = {"schema": "mms"}

    suspensionid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class MasCpChange(Base):
    __tablename__ = "mas_cp_change"
    __table_args__ = {"schema": "mms"}

    nmi = Column(String(10), primary_key=True)
    status_flag = Column(String(1))
    cp_old_security_code = Column(String(4))
    cp_new_security_code = Column(String(4))
    old_local_network_provider = Column(String(10))
    old_local_retailer = Column(String(10))
    old_financial_participant = Column(String(10))
    old_metering_data_agent = Column(String(10))
    old_retailer_of_last_resort = Column(String(10))
    old_responsible_person = Column(String(10))
    new_local_network_provider = Column(String(10))
    new_local_retailer = Column(String(10))
    new_financial_participant = Column(String(10))
    new_metering_data_agent = Column(String(10))
    new_retailer_of_last_resort = Column(String(10))
    new_responsible_person = Column(String(10))
    old_lnsp_ok = Column(String(1))
    old_lr_ok = Column(String(1))
    old_frmp_ok = Column(String(1))
    old_mda_ok = Column(String(1))
    old_rolr_ok = Column(String(1))
    old_rp_ok = Column(String(1))
    new_lnsp_ok = Column(String(1))
    new_lr_ok = Column(String(1))
    new_frmp_ok = Column(String(1))
    new_mda_ok = Column(String(1))
    new_rolr_ok = Column(String(1))
    new_rp_ok = Column(String(1))
    prudential_ok = Column(String(1))
    initial_change_date = Column(TIMESTAMP(precision=3))
    current_change_date = Column(TIMESTAMP(precision=3))
    cp_name = Column(String(30))
    cp_detail_1 = Column(String(30))
    cp_detail_2 = Column(String(30))
    city_suburb = Column(String(30))
    state = Column(String(3))
    post_code = Column(String(4))
    tx_node = Column(String(4))
    aggregate_data = Column(String(1))
    average_daily_load_kwh = Column(Numeric(8, 0))
    distribution_loss = Column(Numeric(5, 4))
    old_lsnp_text = Column(String(30))
    old_lr_text = Column(String(30))
    old_frmp_text = Column(String(30))
    old_mda_text = Column(String(30))
    old_rolr_text = Column(String(30))
    old_rp_text = Column(String(30))
    new_lsnp_text = Column(String(30))
    new_lr_text = Column(String(30))
    new_frmp_text = Column(String(30))
    new_mda_text = Column(String(30))
    new_rolr_text = Column(String(30))
    new_rp_text = Column(String(30))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    nmi_class = Column(String(9))
    metering_type = Column(String(9))
    jurisdiction = Column(String(3))
    create_date = Column(TIMESTAMP(precision=3))
    expiry_date = Column(TIMESTAMP(precision=3))
    meter_read_date = Column(TIMESTAMP(precision=3))


class MasCpMaster(Base):
    __tablename__ = "mas_cp_master"
    __table_args__ = (UniqueConstraint("nmi", "valid_to_date"), {"schema": "mms"})

    nmi = Column(String(10), primary_key=True, nullable=False)
    cp_security_code = Column(String(4))
    in_use = Column(String(1))
    valid_from_date = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    valid_to_date = Column(TIMESTAMP(precision=3), nullable=False)
    local_network_provider = Column(String(10))
    local_retailer = Column(String(10))
    financial_participant = Column(String(10))
    metering_data_agent = Column(String(10))
    retailer_of_last_resort = Column(String(10))
    responsible_person = Column(String(10))
    cp_name = Column(String(30))
    cp_detail_1 = Column(String(30))
    cp_detail_2 = Column(String(30))
    city_suburb = Column(String(30))
    state = Column(String(3))
    post_code = Column(String(4))
    tx_node = Column(String(4))
    aggregate_data = Column(String(1))
    average_daily_load_kwh = Column(Numeric(8, 0))
    distribution_loss = Column(Numeric(5, 4))
    lsnp_text = Column(String(30))
    lr_text = Column(String(30))
    frmp_text = Column(String(30))
    mda_text = Column(String(30))
    rolr_text = Column(String(30))
    rp_text = Column(String(30))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    nmi_class = Column(String(9))
    metering_type = Column(String(9))
    jurisdiction = Column(String(3))


class MccCasesolution(Base):
    __tablename__ = "mcc_casesolution"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True)


class MccConstraintsolution(Base):
    __tablename__ = "mcc_constraintsolution"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    constraintid = Column(String(20), primary_key=True, nullable=False)
    rhs = Column(Numeric(15, 5))
    marginalvalue = Column(Numeric(15, 5))


class Meterdatum(Base):
    __tablename__ = "meterdata"
    __table_args__ = {"schema": "mms"}

    participantid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    meterrunno = Column(Numeric(6, 0), primary_key=True, nullable=False)
    connectionpointid = Column(String(10), primary_key=True, nullable=False)
    importenergyvalue = Column(Numeric(9, 6))
    exportenergyvalue = Column(Numeric(9, 6))
    importreactivevalue = Column(Numeric(9, 6))
    exportreactivevalue = Column(Numeric(9, 6))
    hostdistributor = Column(String(10), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    mda = Column(String(10), primary_key=True, nullable=False)


class MeterdataAggregateRead(Base):
    __tablename__ = "meterdata_aggregate_reads"
    __table_args__ = {"schema": "mms"}

    case_id = Column(Numeric(15, 0), primary_key=True, nullable=False)
    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    connectionpointid = Column(String(20), primary_key=True, nullable=False)
    meter_type = Column(String(20), primary_key=True, nullable=False)
    frmp = Column(String(20), primary_key=True, nullable=False)
    lr = Column(String(20), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    importvalue = Column(Numeric(18, 8), nullable=False)
    exportvalue = Column(Numeric(18, 8), nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3))


class MeterdataGenDuid(Base):
    __tablename__ = "meterdata_gen_duid"
    __table_args__ = {"schema": "mms"}

    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    mwh_reading = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class MeterdataIndividualRead(Base):
    __tablename__ = "meterdata_individual_reads"
    __table_args__ = {"schema": "mms"}

    case_id = Column(Numeric(15, 0), primary_key=True, nullable=False)
    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    meter_id = Column(String(20), primary_key=True, nullable=False)
    meter_id_suffix = Column(String(20), primary_key=True, nullable=False)
    frmp = Column(String(20), nullable=False)
    lr = Column(String(20), nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    connectionpointid = Column(String(20), nullable=False)
    meter_type = Column(String(20), nullable=False)
    importvalue = Column(Numeric(18, 8), nullable=False)
    exportvalue = Column(Numeric(18, 8), nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3))


class MeterdataInterconnector(Base):
    __tablename__ = "meterdata_interconnector"
    __table_args__ = {"schema": "mms"}

    case_id = Column(Numeric(15, 0), primary_key=True, nullable=False)
    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    interconnectorid = Column(String(20), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    importvalue = Column(Numeric(18, 8))
    exportvalue = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3))


class MeterdataTrk(Base):
    __tablename__ = "meterdata_trk"
    __table_args__ = {"schema": "mms"}

    case_id = Column(Numeric(15, 0), primary_key=True)
    aggregate_reads_load_datetime = Column(TIMESTAMP(precision=3))
    individual_reads_load_datetime = Column(TIMESTAMP(precision=3))
    startdate = Column(TIMESTAMP(precision=3))
    enddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3))


class Meterdatatrk(Base):
    __tablename__ = "meterdatatrk"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    meterrunno = Column(Numeric(6, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    filename = Column(String(40))
    ackfilename = Column(String(40))
    connectionpointid = Column(String(10), primary_key=True, nullable=False)
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    meteringdataagent = Column(String(10), primary_key=True, nullable=False)
    hostdistributor = Column(String(10), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class MmsDataModelAudit(Base):
    __tablename__ = "mms_data_model_audit"
    __table_args__ = {"schema": "mms"}

    installation_date = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    mmsdm_version = Column(String(20), primary_key=True, nullable=False)
    install_type = Column(String(10), primary_key=True, nullable=False)
    script_version = Column(String(20))
    nem_change_notice = Column(String(20))
    project_title = Column(String(200))
    username = Column(String(40))
    status = Column(String(10))


class MnspDayoffer(Base):
    __tablename__ = "mnsp_dayoffer"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    offerdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    linkid = Column(String(10), primary_key=True, nullable=False)
    entrytype = Column(String(20))
    rebidexplanation = Column(String(500))
    priceband1 = Column(Numeric(9, 2))
    priceband2 = Column(Numeric(9, 2))
    priceband3 = Column(Numeric(9, 2))
    priceband4 = Column(Numeric(9, 2))
    priceband5 = Column(Numeric(9, 2))
    priceband6 = Column(Numeric(9, 2))
    priceband7 = Column(Numeric(9, 2))
    priceband8 = Column(Numeric(9, 2))
    priceband9 = Column(Numeric(9, 2))
    priceband10 = Column(Numeric(9, 2))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    mr_factor = Column(Numeric(16, 6))


class MnspFiletrk(Base):
    __tablename__ = "mnsp_filetrk"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    offerdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    filename = Column(String(40), primary_key=True, nullable=False)
    status = Column(String(10))
    ackfilename = Column(String(40))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class MnspInterconnector(Base):
    __tablename__ = "mnsp_interconnector"
    __table_args__ = {"schema": "mms"}

    linkid = Column(String(10), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10))
    fromregion = Column(String(10))
    toregion = Column(String(10))
    maxcapacity = Column(Numeric(5, 0))
    tlf = Column(Numeric(12, 7))
    lhsfactor = Column(Numeric(12, 7))
    meterflowconstant = Column(Numeric(12, 7))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    from_region_tlf = Column(Numeric(12, 7))
    to_region_tlf = Column(Numeric(12, 7))


class MnspOffertrk(Base):
    __tablename__ = "mnsp_offertrk"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    offerdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    filename = Column(String(40), primary_key=True, nullable=False)
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class MnspParticipant(Base):
    __tablename__ = "mnsp_participant"
    __table_args__ = {"schema": "mms"}

    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class MnspPeroffer(Base):
    __tablename__ = "mnsp_peroffer"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    offerdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    linkid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(22, 0), primary_key=True, nullable=False)
    maxavail = Column(Numeric(6, 0))
    bandavail1 = Column(Numeric(6, 0))
    bandavail2 = Column(Numeric(6, 0))
    bandavail3 = Column(Numeric(6, 0))
    bandavail4 = Column(Numeric(6, 0))
    bandavail5 = Column(Numeric(6, 0))
    bandavail6 = Column(Numeric(6, 0))
    bandavail7 = Column(Numeric(6, 0))
    bandavail8 = Column(Numeric(6, 0))
    bandavail9 = Column(Numeric(6, 0))
    bandavail10 = Column(Numeric(6, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    fixedload = Column(Numeric(12, 6))
    rampuprate = Column(Numeric(6, 0))
    pasaavailability = Column(Numeric(12, 0))
    mr_capacity = Column(Numeric(6, 0))


class MrDayofferStack(Base):
    __tablename__ = "mr_dayoffer_stack"
    __table_args__ = {"schema": "mms"}

    mr_date = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    version_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    stack_position = Column(Numeric(3, 0), primary_key=True, nullable=False)
    duid = Column(String(10))
    authorised = Column(Numeric(1, 0))
    offer_settlementdate = Column(TIMESTAMP(precision=3))
    offer_offerdate = Column(TIMESTAMP(precision=3))
    offer_versionno = Column(Numeric(3, 0))
    offer_type = Column(String(20))
    laof = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class MrEvent(Base):
    __tablename__ = "mr_event"
    __table_args__ = {"schema": "mms"}

    mr_date = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    description = Column(String(200))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(20))
    offer_cut_off_time = Column(TIMESTAMP(precision=3))
    settlement_complete = Column(Numeric(1, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class MrEventSchedule(Base):
    __tablename__ = "mr_event_schedule"
    __table_args__ = {"schema": "mms"}

    mr_date = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    version_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    demand_effectivedate = Column(TIMESTAMP(precision=3))
    demand_offerdate = Column(TIMESTAMP(precision=3))
    demand_versionno = Column(Numeric(3, 0))
    authorisedby = Column(String(20))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class MrPerofferStack(Base):
    __tablename__ = "mr_peroffer_stack"
    __table_args__ = {"schema": "mms"}

    mr_date = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    version_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    stack_position = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    duid = Column(String(10))
    accepted_capacity = Column(Numeric(6, 0))
    deducted_capacity = Column(Numeric(6, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class MtpasaCaseSet(Base):
    __tablename__ = "mtpasa_case_set"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    run_no = Column(Numeric(3, 0), primary_key=True, nullable=False)
    casesetid = Column(Numeric(3, 0))
    runtypeid = Column(Numeric(1, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class MtpasaCaseresult(Base):
    __tablename__ = "mtpasa_caseresult"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    run_no = Column(Numeric(4, 0), primary_key=True, nullable=False)
    plexos_version = Column(String(20))
    lastchanged = Column(TIMESTAMP(precision=3))


class MtpasaCasesolution(Base):
    __tablename__ = "mtpasa_casesolution"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    run_no = Column(Numeric(3, 0), primary_key=True, nullable=False)
    pasaversion = Column(String(10))
    reservecondition = Column(Numeric(1, 0))
    lorcondition = Column(Numeric(1, 0))
    capacityobjfunction = Column(Numeric(12, 3))
    capacityoption = Column(Numeric(12, 3))
    maxsurplusreserveoption = Column(Numeric(12, 3))
    maxsparecapacityoption = Column(Numeric(12, 3))
    interconnectorflowpenalty = Column(Numeric(12, 3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    runtype = Column(String(50))
    reliabilitylrcdemandoption = Column(Numeric(12, 3))
    outagelrcdemandoption = Column(Numeric(12, 3))
    lordemandoption = Column(Numeric(12, 3))
    reliabilitylrccapacityoption = Column(String(10))
    outagelrccapacityoption = Column(String(10))
    lorcapacityoption = Column(String(10))
    loruigfoption = Column(Numeric(3, 0))
    reliabilitylrcuigfoption = Column(Numeric(3, 0))
    outagelrcuigfoption = Column(Numeric(3, 0))


class MtpasaConstraintresult(Base):
    __tablename__ = "mtpasa_constraintresult"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    run_no = Column(Numeric(4, 0), primary_key=True, nullable=False)
    runtype = Column(String(20), primary_key=True, nullable=False)
    demand_poe_type = Column(String(20), primary_key=True, nullable=False)
    day = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    constraintid = Column(String(20), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3))
    versionno = Column(Numeric(3, 0))
    periodid = Column(Numeric(3, 0))
    probabilityofbinding = Column(Numeric(8, 5))
    probabilityofviolation = Column(Numeric(8, 5))
    constraintviolation90 = Column(Numeric(12, 2))
    constraintviolation50 = Column(Numeric(12, 2))
    constraintviolation10 = Column(Numeric(12, 2))
    lastchanged = Column(TIMESTAMP(precision=3))


class MtpasaConstraintsolution(Base):
    __tablename__ = "mtpasa_constraintsolution"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    run_no = Column(Numeric(3, 0), primary_key=True, nullable=False)
    energyblock = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    day = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    ldcblock = Column(Numeric(3, 0), primary_key=True, nullable=False)
    constraintid = Column(String(20), primary_key=True, nullable=False)
    capacityrhs = Column(Numeric(12, 2))
    capacitymarginalvalue = Column(Numeric(12, 2))
    capacityviolationdegree = Column(Numeric(12, 2))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    runtype = Column(
        String(20),
        primary_key=True,
        nullable=False,
        server_default=text("'OUTAGE_LRC'::character varying"),
    )


class MtpasaConstraintsummary(Base):
    __tablename__ = "mtpasa_constraintsummary"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    run_no = Column(Numeric(4, 0), primary_key=True, nullable=False)
    runtype = Column(String(20), primary_key=True, nullable=False)
    demand_poe_type = Column(String(20), primary_key=True, nullable=False)
    day = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    constraintid = Column(String(20), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3))
    versionno = Column(Numeric(3, 0))
    aggregation_period = Column(String(20), primary_key=True, nullable=False)
    constrainthoursbinding = Column(Numeric(12, 2))
    lastchanged = Column(TIMESTAMP(precision=3))


class MtpasaInterconnectorresult(Base):
    __tablename__ = "mtpasa_interconnectorresult"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    run_no = Column(Numeric(4, 0), primary_key=True, nullable=False)
    runtype = Column(String(20), primary_key=True, nullable=False)
    demand_poe_type = Column(String(20), primary_key=True, nullable=False)
    day = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    interconnectorid = Column(String(20), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0))
    flow90 = Column(Numeric(12, 2))
    flow50 = Column(Numeric(12, 2))
    flow10 = Column(Numeric(12, 2))
    probabilityofbindingexport = Column(Numeric(8, 5))
    probabilityofbindingimport = Column(Numeric(8, 5))
    calculatedexportlimit = Column(Numeric(12, 2))
    calculatedimportlimit = Column(Numeric(12, 2))
    lastchanged = Column(TIMESTAMP(precision=3))


class MtpasaInterconnectorsolution(Base):
    __tablename__ = "mtpasa_interconnectorsolution"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    run_no = Column(Numeric(3, 0), primary_key=True, nullable=False)
    energyblock = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    day = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    ldcblock = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    capacitymwflow = Column(Numeric(12, 2))
    capacitymarginalvalue = Column(Numeric(12, 2))
    capacityviolationdegree = Column(Numeric(12, 2))
    calculatedexportlimit = Column(Numeric(12, 2))
    calculatedimportlimit = Column(Numeric(12, 2))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    runtype = Column(
        String(20),
        primary_key=True,
        nullable=False,
        server_default=text("'OUTAGE_LRC'::character varying"),
    )
    exportlimitconstraintid = Column(String(20))
    importlimitconstraintid = Column(String(20))


class MtpasaIntermittentAvail(Base):
    __tablename__ = "mtpasa_intermittent_avail"
    __table_args__ = {"schema": "mms"}

    tradingdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20), primary_key=True, nullable=False)
    offerdatetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    clusterid = Column(String(20), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3))
    elements_unavailable = Column(Numeric(3, 0))


class MtpasaIntermittentLimit(Base):
    __tablename__ = "mtpasa_intermittent_limit"
    __table_args__ = {"schema": "mms"}

    tradingdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20), primary_key=True, nullable=False)
    offerdatetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3))
    uppermwlimit = Column(Numeric(6, 0))
    authorisedbyuser = Column(String(20))
    authorisedbyparticipantid = Column(String(20))


class MtpasaLolpresult(Base):
    __tablename__ = "mtpasa_lolpresult"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    run_no = Column(Numeric(4, 0), primary_key=True, nullable=False)
    runtype = Column(String(20), primary_key=True, nullable=False)
    day = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    worst_interval_periodid = Column(Numeric(3, 0))
    worst_interval_demand = Column(Numeric(12, 2))
    worst_interval_intgen = Column(Numeric(12, 2))
    worst_interval_dsp = Column(Numeric(12, 2))
    lossofloadprobability = Column(Numeric(8, 5))
    lossofloadmagnitude = Column(String(20))
    lastchanged = Column(TIMESTAMP(precision=3))


class MtpasaOfferdatum(Base):
    __tablename__ = "mtpasa_offerdata"
    __table_args__ = {"schema": "mms"}

    participantid = Column(String(20), primary_key=True, nullable=False)
    offerdatetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    unitid = Column(String(20), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    energy = Column(Numeric(9, 0))
    capacity1 = Column(Numeric(9, 0))
    capacity2 = Column(Numeric(9, 0))
    capacity3 = Column(Numeric(9, 0))
    capacity4 = Column(Numeric(9, 0))
    capacity5 = Column(Numeric(9, 0))
    capacity6 = Column(Numeric(9, 0))
    capacity7 = Column(Numeric(9, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class MtpasaOfferfiletrk(Base):
    __tablename__ = "mtpasa_offerfiletrk"
    __table_args__ = {"schema": "mms"}

    participantid = Column(String(20), primary_key=True, nullable=False)
    offerdatetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    filename = Column(String(200))


class MtpasaRegionavailTrk(Base):
    __tablename__ = "mtpasa_regionavail_trk"
    __table_args__ = {"schema": "mms"}

    publish_datetime = Column(TIMESTAMP(precision=3), primary_key=True)
    startdate = Column(TIMESTAMP(precision=3))
    enddate = Column(TIMESTAMP(precision=3))
    latest_offer_datetime = Column(TIMESTAMP(precision=3))


class MtpasaRegionavailability(Base):
    __tablename__ = "mtpasa_regionavailability"
    __table_args__ = {"schema": "mms"}

    publish_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    day = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    pasaavailability_scheduled = Column(Numeric(12, 0))
    latest_offer_datetime = Column(TIMESTAMP(precision=3))
    energyunconstrainedcapacity = Column(Numeric(12, 0))
    energyconstrainedcapacity = Column(Numeric(12, 0))
    nonscheduledgeneration = Column(Numeric(12, 2))
    demand10 = Column(Numeric(12, 2))
    demand50 = Column(Numeric(12, 2))
    energyreqdemand10 = Column(Numeric(12, 2))
    energyreqdemand50 = Column(Numeric(12, 2))
    lastchanged = Column(TIMESTAMP(precision=3))


class MtpasaRegioniteration(Base):
    __tablename__ = "mtpasa_regioniteration"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    run_no = Column(Numeric(4, 0), primary_key=True, nullable=False)
    runtype = Column(String(20), primary_key=True, nullable=False)
    demand_poe_type = Column(String(20), primary_key=True, nullable=False)
    aggregation_period = Column(String(20), primary_key=True, nullable=False)
    period_ending = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    use_iteration_id = Column(Numeric(5, 0), primary_key=True, nullable=False)
    use_iteration_event_number = Column(Numeric(12, 2))
    use_iteration_event_average = Column(Numeric(12, 2))
    lastchanged = Column(TIMESTAMP(precision=3))


class MtpasaRegionresult(Base):
    __tablename__ = "mtpasa_regionresult"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    run_no = Column(Numeric(4, 0), primary_key=True, nullable=False)
    runtype = Column(String(20), primary_key=True, nullable=False)
    demand_poe_type = Column(String(20), primary_key=True, nullable=False)
    day = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0))
    demand = Column(Numeric(12, 2))
    aggregateinstalledcapacity = Column(Numeric(12, 2))
    numberofiterations = Column(Numeric(12, 2))
    use_numberofiterations = Column(Numeric(12, 2))
    use_max = Column(Numeric(12, 2))
    use_upperquartile = Column(Numeric(12, 2))
    use_median = Column(Numeric(12, 2))
    use_lowerquartile = Column(Numeric(12, 2))
    use_min = Column(Numeric(12, 2))
    use_average = Column(Numeric(12, 2))
    use_event_average = Column(Numeric(12, 2))
    totalscheduledgen90 = Column(Numeric(12, 2))
    totalscheduledgen50 = Column(Numeric(12, 2))
    totalscheduledgen10 = Column(Numeric(12, 2))
    totalintermittentgen90 = Column(Numeric(12, 2))
    totalintermittentgen50 = Column(Numeric(12, 2))
    totalintermittentgen10 = Column(Numeric(12, 2))
    demandsideparticipation90 = Column(Numeric(12, 2))
    demandsideparticipation50 = Column(Numeric(12, 2))
    demandsideparticipation10 = Column(Numeric(12, 2))
    lastchanged = Column(TIMESTAMP(precision=3))
    totalsemischedulegen90 = Column(Numeric(12, 2))
    totalsemischedulegen50 = Column(Numeric(12, 2))
    totalsemischedulegen10 = Column(Numeric(12, 2))


class MtpasaRegionsolution(Base):
    __tablename__ = "mtpasa_regionsolution"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    run_no = Column(Numeric(3, 0), primary_key=True, nullable=False)
    energyblock = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    day = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    ldcblock = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    demand10 = Column(Numeric(12, 2))
    reservereq = Column(Numeric(12, 2))
    capacityreq = Column(Numeric(12, 2))
    energyreqdemand10 = Column(Numeric(12, 2))
    unconstrainedcapacity = Column(Numeric(12, 0))
    constrainedcapacity = Column(Numeric(12, 0))
    netinterchangeunderscarcity = Column(Numeric(12, 2))
    surpluscapacity = Column(Numeric(12, 2))
    surplusreserve = Column(Numeric(12, 2))
    reservecondition = Column(Numeric(1, 0))
    maxsurplusreserve = Column(Numeric(12, 2))
    maxsparecapacity = Column(Numeric(12, 2))
    lorcondition = Column(Numeric(1, 0))
    aggregatecapacityavailable = Column(Numeric(12, 2))
    aggregatescheduledload = Column(Numeric(12, 2))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    aggregatepasaavailability = Column(Numeric(12, 0))
    runtype = Column(
        String(20),
        primary_key=True,
        nullable=False,
        server_default=text("'OUTAGE_LRC'::character varying"),
    )
    calculatedlor1level = Column(Numeric(16, 6))
    calculatedlor2level = Column(Numeric(16, 6))
    msrnetinterchangeunderscarcity = Column(Numeric(12, 2))
    lornetinterchangeunderscarcity = Column(Numeric(12, 2))
    totalintermittentgeneration = Column(Numeric(15, 5))
    demand50 = Column(Numeric(12, 2))
    demand_and_nonschedgen = Column(Numeric(15, 5))
    uigf = Column(Numeric(12, 2))
    semischeduledcapacity = Column(Numeric(12, 2))
    lor_semischeduledcapacity = Column(Numeric(12, 2))
    deficitreserve = Column(Numeric(16, 6))
    maxusefulresponse = Column(Numeric(12, 2))
    murnetinterchangeunderscarcity = Column(Numeric(12, 2))
    lortotalintermittentgeneration = Column(Numeric(15, 5))
    energyreqdemand50 = Column(Numeric(12, 2))


class MtpasaRegionsummary(Base):
    __tablename__ = "mtpasa_regionsummary"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    run_no = Column(Numeric(4, 0), primary_key=True, nullable=False)
    runtype = Column(String(20), primary_key=True, nullable=False)
    demand_poe_type = Column(String(20), primary_key=True, nullable=False)
    aggregation_period = Column(String(20), primary_key=True, nullable=False)
    period_ending = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    nativedemand = Column(Numeric(12, 2))
    use_percentile10 = Column(Numeric(12, 2))
    use_percentile20 = Column(Numeric(12, 2))
    use_percentile30 = Column(Numeric(12, 2))
    use_percentile40 = Column(Numeric(12, 2))
    use_percentile50 = Column(Numeric(12, 2))
    use_percentile60 = Column(Numeric(12, 2))
    use_percentile70 = Column(Numeric(12, 2))
    use_percentile80 = Column(Numeric(12, 2))
    use_percentile90 = Column(Numeric(12, 2))
    use_percentile100 = Column(Numeric(12, 2))
    use_average = Column(Numeric(12, 2))
    numberofiterations = Column(Numeric(12, 2))
    use_numberofiterations = Column(Numeric(12, 2))
    use_event_max = Column(Numeric(12, 2))
    use_event_upperquartile = Column(Numeric(12, 2))
    use_event_median = Column(Numeric(12, 2))
    use_event_lowerquartile = Column(Numeric(12, 2))
    use_event_min = Column(Numeric(12, 2))
    weight = Column(Numeric(16, 6))
    use_weighted_avg = Column(Numeric(16, 6))
    lrc = Column(Numeric(12, 2))
    lastchanged = Column(TIMESTAMP(precision=3))


class MtpasaReservelimit(Base):
    __tablename__ = "mtpasa_reservelimit"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    version_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    reservelimitid = Column(String(20), primary_key=True, nullable=False)
    description = Column(String(200))
    rhs = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3))


class MtpasaReservelimitRegion(Base):
    __tablename__ = "mtpasa_reservelimit_region"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    version_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    reservelimitid = Column(String(20), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    coef = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3))


class MtpasaReservelimitSet(Base):
    __tablename__ = "mtpasa_reservelimit_set"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    version_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    reservelimit_set_id = Column(String(20))
    description = Column(String(200))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(20))
    lastchanged = Column(TIMESTAMP(precision=3))


class MtpasaReservelimitsolution(Base):
    __tablename__ = "mtpasa_reservelimitsolution"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    run_no = Column(Numeric(3, 0), primary_key=True, nullable=False)
    runtype = Column(String(20), primary_key=True, nullable=False)
    energyblock = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    day = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    ldcblock = Column(Numeric(3, 0), primary_key=True, nullable=False)
    reservelimitid = Column(String(20), primary_key=True, nullable=False)
    marginalvalue = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3))


class MtpasaconstraintsolutionD(Base):
    __tablename__ = "mtpasaconstraintsolution_d"
    __table_args__ = {"schema": "mms"}

    datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    constraint_id = Column(String(20), primary_key=True, nullable=False)
    degree_of_violation = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    run_datetime = Column(TIMESTAMP(precision=3))


class MtpasainterconnectorsolutionD(Base):
    __tablename__ = "mtpasainterconnectorsolution_d"
    __table_args__ = {"schema": "mms"}

    datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    interconnector_id = Column(String(12), primary_key=True, nullable=False)
    positive_interconnector_flow = Column(Numeric(16, 6))
    positive_transfer_limits = Column(Numeric(16, 6))
    positive_binding = Column(String(10))
    negative_interconnector_flow = Column(Numeric(16, 6))
    negative_transfer_limits = Column(Numeric(16, 6))
    negative_binding = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    run_datetime = Column(TIMESTAMP(precision=3))


class MtpasaregionsolutionD(Base):
    __tablename__ = "mtpasaregionsolution_d"
    __table_args__ = {"schema": "mms"}

    datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    region_id = Column(String(12), primary_key=True, nullable=False)
    run_datetime = Column(TIMESTAMP(precision=3))
    reserve_condition = Column(String(50))
    reserve_surplus = Column(Numeric(16, 6))
    capacity_requirement = Column(Numeric(16, 6))
    minimum_reserve_requirement = Column(Numeric(16, 6))
    region_demand_10poe = Column(Numeric(16, 6))
    demand_minus_scheduled_load = Column(Numeric(16, 6))
    constrained_capacity = Column(Numeric(16, 6))
    unconstrained_capacity = Column(Numeric(16, 6))
    net_interchange = Column(Numeric(16, 6))
    energy_requirement_10poe = Column(Numeric(16, 6))
    reported_block_id = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class NegativeResidue(Base):
    __tablename__ = "negative_residue"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    nrm_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    directional_interconnectorid = Column(String(30), primary_key=True, nullable=False)
    nrm_activated_flag = Column(Numeric(1, 0))
    cumul_negresidue_amount = Column(Numeric(15, 5))
    cumul_negresidue_prev_ti = Column(Numeric(15, 5))
    negresidue_current_ti = Column(Numeric(15, 5))
    negresidue_pd_next_ti = Column(Numeric(15, 5))
    price_revision = Column(String(30))
    predispatchseqno = Column(String(20))
    event_activated_di = Column(TIMESTAMP(precision=3))
    event_deactivated_di = Column(TIMESTAMP(precision=3))
    di_notbinding_count = Column(Numeric(2, 0))
    di_violated_count = Column(Numeric(2, 0))
    nrmconstraint_blocked_flag = Column(Numeric(1, 0))


class NetworkEquipmentdetail(Base):
    __tablename__ = "network_equipmentdetail"
    __table_args__ = {"schema": "mms"}

    substationid = Column(String(30), primary_key=True, nullable=False)
    equipmenttype = Column(String(10), primary_key=True, nullable=False)
    equipmentid = Column(String(30), primary_key=True, nullable=False)
    validfrom = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    validto = Column(TIMESTAMP(precision=3))
    voltage = Column(String(20))
    description = Column(String(100))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class NetworkOutageconstraintset(Base):
    __tablename__ = "network_outageconstraintset"
    __table_args__ = {"schema": "mms"}

    outageid = Column(Numeric(15, 0), primary_key=True, nullable=False)
    genconsetid = Column(String(50), primary_key=True, nullable=False)
    startinterval = Column(TIMESTAMP(precision=3))
    endinterval = Column(TIMESTAMP(precision=3))


class NetworkOutagedetail(Base):
    __tablename__ = "network_outagedetail"
    __table_args__ = {"schema": "mms"}

    outageid = Column(Numeric(15, 0), primary_key=True, nullable=False)
    substationid = Column(String(30), primary_key=True, nullable=False)
    equipmenttype = Column(String(10), primary_key=True, nullable=False)
    equipmentid = Column(String(30), primary_key=True, nullable=False)
    starttime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    endtime = Column(TIMESTAMP(precision=3))
    submitteddate = Column(TIMESTAMP(precision=3))
    outagestatuscode = Column(String(10))
    resubmitreason = Column(String(50))
    resubmitoutageid = Column(Numeric(15, 0))
    recalltimeday = Column(Numeric(10, 0))
    recalltimenight = Column(Numeric(10, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    reason = Column(String(100))
    issecondary = Column(Numeric(1, 0))
    actual_starttime = Column(TIMESTAMP(precision=3))
    actual_endtime = Column(TIMESTAMP(precision=3))
    companyrefcode = Column(String(20))


class NetworkOutagestatuscode(Base):
    __tablename__ = "network_outagestatuscode"
    __table_args__ = {"schema": "mms"}

    outagestatuscode = Column(String(10), primary_key=True)
    description = Column(String(100))
    lastchanged = Column(TIMESTAMP(precision=3))


class NetworkRating(Base):
    __tablename__ = "network_rating"
    __table_args__ = {"schema": "mms"}

    spd_id = Column(String(21), primary_key=True, nullable=False)
    validfrom = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    validto = Column(TIMESTAMP(precision=3))
    regionid = Column(String(10))
    substationid = Column(String(30))
    equipmenttype = Column(String(10))
    equipmentid = Column(String(30))
    ratinglevel = Column(String(10))
    isdynamic = Column(Numeric(1, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class NetworkRealtimerating(Base):
    __tablename__ = "network_realtimerating"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    spd_id = Column(String(21), primary_key=True, nullable=False)
    ratingvalue = Column(Numeric(16, 6), nullable=False)


class NetworkStaticrating(Base):
    __tablename__ = "network_staticrating"
    __table_args__ = {"schema": "mms"}

    substationid = Column(String(30), primary_key=True, nullable=False)
    equipmenttype = Column(String(10), primary_key=True, nullable=False)
    equipmentid = Column(String(30), primary_key=True, nullable=False)
    ratinglevel = Column(String(10), primary_key=True, nullable=False)
    applicationid = Column(String(20), primary_key=True, nullable=False)
    validfrom = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    validto = Column(TIMESTAMP(precision=3))
    ratingvalue = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class NetworkSubstationdetail(Base):
    __tablename__ = "network_substationdetail"
    __table_args__ = {"schema": "mms"}

    substationid = Column(String(30), primary_key=True, nullable=False)
    validfrom = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    validto = Column(TIMESTAMP(precision=3))
    description = Column(String(100))
    regionid = Column(String(10))
    ownerid = Column(String(30))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Oartrack(Base):
    __tablename__ = "oartrack"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    offerdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    filename = Column(String(40))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Offeragcdatum(Base):
    __tablename__ = "offeragcdata"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True, nullable=False, index=True)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    availability = Column(Numeric(4, 0))
    upperlimit = Column(Numeric(4, 0))
    lowerlimit = Column(Numeric(4, 0))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    filename = Column(String(40))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    agcup = Column(Numeric(3, 0))
    agcdown = Column(Numeric(3, 0))


class Offerastrk(Base):
    __tablename__ = "offerastrk"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    filename = Column(String(40))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Offerfiletrk(Base):
    __tablename__ = "offerfiletrk"
    __table_args__ = {"schema": "mms"}

    offerdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    status = Column(String(10))
    ackfilename = Column(String(40))
    enddate = Column(TIMESTAMP(precision=3))
    filename = Column(String(40), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Offergovdatum(Base):
    __tablename__ = "offergovdata"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True, nullable=False, index=True)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    sec6availup = Column(Numeric(6, 0))
    sec6availdown = Column(Numeric(6, 0))
    sec60availup = Column(Numeric(6, 0))
    sec60availdown = Column(Numeric(6, 0))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    filename = Column(String(40))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Offerlsheddatum(Base):
    __tablename__ = "offerlsheddata"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    availableload = Column(Numeric(4, 0))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    filename = Column(String(40))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)


class Offerrestartdatum(Base):
    __tablename__ = "offerrestartdata"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True, nullable=False)
    offerdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    availability = Column(String(3))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    filename = Column(String(40))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)


class Offerrpowerdatum(Base):
    __tablename__ = "offerrpowerdata"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True, nullable=False, index=True)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    availability = Column(Numeric(3, 0))
    mta = Column(Numeric(6, 0))
    mtg = Column(Numeric(6, 0))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    filename = Column(String(40))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Offeruloadingdatum(Base):
    __tablename__ = "offeruloadingdata"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True, nullable=False, index=True)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    availableload = Column(Numeric(4, 0))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    filename = Column(String(40))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)


class Offerunloadingdatum(Base):
    __tablename__ = "offerunloadingdata"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(10), primary_key=True, nullable=False, index=True)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    availableload = Column(Numeric(4, 0))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    filename = Column(String(40))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)


class Overriderrp(Base):
    __tablename__ = "overriderrp"
    __table_args__ = {"schema": "mms"}

    regionid = Column(String(10), primary_key=True, nullable=False)
    startdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    startperiod = Column(Numeric(3, 0), primary_key=True, nullable=False)
    enddate = Column(TIMESTAMP(precision=3))
    endperiod = Column(Numeric(3, 0))
    rrp = Column(Numeric(15, 0))
    description = Column(String(128))
    authorisestart = Column(String(15))
    authoriseend = Column(String(15))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class P5minBlockedconstraint(Base):
    __tablename__ = "p5min_blockedconstraint"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    constraintid = Column(String(20), primary_key=True, nullable=False)


class P5minCasesolution(Base):
    __tablename__ = "p5min_casesolution"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True)
    startinterval_datetime = Column(String(20))
    totalobjective = Column(Numeric(27, 10))
    nonphysicallosses = Column(Numeric(1, 0))
    totalareagenviolation = Column(Numeric(15, 5))
    totalinterconnectorviolation = Column(Numeric(15, 5))
    totalgenericviolation = Column(Numeric(15, 5))
    totalramprateviolation = Column(Numeric(15, 5))
    totalunitmwcapacityviolation = Column(Numeric(15, 5))
    total5minviolation = Column(Numeric(15, 5))
    totalregviolation = Column(Numeric(15, 5))
    total6secviolation = Column(Numeric(15, 5))
    total60secviolation = Column(Numeric(15, 5))
    totalenergyconstrviolation = Column(Numeric(15, 5))
    totalenergyofferviolation = Column(Numeric(15, 5))
    totalasprofileviolation = Column(Numeric(15, 5))
    totalfaststartviolation = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    intervention = Column(Numeric(2, 0))


class P5minConstraintsolution(Base):
    __tablename__ = "p5min_constraintsolution"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    constraintid = Column(String(20), primary_key=True, nullable=False)
    rhs = Column(Numeric(15, 5))
    marginalvalue = Column(Numeric(15, 5))
    violationdegree = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    duid = Column(String(20))
    genconid_effectivedate = Column(TIMESTAMP(precision=3))
    genconid_versionno = Column(Numeric(22, 0))
    lhs = Column(Numeric(15, 5))
    intervention = Column(Numeric(2, 0))


class P5minInterconnectorsoln(Base):
    __tablename__ = "p5min_interconnectorsoln"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    meteredmwflow = Column(Numeric(15, 5))
    mwflow = Column(Numeric(15, 5))
    mwlosses = Column(Numeric(15, 5))
    marginalvalue = Column(Numeric(15, 5))
    violationdegree = Column(Numeric(15, 5))
    mnsp = Column(Numeric(1, 0))
    exportlimit = Column(Numeric(15, 5))
    importlimit = Column(Numeric(15, 5))
    marginalloss = Column(Numeric(15, 5))
    exportgenconid = Column(String(20))
    importgenconid = Column(String(20))
    fcasexportlimit = Column(Numeric(15, 5))
    fcasimportlimit = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    local_price_adjustment_export = Column(Numeric(10, 2))
    locally_constrained_export = Column(Numeric(1, 0))
    local_price_adjustment_import = Column(Numeric(10, 2))
    locally_constrained_import = Column(Numeric(1, 0))
    intervention = Column(Numeric(2, 0))


class P5minLocalPrice(Base):
    __tablename__ = "p5min_local_price"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20), primary_key=True, nullable=False)
    local_price_adjustment = Column(Numeric(10, 2))
    locally_constrained = Column(Numeric(1, 0))


class P5minRegionsolution(Base):
    __tablename__ = "p5min_regionsolution"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    rrp = Column(Numeric(15, 5))
    rop = Column(Numeric(15, 5))
    excessgeneration = Column(Numeric(15, 5))
    raise6secrrp = Column(Numeric(15, 5))
    raise6secrop = Column(Numeric(15, 5))
    raise60secrrp = Column(Numeric(15, 5))
    raise60secrop = Column(Numeric(15, 5))
    raise5minrrp = Column(Numeric(15, 5))
    raise5minrop = Column(Numeric(15, 5))
    raiseregrrp = Column(Numeric(15, 5))
    raiseregrop = Column(Numeric(15, 5))
    lower6secrrp = Column(Numeric(15, 5))
    lower6secrop = Column(Numeric(15, 5))
    lower60secrrp = Column(Numeric(15, 5))
    lower60secrop = Column(Numeric(15, 5))
    lower5minrrp = Column(Numeric(15, 5))
    lower5minrop = Column(Numeric(15, 5))
    lowerregrrp = Column(Numeric(15, 5))
    lowerregrop = Column(Numeric(15, 5))
    totaldemand = Column(Numeric(15, 5))
    availablegeneration = Column(Numeric(15, 5))
    availableload = Column(Numeric(15, 5))
    demandforecast = Column(Numeric(15, 5))
    dispatchablegeneration = Column(Numeric(15, 5))
    dispatchableload = Column(Numeric(15, 5))
    netinterchange = Column(Numeric(15, 5))
    lower5mindispatch = Column(Numeric(15, 5))
    lower5minimport = Column(Numeric(15, 5))
    lower5minlocaldispatch = Column(Numeric(15, 5))
    lower5minlocalreq = Column(Numeric(15, 5))
    lower5minreq = Column(Numeric(15, 5))
    lower60secdispatch = Column(Numeric(15, 5))
    lower60secimport = Column(Numeric(15, 5))
    lower60seclocaldispatch = Column(Numeric(15, 5))
    lower60seclocalreq = Column(Numeric(15, 5))
    lower60secreq = Column(Numeric(15, 5))
    lower6secdispatch = Column(Numeric(15, 5))
    lower6secimport = Column(Numeric(15, 5))
    lower6seclocaldispatch = Column(Numeric(15, 5))
    lower6seclocalreq = Column(Numeric(15, 5))
    lower6secreq = Column(Numeric(15, 5))
    raise5mindispatch = Column(Numeric(15, 5))
    raise5minimport = Column(Numeric(15, 5))
    raise5minlocaldispatch = Column(Numeric(15, 5))
    raise5minlocalreq = Column(Numeric(15, 5))
    raise5minreq = Column(Numeric(15, 5))
    raise60secdispatch = Column(Numeric(15, 5))
    raise60secimport = Column(Numeric(15, 5))
    raise60seclocaldispatch = Column(Numeric(15, 5))
    raise60seclocalreq = Column(Numeric(15, 5))
    raise60secreq = Column(Numeric(15, 5))
    raise6secdispatch = Column(Numeric(15, 5))
    raise6secimport = Column(Numeric(15, 5))
    raise6seclocaldispatch = Column(Numeric(15, 5))
    raise6seclocalreq = Column(Numeric(15, 5))
    raise6secreq = Column(Numeric(15, 5))
    aggregatedispatcherror = Column(Numeric(15, 5))
    initialsupply = Column(Numeric(15, 5))
    clearedsupply = Column(Numeric(15, 5))
    lowerregimport = Column(Numeric(15, 5))
    lowerregdispatch = Column(Numeric(15, 5))
    lowerreglocaldispatch = Column(Numeric(15, 5))
    lowerreglocalreq = Column(Numeric(15, 5))
    lowerregreq = Column(Numeric(15, 5))
    raiseregimport = Column(Numeric(15, 5))
    raiseregdispatch = Column(Numeric(15, 5))
    raisereglocaldispatch = Column(Numeric(15, 5))
    raisereglocalreq = Column(Numeric(15, 5))
    raiseregreq = Column(Numeric(15, 5))
    raise5minlocalviolation = Column(Numeric(15, 5))
    raisereglocalviolation = Column(Numeric(15, 5))
    raise60seclocalviolation = Column(Numeric(15, 5))
    raise6seclocalviolation = Column(Numeric(15, 5))
    lower5minlocalviolation = Column(Numeric(15, 5))
    lowerreglocalviolation = Column(Numeric(15, 5))
    lower60seclocalviolation = Column(Numeric(15, 5))
    lower6seclocalviolation = Column(Numeric(15, 5))
    raise5minviolation = Column(Numeric(15, 5))
    raiseregviolation = Column(Numeric(15, 5))
    raise60secviolation = Column(Numeric(15, 5))
    raise6secviolation = Column(Numeric(15, 5))
    lower5minviolation = Column(Numeric(15, 5))
    lowerregviolation = Column(Numeric(15, 5))
    lower60secviolation = Column(Numeric(15, 5))
    lower6secviolation = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    totalintermittentgeneration = Column(Numeric(15, 5))
    demand_and_nonschedgen = Column(Numeric(15, 5))
    uigf = Column(Numeric(15, 5))
    semischedule_clearedmw = Column(Numeric(15, 5))
    semischedule_compliancemw = Column(Numeric(15, 5))
    intervention = Column(Numeric(2, 0))
    ss_solar_uigf = Column(Numeric(15, 5))
    ss_wind_uigf = Column(Numeric(15, 5))
    ss_solar_clearedmw = Column(Numeric(15, 5))
    ss_wind_clearedmw = Column(Numeric(15, 5))
    ss_solar_compliancemw = Column(Numeric(15, 5))
    ss_wind_compliancemw = Column(Numeric(15, 5))


class P5minUnitsolution(Base):
    __tablename__ = "p5min_unitsolution"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    connectionpointid = Column(String(12))
    tradetype = Column(Numeric(2, 0))
    agcstatus = Column(Numeric(2, 0))
    initialmw = Column(Numeric(15, 5))
    totalcleared = Column(Numeric(15, 5))
    rampdownrate = Column(Numeric(15, 5))
    rampuprate = Column(Numeric(15, 5))
    lower5min = Column(Numeric(15, 5))
    lower60sec = Column(Numeric(15, 5))
    lower6sec = Column(Numeric(15, 5))
    raise5min = Column(Numeric(15, 5))
    raise60sec = Column(Numeric(15, 5))
    raise6sec = Column(Numeric(15, 5))
    lowerreg = Column(Numeric(15, 5))
    raisereg = Column(Numeric(15, 5))
    availability = Column(Numeric(15, 5))
    raise6secflags = Column(Numeric(3, 0))
    raise60secflags = Column(Numeric(3, 0))
    raise5minflags = Column(Numeric(3, 0))
    raiseregflags = Column(Numeric(3, 0))
    lower6secflags = Column(Numeric(3, 0))
    lower60secflags = Column(Numeric(3, 0))
    lower5minflags = Column(Numeric(3, 0))
    lowerregflags = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    semidispatchcap = Column(Numeric(3, 0))
    intervention = Column(Numeric(2, 0))


class Participant(Base):
    __tablename__ = "participant"
    __table_args__ = {"schema": "mms"}

    participantid = Column(String(10), primary_key=True)
    participantclassid = Column(String(20))
    name = Column(String(80))
    description = Column(String(64))
    acn = Column(String(9))
    primarybusiness = Column(String(40))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class ParticipantBandfeeAlloc(Base):
    __tablename__ = "participant_bandfee_alloc"
    __table_args__ = {"schema": "mms"}

    participantid = Column(String(10), primary_key=True, nullable=False)
    marketfeeid = Column(String(10), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantcategoryid = Column(String(10), primary_key=True, nullable=False)
    marketfeevalue = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Participantaccount(Base):
    __tablename__ = "participantaccount"
    __table_args__ = {"schema": "mms"}

    accountname = Column(String(80))
    participantid = Column(String(10), primary_key=True)
    accountnumber = Column(String(16))
    bankname = Column(String(16))
    banknumber = Column(Numeric(10, 0))
    branchname = Column(String(16))
    branchnumber = Column(Numeric(10, 0))
    bsbnumber = Column(String(20))
    nemmcocreditaccountnumber = Column(Numeric(10, 0))
    nemmcodebitaccountnumber = Column(Numeric(10, 0))
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    effectivedate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    abn = Column(String(20))


class Participantcategory(Base):
    __tablename__ = "participantcategory"
    __table_args__ = {"schema": "mms"}

    participantcategoryid = Column(String(10), primary_key=True)
    description = Column(String(64))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Participantcategoryalloc(Base):
    __tablename__ = "participantcategoryalloc"
    __table_args__ = {"schema": "mms"}

    participantcategoryid = Column(String(10), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Participantclas(Base):
    __tablename__ = "participantclass"
    __table_args__ = {"schema": "mms"}

    participantclassid = Column(String(20), primary_key=True)
    description = Column(String(64))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Participantcreditdetail(Base):
    __tablename__ = "participantcreditdetail"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    creditlimit = Column(Numeric(10, 0))
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Participantnoticetrk(Base):
    __tablename__ = "participantnoticetrk"
    __table_args__ = {"schema": "mms"}

    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    noticeid = Column(Numeric(10, 0), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Pasacasesolution(Base):
    __tablename__ = "pasacasesolution"
    __table_args__ = {"schema": "mms"}

    caseid = Column(String(20), primary_key=True)
    solutioncomplete = Column(Numeric(16, 6))
    pasaversion = Column(Numeric(27, 10))
    excessgeneration = Column(Numeric(16, 6))
    deficitcapacity = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    datetime = Column(TIMESTAMP(precision=3))


class Pasaconstraintsolution(Base):
    __tablename__ = "pasaconstraintsolution"
    __table_args__ = {"schema": "mms"}

    caseid = Column(String(20), nullable=False)
    constraintid = Column(String(20), primary_key=True, nullable=False)
    periodid = Column(String(20), primary_key=True, nullable=False)
    capacitymarginalvalue = Column(Numeric(16, 6))
    capacityviolationdegree = Column(Numeric(16, 6))
    excessgenmarginalvalue = Column(Numeric(16, 6))
    excessgenviolationdegree = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    datetime = Column(TIMESTAMP(precision=3))


class Pasainterconnectorsolution(Base):
    __tablename__ = "pasainterconnectorsolution"
    __table_args__ = {"schema": "mms"}

    caseid = Column(String(20), nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(String(20), primary_key=True, nullable=False)
    capacitymwflow = Column(Numeric(16, 6))
    capacitymarginalvalue = Column(Numeric(16, 6))
    capacityviolationdegree = Column(Numeric(16, 6))
    excessgenmwflow = Column(Numeric(16, 6))
    excessgenmarginalvalue = Column(Numeric(16, 6))
    excessgenviolationdegree = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    importlimit = Column(Numeric(15, 5))
    exportlimit = Column(Numeric(15, 5))
    datetime = Column(TIMESTAMP(precision=3))


class Pasaregionsolution(Base):
    __tablename__ = "pasaregionsolution"
    __table_args__ = {"schema": "mms"}

    caseid = Column(String(20), nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(String(20), primary_key=True, nullable=False)
    demand10 = Column(Numeric(16, 6))
    demand50 = Column(Numeric(16, 6))
    demand90 = Column(Numeric(16, 6))
    unconstrainedcapacity = Column(Numeric(16, 6))
    constrainedcapacity = Column(Numeric(16, 6))
    capacitysurplus = Column(Numeric(16, 6))
    reservereq = Column(Numeric(16, 6))
    reservecondition = Column(Numeric(16, 6))
    reservesurplus = Column(Numeric(16, 6))
    loadrejectionreservereq = Column(Numeric(16, 6))
    loadrejectionreservesurplus = Column(Numeric(16, 6))
    netinterchangeunderexcess = Column(Numeric(16, 6))
    netinterchangeunderscarcity = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    excessgeneration = Column(Numeric(22, 0))
    energyrequired = Column(Numeric(15, 5))
    capacityrequired = Column(Numeric(15, 5))
    datetime = Column(TIMESTAMP(precision=3))


class PdpasaCasesolution(Base):
    __tablename__ = "pdpasa_casesolution"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True)
    pasaversion = Column(String(10))
    reservecondition = Column(Numeric(1, 0))
    lorcondition = Column(Numeric(1, 0))
    capacityobjfunction = Column(Numeric(12, 3))
    capacityoption = Column(Numeric(12, 3))
    maxsurplusreserveoption = Column(Numeric(12, 3))
    maxsparecapacityoption = Column(Numeric(12, 3))
    interconnectorflowpenalty = Column(Numeric(12, 3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    reliabilitylrcdemandoption = Column(Numeric(12, 3))
    outagelrcdemandoption = Column(Numeric(12, 3))
    lordemandoption = Column(Numeric(12, 3))
    reliabilitylrccapacityoption = Column(String(10))
    outagelrccapacityoption = Column(String(10))
    lorcapacityoption = Column(String(10))
    loruigfoption = Column(Numeric(3, 0))
    reliabilitylrcuigfoption = Column(Numeric(3, 0))
    outagelrcuigfoption = Column(Numeric(3, 0))


class PdpasaRegionsolution(Base):
    __tablename__ = "pdpasa_regionsolution"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    demand10 = Column(Numeric(12, 2))
    demand50 = Column(Numeric(12, 2))
    demand90 = Column(Numeric(12, 2))
    reservereq = Column(Numeric(12, 2))
    capacityreq = Column(Numeric(12, 2))
    energyreqdemand50 = Column(Numeric(12, 2))
    unconstrainedcapacity = Column(Numeric(12, 0))
    constrainedcapacity = Column(Numeric(12, 0))
    netinterchangeunderscarcity = Column(Numeric(12, 2))
    surpluscapacity = Column(Numeric(12, 2))
    surplusreserve = Column(Numeric(12, 2))
    reservecondition = Column(Numeric(1, 0))
    maxsurplusreserve = Column(Numeric(12, 2))
    maxsparecapacity = Column(Numeric(12, 2))
    lorcondition = Column(Numeric(1, 0))
    aggregatecapacityavailable = Column(Numeric(12, 2))
    aggregatescheduledload = Column(Numeric(12, 2))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    aggregatepasaavailability = Column(Numeric(12, 0))
    runtype = Column(
        String(20),
        primary_key=True,
        nullable=False,
        server_default=text("'OUTAGE_LRC'::character varying"),
    )
    energyreqdemand10 = Column(Numeric(12, 2))
    calculatedlor1level = Column(Numeric(16, 6))
    calculatedlor2level = Column(Numeric(16, 6))
    msrnetinterchangeunderscarcity = Column(Numeric(12, 2))
    lornetinterchangeunderscarcity = Column(Numeric(12, 2))
    totalintermittentgeneration = Column(Numeric(15, 5))
    demand_and_nonschedgen = Column(Numeric(15, 5))
    uigf = Column(Numeric(12, 2))
    semischeduledcapacity = Column(Numeric(12, 2))
    lor_semischeduledcapacity = Column(Numeric(12, 2))
    lcr = Column(Numeric(16, 6))
    lcr2 = Column(Numeric(16, 6))
    fum = Column(Numeric(16, 6))
    ss_solar_uigf = Column(Numeric(12, 2))
    ss_wind_uigf = Column(Numeric(12, 2))
    ss_solar_capacity = Column(Numeric(12, 2))
    ss_wind_capacity = Column(Numeric(12, 2))
    ss_solar_cleared = Column(Numeric(12, 2))
    ss_wind_cleared = Column(Numeric(12, 2))


class Perdemand(Base):
    __tablename__ = "perdemand"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3))
    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    offerdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    resdemand = Column(Numeric(10, 0))
    demand90probability = Column(Numeric(10, 0))
    demand10probability = Column(Numeric(10, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    mr_schedule = Column(Numeric(6, 0))


class Peroffer(Base):
    __tablename__ = "peroffer"
    __table_args__ = (Index("peroffer_ndx2", "duid", "lastchanged"), {"schema": "mms"})

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    offerdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    selfdispatch = Column(Numeric(12, 6))
    maxavail = Column(Numeric(12, 6))
    fixedload = Column(Numeric(12, 6))
    rocup = Column(Numeric(6, 0))
    rocdown = Column(Numeric(6, 0))
    bandavail1 = Column(Numeric(6, 0))
    bandavail2 = Column(Numeric(6, 0))
    bandavail3 = Column(Numeric(6, 0))
    bandavail4 = Column(Numeric(6, 0))
    bandavail5 = Column(Numeric(6, 0))
    bandavail6 = Column(Numeric(6, 0))
    bandavail7 = Column(Numeric(6, 0))
    bandavail8 = Column(Numeric(6, 0))
    bandavail9 = Column(Numeric(6, 0))
    bandavail10 = Column(Numeric(6, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    pasaavailability = Column(Numeric(12, 0))
    mr_capacity = Column(Numeric(6, 0))


class PerofferD(Base):
    __tablename__ = "peroffer_d"
    __table_args__ = (Index("peroffer_d_ndx2", "duid", "lastchanged"), {"schema": "mms"})

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    offerdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    selfdispatch = Column(Numeric(12, 6))
    maxavail = Column(Numeric(12, 6))
    fixedload = Column(Numeric(12, 6))
    rocup = Column(Numeric(6, 0))
    rocdown = Column(Numeric(6, 0))
    bandavail1 = Column(Numeric(6, 0))
    bandavail2 = Column(Numeric(6, 0))
    bandavail3 = Column(Numeric(6, 0))
    bandavail4 = Column(Numeric(6, 0))
    bandavail5 = Column(Numeric(6, 0))
    bandavail6 = Column(Numeric(6, 0))
    bandavail7 = Column(Numeric(6, 0))
    bandavail8 = Column(Numeric(6, 0))
    bandavail9 = Column(Numeric(6, 0))
    bandavail10 = Column(Numeric(6, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    pasaavailability = Column(Numeric(12, 0))
    mr_capacity = Column(Numeric(6, 0))


class PredispatchFcasReq(Base):
    __tablename__ = "predispatch_fcas_req"
    __table_args__ = {"schema": "mms"}

    predispatchseqno = Column(String(20))
    runno = Column(Numeric(3, 0))
    intervention = Column(Numeric(2, 0))
    periodid = Column(String(20))
    genconid = Column(String(20), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    bidtype = Column(String(10), primary_key=True, nullable=False)
    genconeffectivedate = Column(TIMESTAMP(precision=3))
    genconversionno = Column(Numeric(3, 0))
    marginalvalue = Column(Numeric(16, 6))
    datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    base_cost = Column(Numeric(18, 8))
    adjusted_cost = Column(Numeric(18, 8))
    estimated_cmpf = Column(Numeric(18, 8))
    estimated_crmpf = Column(Numeric(18, 8))
    recovery_factor_cmpf = Column(Numeric(18, 8))
    recovery_factor_crmpf = Column(Numeric(18, 8))


class PredispatchLocalPrice(Base):
    __tablename__ = "predispatch_local_price"
    __table_args__ = {"schema": "mms"}

    predispatchseqno = Column(String(20), nullable=False)
    datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20), primary_key=True, nullable=False)
    periodid = Column(String(20))
    local_price_adjustment = Column(Numeric(10, 2))
    locally_constrained = Column(Numeric(1, 0))
    lastchanged = Column(TIMESTAMP(precision=3))


class PredispatchMnspbidtrk(Base):
    __tablename__ = "predispatch_mnspbidtrk"
    __table_args__ = {"schema": "mms"}

    predispatchseqno = Column(String(20), primary_key=True, nullable=False)
    linkid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(String(20), primary_key=True, nullable=False)
    participantid = Column(String(10))
    settlementdate = Column(TIMESTAMP(precision=3))
    offerdate = Column(TIMESTAMP(precision=3))
    versionno = Column(Numeric(3, 0))
    datetime = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Predispatchbidtrk(Base):
    __tablename__ = "predispatchbidtrk"
    __table_args__ = (
        Index("predispatchbidtrk_ndx2", "duid", "lastchanged"),
        Index("predispatchbidtrk_ndx3", "duid", "settlementdate"),
        {"schema": "mms"},
    )

    predispatchseqno = Column(String(20), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(String(20), primary_key=True, nullable=False)
    bidtype = Column(String(10))
    offerdate = Column(TIMESTAMP(precision=3))
    versionno = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    settlementdate = Column(TIMESTAMP(precision=3))
    datetime = Column(TIMESTAMP(precision=3))


class Predispatchblockedconstraint(Base):
    __tablename__ = "predispatchblockedconstraint"
    __table_args__ = {"schema": "mms"}

    predispatchseqno = Column(String(20), primary_key=True, nullable=False)
    constraintid = Column(String(20), primary_key=True, nullable=False)


class Predispatchcasesolution(Base):
    __tablename__ = "predispatchcasesolution"
    __table_args__ = {"schema": "mms"}

    predispatchseqno = Column(String(20), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    solutionstatus = Column(Numeric(2, 0))
    spdversion = Column(String(20))
    nonphysicallosses = Column(Numeric(1, 0))
    totalobjective = Column(Numeric(27, 10))
    totalareagenviolation = Column(Numeric(15, 5))
    totalinterconnectorviolation = Column(Numeric(15, 5))
    totalgenericviolation = Column(Numeric(15, 5))
    totalramprateviolation = Column(Numeric(15, 5))
    totalunitmwcapacityviolation = Column(Numeric(15, 5))
    total5minviolation = Column(Numeric(15, 5))
    totalregviolation = Column(Numeric(15, 5))
    total6secviolation = Column(Numeric(15, 5))
    total60secviolation = Column(Numeric(15, 5))
    totalasprofileviolation = Column(Numeric(15, 5))
    totalenergyconstrviolation = Column(Numeric(15, 5))
    totalenergyofferviolation = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    intervention = Column(Numeric(2, 0))


class Predispatchconstraint(Base):
    __tablename__ = "predispatchconstraint"
    __table_args__ = {"schema": "mms"}

    predispatchseqno = Column(String(20), index=True)
    runno = Column(Numeric(3, 0))
    constraintid = Column(String(20), primary_key=True, nullable=False)
    periodid = Column(String(20))
    intervention = Column(Numeric(2, 0))
    rhs = Column(Numeric(15, 5))
    marginalvalue = Column(Numeric(15, 5))
    violationdegree = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(20))
    genconid_effectivedate = Column(TIMESTAMP(precision=3))
    genconid_versionno = Column(Numeric(22, 0))
    lhs = Column(Numeric(15, 5))


class Predispatchinterconnectorre(Base):
    __tablename__ = "predispatchinterconnectorres"
    __table_args__ = {"schema": "mms"}

    predispatchseqno = Column(String(20), index=True)
    runno = Column(Numeric(3, 0))
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(String(20))
    intervention = Column(Numeric(2, 0))
    meteredmwflow = Column(Numeric(15, 5))
    mwflow = Column(Numeric(15, 5))
    mwlosses = Column(Numeric(15, 5))
    marginalvalue = Column(Numeric(15, 5))
    violationdegree = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    exportlimit = Column(Numeric(15, 5))
    importlimit = Column(Numeric(15, 5))
    marginalloss = Column(Numeric(15, 5))
    exportgenconid = Column(String(20))
    importgenconid = Column(String(20))
    fcasexportlimit = Column(Numeric(15, 5))
    fcasimportlimit = Column(Numeric(15, 5))
    local_price_adjustment_export = Column(Numeric(10, 2))
    locally_constrained_export = Column(Numeric(1, 0))
    local_price_adjustment_import = Column(Numeric(10, 2))
    locally_constrained_import = Column(Numeric(1, 0))


class Predispatchintersensitivity(Base):
    __tablename__ = "predispatchintersensitivities"
    __table_args__ = {"schema": "mms"}

    predispatchseqno = Column(String(20))
    runno = Column(Numeric(3, 0))
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(String(20))
    intervention = Column(Numeric(2, 0))
    datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    intervention_active = Column(Numeric(1, 0))
    mwflow1 = Column(Numeric(15, 5))
    mwflow2 = Column(Numeric(15, 5))
    mwflow3 = Column(Numeric(15, 5))
    mwflow4 = Column(Numeric(15, 5))
    mwflow5 = Column(Numeric(15, 5))
    mwflow6 = Column(Numeric(15, 5))
    mwflow7 = Column(Numeric(15, 5))
    mwflow8 = Column(Numeric(15, 5))
    mwflow9 = Column(Numeric(15, 5))
    mwflow10 = Column(Numeric(15, 5))
    mwflow11 = Column(Numeric(15, 5))
    mwflow12 = Column(Numeric(15, 5))
    mwflow13 = Column(Numeric(15, 5))
    mwflow14 = Column(Numeric(15, 5))
    mwflow15 = Column(Numeric(15, 5))
    mwflow16 = Column(Numeric(15, 5))
    mwflow17 = Column(Numeric(15, 5))
    mwflow18 = Column(Numeric(15, 5))
    mwflow19 = Column(Numeric(15, 5))
    mwflow20 = Column(Numeric(15, 5))
    mwflow21 = Column(Numeric(15, 5))
    mwflow22 = Column(Numeric(15, 5))
    mwflow23 = Column(Numeric(15, 5))
    mwflow24 = Column(Numeric(15, 5))
    mwflow25 = Column(Numeric(15, 5))
    mwflow26 = Column(Numeric(15, 5))
    mwflow27 = Column(Numeric(15, 5))
    mwflow28 = Column(Numeric(15, 5))
    mwflow29 = Column(Numeric(15, 5))
    mwflow30 = Column(Numeric(15, 5))
    mwflow31 = Column(Numeric(15, 5))
    mwflow32 = Column(Numeric(15, 5))
    mwflow33 = Column(Numeric(15, 5))
    mwflow34 = Column(Numeric(15, 5))
    mwflow35 = Column(Numeric(15, 5))
    mwflow36 = Column(Numeric(15, 5))
    mwflow37 = Column(Numeric(15, 5))
    mwflow38 = Column(Numeric(15, 5))
    mwflow39 = Column(Numeric(15, 5))
    mwflow40 = Column(Numeric(15, 5))
    mwflow41 = Column(Numeric(15, 5))
    mwflow42 = Column(Numeric(15, 5))
    mwflow43 = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Predispatchload(Base):
    __tablename__ = "predispatchload"
    __table_args__ = (Index("predispatchload_ndx2", "duid", "lastchanged"), {"schema": "mms"})

    predispatchseqno = Column(String(20), index=True)
    runno = Column(Numeric(3, 0))
    duid = Column(String(10), primary_key=True, nullable=False)
    tradetype = Column(Numeric(2, 0))
    periodid = Column(String(20))
    intervention = Column(Numeric(2, 0))
    connectionpointid = Column(String(12))
    agcstatus = Column(Numeric(2, 0))
    dispatchmode = Column(Numeric(2, 0))
    initialmw = Column(Numeric(15, 5))
    totalcleared = Column(Numeric(15, 5))
    lower5min = Column(Numeric(15, 5))
    lower60sec = Column(Numeric(15, 5))
    lower6sec = Column(Numeric(15, 5))
    raise5min = Column(Numeric(15, 5))
    raise60sec = Column(Numeric(15, 5))
    raise6sec = Column(Numeric(15, 5))
    rampdownrate = Column(Numeric(15, 5))
    rampuprate = Column(Numeric(15, 5))
    downepf = Column(Numeric(15, 5))
    upepf = Column(Numeric(15, 5))
    marginal5minvalue = Column(Numeric(15, 5))
    marginal60secvalue = Column(Numeric(15, 5))
    marginal6secvalue = Column(Numeric(15, 5))
    marginalvalue = Column(Numeric(15, 5))
    violation5mindegree = Column(Numeric(15, 5))
    violation60secdegree = Column(Numeric(15, 5))
    violation6secdegree = Column(Numeric(15, 5))
    violationdegree = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    lowerreg = Column(Numeric(15, 5))
    raisereg = Column(Numeric(15, 5))
    availability = Column(Numeric(15, 5))
    raise6secflags = Column(Numeric(3, 0))
    raise60secflags = Column(Numeric(3, 0))
    raise5minflags = Column(Numeric(3, 0))
    raiseregflags = Column(Numeric(3, 0))
    lower6secflags = Column(Numeric(3, 0))
    lower60secflags = Column(Numeric(3, 0))
    lower5minflags = Column(Numeric(3, 0))
    lowerregflags = Column(Numeric(3, 0))
    raise6secactualavailability = Column(Numeric(16, 6))
    raise60secactualavailability = Column(Numeric(16, 6))
    raise5minactualavailability = Column(Numeric(16, 6))
    raiseregactualavailability = Column(Numeric(16, 6))
    lower6secactualavailability = Column(Numeric(16, 6))
    lower60secactualavailability = Column(Numeric(16, 6))
    lower5minactualavailability = Column(Numeric(16, 6))
    lowerregactualavailability = Column(Numeric(16, 6))
    semidispatchcap = Column(Numeric(3, 0))


class Predispatchoffertrk(Base):
    __tablename__ = "predispatchoffertrk"
    __table_args__ = {"schema": "mms"}

    predispatchseqno = Column(String(20), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    bidtype = Column(String(20), primary_key=True, nullable=False)
    periodid = Column(String(20), primary_key=True, nullable=False)
    bidsettlementdate = Column(TIMESTAMP(precision=3))
    bidofferdate = Column(TIMESTAMP(precision=3))
    datetime = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Predispatchprice(Base):
    __tablename__ = "predispatchprice"
    __table_args__ = {"schema": "mms"}

    predispatchseqno = Column(String(20), index=True)
    runno = Column(Numeric(3, 0))
    regionid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(String(20))
    intervention = Column(Numeric(2, 0))
    rrp = Column(Numeric(15, 5))
    eep = Column(Numeric(15, 5))
    rrp1 = Column(Numeric(15, 5))
    eep1 = Column(Numeric(15, 5))
    rrp2 = Column(Numeric(15, 5))
    eep2 = Column(Numeric(15, 5))
    rrp3 = Column(Numeric(15, 5))
    eep3 = Column(Numeric(15, 5))
    rrp4 = Column(Numeric(15, 5))
    eep4 = Column(Numeric(15, 5))
    rrp5 = Column(Numeric(15, 5))
    eep5 = Column(Numeric(15, 5))
    rrp6 = Column(Numeric(15, 5))
    eep6 = Column(Numeric(15, 5))
    rrp7 = Column(Numeric(15, 5))
    eep7 = Column(Numeric(15, 5))
    rrp8 = Column(Numeric(15, 5))
    eep8 = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    raise6secrrp = Column(Numeric(15, 5))
    raise60secrrp = Column(Numeric(15, 5))
    raise5minrrp = Column(Numeric(15, 5))
    raiseregrrp = Column(Numeric(15, 5))
    lower6secrrp = Column(Numeric(15, 5))
    lower60secrrp = Column(Numeric(15, 5))
    lower5minrrp = Column(Numeric(15, 5))
    lowerregrrp = Column(Numeric(15, 5))


class Predispatchpricesensitivity(Base):
    __tablename__ = "predispatchpricesensitivities"
    __table_args__ = {"schema": "mms"}

    predispatchseqno = Column(String(20), index=True)
    runno = Column(Numeric(3, 0))
    regionid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(String(20))
    intervention = Column(Numeric(2, 0))
    rrpeep1 = Column(Numeric(15, 5))
    rrpeep2 = Column(Numeric(15, 5))
    rrpeep3 = Column(Numeric(15, 5))
    rrpeep4 = Column(Numeric(15, 5))
    rrpeep5 = Column(Numeric(15, 5))
    rrpeep6 = Column(Numeric(15, 5))
    rrpeep7 = Column(Numeric(15, 5))
    rrpeep8 = Column(Numeric(15, 5))
    rrpeep9 = Column(Numeric(15, 5))
    rrpeep10 = Column(Numeric(15, 5))
    rrpeep11 = Column(Numeric(15, 5))
    rrpeep12 = Column(Numeric(15, 5))
    rrpeep13 = Column(Numeric(15, 5))
    rrpeep14 = Column(Numeric(15, 5))
    rrpeep15 = Column(Numeric(15, 5))
    rrpeep16 = Column(Numeric(15, 5))
    rrpeep17 = Column(Numeric(15, 5))
    rrpeep18 = Column(Numeric(15, 5))
    rrpeep19 = Column(Numeric(15, 5))
    rrpeep20 = Column(Numeric(15, 5))
    rrpeep21 = Column(Numeric(15, 5))
    rrpeep22 = Column(Numeric(15, 5))
    rrpeep23 = Column(Numeric(15, 5))
    rrpeep24 = Column(Numeric(15, 5))
    rrpeep25 = Column(Numeric(15, 5))
    rrpeep26 = Column(Numeric(15, 5))
    rrpeep27 = Column(Numeric(15, 5))
    rrpeep28 = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    rrpeep29 = Column(Numeric(15, 5))
    rrpeep30 = Column(Numeric(15, 5))
    rrpeep31 = Column(Numeric(15, 5))
    rrpeep32 = Column(Numeric(15, 5))
    rrpeep33 = Column(Numeric(15, 5))
    rrpeep34 = Column(Numeric(15, 5))
    rrpeep35 = Column(Numeric(15, 5))
    intervention_active = Column(Numeric(1, 0))
    rrpeep36 = Column(Numeric(15, 5))
    rrpeep37 = Column(Numeric(15, 5))
    rrpeep38 = Column(Numeric(15, 5))
    rrpeep39 = Column(Numeric(15, 5))
    rrpeep40 = Column(Numeric(15, 5))
    rrpeep41 = Column(Numeric(15, 5))
    rrpeep42 = Column(Numeric(15, 5))
    rrpeep43 = Column(Numeric(15, 5))


class Predispatchregionsum(Base):
    __tablename__ = "predispatchregionsum"
    __table_args__ = {"schema": "mms"}

    predispatchseqno = Column(String(20), index=True)
    runno = Column(Numeric(3, 0))
    regionid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(String(20))
    intervention = Column(Numeric(2, 0))
    totaldemand = Column(Numeric(15, 5))
    availablegeneration = Column(Numeric(15, 5))
    availableload = Column(Numeric(15, 5))
    demandforecast = Column(Numeric(15, 5))
    dispatchablegeneration = Column(Numeric(15, 5))
    dispatchableload = Column(Numeric(15, 5))
    netinterchange = Column(Numeric(15, 5))
    excessgeneration = Column(Numeric(15, 5))
    lower5mindispatch = Column(Numeric(15, 5))
    lower5minimport = Column(Numeric(15, 5))
    lower5minlocaldispatch = Column(Numeric(15, 5))
    lower5minlocalprice = Column(Numeric(15, 5))
    lower5minlocalreq = Column(Numeric(15, 5))
    lower5minprice = Column(Numeric(15, 5))
    lower5minreq = Column(Numeric(15, 5))
    lower5minsupplyprice = Column(Numeric(15, 5))
    lower60secdispatch = Column(Numeric(15, 5))
    lower60secimport = Column(Numeric(15, 5))
    lower60seclocaldispatch = Column(Numeric(15, 5))
    lower60seclocalprice = Column(Numeric(15, 5))
    lower60seclocalreq = Column(Numeric(15, 5))
    lower60secprice = Column(Numeric(15, 5))
    lower60secreq = Column(Numeric(15, 5))
    lower60secsupplyprice = Column(Numeric(15, 5))
    lower6secdispatch = Column(Numeric(15, 5))
    lower6secimport = Column(Numeric(15, 5))
    lower6seclocaldispatch = Column(Numeric(15, 5))
    lower6seclocalprice = Column(Numeric(15, 5))
    lower6seclocalreq = Column(Numeric(15, 5))
    lower6secprice = Column(Numeric(15, 5))
    lower6secreq = Column(Numeric(15, 5))
    lower6secsupplyprice = Column(Numeric(15, 5))
    raise5mindispatch = Column(Numeric(15, 5))
    raise5minimport = Column(Numeric(15, 5))
    raise5minlocaldispatch = Column(Numeric(15, 5))
    raise5minlocalprice = Column(Numeric(15, 5))
    raise5minlocalreq = Column(Numeric(15, 5))
    raise5minprice = Column(Numeric(15, 5))
    raise5minreq = Column(Numeric(15, 5))
    raise5minsupplyprice = Column(Numeric(15, 5))
    raise60secdispatch = Column(Numeric(15, 5))
    raise60secimport = Column(Numeric(15, 5))
    raise60seclocaldispatch = Column(Numeric(15, 5))
    raise60seclocalprice = Column(Numeric(15, 5))
    raise60seclocalreq = Column(Numeric(15, 5))
    raise60secprice = Column(Numeric(15, 5))
    raise60secreq = Column(Numeric(15, 5))
    raise60secsupplyprice = Column(Numeric(15, 5))
    raise6secdispatch = Column(Numeric(15, 5))
    raise6secimport = Column(Numeric(15, 5))
    raise6seclocaldispatch = Column(Numeric(15, 5))
    raise6seclocalprice = Column(Numeric(15, 5))
    raise6seclocalreq = Column(Numeric(15, 5))
    raise6secprice = Column(Numeric(15, 5))
    raise6secreq = Column(Numeric(15, 5))
    raise6secsupplyprice = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    initialsupply = Column(Numeric(15, 5))
    clearedsupply = Column(Numeric(15, 5))
    lowerregimport = Column(Numeric(15, 5))
    lowerreglocaldispatch = Column(Numeric(15, 5))
    lowerreglocalreq = Column(Numeric(15, 5))
    lowerregreq = Column(Numeric(15, 5))
    raiseregimport = Column(Numeric(15, 5))
    raisereglocaldispatch = Column(Numeric(15, 5))
    raisereglocalreq = Column(Numeric(15, 5))
    raiseregreq = Column(Numeric(15, 5))
    raise5minlocalviolation = Column(Numeric(15, 5))
    raisereglocalviolation = Column(Numeric(15, 5))
    raise60seclocalviolation = Column(Numeric(15, 5))
    raise6seclocalviolation = Column(Numeric(15, 5))
    lower5minlocalviolation = Column(Numeric(15, 5))
    lowerreglocalviolation = Column(Numeric(15, 5))
    lower60seclocalviolation = Column(Numeric(15, 5))
    lower6seclocalviolation = Column(Numeric(15, 5))
    raise5minviolation = Column(Numeric(15, 5))
    raiseregviolation = Column(Numeric(15, 5))
    raise60secviolation = Column(Numeric(15, 5))
    raise6secviolation = Column(Numeric(15, 5))
    lower5minviolation = Column(Numeric(15, 5))
    lowerregviolation = Column(Numeric(15, 5))
    lower60secviolation = Column(Numeric(15, 5))
    lower6secviolation = Column(Numeric(15, 5))
    raise6secactualavailability = Column(Numeric(16, 6))
    raise60secactualavailability = Column(Numeric(16, 6))
    raise5minactualavailability = Column(Numeric(16, 6))
    raiseregactualavailability = Column(Numeric(16, 6))
    lower6secactualavailability = Column(Numeric(16, 6))
    lower60secactualavailability = Column(Numeric(16, 6))
    lower5minactualavailability = Column(Numeric(16, 6))
    lowerregactualavailability = Column(Numeric(16, 6))
    decavailability = Column(Numeric(16, 6))
    lorsurplus = Column(Numeric(16, 6))
    lrcsurplus = Column(Numeric(16, 6))
    totalintermittentgeneration = Column(Numeric(15, 5))
    demand_and_nonschedgen = Column(Numeric(15, 5))
    uigf = Column(Numeric(15, 5))
    semischedule_clearedmw = Column(Numeric(15, 5))
    semischedule_compliancemw = Column(Numeric(15, 5))
    ss_solar_uigf = Column(Numeric(15, 5))
    ss_wind_uigf = Column(Numeric(15, 5))
    ss_solar_clearedmw = Column(Numeric(15, 5))
    ss_wind_clearedmw = Column(Numeric(15, 5))
    ss_solar_compliancemw = Column(Numeric(15, 5))
    ss_wind_compliancemw = Column(Numeric(15, 5))


class Predispatchscenariodemand(Base):
    __tablename__ = "predispatchscenariodemand"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    scenario = Column(Numeric(2, 0), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    deltamw = Column(Numeric(4, 0))


class Predispatchscenariodemandtrk(Base):
    __tablename__ = "predispatchscenariodemandtrk"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Prudentialcompanyposition(Base):
    __tablename__ = "prudentialcompanyposition"
    __table_args__ = {"schema": "mms"}

    prudential_date = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    company_id = Column(String(20), primary_key=True, nullable=False)
    mcl = Column(Numeric(16, 6))
    credit_support = Column(Numeric(16, 6))
    trading_limit = Column(Numeric(16, 6))
    current_amount_balance = Column(Numeric(16, 6))
    security_deposit_provision = Column(Numeric(16, 6))
    security_deposit_offset = Column(Numeric(16, 6))
    security_deposit_balance = Column(Numeric(16, 6))
    expost_realloc_balance = Column(Numeric(16, 6))
    default_balance = Column(Numeric(16, 6))
    outstandings = Column(Numeric(16, 6))
    trading_margin = Column(Numeric(16, 6))
    typical_accrual = Column(Numeric(16, 6))
    prudential_margin = Column(Numeric(16, 6))
    early_payment_amount = Column(Numeric(18, 8))
    percentage_outstandings = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Prudentialruntrk(Base):
    __tablename__ = "prudentialruntrk"
    __table_args__ = {"schema": "mms"}

    prudential_date = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Reallocation(Base):
    __tablename__ = "reallocation"
    __table_args__ = {"schema": "mms"}

    reallocationid = Column(String(20), primary_key=True)
    creditparticipantid = Column(String(10))
    debitparticipantid = Column(String(10))
    regionid = Column(String(10))
    agreementtype = Column(String(10))
    creditreference = Column(String(400))
    debitreference = Column(String(400))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    startdate = Column(TIMESTAMP(precision=3))
    enddate = Column(TIMESTAMP(precision=3))
    current_stepid = Column(String(20))
    daytype = Column(String(20))
    reallocation_type = Column(String(1))
    calendarid = Column(String(30))
    intervallength = Column(Numeric(3, 0))


class Reallocationdetail(Base):
    __tablename__ = "reallocationdetails"
    __table_args__ = {"schema": "mms"}

    reallocationid = Column(String(20), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Reallocationinterval(Base):
    __tablename__ = "reallocationinterval"
    __table_args__ = {"schema": "mms"}

    reallocationid = Column(String(20), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    value = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    nrp = Column(Numeric(15, 5))


class Reallocationintervals(Base):
    __tablename__ = "reallocationintervals"
    __table_args__ = {"schema": "mms"}

    reallocationid = Column(String(20), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    reallocationvalue = Column(Numeric(6, 2))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Reallocations(Base):
    __tablename__ = "reallocations"
    __table_args__ = {"schema": "mms"}

    reallocationid = Column(String(20), primary_key=True)
    startdate = Column(TIMESTAMP(precision=3))
    startperiod = Column(Numeric(3, 0))
    enddate = Column(TIMESTAMP(precision=3))
    endperiod = Column(Numeric(3, 0))
    participanttoid = Column(String(10))
    participantfromid = Column(String(10))
    agreementtype = Column(String(10))
    deregistrationdate = Column(TIMESTAMP(precision=3))
    deregistrationperiod = Column(Numeric(3, 0))
    regionid = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Region(Base):
    __tablename__ = "region"
    __table_args__ = {"schema": "mms"}

    regionid = Column(String(10), primary_key=True)
    description = Column(String(64))
    regionstatus = Column(String(8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Regionapc(Base):
    __tablename__ = "regionapc"
    __table_args__ = {"schema": "mms"}

    regionid = Column(String(10), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Regionapcinterval(Base):
    __tablename__ = "regionapcintervals"
    __table_args__ = {"schema": "mms"}

    regionid = Column(String(10), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    apcvalue = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    apctype = Column(Numeric(3, 0))
    fcasapcvalue = Column(Numeric(16, 6))
    apfvalue = Column(Numeric(16, 6))


class RegionfcasrelaxationOcd(Base):
    __tablename__ = "regionfcasrelaxation_ocd"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    servicetype = Column(String(10), primary_key=True, nullable=False)
    _global = Column("global", Numeric(1, 0), primary_key=True, nullable=False)
    requirement = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Regionstandingdatum(Base):
    __tablename__ = "regionstandingdata"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    rsoid = Column(String(10))
    regionalreferencepointid = Column(String(10))
    peaktradingperiod = Column(Numeric(3, 0))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    scalingfactor = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Resdemandtrk(Base):
    __tablename__ = "resdemandtrk"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    offerdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    filename = Column(String(40))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Reserve(Base):
    __tablename__ = "reserve"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(12), primary_key=True, nullable=False)
    periodid = Column(Numeric(2, 0), primary_key=True, nullable=False)
    lower5min = Column(Numeric(6, 0))
    lower60sec = Column(Numeric(6, 0))
    lower6sec = Column(Numeric(6, 0))
    raise5min = Column(Numeric(6, 0))
    raise60sec = Column(Numeric(6, 0))
    raise6sec = Column(Numeric(6, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    pasareserve = Column(Numeric(6, 0))
    loadrejectionreservereq = Column(Numeric(10, 0))
    raisereg = Column(Numeric(6, 0))
    lowerreg = Column(Numeric(6, 0))
    lor1level = Column(Numeric(6, 0))
    lor2level = Column(Numeric(6, 0))


class ResidueBidTrk(Base):
    __tablename__ = "residue_bid_trk"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(30))
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    bidloaddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    auctionid = Column(String(30), primary_key=True, nullable=False)


class ResidueConDatum(Base):
    __tablename__ = "residue_con_data"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(30), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    unitspurchased = Column(Numeric(17, 5))
    linkpayment = Column(Numeric(17, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    secondary_units_sold = Column(Numeric(18, 8))


class ResidueConEstimatesTrk(Base):
    __tablename__ = "residue_con_estimates_trk"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(30), primary_key=True, nullable=False)
    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    quarter = Column(Numeric(1, 0), primary_key=True, nullable=False)
    valuationid = Column(String(15), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class ResidueConFund(Base):
    __tablename__ = "residue_con_funds"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(30), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    defaultunits = Column(Numeric(5, 0))
    rolloverunits = Column(Numeric(5, 0))
    reallocatedunits = Column(Numeric(5, 0))
    unitsoffered = Column(Numeric(5, 0))
    meanreserveprice = Column(Numeric(9, 2))
    scalefactor = Column(Numeric(8, 5))
    actualreserveprice = Column(Numeric(9, 2))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class ResidueContract(Base):
    __tablename__ = "residue_contracts"
    __table_args__ = {"schema": "mms"}

    contractyear = Column(Numeric(4, 0), primary_key=True, nullable=False)
    quarter = Column(Numeric(1, 0), primary_key=True, nullable=False)
    tranche = Column(Numeric(2, 0), primary_key=True, nullable=False)
    contractid = Column(String(30))
    startdate = Column(TIMESTAMP(precision=3))
    enddate = Column(TIMESTAMP(precision=3))
    notifydate = Column(TIMESTAMP(precision=3))
    auctiondate = Column(TIMESTAMP(precision=3))
    calcmethod = Column(String(20))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    notifypostdate = Column(TIMESTAMP(precision=3))
    notifyby = Column(String(15))
    postdate = Column(TIMESTAMP(precision=3))
    postedby = Column(String(15))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    description = Column(String(80))
    auctionid = Column(String(30))


class ResidueFundsBid(Base):
    __tablename__ = "residue_funds_bid"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(30), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    loaddate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    optionid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    units = Column(Numeric(5, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class ResiduePriceBid(Base):
    __tablename__ = "residue_price_bid"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(30))
    participantid = Column(String(10), primary_key=True, nullable=False)
    loaddate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    optionid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    bidprice = Column(Numeric(17, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    auctionid = Column(String(30), primary_key=True, nullable=False)


class ResiduePriceFundsBid(Base):
    __tablename__ = "residue_price_funds_bid"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(30), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    units = Column(Numeric(5, 0))
    bidprice = Column(Numeric(17, 5))
    linkedbidflag = Column(Numeric(6, 0), primary_key=True, nullable=False)
    auctionid = Column(String(30), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class ResiduePublicDatum(Base):
    __tablename__ = "residue_public_data"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(30), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    unitsoffered = Column(Numeric(5, 0))
    unitssold = Column(Numeric(16, 6))
    clearingprice = Column(Numeric(17, 5))
    reserveprice = Column(Numeric(17, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class ResidueTrk(Base):
    __tablename__ = "residue_trk"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(30))
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    rundate = Column(TIMESTAMP(precision=3))
    authoriseddate = Column(TIMESTAMP(precision=3))
    authorisedby = Column(String(15))
    postdate = Column(TIMESTAMP(precision=3))
    postedby = Column(String(15))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    status = Column(String(15))
    auctionid = Column(String(30), primary_key=True, nullable=False)


class Residuecontractpayment(Base):
    __tablename__ = "residuecontractpayments"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(30), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Residuefiletrk(Base):
    __tablename__ = "residuefiletrk"
    __table_args__ = {"schema": "mms"}

    contractid = Column(String(30))
    participantid = Column(String(10), primary_key=True, nullable=False)
    loaddate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    filename = Column(String(40))
    ackfilename = Column(String(40))
    status = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    auctionid = Column(String(30), primary_key=True, nullable=False)


class RooftopPvActual(Base):
    __tablename__ = "rooftop_pv_actual"
    __table_args__ = {"schema": "mms"}

    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    type = Column(String(20), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    power = Column(Numeric(12, 3))
    qi = Column(Numeric(2, 1))
    lastchanged = Column(TIMESTAMP(precision=3))


class RooftopPvForecast(Base):
    __tablename__ = "rooftop_pv_forecast"
    __table_args__ = {"schema": "mms"}

    version_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    powermean = Column(Numeric(12, 3))
    powerpoe50 = Column(Numeric(12, 3))
    powerpoelow = Column(Numeric(12, 3))
    powerpoehigh = Column(Numeric(12, 3))
    lastchanged = Column(TIMESTAMP(precision=3))


class SecdepositInterestRate(Base):
    __tablename__ = "secdeposit_interest_rate"
    __table_args__ = {"schema": "mms"}

    interest_acct_id = Column(String(20), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    version_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    interest_rate = Column(Numeric(18, 8))


class SecdepositProvision(Base):
    __tablename__ = "secdeposit_provision"
    __table_args__ = {"schema": "mms"}

    security_deposit_id = Column(String(20), primary_key=True, nullable=False)
    participantid = Column(String(20), primary_key=True, nullable=False)
    transaction_date = Column(TIMESTAMP(precision=3))
    maturity_contractyear = Column(Numeric(4, 0))
    maturity_weekno = Column(Numeric(3, 0))
    amount = Column(Numeric(18, 8))
    interest_rate = Column(Numeric(18, 8))
    interest_calc_type = Column(String(20))
    interest_acct_id = Column(String(20))


class SetAncillarySummary(Base):
    __tablename__ = "set_ancillary_summary"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    service = Column(String(20), primary_key=True, nullable=False)
    paymenttype = Column(String(20), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    paymentamount = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class SetApcCompensation(Base):
    __tablename__ = "set_apc_compensation"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    apeventid = Column(Numeric(6, 0), primary_key=True, nullable=False)
    claimid = Column(Numeric(6, 0), primary_key=True, nullable=False)
    participantid = Column(String(20), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    compensation_amount = Column(Numeric(18, 8))


class SetApcRecovery(Base):
    __tablename__ = "set_apc_recovery"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    apeventid = Column(Numeric(6, 0), primary_key=True, nullable=False)
    claimid = Column(Numeric(6, 0), primary_key=True, nullable=False)
    participantid = Column(String(20), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(20), primary_key=True, nullable=False)
    recovery_amount = Column(Numeric(18, 8))
    region_recovery_amount = Column(Numeric(18, 8))


class SetCspDerogationAmount(Base):
    __tablename__ = "set_csp_derogation_amount"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    amount_id = Column(String(20), primary_key=True, nullable=False)
    derogation_amount = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class SetCspSupportdataConstraint(Base):
    __tablename__ = "set_csp_supportdata_constraint"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    constraintid = Column(String(20), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    marginalvalue = Column(Numeric(18, 8))
    rhs = Column(Numeric(18, 8))
    lowertumut_factor = Column(Numeric(18, 8))
    uppertumut_factor = Column(Numeric(18, 8))
    lowertumut_cspa_coeff = Column(Numeric(18, 8))
    uppertumut_cspa_coeff = Column(Numeric(18, 8))
    abs_x = Column(Numeric(18, 8))
    abs_y = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class SetCspSupportdataEnergydiff(Base):
    __tablename__ = "set_csp_supportdata_energydiff"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    lowertumut_spdp = Column(Numeric(18, 8))
    uppertumut_spdp = Column(Numeric(18, 8))
    lowertumut_evdp = Column(Numeric(18, 8))
    uppertumut_evdp = Column(Numeric(18, 8))
    flow_direction = Column(String(20))
    total_x = Column(Numeric(18, 8))
    total_y = Column(Numeric(18, 8))
    lowertumut_age = Column(Numeric(18, 8))
    uppertumut_age = Column(Numeric(18, 8))
    eva = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class SetCspSupportdataSubprice(Base):
    __tablename__ = "set_csp_supportdata_subprice"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0))
    rrp = Column(Numeric(18, 8))
    is_csp_interval = Column(Numeric(1, 0))
    lowertumut_tlf = Column(Numeric(18, 8))
    uppertumut_tlf = Column(Numeric(18, 8))
    lowertumut_price = Column(Numeric(18, 8))
    uppertumut_price = Column(Numeric(18, 8))
    lowertumut_cspa_coeff = Column(Numeric(18, 8))
    uppertumut_cspa_coeff = Column(Numeric(18, 8))
    lowertumut_spdp_uncapped = Column(Numeric(18, 8))
    uppertumut_spdp_uncapped = Column(Numeric(18, 8))
    lowertumut_spdp = Column(Numeric(18, 8))
    uppertumut_spdp = Column(Numeric(18, 8))
    interval_abs_x = Column(Numeric(18, 8))
    interval_abs_y = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class SetFcasPayment(Base):
    __tablename__ = "set_fcas_payment"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10))
    duid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10))
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    lower6sec_payment = Column(Numeric(18, 8))
    raise6sec_payment = Column(Numeric(18, 8))
    lower60sec_payment = Column(Numeric(18, 8))
    raise60sec_payment = Column(Numeric(18, 8))
    lower5min_payment = Column(Numeric(18, 8))
    raise5min_payment = Column(Numeric(18, 8))
    lowerreg_payment = Column(Numeric(18, 8))
    raisereg_payment = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class SetFcasRecovery(Base):
    __tablename__ = "set_fcas_recovery"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(String(3), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    lower6sec_recovery = Column(Numeric(18, 8))
    raise6sec_recovery = Column(Numeric(18, 8))
    lower60sec_recovery = Column(Numeric(18, 8))
    raise60sec_recovery = Column(Numeric(18, 8))
    lower5min_recovery = Column(Numeric(18, 8))
    raise5min_recovery = Column(Numeric(18, 8))
    lowerreg_recovery = Column(Numeric(18, 8))
    raisereg_recovery = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    lower6sec_recovery_gen = Column(Numeric(18, 8))
    raise6sec_recovery_gen = Column(Numeric(18, 8))
    lower60sec_recovery_gen = Column(Numeric(18, 8))
    raise60sec_recovery_gen = Column(Numeric(18, 8))
    lower5min_recovery_gen = Column(Numeric(18, 8))
    raise5min_recovery_gen = Column(Numeric(18, 8))
    lowerreg_recovery_gen = Column(Numeric(18, 8))
    raisereg_recovery_gen = Column(Numeric(18, 8))


class SetFcasRegulationTrk(Base):
    __tablename__ = "set_fcas_regulation_trk"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    constraintid = Column(String(20), primary_key=True, nullable=False)
    cmpf = Column(Numeric(18, 8))
    crmpf = Column(Numeric(18, 8))
    recovery_factor_cmpf = Column(Numeric(18, 8))
    recovery_factor_crmpf = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class SetMrPayment(Base):
    __tablename__ = "set_mr_payment"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    participantid = Column(String(10))
    duid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    mr_capacity = Column(Numeric(16, 6))
    uncapped_payment = Column(Numeric(16, 6))
    capped_payment = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class SetMrRecovery(Base):
    __tablename__ = "set_mr_recovery"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    participantid = Column(String(10))
    duid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    arodef = Column(Numeric(16, 6))
    nta = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class SetNmasRecovery(Base):
    __tablename__ = "set_nmas_recovery"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(20), primary_key=True, nullable=False)
    service = Column(String(10), primary_key=True, nullable=False)
    contractid = Column(String(10), primary_key=True, nullable=False)
    paymenttype = Column(String(20), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    rbf = Column(Numeric(18, 8))
    payment_amount = Column(Numeric(18, 8))
    participant_energy = Column(Numeric(18, 8))
    region_energy = Column(Numeric(18, 8))
    recovery_amount = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    participant_generation = Column(Numeric(18, 8))
    region_generation = Column(Numeric(18, 8))
    recovery_amount_customer = Column(Numeric(18, 8))
    recovery_amount_generator = Column(Numeric(18, 8))


class SetNmasRecoveryRbf(Base):
    __tablename__ = "set_nmas_recovery_rbf"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    service = Column(String(10), primary_key=True, nullable=False)
    contractid = Column(String(10), primary_key=True, nullable=False)
    paymenttype = Column(String(20), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    rbf = Column(Numeric(18, 8))
    payment_amount = Column(Numeric(18, 8))
    recovery_amount = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class SetRunParameter(Base):
    __tablename__ = "set_run_parameter"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    parameterid = Column(String(20), primary_key=True, nullable=False)
    numvalue = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Setagcpayment(Base):
    __tablename__ = "setagcpayment"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    contractid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    duid = Column(String(10))
    regionid = Column(String(10))
    tlf = Column(Numeric(7, 5))
    ebp = Column(Numeric(15, 5))
    rrp = Column(Numeric(15, 5))
    clearedmw = Column(Numeric(15, 5))
    initialmw = Column(Numeric(15, 5))
    enablingpayment = Column(Numeric(15, 5))
    contractversionno = Column(Numeric(3, 0))
    offerdate = Column(TIMESTAMP(precision=3))
    offerversionno = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Setagcrecovery(Base):
    __tablename__ = "setagcrecovery"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    contractid = Column(String(10))
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    enablingpayment = Column(Numeric(15, 5))
    participantdemand = Column(Numeric(15, 5))
    regiondemand = Column(Numeric(15, 5))
    enablingrecovery = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    enablingrecovery_gen = Column(Numeric(15, 5))
    participantdemand_gen = Column(Numeric(15, 5))
    regiondemand_gen = Column(Numeric(15, 5))


class Setapccompensation(Base):
    __tablename__ = "setapccompensation"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    apccompensation = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Setapcrecovery(Base):
    __tablename__ = "setapcrecovery"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    totalcompensation = Column(Numeric(15, 5))
    participantdemand = Column(Numeric(15, 5))
    regiondemand = Column(Numeric(15, 5))
    apcrecovery = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class SetcfgParticipantMpf(Base):
    __tablename__ = "setcfg_participant_mpf"
    __table_args__ = {"schema": "mms"}

    participantid = Column(String(10), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantcategoryid = Column(String(10), primary_key=True, nullable=False)
    connectionpointid = Column(String(10), primary_key=True, nullable=False)
    mpf = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class SetcfgParticipantMpftrk(Base):
    __tablename__ = "setcfg_participant_mpftrk"
    __table_args__ = {"schema": "mms"}

    participantid = Column(String(10), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Setcpdatum(Base):
    __tablename__ = "setcpdata"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(10, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(10, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    tcpid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10))
    igenergy = Column(Numeric(16, 6))
    xgenergy = Column(Numeric(16, 6))
    inenergy = Column(Numeric(16, 6))
    xnenergy = Column(Numeric(16, 6))
    ipower = Column(Numeric(16, 6))
    xpower = Column(Numeric(16, 6))
    rrp = Column(Numeric(20, 5))
    eep = Column(Numeric(16, 6))
    tlf = Column(Numeric(7, 5))
    cprrp = Column(Numeric(16, 6))
    cpeep = Column(Numeric(16, 6))
    ta = Column(Numeric(16, 6))
    ep = Column(Numeric(16, 6))
    apc = Column(Numeric(16, 6))
    resc = Column(Numeric(16, 6))
    resp = Column(Numeric(16, 6))
    meterrunno = Column(Numeric(10, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    hostdistributor = Column(String(10))
    mda = Column(String(10), primary_key=True, nullable=False)


class Setcpdataregion(Base):
    __tablename__ = "setcpdataregion"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(22, 10), primary_key=True, nullable=False)
    periodid = Column(Numeric(22, 10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    sumigenergy = Column(Numeric(27, 5))
    sumxgenergy = Column(Numeric(27, 5))
    suminenergy = Column(Numeric(27, 5))
    sumxnenergy = Column(Numeric(27, 5))
    sumipower = Column(Numeric(22, 0))
    sumxpower = Column(Numeric(22, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    sumep = Column(Numeric(15, 5))


class Setfcascomp(Base):
    __tablename__ = "setfcascomp"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10))
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    ccprice = Column(Numeric(15, 5))
    clearedmw = Column(Numeric(15, 5))
    unconstrainedmw = Column(Numeric(15, 5))
    ebp = Column(Numeric(15, 5))
    tlf = Column(Numeric(7, 5))
    rrp = Column(Numeric(15, 5))
    excessgen = Column(Numeric(15, 5))
    fcascomp = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Setfcasrecovery(Base):
    __tablename__ = "setfcasrecovery"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    duid = Column(String(10))
    participantid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    fcascomp = Column(Numeric(15, 5))
    participantdemand = Column(Numeric(15, 5))
    regiondemand = Column(Numeric(15, 5))
    fcasrecovery = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    fcasrecovery_gen = Column(Numeric(15, 5))
    participantdemand_gen = Column(Numeric(15, 5))
    regiondemand_gen = Column(Numeric(15, 5))


class Setfcasregionrecovery(Base):
    __tablename__ = "setfcasregionrecovery"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    bidtype = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    generatorregionenergy = Column(Numeric(16, 6))
    customerregionenergy = Column(Numeric(16, 6))
    regionrecovery = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Setgendatum(Base):
    __tablename__ = "setgendata"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(10, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(10, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), index=True)
    stationid = Column(String(10), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    gensetid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    genergy = Column(Numeric(16, 6))
    aenergy = Column(Numeric(16, 6))
    gpower = Column(Numeric(16, 6))
    apower = Column(Numeric(16, 6))
    rrp = Column(Numeric(20, 5))
    eep = Column(Numeric(16, 6))
    tlf = Column(Numeric(7, 5))
    cprrp = Column(Numeric(16, 6))
    cpeep = Column(Numeric(16, 6))
    netenergy = Column(Numeric(16, 6))
    energycost = Column(Numeric(16, 6))
    excessenergycost = Column(Numeric(16, 6))
    apc = Column(Numeric(16, 6))
    resc = Column(Numeric(16, 6))
    resp = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    expenergy = Column(Numeric(15, 6))
    expenergycost = Column(Numeric(15, 6))
    meterrunno = Column(Numeric(6, 0))
    mda = Column(String(10))
    secondary_tlf = Column(Numeric(7, 5))


class Setgendataregion(Base):
    __tablename__ = "setgendataregion"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(22, 10), primary_key=True, nullable=False)
    periodid = Column(Numeric(22, 10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    genergy = Column(Numeric(22, 0))
    aenergy = Column(Numeric(22, 0))
    gpower = Column(Numeric(22, 0))
    apower = Column(Numeric(22, 0))
    netenergy = Column(Numeric(27, 5))
    energycost = Column(Numeric(27, 5))
    excessenergycost = Column(Numeric(27, 5))
    expenergy = Column(Numeric(27, 6))
    expenergycost = Column(Numeric(27, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Setgovpayment(Base):
    __tablename__ = "setgovpayment"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    contractid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    duid = Column(String(10))
    regionid = Column(String(10))
    tlf = Column(Numeric(7, 5))
    rl6secraise = Column(Numeric(15, 5))
    rl60secraise = Column(Numeric(15, 5))
    rl6seclower = Column(Numeric(15, 5))
    rl60seclower = Column(Numeric(15, 5))
    deadbandup = Column(Numeric(7, 5))
    deadbanddown = Column(Numeric(7, 5))
    r6 = Column(Numeric(15, 5))
    r60 = Column(Numeric(15, 5))
    l6 = Column(Numeric(15, 5))
    l60 = Column(Numeric(15, 5))
    rl6 = Column(Numeric(15, 5))
    rl60 = Column(Numeric(15, 5))
    ll6 = Column(Numeric(15, 5))
    ll60 = Column(Numeric(15, 5))
    enabling6rpayment = Column(Numeric(15, 5))
    enabling60rpayment = Column(Numeric(15, 5))
    enabling6lpayment = Column(Numeric(15, 5))
    enabling60lpayment = Column(Numeric(15, 5))
    contractversionno = Column(Numeric(3, 0))
    offerdate = Column(TIMESTAMP(precision=3))
    offerversionno = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Setgovrecovery(Base):
    __tablename__ = "setgovrecovery"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    contractid = Column(String(10))
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    enabling6rpayment = Column(Numeric(15, 5))
    enabling60rpayment = Column(Numeric(15, 5))
    enabling6lpayment = Column(Numeric(15, 5))
    enabling60lpayment = Column(Numeric(15, 5))
    participantdemand = Column(Numeric(15, 5))
    regiondemand = Column(Numeric(15, 5))
    enabling6rrecovery = Column(Numeric(15, 5))
    enabling60rrecovery = Column(Numeric(15, 5))
    enabling6lrecovery = Column(Numeric(15, 5))
    enabling60lrecovery = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    enabling6lrecovery_gen = Column(Numeric(15, 5))
    enabling6rrecovery_gen = Column(Numeric(15, 5))
    enabling60lrecovery_gen = Column(Numeric(15, 5))
    enabling60rrecovery_gen = Column(Numeric(15, 5))
    participantdemand_gen = Column(Numeric(15, 5))
    regiondemand_gen = Column(Numeric(15, 5))


class Setintervention(Base):
    __tablename__ = "setintervention"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    contractid = Column(String(10))
    contractversion = Column(Numeric(3, 0))
    participantid = Column(String(10))
    regionid = Column(String(10))
    duid = Column(String(10), primary_key=True, nullable=False)
    rcf = Column(CHAR(1))
    interventionpayment = Column(Numeric(12, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Setinterventionrecovery(Base):
    __tablename__ = "setinterventionrecovery"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    contractid = Column(String(10), primary_key=True, nullable=False)
    rcf = Column(CHAR(1))
    participantid = Column(String(10), primary_key=True, nullable=False)
    participantdemand = Column(Numeric(12, 5))
    totaldemand = Column(Numeric(12, 5))
    interventionpayment = Column(Numeric(12, 5))
    interventionamount = Column(Numeric(12, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    regionid = Column(String(10))


class Setintraregionresidue(Base):
    __tablename__ = "setintraregionresidues"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    ep = Column(Numeric(15, 5))
    ec = Column(Numeric(15, 5))
    rrp = Column(Numeric(15, 5))
    exp = Column(Numeric(15, 5))
    irss = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Setiraucsurplu(Base):
    __tablename__ = "setiraucsurplus"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    settlementrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    contractid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(2, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    totalsurplus = Column(Numeric(15, 5))
    contractallocation = Column(Numeric(8, 5))
    surplusvalue = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    csp_derogation_amount = Column(Numeric(18, 8))
    unadjusted_irsr = Column(Numeric(18, 8))


class Setirfmrecovery(Base):
    __tablename__ = "setirfmrecovery"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    irfmid = Column(String(10), primary_key=True, nullable=False)
    irmfversion = Column(Numeric(3, 0))
    participantid = Column(String(10), primary_key=True, nullable=False)
    participantdemand = Column(Numeric(12, 5))
    totaltcd = Column(Numeric(12, 5))
    totaltfd = Column(Numeric(12, 5))
    irfmamount = Column(Numeric(12, 5))
    irfmpayment = Column(Numeric(12, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Setirnspsurplu(Base):
    __tablename__ = "setirnspsurplus"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    settlementrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    contractid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(2, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    totalsurplus = Column(Numeric(15, 5))
    contractallocation = Column(Numeric(8, 5))
    surplusvalue = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    csp_derogation_amount = Column(Numeric(18, 8))
    unadjusted_irsr = Column(Numeric(18, 8))


class Setirpartsurplu(Base):
    __tablename__ = "setirpartsurplus"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    settlementrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    contractid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(2, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    totalsurplus = Column(Numeric(15, 5))
    contractallocation = Column(Numeric(8, 5))
    surplusvalue = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    csp_derogation_amount = Column(Numeric(18, 8))
    unadjusted_irsr = Column(Numeric(18, 8))


class Setirsurplu(Base):
    __tablename__ = "setirsurplus"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    settlementrunno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    mwflow = Column(Numeric(15, 6))
    lossfactor = Column(Numeric(15, 5))
    surplusvalue = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    csp_derogation_amount = Column(Numeric(18, 8))
    unadjusted_irsr = Column(Numeric(18, 8))


class Setlshedpayment(Base):
    __tablename__ = "setlshedpayment"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    contractid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    duid = Column(String(10))
    regionid = Column(String(10))
    tlf = Column(Numeric(7, 5))
    rrp = Column(Numeric(15, 5))
    lseprice = Column(Numeric(15, 5))
    mcpprice = Column(Numeric(15, 5))
    lscr = Column(Numeric(4, 0))
    lsepayment = Column(Numeric(15, 5))
    ccpayment = Column(Numeric(15, 5))
    constrainedmw = Column(Numeric(15, 5))
    unconstrainedmw = Column(Numeric(15, 5))
    als = Column(Numeric(15, 5))
    initialdemand = Column(Numeric(15, 5))
    finaldemand = Column(Numeric(15, 5))
    contractversionno = Column(Numeric(3, 0))
    offerdate = Column(TIMESTAMP(precision=3))
    offerversionno = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    availabilitypayment = Column(Numeric(16, 6))


class Setlshedrecovery(Base):
    __tablename__ = "setlshedrecovery"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    contractid = Column(String(10))
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    lsepayment = Column(Numeric(15, 5))
    ccpayment = Column(Numeric(15, 5))
    participantdemand = Column(Numeric(15, 5))
    regiondemand = Column(Numeric(15, 5))
    lserecovery = Column(Numeric(15, 5))
    ccrecovery = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    lserecovery_gen = Column(Numeric(15, 5))
    ccrecovery_gen = Column(Numeric(15, 5))
    participantdemand_gen = Column(Numeric(15, 5))
    regiondemand_gen = Column(Numeric(15, 5))
    availabilityrecovery = Column(Numeric(16, 6))
    availabilityrecovery_gen = Column(Numeric(16, 6))


class Setluloadpayment(Base):
    __tablename__ = "setluloadpayment"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    contractid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    duid = Column(String(10))
    regionid = Column(String(10))
    tlf = Column(Numeric(7, 5))
    ebp = Column(Numeric(15, 5))
    rrp = Column(Numeric(15, 5))
    enablingprice = Column(Numeric(15, 5))
    usageprice = Column(Numeric(15, 5))
    ccprice = Column(Numeric(15, 5))
    blocksize = Column(Numeric(4, 0))
    acr = Column(Numeric(6, 2))
    unitoutput = Column(Numeric(15, 5))
    unitexcessgen = Column(Numeric(15, 5))
    enablingpayment = Column(Numeric(15, 5))
    usagepayment = Column(Numeric(15, 5))
    compensationpayment = Column(Numeric(15, 5))
    contractversionno = Column(Numeric(3, 0))
    offerdate = Column(TIMESTAMP(precision=3))
    offerversionno = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Setluloadrecovery(Base):
    __tablename__ = "setluloadrecovery"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    contractid = Column(String(10))
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    enablingpayment = Column(Numeric(15, 5))
    usagepayment = Column(Numeric(15, 5))
    compensationpayment = Column(Numeric(15, 5))
    participantdemand = Column(Numeric(15, 5))
    regiondemand = Column(Numeric(15, 5))
    enablingrecovery = Column(Numeric(15, 5))
    usagerecovery = Column(Numeric(15, 5))
    compensationrecovery = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    enablingrecovery_gen = Column(Numeric(15, 5))
    usagerecovery_gen = Column(Numeric(15, 5))
    compensationrecovery_gen = Column(Numeric(15, 5))
    participantdemand_gen = Column(Numeric(15, 5))
    regiondemand_gen = Column(Numeric(15, 5))


class Setlunloadpayment(Base):
    __tablename__ = "setlunloadpayment"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    contractid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    duid = Column(String(10))
    regionid = Column(String(10))
    tlf = Column(Numeric(7, 5))
    ebp = Column(Numeric(15, 5))
    rrp = Column(Numeric(15, 5))
    enablingprice = Column(Numeric(15, 5))
    usageprice = Column(Numeric(15, 5))
    ccprice = Column(Numeric(15, 5))
    clearedmw = Column(Numeric(15, 5))
    unconstrainedmw = Column(Numeric(15, 5))
    controlrange = Column(Numeric(4, 0))
    enablingpayment = Column(Numeric(15, 5))
    usagepayment = Column(Numeric(15, 5))
    compensationpayment = Column(Numeric(15, 5))
    contractversionno = Column(Numeric(3, 0))
    offerdate = Column(TIMESTAMP(precision=3))
    offerversionno = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Setlunloadrecovery(Base):
    __tablename__ = "setlunloadrecovery"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    contractid = Column(String(10))
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    enablingpayment = Column(Numeric(15, 5))
    usagepayment = Column(Numeric(15, 5))
    compensationpayment = Column(Numeric(15, 5))
    participantdemand = Column(Numeric(15, 5))
    regiondemand = Column(Numeric(15, 5))
    enablingrecovery = Column(Numeric(15, 5))
    usagerecovery = Column(Numeric(15, 5))
    compensationrecovery = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    enablingrecovery_gen = Column(Numeric(15, 5))
    usagerecovery_gen = Column(Numeric(15, 5))
    compensationrecovery_gen = Column(Numeric(15, 5))
    participantdemand_gen = Column(Numeric(15, 5))
    regiondemand_gen = Column(Numeric(15, 5))


class Setmarketfee(Base):
    __tablename__ = "setmarketfees"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    marketfeeid = Column(String(10), primary_key=True, nullable=False)
    marketfeevalue = Column(Numeric(15, 5))
    energy = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    participantcategoryid = Column(String(10), primary_key=True, nullable=False)


class Setreallocation(Base):
    __tablename__ = "setreallocations"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    reallocationid = Column(String(20), primary_key=True, nullable=False)
    reallocationvalue = Column(Numeric(15, 5))
    energy = Column(Numeric(15, 5))
    rrp = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Setreserverecovery(Base):
    __tablename__ = "setreserverecovery"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    contractid = Column(String(10), primary_key=True, nullable=False)
    rcf = Column(CHAR(1))
    spotpayment = Column(Numeric(12, 5))
    participantid = Column(String(10), primary_key=True, nullable=False)
    participantdemand = Column(Numeric(12, 5))
    totaldemand = Column(Numeric(12, 5))
    reservepayment = Column(Numeric(12, 5))
    reserveamount = Column(Numeric(12, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    regionid = Column(String(10))


class Setreservetrader(Base):
    __tablename__ = "setreservetrader"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    contractid = Column(String(10))
    contractversion = Column(Numeric(3, 0))
    participantid = Column(String(10))
    regionid = Column(String(10))
    duid = Column(String(10), primary_key=True, nullable=False)
    rcf = Column(CHAR(1))
    unitavail = Column(Numeric(6, 2))
    cpa = Column(Numeric(12, 5))
    cpe = Column(Numeric(12, 5))
    cpu = Column(Numeric(12, 5))
    cptotal = Column(Numeric(12, 5))
    capdifference = Column(Numeric(12, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Setrestartpayment(Base):
    __tablename__ = "setrestartpayment"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    contractid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10))
    restarttype = Column(Numeric(1, 0))
    avaflag = Column(Numeric(1, 0))
    availabilityprice = Column(Numeric(15, 5))
    tcf = Column(Numeric(1, 0))
    availabilitypayment = Column(Numeric(15, 5))
    contractversionno = Column(Numeric(3, 0))
    offerdate = Column(TIMESTAMP(precision=3))
    offerversionno = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    enablingpayment = Column(Numeric(18, 8))


class Setrestartrecovery(Base):
    __tablename__ = "setrestartrecovery"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    contractid = Column(String(10))
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    availabilitypayment = Column(Numeric(15, 5))
    participantdemand = Column(Numeric(15, 5))
    regiondemand = Column(Numeric(15, 5))
    availabilityrecovery = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    availabilityrecovery_gen = Column(Numeric(15, 5))
    participantdemand_gen = Column(Numeric(15, 5))
    regiondemand_gen = Column(Numeric(15, 5))
    enablingpayment = Column(Numeric(18, 8))
    enablingrecovery = Column(Numeric(18, 8))
    enablingrecovery_gen = Column(Numeric(18, 8))


class Setrpowerpayment(Base):
    __tablename__ = "setrpowerpayment"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    contractid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    duid = Column(String(10))
    regionid = Column(String(10))
    tlf = Column(Numeric(7, 5))
    ebp = Column(Numeric(15, 5))
    rrp = Column(Numeric(15, 5))
    mvaraprice = Column(Numeric(15, 5))
    mvareprice = Column(Numeric(15, 5))
    mvargprice = Column(Numeric(15, 5))
    ccprice = Column(Numeric(15, 5))
    synccompensation = Column(Numeric(1, 0))
    mta = Column(Numeric(15, 5))
    mtg = Column(Numeric(15, 5))
    blocksize = Column(Numeric(4, 0))
    avaflag = Column(Numeric(1, 0))
    clearedmw = Column(Numeric(15, 5))
    unconstrainedmw = Column(Numeric(15, 5))
    availabilitypayment = Column(Numeric(15, 5))
    enablingpayment = Column(Numeric(15, 5))
    ccpayment = Column(Numeric(15, 5))
    contractversionno = Column(Numeric(3, 0))
    offerdate = Column(TIMESTAMP(precision=3))
    offerversionno = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    availabilitypayment_rebate = Column(Numeric(18, 8))


class Setrpowerrecovery(Base):
    __tablename__ = "setrpowerrecovery"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    contractid = Column(String(10))
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    availabilitypayment = Column(Numeric(15, 5))
    enablingpayment = Column(Numeric(15, 5))
    ccpayment = Column(Numeric(15, 5))
    participantdemand = Column(Numeric(15, 5))
    regiondemand = Column(Numeric(15, 5))
    availabilityrecovery = Column(Numeric(15, 5))
    enablingrecovery = Column(Numeric(15, 5))
    ccrecovery = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    availabilityrecovery_gen = Column(Numeric(15, 5))
    enablingrecovery_gen = Column(Numeric(15, 5))
    ccrecovery_gen = Column(Numeric(15, 5))
    participantdemand_gen = Column(Numeric(15, 5))
    regiondemand_gen = Column(Numeric(15, 5))


class Setsmallgendatum(Base):
    __tablename__ = "setsmallgendata"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    connectionpointid = Column(String(20), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(20), primary_key=True, nullable=False)
    regionid = Column(String(20))
    importenergy = Column(Numeric(18, 8))
    exportenergy = Column(Numeric(18, 8))
    rrp = Column(Numeric(18, 8))
    tlf = Column(Numeric(18, 8))
    impenergycost = Column(Numeric(18, 8))
    expenergycost = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3))


class Setvicboundaryenergy(Base):
    __tablename__ = "setvicboundaryenergy"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    boundaryenergy = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Setvicenergyfigure(Base):
    __tablename__ = "setvicenergyfigures"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    totalgenoutput = Column(Numeric(15, 5))
    totalpcsd = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    tlr = Column(Numeric(15, 6))
    mlf = Column(Numeric(15, 6))


class Setvicenergyflow(Base):
    __tablename__ = "setvicenergyflow"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    netflow = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Spdconnectionpointconstraint(Base):
    __tablename__ = "spdconnectionpointconstraint"
    __table_args__ = {"schema": "mms"}

    connectionpointid = Column(String(12), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    genconid = Column(String(20), primary_key=True, nullable=False)
    factor = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    bidtype = Column(String(12), primary_key=True, nullable=False)


class Spdinterconnectorconstraint(Base):
    __tablename__ = "spdinterconnectorconstraint"
    __table_args__ = {"schema": "mms"}

    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    genconid = Column(String(20), primary_key=True, nullable=False)
    factor = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Spdregionconstraint(Base):
    __tablename__ = "spdregionconstraint"
    __table_args__ = {"schema": "mms"}

    regionid = Column(String(10), primary_key=True, nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    genconid = Column(String(20), primary_key=True, nullable=False)
    factor = Column(Numeric(16, 6))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    bidtype = Column(String(10), primary_key=True, nullable=False)


class SraCashSecurity(Base):
    __tablename__ = "sra_cash_security"
    __table_args__ = {"schema": "mms"}

    cash_security_id = Column(String(36), primary_key=True)
    participantid = Column(String(10))
    provision_date = Column(TIMESTAMP(precision=3))
    cash_amount = Column(Numeric(18, 8))
    interest_acct_id = Column(String(20))
    authoriseddate = Column(TIMESTAMP(precision=3))
    finalreturndate = Column(TIMESTAMP(precision=3))
    cash_security_returned = Column(Numeric(18, 8))
    deletiondate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3))


class SraFinancialAucMardetail(Base):
    __tablename__ = "sra_financial_auc_mardetail"
    __table_args__ = {"schema": "mms"}

    sra_year = Column(Numeric(4, 0), primary_key=True, nullable=False)
    sra_quarter = Column(Numeric(3, 0), primary_key=True, nullable=False)
    sra_runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    cash_security_id = Column(String(36), primary_key=True, nullable=False)
    returned_amount = Column(Numeric(18, 8))
    returned_interest = Column(Numeric(18, 8))


class SraFinancialAucMargin(Base):
    __tablename__ = "sra_financial_auc_margin"
    __table_args__ = {"schema": "mms"}

    sra_year = Column(Numeric(4, 0), primary_key=True, nullable=False)
    sra_quarter = Column(Numeric(3, 0), primary_key=True, nullable=False)
    sra_runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    total_cash_security = Column(Numeric(18, 8))
    required_margin = Column(Numeric(18, 8))
    returned_margin = Column(Numeric(18, 8))
    returned_margin_interest = Column(Numeric(18, 8))


class SraFinancialAucReceipt(Base):
    __tablename__ = "sra_financial_auc_receipts"
    __table_args__ = {"schema": "mms"}

    sra_year = Column(Numeric(4, 0), primary_key=True, nullable=False)
    sra_quarter = Column(Numeric(3, 0), primary_key=True, nullable=False)
    sra_runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    contractid = Column(String(10), primary_key=True, nullable=False)
    units_purchased = Column(Numeric(18, 8))
    clearing_price = Column(Numeric(18, 8))
    receipt_amount = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3))
    proceeds_amount = Column(Numeric(18, 8))
    units_sold = Column(Numeric(18, 8))


class SraFinancialAucpayDetail(Base):
    __tablename__ = "sra_financial_aucpay_detail"
    __table_args__ = {"schema": "mms"}

    sra_year = Column(Numeric(4, 0), primary_key=True, nullable=False)
    sra_quarter = Column(Numeric(3, 0), primary_key=True, nullable=False)
    sra_runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    contractid = Column(String(10), primary_key=True, nullable=False)
    maximum_units = Column(Numeric(18, 8))
    units_sold = Column(Numeric(18, 8))
    shortfall_units = Column(Numeric(18, 8))
    reserve_price = Column(Numeric(18, 8))
    clearing_price = Column(Numeric(18, 8))
    payment_amount = Column(Numeric(18, 8))
    shortfall_amount = Column(Numeric(18, 8))
    allocation = Column(Numeric(18, 8))
    net_payment_amount = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3))


class SraFinancialAucpaySum(Base):
    __tablename__ = "sra_financial_aucpay_sum"
    __table_args__ = {"schema": "mms"}

    sra_year = Column(Numeric(4, 0), primary_key=True, nullable=False)
    sra_quarter = Column(Numeric(3, 0), primary_key=True, nullable=False)
    sra_runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    gross_proceeds_amount = Column(Numeric(18, 8))
    total_gross_proceeds_amount = Column(Numeric(18, 8))
    shortfall_amount = Column(Numeric(18, 8))
    total_shortfall_amount = Column(Numeric(18, 8))
    net_payment_amount = Column(Numeric(18, 8))
    lastchanged = Column(TIMESTAMP(precision=3))


class SraFinancialRuntrk(Base):
    __tablename__ = "sra_financial_runtrk"
    __table_args__ = {"schema": "mms"}

    sra_year = Column(Numeric(4, 0), primary_key=True, nullable=False)
    sra_quarter = Column(Numeric(3, 0), primary_key=True, nullable=False)
    sra_runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    runtype = Column(String(20))
    rundate = Column(TIMESTAMP(precision=3))
    posteddate = Column(TIMESTAMP(precision=3))
    interest_versionno = Column(Numeric(3, 0))
    makeup_versionno = Column(Numeric(3, 0))
    lastchanged = Column(TIMESTAMP(precision=3))


class SraOfferProduct(Base):
    __tablename__ = "sra_offer_product"
    __table_args__ = {"schema": "mms"}

    auctionid = Column(String(30), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    loaddate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    optionid = Column(Numeric(4, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10))
    fromregionid = Column(String(10))
    offer_quantity = Column(Numeric(5, 0))
    offer_price = Column(Numeric(18, 8))
    trancheid = Column(String(30))
    lastchanged = Column(TIMESTAMP(precision=3))


class SraOfferProfile(Base):
    __tablename__ = "sra_offer_profile"
    __table_args__ = {"schema": "mms"}

    auctionid = Column(String(30), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    loaddate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    filename = Column(String(40))
    ackfilename = Column(String(40))
    transactionid = Column(String(100))
    lastchanged = Column(TIMESTAMP(precision=3))


class SraPrudentialCashSecurity(Base):
    __tablename__ = "sra_prudential_cash_security"
    __table_args__ = {"schema": "mms"}

    prudential_date = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    prudential_runno = Column(Numeric(8, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    cash_security_id = Column(String(36), primary_key=True, nullable=False)
    cash_security_amount = Column(Numeric(18, 8))


class SraPrudentialCompPosition(Base):
    __tablename__ = "sra_prudential_comp_position"
    __table_args__ = {"schema": "mms"}

    prudential_date = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    prudential_runno = Column(Numeric(8, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    trading_limit = Column(Numeric(18, 8))
    prudential_exposure_amount = Column(Numeric(18, 8))
    trading_margin = Column(Numeric(18, 8))


class SraPrudentialExposure(Base):
    __tablename__ = "sra_prudential_exposure"
    __table_args__ = {"schema": "mms"}

    prudential_date = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    prudential_runno = Column(Numeric(8, 0), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    sra_year = Column(Numeric(4, 0), primary_key=True, nullable=False)
    sra_quarter = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    fromregionid = Column(String(10), primary_key=True, nullable=False)
    max_tranche = Column(Numeric(2, 0))
    auctionid = Column(String(30))
    offer_submissiontime = Column(TIMESTAMP(precision=3))
    average_purchase_price = Column(Numeric(18, 8))
    average_cancellation_price = Column(Numeric(18, 8))
    cancellation_volume = Column(Numeric(18, 8))
    trading_position = Column(Numeric(18, 8))


class SraPrudentialRun(Base):
    __tablename__ = "sra_prudential_run"
    __table_args__ = {"schema": "mms"}

    prudential_date = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    prudential_runno = Column(Numeric(8, 0), primary_key=True, nullable=False)


class Stadualloc(Base):
    __tablename__ = "stadualloc"
    __table_args__ = (
        Index("stadualloc_ndx2", "stationid", "effectivedate", "versionno"),
        {"schema": "mms"},
    )

    duid = Column(String(10), primary_key=True, nullable=False, index=True)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    stationid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Station(Base):
    __tablename__ = "station"
    __table_args__ = {"schema": "mms"}

    stationid = Column(String(10), primary_key=True)
    stationname = Column(String(80))
    address1 = Column(String(80))
    address2 = Column(String(80))
    address3 = Column(String(80))
    address4 = Column(String(80))
    city = Column(String(40))
    state = Column(String(10))
    postcode = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    connectionpointid = Column(String(10))


class Stationoperatingstatu(Base):
    __tablename__ = "stationoperatingstatus"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    stationid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    status = Column(String(20))
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Stationowner(Base):
    __tablename__ = "stationowner"
    __table_args__ = (
        Index("stationowner_ndx2", "stationid", "effectivedate", "versionno"),
        {"schema": "mms"},
    )

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False, index=True)
    stationid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Stationownertrk(Base):
    __tablename__ = "stationownertrk"
    __table_args__ = {"schema": "mms"}

    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    participantid = Column(String(10), primary_key=True, nullable=False)
    versionno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    authorisedby = Column(String(15))
    authoriseddate = Column(TIMESTAMP(precision=3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class StpasaCasesolution(Base):
    __tablename__ = "stpasa_casesolution"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True)
    pasaversion = Column(String(10))
    reservecondition = Column(Numeric(1, 0))
    lorcondition = Column(Numeric(1, 0))
    capacityobjfunction = Column(Numeric(12, 3))
    capacityoption = Column(Numeric(12, 3))
    maxsurplusreserveoption = Column(Numeric(12, 3))
    maxsparecapacityoption = Column(Numeric(12, 3))
    interconnectorflowpenalty = Column(Numeric(12, 3))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    reliabilitylrcdemandoption = Column(Numeric(12, 3))
    outagelrcdemandoption = Column(Numeric(12, 3))
    lordemandoption = Column(Numeric(12, 3))
    reliabilitylrccapacityoption = Column(String(10))
    outagelrccapacityoption = Column(String(10))
    lorcapacityoption = Column(String(10))
    loruigfoption = Column(Numeric(3, 0))
    reliabilitylrcuigfoption = Column(Numeric(3, 0))
    outagelrcuigfoption = Column(Numeric(3, 0))


class StpasaConstraintsolution(Base):
    __tablename__ = "stpasa_constraintsolution"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    constraintid = Column(String(20), primary_key=True, nullable=False)
    capacityrhs = Column(Numeric(12, 2))
    capacitymarginalvalue = Column(Numeric(12, 2))
    capacityviolationdegree = Column(Numeric(12, 2))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    runtype = Column(
        String(20),
        primary_key=True,
        nullable=False,
        server_default=text("'OUTAGE_LRC'::character varying"),
    )


class StpasaInterconnectorsoln(Base):
    __tablename__ = "stpasa_interconnectorsoln"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    capacitymwflow = Column(Numeric(12, 2))
    capacitymarginalvalue = Column(Numeric(12, 2))
    capacityviolationdegree = Column(Numeric(12, 2))
    calculatedexportlimit = Column(Numeric(12, 2))
    calculatedimportlimit = Column(Numeric(12, 2))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    runtype = Column(
        String(20),
        primary_key=True,
        nullable=False,
        server_default=text("'OUTAGE_LRC'::character varying"),
    )
    exportlimitconstraintid = Column(String(20))
    importlimitconstraintid = Column(String(20))


class StpasaRegionsolution(Base):
    __tablename__ = "stpasa_regionsolution"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    demand10 = Column(Numeric(12, 2))
    demand50 = Column(Numeric(12, 2))
    demand90 = Column(Numeric(12, 2))
    reservereq = Column(Numeric(12, 2))
    capacityreq = Column(Numeric(12, 2))
    energyreqdemand50 = Column(Numeric(12, 2))
    unconstrainedcapacity = Column(Numeric(12, 0))
    constrainedcapacity = Column(Numeric(12, 0))
    netinterchangeunderscarcity = Column(Numeric(12, 2))
    surpluscapacity = Column(Numeric(12, 2))
    surplusreserve = Column(Numeric(12, 2))
    reservecondition = Column(Numeric(1, 0))
    maxsurplusreserve = Column(Numeric(12, 2))
    maxsparecapacity = Column(Numeric(12, 2))
    lorcondition = Column(Numeric(1, 0))
    aggregatecapacityavailable = Column(Numeric(12, 2))
    aggregatescheduledload = Column(Numeric(12, 2))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    aggregatepasaavailability = Column(Numeric(12, 0))
    runtype = Column(
        String(20),
        primary_key=True,
        nullable=False,
        server_default=text("'OUTAGE_LRC'::character varying"),
    )
    energyreqdemand10 = Column(Numeric(12, 2))
    calculatedlor1level = Column(Numeric(16, 6))
    calculatedlor2level = Column(Numeric(16, 6))
    msrnetinterchangeunderscarcity = Column(Numeric(12, 2))
    lornetinterchangeunderscarcity = Column(Numeric(12, 2))
    totalintermittentgeneration = Column(Numeric(15, 5))
    demand_and_nonschedgen = Column(Numeric(15, 5))
    uigf = Column(Numeric(12, 2))
    semischeduledcapacity = Column(Numeric(12, 2))
    lor_semischeduledcapacity = Column(Numeric(12, 2))
    lcr = Column(Numeric(16, 6))
    lcr2 = Column(Numeric(16, 6))
    fum = Column(Numeric(16, 6))
    ss_solar_uigf = Column(Numeric(12, 2))
    ss_wind_uigf = Column(Numeric(12, 2))
    ss_solar_capacity = Column(Numeric(12, 2))
    ss_wind_capacity = Column(Numeric(12, 2))
    ss_solar_cleared = Column(Numeric(12, 2))
    ss_wind_cleared = Column(Numeric(12, 2))


class StpasaSystemsolution(Base):
    __tablename__ = "stpasa_systemsolution"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), nullable=False, index=True)
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True)
    systemdemand50 = Column(Numeric(12, 2))
    reservereq = Column(Numeric(12, 2))
    unconstrainedcapacity = Column(Numeric(12, 2))
    constrainedcapacity = Column(Numeric(12, 2))
    surpluscapacity = Column(Numeric(12, 2))
    surplusreserve = Column(Numeric(12, 2))
    reservecondition = Column(Numeric(1, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class StpasaUnitsolution(Base):
    __tablename__ = "stpasa_unitsolution"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    interval_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    connectionpointid = Column(String(10))
    expectedmaxcapacity = Column(Numeric(12, 2))
    capacitymarginalvalue = Column(Numeric(12, 2))
    capacityviolationdegree = Column(Numeric(12, 2))
    capacityavailable = Column(Numeric(12, 2))
    energyconstrained = Column(Numeric(1, 0))
    energyavailable = Column(Numeric(10, 0))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    pasaavailability = Column(Numeric(12, 0))
    runtype = Column(
        String(20),
        primary_key=True,
        nullable=False,
        server_default=text("'OUTAGE_LRC'::character varying"),
    )


class Tradinginterconnect(Base):
    __tablename__ = "tradinginterconnect"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    interconnectorid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    meteredmwflow = Column(Numeric(15, 5))
    mwflow = Column(Numeric(15, 5))
    mwlosses = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class Tradingload(Base):
    __tablename__ = "tradingload"
    __table_args__ = (Index("tradingload_ndx2", "duid", "lastchanged"), {"schema": "mms"})

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    duid = Column(String(10), primary_key=True, nullable=False)
    tradetype = Column(Numeric(2, 0), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    initialmw = Column(Numeric(15, 5))
    totalcleared = Column(Numeric(15, 5))
    rampdownrate = Column(Numeric(15, 5))
    rampuprate = Column(Numeric(15, 5))
    lower5min = Column(Numeric(15, 5))
    lower60sec = Column(Numeric(15, 5))
    lower6sec = Column(Numeric(15, 5))
    raise5min = Column(Numeric(15, 5))
    raise60sec = Column(Numeric(15, 5))
    raise6sec = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    lowerreg = Column(Numeric(15, 5))
    raisereg = Column(Numeric(15, 5))
    availability = Column(Numeric(15, 5))
    semidispatchcap = Column(Numeric(3, 0))


class Tradingprice(Base):
    __tablename__ = "tradingprice"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    rrp = Column(Numeric(15, 5))
    eep = Column(Numeric(15, 5))
    invalidflag = Column(String(1))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    rop = Column(Numeric(15, 5))
    raise6secrrp = Column(Numeric(15, 5))
    raise6secrop = Column(Numeric(15, 5))
    raise60secrrp = Column(Numeric(15, 5))
    raise60secrop = Column(Numeric(15, 5))
    raise5minrrp = Column(Numeric(15, 5))
    raise5minrop = Column(Numeric(15, 5))
    raiseregrrp = Column(Numeric(15, 5))
    raiseregrop = Column(Numeric(15, 5))
    lower6secrrp = Column(Numeric(15, 5))
    lower6secrop = Column(Numeric(15, 5))
    lower60secrrp = Column(Numeric(15, 5))
    lower60secrop = Column(Numeric(15, 5))
    lower5minrrp = Column(Numeric(15, 5))
    lower5minrop = Column(Numeric(15, 5))
    lowerregrrp = Column(Numeric(15, 5))
    lowerregrop = Column(Numeric(15, 5))
    price_status = Column(String(20))


class Tradingregionsum(Base):
    __tablename__ = "tradingregionsum"
    __table_args__ = {"schema": "mms"}

    settlementdate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    runno = Column(Numeric(3, 0), primary_key=True, nullable=False)
    regionid = Column(String(10), primary_key=True, nullable=False)
    periodid = Column(Numeric(3, 0), primary_key=True, nullable=False)
    totaldemand = Column(Numeric(15, 5))
    availablegeneration = Column(Numeric(15, 5))
    availableload = Column(Numeric(15, 5))
    demandforecast = Column(Numeric(15, 5))
    dispatchablegeneration = Column(Numeric(15, 5))
    dispatchableload = Column(Numeric(15, 5))
    netinterchange = Column(Numeric(15, 5))
    excessgeneration = Column(Numeric(15, 5))
    lower5mindispatch = Column(Numeric(15, 5))
    lower5minimport = Column(Numeric(15, 5))
    lower5minlocaldispatch = Column(Numeric(15, 5))
    lower5minlocalprice = Column(Numeric(15, 5))
    lower5minlocalreq = Column(Numeric(15, 5))
    lower5minprice = Column(Numeric(15, 5))
    lower5minreq = Column(Numeric(15, 5))
    lower5minsupplyprice = Column(Numeric(15, 5))
    lower60secdispatch = Column(Numeric(15, 5))
    lower60secimport = Column(Numeric(15, 5))
    lower60seclocaldispatch = Column(Numeric(15, 5))
    lower60seclocalprice = Column(Numeric(15, 5))
    lower60seclocalreq = Column(Numeric(15, 5))
    lower60secprice = Column(Numeric(15, 5))
    lower60secreq = Column(Numeric(15, 5))
    lower60secsupplyprice = Column(Numeric(15, 5))
    lower6secdispatch = Column(Numeric(15, 5))
    lower6secimport = Column(Numeric(15, 5))
    lower6seclocaldispatch = Column(Numeric(15, 5))
    lower6seclocalprice = Column(Numeric(15, 5))
    lower6seclocalreq = Column(Numeric(15, 5))
    lower6secprice = Column(Numeric(15, 5))
    lower6secreq = Column(Numeric(15, 5))
    lower6secsupplyprice = Column(Numeric(15, 5))
    raise5mindispatch = Column(Numeric(15, 5))
    raise5minimport = Column(Numeric(15, 5))
    raise5minlocaldispatch = Column(Numeric(15, 5))
    raise5minlocalprice = Column(Numeric(15, 5))
    raise5minlocalreq = Column(Numeric(15, 5))
    raise5minprice = Column(Numeric(15, 5))
    raise5minreq = Column(Numeric(15, 5))
    raise5minsupplyprice = Column(Numeric(15, 5))
    raise60secdispatch = Column(Numeric(15, 5))
    raise60secimport = Column(Numeric(15, 5))
    raise60seclocaldispatch = Column(Numeric(15, 5))
    raise60seclocalprice = Column(Numeric(15, 5))
    raise60seclocalreq = Column(Numeric(15, 5))
    raise60secprice = Column(Numeric(15, 5))
    raise60secreq = Column(Numeric(15, 5))
    raise60secsupplyprice = Column(Numeric(15, 5))
    raise6secdispatch = Column(Numeric(15, 5))
    raise6secimport = Column(Numeric(15, 5))
    raise6seclocaldispatch = Column(Numeric(15, 5))
    raise6seclocalprice = Column(Numeric(15, 5))
    raise6seclocalreq = Column(Numeric(15, 5))
    raise6secprice = Column(Numeric(15, 5))
    raise6secreq = Column(Numeric(15, 5))
    raise6secsupplyprice = Column(Numeric(15, 5))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    initialsupply = Column(Numeric(15, 5))
    clearedsupply = Column(Numeric(15, 5))
    lowerregimport = Column(Numeric(15, 5))
    lowerreglocaldispatch = Column(Numeric(15, 5))
    lowerreglocalreq = Column(Numeric(15, 5))
    lowerregreq = Column(Numeric(15, 5))
    raiseregimport = Column(Numeric(15, 5))
    raisereglocaldispatch = Column(Numeric(15, 5))
    raisereglocalreq = Column(Numeric(15, 5))
    raiseregreq = Column(Numeric(15, 5))
    raise5minlocalviolation = Column(Numeric(15, 5))
    raisereglocalviolation = Column(Numeric(15, 5))
    raise60seclocalviolation = Column(Numeric(15, 5))
    raise6seclocalviolation = Column(Numeric(15, 5))
    lower5minlocalviolation = Column(Numeric(15, 5))
    lowerreglocalviolation = Column(Numeric(15, 5))
    lower60seclocalviolation = Column(Numeric(15, 5))
    lower6seclocalviolation = Column(Numeric(15, 5))
    raise5minviolation = Column(Numeric(15, 5))
    raiseregviolation = Column(Numeric(15, 5))
    raise60secviolation = Column(Numeric(15, 5))
    raise6secviolation = Column(Numeric(15, 5))
    lower5minviolation = Column(Numeric(15, 5))
    lowerregviolation = Column(Numeric(15, 5))
    lower60secviolation = Column(Numeric(15, 5))
    lower6secviolation = Column(Numeric(15, 5))
    totalintermittentgeneration = Column(Numeric(15, 5))
    demand_and_nonschedgen = Column(Numeric(15, 5))
    uigf = Column(Numeric(15, 5))


class Transmissionlossfactor(Base):
    __tablename__ = "transmissionlossfactor"
    __table_args__ = {"schema": "mms"}

    transmissionlossfactor = Column(Numeric(15, 5), nullable=False)
    effectivedate = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    versionno = Column(Numeric(22, 0), primary_key=True, nullable=False)
    connectionpointid = Column(String(10), primary_key=True, nullable=False)
    regionid = Column(String(10))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)
    secondary_tlf = Column(Numeric(18, 8))


class Valuationid(Base):
    __tablename__ = "valuationid"
    __table_args__ = {"schema": "mms"}

    valuationid = Column(String(15), primary_key=True)
    description = Column(String(80))
    lastchanged = Column(TIMESTAMP(precision=3), index=True)


class VoltageInstruction(Base):
    __tablename__ = "voltage_instruction"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    ems_id = Column(String(60), primary_key=True, nullable=False)
    participantid = Column(String(20))
    station_id = Column(String(60))
    device_id = Column(String(60))
    device_type = Column(String(20))
    control_type = Column(String(20))
    target = Column(Numeric(15, 0))
    conforming = Column(Numeric(1, 0))
    instruction_summary = Column(String(400))
    version_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    instruction_sequence = Column(Numeric(4, 0))
    additional_notes = Column(String(60))


class VoltageInstructionTrk(Base):
    __tablename__ = "voltage_instruction_trk"
    __table_args__ = {"schema": "mms"}

    run_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    file_type = Column(String(20))
    version_datetime = Column(TIMESTAMP(precision=3), primary_key=True, nullable=False)
    se_datetime = Column(TIMESTAMP(precision=3))
    solution_category = Column(String(60))
    solution_status = Column(String(60))
    operating_mode = Column(String(60))
    operating_status = Column(String(100))
    est_expiry = Column(TIMESTAMP(precision=3))
    est_next_instruction = Column(TIMESTAMP(precision=3))
