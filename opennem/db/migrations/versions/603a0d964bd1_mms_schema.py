# pylint: disable=no-member
"""
MMS schema

Revision ID: 603a0d964bd1
Revises: 4508f80f7f9f
Create Date: 2021-05-03 17:58:19.066896

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "603a0d964bd1"
down_revision = "4508f80f7f9f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("create schema if not exists mms;")

    op.create_table(
        "ancillary_recovery_split",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("service", sa.String(length=10), nullable=False),
        sa.Column("paymenttype", sa.String(length=20), nullable=False),
        sa.Column("customer_portion", sa.Numeric(precision=8, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno", "service", "paymenttype"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_ancillary_recovery_split_lastchanged"),
        "ancillary_recovery_split",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "apccomp",
        sa.Column("apcid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("startperiod", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("endperiod", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("apcid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_apccomp_lastchanged"),
        "apccomp",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "apccompamount",
        sa.Column("apcid", sa.String(length=10), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=6, scale=0), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("apcid", "participantid", "versionno", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_apccompamount_lastchanged"),
        "apccompamount",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "apccompamounttrk",
        sa.Column("apcid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("authorisedby", sa.String(length=10), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("apcid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_apccompamounttrk_lastchanged"),
        "apccompamounttrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "apevent",
        sa.Column("apeventid", sa.Numeric(precision=22, scale=0), nullable=False),
        sa.Column(
            "effectivefrominterval",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "effectivetointerval",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("reason", sa.String(length=2000), nullable=True),
        sa.Column("startauthorisedby", sa.String(length=15), nullable=True),
        sa.Column(
            "startauthoriseddate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("endauthorisedby", sa.String(length=15), nullable=True),
        sa.Column(
            "endauthoriseddate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("apeventid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_apevent_lastchanged"),
        "apevent",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "apeventregion",
        sa.Column("apeventid", sa.Numeric(precision=22, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("energyapflag", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("raise6secapflag", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("raise60secapflag", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("raise5minapflag", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("raiseregapflag", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("lower6secapflag", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("lower60secapflag", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("lower5minapflag", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("lowerregapflag", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("apeventid", "regionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_apeventregion_lastchanged"),
        "apeventregion",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "auction",
        sa.Column("auctionid", sa.String(length=30), nullable=False),
        sa.Column("auctiondate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("notifydate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("description", sa.String(length=100), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=30), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("auctionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_auction_lastchanged"),
        "auction",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "auction_calendar",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("quarter", sa.Numeric(precision=1, scale=0), nullable=False),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("notifydate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("paymentdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "reconciliationdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "prelimpurchasestmtdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "prelimproceedsstmtdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "finalpurchasestmtdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "finalproceedsstmtdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("contractyear", "quarter"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_auction_calendar_lastchanged"),
        "auction_calendar",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "auction_ic_allocations",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("quarter", sa.Numeric(precision=1, scale=0), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("maximumunits", sa.Numeric(precision=5, scale=0), nullable=True),
        sa.Column("proportion", sa.Numeric(precision=8, scale=5), nullable=True),
        sa.Column("auctionfee", sa.Numeric(precision=17, scale=5), nullable=True),
        sa.Column("changedate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("changedby", sa.String(length=15), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "auctionfee_sales",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "quarter",
            "versionno",
            "interconnectorid",
            "fromregionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_auction_ic_allocations_lastchanged"),
        "auction_ic_allocations",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "auction_revenue_estimate",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("quarter", sa.Numeric(precision=1, scale=0), nullable=False),
        sa.Column("valuationid", sa.String(length=15), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("monthno", sa.Numeric(precision=1, scale=0), nullable=False),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("revenue", sa.Numeric(precision=17, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "quarter",
            "valuationid",
            "versionno",
            "interconnectorid",
            "fromregionid",
            "monthno",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_auction_revenue_estimate_lastchanged"),
        "auction_revenue_estimate",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "auction_revenue_track",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("quarter", sa.Numeric(precision=1, scale=0), nullable=False),
        sa.Column("valuationid", sa.String(length=15), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("status", sa.String(length=10), nullable=True),
        sa.Column("documentref", sa.String(length=30), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractyear", "quarter", "valuationid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_auction_revenue_track_lastchanged"),
        "auction_revenue_track",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "auction_rp_estimate",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("quarter", sa.Numeric(precision=1, scale=0), nullable=False),
        sa.Column("valuationid", sa.String(length=15), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("rpestimate", sa.Numeric(precision=17, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "quarter",
            "valuationid",
            "versionno",
            "interconnectorid",
            "fromregionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_auction_rp_estimate_lastchanged"),
        "auction_rp_estimate",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "auction_tranche",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("quarter", sa.Numeric(precision=1, scale=0), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("tranche", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("auctiondate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("notifydate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("unitallocation", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("changedate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("changedby", sa.String(length=15), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractyear", "quarter", "versionno", "tranche"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_auction_tranche_lastchanged"),
        "auction_tranche",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "biddayoffer",
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("bidtype", sa.String(length=10), nullable=False),
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column(
            "dailyenergyconstraint",
            sa.Numeric(precision=12, scale=6),
            nullable=True,
        ),
        sa.Column("rebidexplanation", sa.String(length=500), nullable=True),
        sa.Column("priceband1", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband2", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband3", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband4", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband5", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband6", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband7", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband8", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband9", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband10", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("minimumload", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("t1", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("t2", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("t3", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("t4", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("normalstatus", sa.String(length=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("mr_factor", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("entrytype", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("duid", "bidtype", "settlementdate", "offerdate"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_biddayoffer_lastchanged"),
        "biddayoffer",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_biddayoffer_participantid"),
        "biddayoffer",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "biddayoffer_d",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("bidtype", sa.String(length=10), nullable=False),
        sa.Column(
            "bidsettlementdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("versionno", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column(
            "dailyenergyconstraint",
            sa.Numeric(precision=12, scale=6),
            nullable=True,
        ),
        sa.Column("rebidexplanation", sa.String(length=500), nullable=True),
        sa.Column("priceband1", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband2", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband3", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband4", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband5", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband6", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband7", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband8", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband9", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband10", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("minimumload", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("t1", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("t2", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("t3", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("t4", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("normalstatus", sa.String(length=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("mr_factor", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("entrytype", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "duid", "bidtype"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_biddayoffer_d_lastchanged"),
        "biddayoffer_d",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_biddayoffer_d_participantid"),
        "biddayoffer_d",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "bidduiddetails",
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("bidtype", sa.String(length=10), nullable=False),
        sa.Column("maxcapacity", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column(
            "minenablementlevel",
            sa.Numeric(precision=22, scale=0),
            nullable=True,
        ),
        sa.Column(
            "maxenablementlevel",
            sa.Numeric(precision=22, scale=0),
            nullable=True,
        ),
        sa.Column("maxlowerangle", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("maxupperangle", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("duid", "effectivedate", "versionno", "bidtype"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_bidduiddetails_lastchanged"),
        "bidduiddetails",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "bidduiddetailstrk",
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("duid", "effectivedate", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_bidduiddetailstrk_lastchanged"),
        "bidduiddetailstrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "bidofferfiletrk",
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("filename", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=20), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("participantid", "offerdate"),
        sa.UniqueConstraint("filename"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_bidofferfiletrk_lastchanged"),
        "bidofferfiletrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "bidperoffer",
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("bidtype", sa.String(length=10), nullable=False),
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=22, scale=0), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("maxavail", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("fixedload", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("rocup", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("rocdown", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("enablementmin", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("enablementmax", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lowbreakpoint", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("highbreakpoint", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail1", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("bandavail2", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("bandavail3", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("bandavail4", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("bandavail5", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("bandavail6", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("bandavail7", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("bandavail8", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("bandavail9", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("bandavail10", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "pasaavailability",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.Column("mr_capacity", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("duid", "bidtype", "settlementdate", "offerdate", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_bidperoffer_lastchanged"),
        "bidperoffer",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "bidperoffer_d",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("bidtype", sa.String(length=10), nullable=False),
        sa.Column(
            "bidsettlementdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("periodid", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("versionno", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("maxavail", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("fixedload", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("rocup", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("rocdown", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("enablementmin", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("enablementmax", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lowbreakpoint", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("highbreakpoint", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail1", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("bandavail2", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("bandavail3", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("bandavail4", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("bandavail5", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("bandavail6", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("bandavail7", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("bandavail8", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("bandavail9", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("bandavail10", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "pasaavailability",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("mr_capacity", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "duid", "bidtype", "interval_datetime"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_bidperoffer_d_lastchanged"),
        "bidperoffer_d",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "bidtypes",
        sa.Column("bidtype", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("description", sa.String(length=64), nullable=True),
        sa.Column("numberofbands", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column(
            "numdaysaheadpricelocked",
            sa.Numeric(precision=2, scale=0),
            nullable=True,
        ),
        sa.Column("validationrule", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("spdalias", sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint("bidtype", "effectivedate", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_bidtypes_lastchanged"),
        "bidtypes",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "bidtypestrk",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_bidtypestrk_lastchanged"),
        "bidtypestrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billadjustments",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("participanttype", sa.String(length=10), nullable=True),
        sa.Column("adjcontractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("adjweekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("adjbillrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("prevamount", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("adjamount", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lrs", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("prs", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("ofs", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("irn", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("irp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("interestamount", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "participantid",
            "adjcontractyear",
            "adjweekno",
            "adjbillrunno",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billadjustments_lastchanged"),
        "billadjustments",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billadjustments_participantid"),
        "billadjustments",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billing_apc_compensation",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("apeventid", sa.Numeric(precision=6, scale=0), nullable=False),
        sa.Column("claimid", sa.Numeric(precision=6, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=20), nullable=True),
        sa.Column(
            "compensation_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(length=20), nullable=True),
        sa.Column("compensation_type", sa.String(length=20), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractyear", "weekno", "billrunno", "apeventid", "claimid"),
        schema="mms",
    )
    op.create_table(
        "billing_apc_recovery",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("apeventid", sa.Numeric(precision=6, scale=0), nullable=False),
        sa.Column("claimid", sa.Numeric(precision=6, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=20), nullable=False),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column("recovery_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "eligibility_start_interval",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "eligibility_end_interval",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "participant_demand",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("region_demand", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "apeventid",
            "claimid",
            "participantid",
            "regionid",
        ),
        schema="mms",
    )
    op.create_table(
        "billing_co2e_publication",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column("sentoutenergy", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "generatoremissions",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("intensityindex", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint("contractyear", "weekno", "settlementdate", "regionid"),
        schema="mms",
    )
    op.create_table(
        "billing_co2e_publication_trk",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractyear", "weekno"),
        schema="mms",
    )
    op.create_table(
        "billing_csp_derogation_amount",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("amount_id", sa.String(length=20), nullable=False),
        sa.Column(
            "derogation_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear", "weekno", "billrunno", "participantid", "amount_id"
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billing_csp_derogation_amount_lastchanged"),
        "billing_csp_derogation_amount",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billing_daily_energy_summary",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("participantid", sa.String(length=20), nullable=False),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column(
            "customer_energy_purchased",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "generator_energy_sold",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "generator_energy_purchased",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "settlementdate",
            "participantid",
            "regionid",
        ),
        schema="mms",
    )
    op.create_table(
        "billing_direction_recon_other",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("direction_id", sa.String(length=20), nullable=False),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column("direction_desc", sa.String(length=200), nullable=True),
        sa.Column("direction_type_id", sa.String(length=20), nullable=True),
        sa.Column(
            "direction_start_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "direction_end_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "direction_start_interval",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "direction_end_interval",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "compensation_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("interest_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "independent_expert_fee",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("cra", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "regional_customer_energy",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "regional_generator_energy",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "regional_benefit_factor",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("contractyear", "weekno", "billrunno", "direction_id", "regionid"),
        schema="mms",
    )
    op.create_table(
        "billing_direction_reconciliatn",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("direction_id", sa.String(length=20), nullable=False),
        sa.Column("direction_desc", sa.String(length=200), nullable=True),
        sa.Column(
            "direction_start_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "direction_end_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "compensation_amount",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "independent_expert_fee",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("interest_amount", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("cra", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("nem_fee_id", sa.String(length=20), nullable=True),
        sa.Column(
            "nem_fixed_fee_amount",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "mkt_customer_perc",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("generator_perc", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractyear", "weekno", "billrunno", "direction_id"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billing_direction_reconciliatn_lastchanged"),
        "billing_direction_reconciliatn",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billing_eftshortfall_amount",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=20), nullable=False),
        sa.Column(
            "shortfall_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("shortfall", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("shortfall_company_id", sa.String(length=20), nullable=True),
        sa.Column(
            "company_shortfall_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "participant_net_energy",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "company_net_energy",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("contractyear", "weekno", "billrunno", "participantid"),
        schema="mms",
    )
    op.create_table(
        "billing_eftshortfall_detail",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=20), nullable=False),
        sa.Column("transaction_type", sa.String(length=40), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "participantid",
            "transaction_type",
        ),
        schema="mms",
    )
    op.create_table(
        "billing_gst_detail",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("bas_class", sa.String(length=30), nullable=False),
        sa.Column("transaction_type", sa.String(length=30), nullable=False),
        sa.Column(
            "gst_exclusive_amount",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("gst_amount", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "participantid",
            "bas_class",
            "transaction_type",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billing_gst_detail_lastchanged"),
        "billing_gst_detail",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billing_gst_summary",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("bas_class", sa.String(length=30), nullable=False),
        sa.Column(
            "gst_exclusive_amount",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("gst_amount", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear", "weekno", "billrunno", "participantid", "bas_class"
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billing_gst_summary_lastchanged"),
        "billing_gst_summary",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billing_mr_payment",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("mr_date", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("mr_amount", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "mr_date",
            "regionid",
            "duid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billing_mr_payment_lastchanged"),
        "billing_mr_payment",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billing_mr_recovery",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("mr_date", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("mr_amount", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "mr_date",
            "regionid",
            "duid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billing_mr_recovery_lastchanged"),
        "billing_mr_recovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billing_mr_shortfall",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("mr_date", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("age", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("rsa", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "mr_date",
            "regionid",
            "participantid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billing_mr_shortfall_lastchanged"),
        "billing_mr_shortfall",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billing_mr_summary",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("mr_date", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("total_payments", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("total_recovery", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("total_rsa", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("aage", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractyear", "weekno", "billrunno", "mr_date", "regionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billing_mr_summary_lastchanged"),
        "billing_mr_summary",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billing_nmas_tst_payments",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=20), nullable=False),
        sa.Column("service", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("payment_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "participantid",
            "service",
            "contractid",
        ),
        schema="mms",
    )
    op.create_table(
        "billing_nmas_tst_recovery",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=20), nullable=False),
        sa.Column("service", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("rbf", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("test_payment", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "recovery_start_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "recovery_end_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "participant_energy",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("region_energy", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("nem_energy", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "customer_proportion",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "generator_proportion",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "participant_generation",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("nem_generation", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("recovery_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "participantid",
            "service",
            "contractid",
            "regionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billing_nmas_tst_recovery_lastchanged"),
        "billing_nmas_tst_recovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billing_nmas_tst_recvry_rbf",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("service", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("rbf", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("payment_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("recovery_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "service",
            "contractid",
            "regionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billing_nmas_tst_recvry_rbf_lastchanged"),
        "billing_nmas_tst_recvry_rbf",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billing_nmas_tst_recvry_trk",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column(
            "recovery_contractyear",
            sa.Numeric(precision=4, scale=0),
            nullable=False,
        ),
        sa.Column("recovery_weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column(
            "recovery_billrunno",
            sa.Numeric(precision=3, scale=0),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "recovery_contractyear",
            "recovery_weekno",
            "recovery_billrunno",
        ),
        schema="mms",
    )
    op.create_table(
        "billing_res_trader_payment",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("contractid", sa.String(length=20), nullable=False),
        sa.Column("payment_type", sa.String(length=40), nullable=False),
        sa.Column("participantid", sa.String(length=20), nullable=False),
        sa.Column("payment_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "contractid",
            "payment_type",
            "participantid",
        ),
        schema="mms",
    )
    op.create_table(
        "billing_res_trader_recovery",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column("participantid", sa.String(length=20), nullable=False),
        sa.Column("recovery_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear", "weekno", "billrunno", "regionid", "participantid"
        ),
        schema="mms",
    )
    op.create_table(
        "billing_secdep_interest_pay",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("security_deposit_id", sa.String(length=20), nullable=False),
        sa.Column("participantid", sa.String(length=20), nullable=False),
        sa.Column("interest_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("interest_calc_type", sa.String(length=20), nullable=True),
        sa.Column("interest_acct_id", sa.String(length=20), nullable=True),
        sa.Column("interest_rate", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "security_deposit_id",
            "participantid",
        ),
        schema="mms",
    )
    op.create_table(
        "billing_secdep_interest_rate",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("interest_acct_id", sa.String(length=20), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("interest_rate", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "interest_acct_id",
            "effectivedate",
        ),
        schema="mms",
    )
    op.create_table(
        "billing_secdeposit_application",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=20), nullable=False),
        sa.Column(
            "application_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("contractyear", "weekno", "billrunno", "participantid"),
        schema="mms",
    )
    op.create_table(
        "billingapccompensation",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("apccompensation", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear", "weekno", "billrunno", "participantid", "regionid"
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingapccompensation_lastchanged"),
        "billingapccompensation",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingapcrecovery",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("apcrecovery", sa.Numeric(precision=15, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear", "weekno", "billrunno", "participantid", "regionid"
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingapcrecovery_lastchanged"),
        "billingapcrecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingaspayments",
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("connectionpointid", sa.String(length=10), nullable=False),
        sa.Column("raise6sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower6sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise60sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower60sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("agc", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("fcascomp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("loadshed", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rgul", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rguu", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("reactivepower", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("systemrestart", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lower5min", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise5min", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lowerreg", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raisereg", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "availability_reactive",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "availability_reactive_rbt",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "participantid",
            "connectionpointid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingaspayments_lastchanged"),
        "billingaspayments",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingasrecovery",
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("raise6sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower6sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise60sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower60sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("agc", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("fcascomp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("loadshed", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rgul", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rguu", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("reactivepower", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("systemrestart", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("raise6sec_gen", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower6sec_gen", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise60sec_gen", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower60sec_gen", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("agc_gen", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("fcascomp_gen", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("loadshed_gen", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rgul_gen", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rguu_gen", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "reactivepower_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "systemrestart_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower5min", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise5min", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lowerreg", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raisereg", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower5min_gen", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("raise5min_gen", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lowerreg_gen", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("raisereg_gen", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column(
            "availability_reactive",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "availability_reactive_rbt",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "availability_reactive_gen",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "availability_reactive_rbt_gen",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "regionid", "contractyear", "weekno", "billrunno", "participantid"
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingasrecovery_lastchanged"),
        "billingasrecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingcalendar",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "preliminarystatementdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "finalstatementdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("paymentdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "revision1_statementdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "revision2_statementdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("contractyear", "weekno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingcalendar_lastchanged"),
        "billingcalendar",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingcpdata",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("connectionpointid", sa.String(length=10), nullable=False),
        sa.Column("aggregateenergy", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("purchases", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("mda", sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "participantid",
            "connectionpointid",
            "mda",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingcpdata_lastchanged"),
        "billingcpdata",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingcpdata_participantid"),
        "billingcpdata",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingcpsum",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("participanttype", sa.String(length=10), nullable=False),
        sa.Column("previousamount", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("adjustedamount", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("adjustmentweekno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("adjustmentrunno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "participantid",
            "participanttype",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingcpsum_lastchanged"),
        "billingcpsum",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingcpsum_participantid"),
        "billingcpsum",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingcustexcessgen",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column(
            "excessgenpayment",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "participantid",
            "settlementdate",
            "periodid",
            "regionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingcustexcessgen_lastchanged"),
        "billingcustexcessgen",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingdaytrk",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractyear", "weekno", "billrunno", "settlementdate"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingdaytrk_lastchanged"),
        "billingdaytrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingexcessgen",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column(
            "excessenergycost",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "participantid",
            "settlementdate",
            "periodid",
            "regionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingexcessgen_lastchanged"),
        "billingexcessgen",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingexcessgen_participantid"),
        "billingexcessgen",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingfees",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("marketfeeid", sa.String(length=10), nullable=False),
        sa.Column("rate", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("energy", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("value", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("participantcategoryid", sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "participantid",
            "marketfeeid",
            "participantcategoryid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingfees_lastchanged"),
        "billingfees",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingfees_participantid"),
        "billingfees",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingfinancialadjustments",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("participanttype", sa.String(length=10), nullable=True),
        sa.Column("adjustmentitem", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("value", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("financialcode", sa.Numeric(precision=10, scale=0), nullable=True),
        sa.Column("bas_class", sa.String(length=30), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "participantid",
            "adjustmentitem",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingfinancialadjustments_lastchanged"),
        "billingfinancialadjustments",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billinggendata",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("connectionpointid", sa.String(length=10), nullable=False),
        sa.Column("stationid", sa.String(length=10), nullable=True),
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column("aggregateenergy", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("sales", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("purchases", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("purchasedenergy", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("mda", sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "participantid",
            "connectionpointid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billinggendata_lastchanged"),
        "billinggendata",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billinggendata_participantid"),
        "billinggendata",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billinginterresidues",
        sa.Column("allocation", sa.Numeric(precision=6, scale=3), nullable=True),
        sa.Column("totalsurplus", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("surplusvalue", sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint(
            "interconnectorid",
            "contractyear",
            "weekno",
            "billrunno",
            "participantid",
            "regionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billinginterresidues_lastchanged"),
        "billinginterresidues",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingintervention",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column(
            "marketintervention",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalintervention",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractyear", "weekno", "billrunno", "participantid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingintervention_lastchanged"),
        "billingintervention",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billinginterventionregion",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column(
            "regionintervention",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear", "weekno", "billrunno", "participantid", "regionid"
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billinginterventionregion_lastchanged"),
        "billinginterventionregion",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingintraresidues",
        sa.Column("allocation", sa.Numeric(precision=6, scale=3), nullable=True),
        sa.Column("totalsurplus", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("surplusvalue", sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint(
            "contractyear", "weekno", "billrunno", "participantid", "regionid"
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingintraresidues_lastchanged"),
        "billingintraresidues",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingiraucsurplus",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("residueyear", sa.Numeric(precision=4, scale=0), nullable=True),
        sa.Column("quarter", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("contractid", sa.String(length=30), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("totalresidues", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("adjustment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "contractid",
            "participantid",
            "interconnectorid",
            "fromregionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingiraucsurplus_lastchanged"),
        "billingiraucsurplus",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingiraucsurplussum",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("residueyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("quarter", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("totalsurplus", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("auctionfees", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("actualpayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("auctionfees_gst", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "csp_derogation_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("unadjusted_irsr", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "negative_residues",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "residueyear",
            "quarter",
            "billrunno",
            "interconnectorid",
            "fromregionid",
            "participantid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingiraucsurplussum_lastchanged"),
        "billingiraucsurplussum",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingirfm",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("irfmpayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractyear", "weekno", "billrunno", "participantid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingirfm_lastchanged"),
        "billingirfm",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingirnspsurplus",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("residueyear", sa.Numeric(precision=4, scale=0), nullable=True),
        sa.Column("quarter", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("contractid", sa.String(length=30), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("totalresidues", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("adjustment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "contractid",
            "participantid",
            "interconnectorid",
            "fromregionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingirnspsurplus_lastchanged"),
        "billingirnspsurplus",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingirnspsurplussum",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("residueyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("quarter", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("totalsurplus", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("auctionfees", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("auctionfees_gst", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "csp_derogation_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("unadjusted_irsr", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "residueyear",
            "quarter",
            "billrunno",
            "interconnectorid",
            "fromregionid",
            "participantid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingirnspsurplussum_lastchanged"),
        "billingirnspsurplussum",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingirpartsurplus",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("residueyear", sa.Numeric(precision=4, scale=0), nullable=True),
        sa.Column("quarter", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("contractid", sa.String(length=30), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("totalresidues", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("adjustment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("actualpayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "contractid",
            "participantid",
            "interconnectorid",
            "fromregionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingirpartsurplus_lastchanged"),
        "billingirpartsurplus",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingirpartsurplussum",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("residueyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("quarter", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("totalsurplus", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("auctionfees", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("actualpayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("auctionfees_gst", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "csp_derogation_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("unadjusted_irsr", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "auctionfees_totalgross_adj",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "residueyear",
            "quarter",
            "billrunno",
            "interconnectorid",
            "fromregionid",
            "participantid",
        ),
        schema="mms",
    )
    op.create_index(
        "billingirpartsurplussum_i01",
        "billingirpartsurplussum",
        ["residueyear", "quarter"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingirpartsurplussum_lastchanged"),
        "billingirpartsurplussum",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingprioradjustments",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("adjcontractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("adjweekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("adjbillrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("prevamount", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("adjamount", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("irn", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("irp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("interestamount", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("irsr_prevamount", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("irsr_adjamount", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "irsr_interestamount",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "adjcontractyear",
            "adjweekno",
            "adjbillrunno",
            "participantid",
        ),
        schema="mms",
    )
    op.create_index(
        "billingprioradjustments_ndx2",
        "billingprioradjustments",
        ["participantid", "lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingprioradjustments_lastchanged"),
        "billingprioradjustments",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingrealloc",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("counterparty", sa.String(length=10), nullable=False),
        sa.Column("value", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "participantid",
            "counterparty",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingrealloc_lastchanged"),
        "billingrealloc",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingrealloc_participantid"),
        "billingrealloc",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingrealloc_detail",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("counterparty", sa.String(length=10), nullable=False),
        sa.Column("reallocationid", sa.String(length=20), nullable=False),
        sa.Column("value", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "participantid",
            "counterparty",
            "reallocationid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingrealloc_detail_lastchanged"),
        "billingrealloc_detail",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingregionexports",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("exportto", sa.String(length=10), nullable=False),
        sa.Column("energy", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("value", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("surplusenergy", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("surplusvalue", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractyear", "weekno", "billrunno", "regionid", "exportto"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingregionexports_lastchanged"),
        "billingregionexports",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingregionfigures",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("energyout", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("valueout", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("energypurchased", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("valuepurchased", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("excessgen", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("reservetrading", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("intcompo", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("adminpricecompo", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("settsurplus", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("aspayment", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("poolfees", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractyear", "weekno", "billrunno", "regionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingregionfigures_lastchanged"),
        "billingregionfigures",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingregionimports",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("importfrom", sa.String(length=10), nullable=False),
        sa.Column("energy", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("value", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("surplusenergy", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("surplusvalue", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractyear", "weekno", "billrunno", "regionid", "importfrom"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingregionimports_lastchanged"),
        "billingregionimports",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingreserverecovery",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("marketreserve", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractyear", "weekno", "billrunno", "participantid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingreserverecovery_lastchanged"),
        "billingreserverecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingreserveregionrecovery",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("regionreserve", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear", "weekno", "billrunno", "participantid", "regionid"
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingreserveregionrecovery_lastchanged"),
        "billingreserveregionrecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingreservetrader",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("marketreserve", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("totalreserve", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "totalcapdifference",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("contractyear", "weekno", "billrunno", "participantid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingreservetrader_lastchanged"),
        "billingreservetrader",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingreservetraderregion",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("regionreserve", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear", "weekno", "billrunno", "participantid", "regionid"
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingreservetraderregion_lastchanged"),
        "billingreservetraderregion",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingruntrk",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("status", sa.String(length=6), nullable=True),
        sa.Column("adj_cleared", sa.String(length=1), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=10), nullable=True),
        sa.Column("postdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("postby", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("receiptpostdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("receiptpostby", sa.String(length=10), nullable=True),
        sa.Column("paymentpostdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("paymentpostby", sa.String(length=10), nullable=True),
        sa.Column("shortfall", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("makeup", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.PrimaryKeyConstraint("contractyear", "weekno", "billrunno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingruntrk_lastchanged"),
        "billingruntrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billingsmelterreduction",
        sa.Column("contractyear", sa.Numeric(precision=22, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=22, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=22, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("rate1", sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column("ra1", sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column("rate2", sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column("ra2", sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column("te", sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column("pcsd", sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractyear", "weekno", "billrunno", "participantid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingsmelterreduction_lastchanged"),
        "billingsmelterreduction",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billingsmelterreduction_participantid"),
        "billingsmelterreduction",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billinterventionrecovery",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column(
            "marketintervention",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractyear", "weekno", "billrunno", "participantid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billinterventionrecovery_lastchanged"),
        "billinterventionrecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billinterventionregionrecovery",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column(
            "regionintervention",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractyear", "weekno", "billrunno", "participantid", "regionid"
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billinterventionregionrecovery_lastchanged"),
        "billinterventionregionrecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billsmelterrate",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("contractyear", sa.Numeric(precision=22, scale=0), nullable=False),
        sa.Column("rar1", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("rar2", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno", "contractyear"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billsmelterrate_lastchanged"),
        "billsmelterrate",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "billwhitehole",
        sa.Column("contractyear", sa.Numeric(precision=22, scale=0), nullable=False),
        sa.Column("weekno", sa.Numeric(precision=22, scale=0), nullable=False),
        sa.Column("billrunno", sa.Numeric(precision=22, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("nl", sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column(
            "participantdemand",
            sa.Numeric(precision=15, scale=6),
            nullable=True,
        ),
        sa.Column("regiondemand", sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column(
            "whiteholepayment",
            sa.Numeric(precision=15, scale=6),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint(
            "contractyear",
            "weekno",
            "billrunno",
            "participantid",
            "interconnectorid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_billwhitehole_lastchanged"),
        "billwhitehole",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "connectionpoint",
        sa.Column("connectionpointid", sa.String(length=10), nullable=False),
        sa.Column("connectionpointname", sa.String(length=80), nullable=True),
        sa.Column("connectionpointtype", sa.String(length=20), nullable=True),
        sa.Column("address1", sa.String(length=80), nullable=True),
        sa.Column("address2", sa.String(length=80), nullable=True),
        sa.Column("address3", sa.String(length=80), nullable=True),
        sa.Column("address4", sa.String(length=80), nullable=True),
        sa.Column("city", sa.String(length=40), nullable=True),
        sa.Column("state", sa.String(length=10), nullable=True),
        sa.Column("postcode", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("connectionpointid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_connectionpoint_lastchanged"),
        "connectionpoint",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "connectionpointdetails",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("connectionpointid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("transmissioncptid", sa.String(length=10), nullable=True),
        sa.Column("meterdataprovider", sa.String(length=10), nullable=True),
        sa.Column(
            "transmissionlossfactor",
            sa.Numeric(precision=7, scale=5),
            nullable=True,
        ),
        sa.Column(
            "distributionlossfactor",
            sa.Numeric(precision=7, scale=5),
            nullable=True,
        ),
        sa.Column("networkserviceprovider", sa.String(length=10), nullable=True),
        sa.Column("finresporgan", sa.String(length=10), nullable=True),
        sa.Column(
            "nationalmeterinstallid",
            sa.Numeric(precision=7, scale=5),
            nullable=True,
        ),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("inuse", sa.String(length=1), nullable=True),
        sa.Column("lnsp", sa.String(length=10), nullable=True),
        sa.Column("mda", sa.String(length=10), nullable=True),
        sa.Column("rolr", sa.String(length=10), nullable=True),
        sa.Column("rp", sa.String(length=10), nullable=True),
        sa.Column("aggregateddata", sa.String(length=1), nullable=True),
        sa.Column("valid_todate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lr", sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno", "connectionpointid"),
        schema="mms",
    )
    op.create_index(
        "connectionpointdetai_ndx2",
        "connectionpointdetails",
        ["meterdataprovider", "networkserviceprovider", "finresporgan"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_connectionpointdetails_connectionpointid"),
        "connectionpointdetails",
        ["connectionpointid"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_connectionpointdetails_lastchanged"),
        "connectionpointdetails",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "connectionpointoperatingsta",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("connectionpointid", sa.String(length=10), nullable=False),
        sa.Column("operatingstatus", sa.String(length=16), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno", "connectionpointid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_connectionpointoperatingsta_connectionpointid"),
        "connectionpointoperatingsta",
        ["connectionpointid"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_connectionpointoperatingsta_lastchanged"),
        "connectionpointoperatingsta",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "constraintrelaxation_ocd",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("constraintid", sa.String(length=20), nullable=False),
        sa.Column("rhs", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "versionno",
            sa.Numeric(precision=3, scale=0),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("settlementdate", "runno", "constraintid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_constraintrelaxation_ocd_lastchanged"),
        "constraintrelaxation_ocd",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "contractagc",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column("crr", sa.Numeric(precision=4, scale=0), nullable=True),
        sa.Column("crl", sa.Numeric(precision=4, scale=0), nullable=True),
        sa.Column("rlprice", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("ccprice", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("bs", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractid", "versionno"),
        schema="mms",
    )
    op.create_index(
        "contractagc_ndx2",
        "contractagc",
        ["participantid", "contractid"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_contractagc_lastchanged"),
        "contractagc",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "contractgovernor",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column("ccprice", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "lower60secbreakpoint",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column("lower60secmax", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column(
            "lower6secbreakpoint",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column("lower6secmax", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column(
            "raise60secbreakpoint",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "raise60seccapacity",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column("raise60secmax", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column(
            "raise6secbreakpoint",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "raise6seccapacity",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column("raise6secmax", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column(
            "price6secraisemandatory",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "quant6secraisemandatory",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "price6secraisecontract",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "quant6secraisecontract",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "price60secraisemandatory",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "quant60secraisemandatory",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "price60secraisecontract",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "quant60secraisecontract",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "price6seclowermandatory",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "quant6seclowermandatory",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "price6seclowercontract",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "quant6seclowercontract",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "price60seclowermandatory",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "quant60seclowermandatory",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "price60seclowercontract",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "quant60seclowercontract",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("deadbandup", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("deadbanddown", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column(
            "droop6secraisebreakpoint",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "droop6secraisecapacity",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "droop6secraisemax",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "droop60secraisebreakpoint",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "droop60secraisecapacity",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "droop60secraisemax",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "droop6seclowerbreakpoint",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "droop6seclowermax",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "droop60seclowerbreakpoint",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "droop60seclowermax",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_contractgovernor_lastchanged"),
        "contractgovernor",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_contractgovernor_participantid"),
        "contractgovernor",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "contractloadshed",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column("lseprice", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("mcpprice", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("tenderedprice", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("lscr", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("ilscalingfactor", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower60secbreakpoint",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column("lower60secmax", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column(
            "lower6secbreakpoint",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column("lower6secmax", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column(
            "raise60secbreakpoint",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "raise60seccapacity",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column("raise60secmax", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column(
            "raise6secbreakpoint",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "raise6seccapacity",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column("raise6secmax", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column(
            "price6secraisemandatory",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "quant6secraisemandatory",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "price6secraisecontract",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "quant6secraisecontract",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "price60secraisemandatory",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "quant60secraisemandatory",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "price60secraisecontract",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "quant60secraisecontract",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "price6seclowermandatory",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "quant6seclowermandatory",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "price6seclowercontract",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "quant6seclowercontract",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "price60seclowermandatory",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "quant60seclowermandatory",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "price60seclowercontract",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "quant60seclowercontract",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "default_testingpayment_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "service_start_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("contractid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_contractloadshed_lastchanged"),
        "contractloadshed",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_contractloadshed_participantid"),
        "contractloadshed",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "contractreactivepower",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column("synccompensation", sa.String(length=1), nullable=True),
        sa.Column("mvaraprice", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("mvareprice", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("mvargprice", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("ccprice", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("mta", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("mtg", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("mmca", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("mmcg", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("eu", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("pp", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("bs", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "default_testingpayment_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "service_start_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "availability_mwh_threshold",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("mvar_threshold", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("rebate_cap", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "rebate_amount_per_mvar",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "isrebateapplicable",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("contractid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_contractreactivepower_lastchanged"),
        "contractreactivepower",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_contractreactivepower_participantid"),
        "contractreactivepower",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "contractreserveflag",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("rcf", sa.CHAR(length=1), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractid", "versionno", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_contractreserveflag_lastchanged"),
        "contractreserveflag",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "contractreservethreshold",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("cra", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("cre", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("cru", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("cta", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("cte", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("ctu", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_contractreservethreshold_lastchanged"),
        "contractreservethreshold",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "contractreservetrader",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("startperiod", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("endperiod", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column(
            "deregistrationdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "deregistrationperiod",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint("contractid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_contractreservetrader_lastchanged"),
        "contractreservetrader",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "contractrestartservices",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("restarttype", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("rcprice", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("triptohouselevel", sa.Numeric(precision=5, scale=0), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "default_testingpayment_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "service_start_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("contractid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_contractrestartservices_lastchanged"),
        "contractrestartservices",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_contractrestartservices_participantid"),
        "contractrestartservices",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "contractrestartunits",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractid", "versionno", "duid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_contractrestartunits_contractid"),
        "contractrestartunits",
        ["contractid"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_contractrestartunits_lastchanged"),
        "contractrestartunits",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "contractunitloading",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column("rprice", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("suprice", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("ccprice", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("acr", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("bs", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("pp", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("eu", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_contractunitloading_lastchanged"),
        "contractunitloading",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_contractunitloading_participantid"),
        "contractunitloading",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "contractunitunloading",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column("rprice", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("suprice", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("ccprice", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_contractunitunloading_lastchanged"),
        "contractunitunloading",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_contractunitunloading_participantid"),
        "contractunitunloading",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dayoffer",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("selfcommitflag", sa.String(length=1), nullable=True),
        sa.Column(
            "dailyenergyconstraint",
            sa.Numeric(precision=12, scale=6),
            nullable=True,
        ),
        sa.Column("entrytype", sa.String(length=20), nullable=True),
        sa.Column("contingencyprice", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("rebidexplanation", sa.String(length=64), nullable=True),
        sa.Column(
            "bandquantisationid",
            sa.Numeric(precision=2, scale=0),
            nullable=True,
        ),
        sa.Column("priceband1", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband2", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband3", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband4", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband5", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband6", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband7", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband8", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband9", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband10", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("maxrampup", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("maxrampdown", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("minimumload", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("t1", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("t2", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("t3", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("t4", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("normalstatus", sa.String(length=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("mr_factor", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "duid", "versionno", "offerdate"),
        schema="mms",
    )
    op.create_index(
        "dayoffer_ndx2",
        "dayoffer",
        ["duid", "lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dayoffer_lastchanged"),
        "dayoffer",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dayoffer_d",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("selfcommitflag", sa.String(length=1), nullable=True),
        sa.Column(
            "dailyenergyconstraint",
            sa.Numeric(precision=12, scale=6),
            nullable=True,
        ),
        sa.Column("entrytype", sa.String(length=20), nullable=True),
        sa.Column("contingencyprice", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("rebidexplanation", sa.String(length=64), nullable=True),
        sa.Column(
            "bandquantisationid",
            sa.Numeric(precision=2, scale=0),
            nullable=True,
        ),
        sa.Column("priceband1", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband2", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband3", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband4", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband5", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband6", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband7", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband8", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband9", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband10", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("maxrampup", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("maxrampdown", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("minimumload", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("t1", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("t2", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("t3", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("t4", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("normalstatus", sa.String(length=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("mr_factor", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "duid", "versionno", "offerdate"),
        schema="mms",
    )
    op.create_index(
        "dayoffer_d_ndx2",
        "dayoffer_d",
        ["duid", "lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dayoffer_d_lastchanged"),
        "dayoffer_d",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "daytrack",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("exanterunstatus", sa.String(length=15), nullable=True),
        sa.Column("exanterunno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("expostrunstatus", sa.String(length=15), nullable=True),
        sa.Column("expostrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "expostrunno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_daytrack_lastchanged"),
        "daytrack",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "defaultdayoffer",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("selfcommitflag", sa.String(length=1), nullable=True),
        sa.Column(
            "dailyenergyconstraint",
            sa.Numeric(precision=12, scale=6),
            nullable=True,
        ),
        sa.Column("entrytype", sa.String(length=20), nullable=True),
        sa.Column("contingencyprice", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("rebidexplanation", sa.String(length=64), nullable=True),
        sa.Column(
            "bandquantisationid",
            sa.Numeric(precision=2, scale=0),
            nullable=True,
        ),
        sa.Column("priceband1", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband2", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband3", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband4", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband5", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband6", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband7", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband8", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband9", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband10", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("maxrampup", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("maxrampdown", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("minimumload", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("t1", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("t2", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("t3", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("t4", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "duid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_defaultdayoffer_lastchanged"),
        "defaultdayoffer",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "defaultoffertrk",
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("filename", sa.String(length=40), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("duid", "effectivedate", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_defaultoffertrk_lastchanged"),
        "defaultoffertrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "defaultperoffer",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("selfdispatch", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("maxavail", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("fixedload", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("rocup", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("rocdown", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("bandavail1", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail2", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail3", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail4", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail5", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail6", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail7", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail8", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail9", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail10", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column(
            "pasaavailability",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("settlementdate", "duid", "periodid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_defaultperoffer_lastchanged"),
        "defaultperoffer",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "deltamw",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("deltamw", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lower5min", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lower60sec", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lower6sec", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("raise5min", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("raise60sec", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("raise6sec", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("raisereg", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lowerreg", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "versionno", "regionid", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_deltamw_lastchanged"),
        "deltamw",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "demandoperationalactual",
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column(
            "operational_demand",
            sa.Numeric(precision=10, scale=0),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("interval_datetime", "regionid"),
        schema="mms",
    )
    op.create_table(
        "demandoperationalforecast",
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column("load_date", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "operational_demand_poe10",
            sa.Numeric(precision=15, scale=2),
            nullable=True,
        ),
        sa.Column(
            "operational_demand_poe50",
            sa.Numeric(precision=15, scale=2),
            nullable=True,
        ),
        sa.Column(
            "operational_demand_poe90",
            sa.Numeric(precision=15, scale=2),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("interval_datetime", "regionid"),
        schema="mms",
    )
    op.create_table(
        "dispatch_constraint_fcas_ocd",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("constraintid", sa.String(length=20), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("rhs", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("marginalvalue", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("violationdegree", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "runno",
            "intervention",
            "constraintid",
            "versionno",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatch_constraint_fcas_ocd_lastchanged"),
        "dispatch_constraint_fcas_ocd",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dispatch_fcas_req",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("genconid", sa.String(length=20), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("bidtype", sa.String(length=10), nullable=False),
        sa.Column(
            "genconeffectivedate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("genconversionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("marginalvalue", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("base_cost", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("adjusted_cost", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("estimated_cmpf", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("estimated_crmpf", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "recovery_factor_cmpf",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "recovery_factor_crmpf",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "runno",
            "intervention",
            "genconid",
            "regionid",
            "bidtype",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatch_fcas_req_lastchanged"),
        "dispatch_fcas_req",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dispatch_interconnection",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("from_regionid", sa.String(length=20), nullable=False),
        sa.Column("to_regionid", sa.String(length=20), nullable=False),
        sa.Column(
            "dispatchinterval",
            sa.Numeric(precision=22, scale=0),
            nullable=True,
        ),
        sa.Column("irlf", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("meteredmwflow", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column(
            "from_region_mw_losses",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "to_region_mw_losses",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "runno",
            "intervention",
            "from_regionid",
            "to_regionid",
        ),
        schema="mms",
    )
    op.create_table(
        "dispatch_local_price",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=20), nullable=False),
        sa.Column(
            "local_price_adjustment",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.Column(
            "locally_constrained",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("settlementdate", "duid"),
        schema="mms",
    )
    op.create_table(
        "dispatch_mnspbidtrk",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("linkid", sa.String(length=10), nullable=False),
        sa.Column(
            "offersettlementdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "offereffectivedate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("offerversionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "runno", "participantid", "linkid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatch_mnspbidtrk_lastchanged"),
        "dispatch_mnspbidtrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dispatch_mr_schedule_trk",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("mr_date", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "version_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "regionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatch_mr_schedule_trk_lastchanged"),
        "dispatch_mr_schedule_trk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dispatch_price_revision",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("bidtype", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("rrp_new", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrp_old", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "runno",
            "intervention",
            "regionid",
            "bidtype",
            "versionno",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatch_price_revision_lastchanged"),
        "dispatch_price_revision",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dispatch_unit_conformance",
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("duid", sa.String(length=20), nullable=False),
        sa.Column("totalcleared", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("actualmw", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("roc", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("availability", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lowerreg", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("raisereg", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("striglm", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("ltriglm", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("mwerror", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("max_mwerror", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lecount", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("secount", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("participant_status_action", sa.String(length=100), nullable=True),
        sa.Column("operating_mode", sa.String(length=20), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("interval_datetime", "duid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatch_unit_conformance_lastchanged"),
        "dispatch_unit_conformance",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dispatch_unit_scada",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=20), nullable=False),
        sa.Column("scadavalue", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "duid"),
        schema="mms",
    )
    op.create_table(
        "dispatchableunit",
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("duname", sa.String(length=20), nullable=True),
        sa.Column("unittype", sa.String(length=20), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("duid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatchableunit_lastchanged"),
        "dispatchableunit",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dispatchbidtrk",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column(
            "offereffectivedate",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("offerversionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("bidtype", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "runno",
            "offereffectivedate",
            "offerversionno",
            "duid",
        ),
        schema="mms",
    )
    op.create_index(
        "dispatchbidtrk_ndx2",
        "dispatchbidtrk",
        ["duid", "lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatchbidtrk_lastchanged"),
        "dispatchbidtrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dispatchblockedconstraint",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("constraintid", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("settlementdate", "runno", "constraintid"),
        schema="mms",
    )
    op.create_table(
        "dispatchcase_ocd",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "runno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatchcase_ocd_lastchanged"),
        "dispatchcase_ocd",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dispatchcasesolution",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("casesubtype", sa.String(length=3), nullable=True),
        sa.Column("solutionstatus", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("spdversion", sa.String(length=20), nullable=True),
        sa.Column(
            "nonphysicallosses",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column("totalobjective", sa.Numeric(precision=27, scale=10), nullable=True),
        sa.Column(
            "totalareagenviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalinterconnectorviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalgenericviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalramprateviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalunitmwcapacityviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "total5minviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalregviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "total6secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "total60secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalasprofileviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalfaststartviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalenergyofferviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "switchruninitialstatus",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column(
            "switchrunbeststatus",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column(
            "switchrunbeststatus_int",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("settlementdate", "runno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatchcasesolution_lastchanged"),
        "dispatchcasesolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dispatchcasesolution_bnc",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("casesubtype", sa.String(length=3), nullable=True),
        sa.Column("solutionstatus", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("spdversion", sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column("startperiod", sa.String(length=20), nullable=True),
        sa.Column(
            "nonphysicallosses",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column("totalobjective", sa.Numeric(precision=27, scale=10), nullable=True),
        sa.Column(
            "totalareagenviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalinterconnectorviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalgenericviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalramprateviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalunitmwcapacityviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "total5minviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalregviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "total6secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "total60secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalenergyconstrviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalenergyofferviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalasprofileviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalfaststartviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "runno", "intervention"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatchcasesolution_bnc_lastchanged"),
        "dispatchcasesolution_bnc",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dispatchconstraint",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("constraintid", sa.String(length=20), nullable=False),
        sa.Column(
            "dispatchinterval",
            sa.Numeric(precision=22, scale=0),
            nullable=False,
        ),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("rhs", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("marginalvalue", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("violationdegree", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("duid", sa.String(length=20), nullable=True),
        sa.Column(
            "genconid_effectivedate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "genconid_versionno",
            sa.Numeric(precision=22, scale=0),
            nullable=True,
        ),
        sa.Column("lhs", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "runno",
            "constraintid",
            "dispatchinterval",
            "intervention",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatchconstraint_lastchanged"),
        "dispatchconstraint",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatchconstraint_settlementdate"),
        "dispatchconstraint",
        ["settlementdate"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dispatchinterconnectorres",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column(
            "dispatchinterval",
            sa.Numeric(precision=22, scale=0),
            nullable=False,
        ),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("meteredmwflow", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwlosses", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("marginalvalue", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("violationdegree", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("exportlimit", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("importlimit", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("marginalloss", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("exportgenconid", sa.String(length=20), nullable=True),
        sa.Column("importgenconid", sa.String(length=20), nullable=True),
        sa.Column("fcasexportlimit", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("fcasimportlimit", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "local_price_adjustment_export",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.Column(
            "locally_constrained_export",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column(
            "local_price_adjustment_import",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.Column(
            "locally_constrained_import",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "runno",
            "interconnectorid",
            "dispatchinterval",
            "intervention",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatchinterconnectorres_lastchanged"),
        "dispatchinterconnectorres",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dispatchload",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("tradetype", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column(
            "dispatchinterval",
            sa.Numeric(precision=22, scale=0),
            nullable=True,
        ),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("connectionpointid", sa.String(length=12), nullable=True),
        sa.Column("dispatchmode", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("agcstatus", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("initialmw", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("totalcleared", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rampdownrate", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rampuprate", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower5min", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower60sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower6sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise5min", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise60sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise6sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("downepf", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("upepf", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "marginal5minvalue",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "marginal60secvalue",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "marginal6secvalue",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("marginalvalue", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "violation5mindegree",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "violation60secdegree",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "violation6secdegree",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("violationdegree", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lowerreg", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raisereg", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("availability", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise6secflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("raise60secflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("raise5minflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("raiseregflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lower6secflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lower60secflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lower5minflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lowerregflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column(
            "raiseregavailability",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raiseregenablementmax",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raiseregenablementmin",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lowerregavailability",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lowerregenablementmax",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lowerregenablementmin",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6secactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "raise60secactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "raise5minactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "raiseregactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "lower6secactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "lower60secactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "lower5minactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "lowerregactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("semidispatchcap", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "runno", "duid", "intervention"),
        schema="mms",
    )
    op.create_index(
        "dispatchload_ndx2",
        "dispatchload",
        ["duid", "lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatchload_lastchanged"),
        "dispatchload",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dispatchload_bnc",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("connectionpointid", sa.String(length=12), nullable=True),
        sa.Column("dispatchmode", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("totalcleared", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raisereg", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise5min", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise60sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise6sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lowerreg", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower5min", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower60sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower6sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raiseregflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("raise5minflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("raise60secflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("raise6secflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lowerregflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lower5minflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lower60secflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lower6secflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "runno", "duid", "intervention"),
        schema="mms",
    )
    op.create_index(
        "dispatchload_bnc_ndx2",
        "dispatchload_bnc",
        ["duid", "lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatchload_bnc_lastchanged"),
        "dispatchload_bnc",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dispatchoffertrk",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("bidtype", sa.String(length=10), nullable=False),
        sa.Column(
            "bidsettlementdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("bidofferdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "duid", "bidtype"),
        schema="mms",
    )
    op.create_index(
        "dispatchoffertrk_ndx2",
        "dispatchoffertrk",
        ["duid", "lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatchoffertrk_lastchanged"),
        "dispatchoffertrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dispatchprice",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("dispatchinterval", sa.String(length=22), nullable=False),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("eep", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("apcflag", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column(
            "marketsuspendedflag",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("raise6secrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise6secrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise6secapcflag", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("raise60secrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise60secrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise60secapcflag",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column("raise5minrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise5minrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise5minapcflag", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("raiseregrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raiseregrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raiseregapcflag", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lower6secrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower6secrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower6secapcflag", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lower60secrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower60secrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower60secapcflag",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column("lower5minrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower5minrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower5minapcflag", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lowerregrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lowerregrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lowerregapcflag", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("price_status", sa.String(length=20), nullable=True),
        sa.Column(
            "pre_ap_energy_price",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "pre_ap_raise6_price",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "pre_ap_raise60_price",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "pre_ap_raise5min_price",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "pre_ap_raisereg_price",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "pre_ap_lower6_price",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "pre_ap_lower60_price",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "pre_ap_lower5min_price",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "pre_ap_lowerreg_price",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "cumul_pre_ap_energy_price",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "cumul_pre_ap_raise6_price",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "cumul_pre_ap_raise60_price",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "cumul_pre_ap_raise5min_price",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "cumul_pre_ap_raisereg_price",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "cumul_pre_ap_lower6_price",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "cumul_pre_ap_lower60_price",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "cumul_pre_ap_lower5min_price",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "cumul_pre_ap_lowerreg_price",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("ocd_status", sa.String(length=14), nullable=True),
        sa.Column("mii_status", sa.String(length=21), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "runno",
            "regionid",
            "dispatchinterval",
            "intervention",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatchprice_lastchanged"),
        "dispatchprice",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dispatchregionsum",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column(
            "dispatchinterval",
            sa.Numeric(precision=22, scale=0),
            nullable=False,
        ),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("totaldemand", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "availablegeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("availableload", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("demandforecast", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "dispatchablegeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "dispatchableload",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("netinterchange", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "excessgeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower5mindispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower5minimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower5minlocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower5minlocalprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower5minlocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower5minprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower5minreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower5minsupplyprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60secdispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60secimport",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60seclocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60seclocalprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60seclocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower60secprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower60secreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower60secsupplyprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower6secdispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower6secimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower6seclocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower6seclocalprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower6seclocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower6secprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower6secreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower6secsupplyprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise5mindispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise5minimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise5minlocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise5minlocalprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise5minlocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise5minprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise5minreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise5minsupplyprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60secdispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60secimport",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60seclocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60seclocalprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60seclocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise60secprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise60secreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise60secsupplyprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6secdispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise6secimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise6seclocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6seclocalprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6seclocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise6secprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise6secreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise6secsupplyprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "aggegatedispatcherror",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "aggregatedispatcherror",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("initialsupply", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("clearedsupply", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lowerregimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lowerreglocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lowerreglocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lowerregreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raiseregimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raisereglocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raisereglocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raiseregreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise5minlocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raisereglocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60seclocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6seclocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower5minlocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lowerreglocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60seclocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower6seclocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise5minviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raiseregviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower5minviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lowerregviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower6secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6secactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "raise60secactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "raise5minactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "raiseregactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "lower6secactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "lower60secactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "lower5minactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "lowerregactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("lorsurplus", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lrcsurplus", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column(
            "totalintermittentgeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "demand_and_nonschedgen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("uigf", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "semischedule_clearedmw",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "semischedule_compliancemw",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("ss_solar_uigf", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("ss_wind_uigf", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "ss_solar_clearedmw",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "ss_wind_clearedmw",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "ss_solar_compliancemw",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "ss_wind_compliancemw",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "runno",
            "regionid",
            "dispatchinterval",
            "intervention",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatchregionsum_lastchanged"),
        "dispatchregionsum",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dispatchtrk",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("reason", sa.String(length=64), nullable=True),
        sa.Column("spdrunno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "runno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dispatchtrk_lastchanged"),
        "dispatchtrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dualloc",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("gensetid", sa.String(length=20), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno", "duid", "gensetid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dualloc_duid"),
        "dualloc",
        ["duid"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dualloc_lastchanged"),
        "dualloc",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dudetail",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("connectionpointid", sa.String(length=10), nullable=True),
        sa.Column("voltlevel", sa.String(length=10), nullable=True),
        sa.Column(
            "registeredcapacity",
            sa.Numeric(precision=6, scale=0),
            nullable=True,
        ),
        sa.Column("agccapability", sa.String(length=1), nullable=True),
        sa.Column("dispatchtype", sa.String(length=10), nullable=True),
        sa.Column("maxcapacity", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("starttype", sa.String(length=20), nullable=True),
        sa.Column("normallyonflag", sa.String(length=1), nullable=True),
        sa.Column("physicaldetailsflag", sa.String(length=1), nullable=True),
        sa.Column("spinningreserveflag", sa.String(length=1), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("intermittentflag", sa.String(length=1), nullable=True),
        sa.Column("semischedule_flag", sa.String(length=1), nullable=True),
        sa.Column(
            "maxrateofchangeup",
            sa.Numeric(precision=6, scale=0),
            nullable=True,
        ),
        sa.Column(
            "maxrateofchangedown",
            sa.Numeric(precision=6, scale=0),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("effectivedate", "duid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dudetail_lastchanged"),
        "dudetail",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "dudetailsummary",
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("start_date", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("end_date", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("dispatchtype", sa.String(length=10), nullable=True),
        sa.Column("connectionpointid", sa.String(length=10), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("stationid", sa.String(length=10), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "transmissionlossfactor",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("starttype", sa.String(length=20), nullable=True),
        sa.Column(
            "distributionlossfactor",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "minimum_energy_price",
            sa.Numeric(precision=9, scale=2),
            nullable=True,
        ),
        sa.Column(
            "maximum_energy_price",
            sa.Numeric(precision=9, scale=2),
            nullable=True,
        ),
        sa.Column("schedule_type", sa.String(length=20), nullable=True),
        sa.Column("min_ramp_rate_up", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column(
            "min_ramp_rate_down",
            sa.Numeric(precision=6, scale=0),
            nullable=True,
        ),
        sa.Column("max_ramp_rate_up", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column(
            "max_ramp_rate_down",
            sa.Numeric(precision=6, scale=0),
            nullable=True,
        ),
        sa.Column("is_aggregated", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("duid", "start_date"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_dudetailsummary_lastchanged"),
        "dudetailsummary",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "emsmaster",
        sa.Column("spd_id", sa.String(length=21), nullable=False),
        sa.Column("spd_type", sa.String(length=1), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("grouping_id", sa.String(length=20), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("spd_id", "spd_type"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_emsmaster_lastchanged"),
        "emsmaster",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "forcemajeure",
        sa.Column("fmid", sa.String(length=10), nullable=False),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("startperiod", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("endperiod", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("apcstartdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("startauthorisedby", sa.String(length=15), nullable=True),
        sa.Column("endauthorisedby", sa.String(length=15), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("fmid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_forcemajeure_lastchanged"),
        "forcemajeure",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "forcemajeureregion",
        sa.Column("fmid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("fmid", "regionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_forcemajeureregion_lastchanged"),
        "forcemajeureregion",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "gdinstruct",
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column("stationid", sa.String(length=10), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("id", sa.Numeric(precision=22, scale=0), nullable=False),
        sa.Column("instructiontypeid", sa.String(length=10), nullable=True),
        sa.Column("instructionsubtypeid", sa.String(length=10), nullable=True),
        sa.Column("instructionclassid", sa.String(length=10), nullable=True),
        sa.Column("reason", sa.String(length=64), nullable=True),
        sa.Column("instlevel", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("issuedtime", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("targettime", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_gdinstruct_duid"),
        "gdinstruct",
        ["duid"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_gdinstruct_lastchanged"),
        "gdinstruct",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_gdinstruct_targettime"),
        "gdinstruct",
        ["targettime"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "gencondata",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("genconid", sa.String(length=20), nullable=False),
        sa.Column("constrainttype", sa.String(length=2), nullable=True),
        sa.Column("constraintvalue", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("description", sa.String(length=256), nullable=True),
        sa.Column("status", sa.String(length=8), nullable=True),
        sa.Column(
            "genericconstraintweight",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("dynamicrhs", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("dispatch", sa.String(length=1), nullable=True),
        sa.Column("predispatch", sa.String(length=1), nullable=True),
        sa.Column("stpasa", sa.String(length=1), nullable=True),
        sa.Column("mtpasa", sa.String(length=1), nullable=True),
        sa.Column("impact", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=128), nullable=True),
        sa.Column("limittype", sa.String(length=64), nullable=True),
        sa.Column("reason", sa.String(length=256), nullable=True),
        sa.Column("modifications", sa.String(length=256), nullable=True),
        sa.Column("additionalnotes", sa.String(length=256), nullable=True),
        sa.Column("p5min_scope_override", sa.String(length=2), nullable=True),
        sa.Column("lrc", sa.String(length=1), nullable=True),
        sa.Column("lor", sa.String(length=1), nullable=True),
        sa.Column("force_scada", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno", "genconid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_gencondata_lastchanged"),
        "gencondata",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "genconset",
        sa.Column("genconsetid", sa.String(length=20), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("genconid", sa.String(length=20), nullable=False),
        sa.Column("genconeffdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("genconversionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("genconsetid", "effectivedate", "versionno", "genconid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_genconset_lastchanged"),
        "genconset",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "genconsetinvoke",
        sa.Column("invocation_id", sa.Numeric(precision=9, scale=0), nullable=False),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("startperiod", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("genconsetid", sa.String(length=20), nullable=False),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("endperiod", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("startauthorisedby", sa.String(length=15), nullable=True),
        sa.Column("endauthorisedby", sa.String(length=15), nullable=True),
        sa.Column("intervention", sa.String(length=1), nullable=True),
        sa.Column("asconstrainttype", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "startintervaldatetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "endintervaldatetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("systemnormal", sa.String(length=1), nullable=True),
        sa.PrimaryKeyConstraint("invocation_id"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_genconsetinvoke_lastchanged"),
        "genconsetinvoke",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "genconsettrk",
        sa.Column("genconsetid", sa.String(length=20), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("description", sa.String(length=256), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("coverage", sa.String(length=64), nullable=True),
        sa.Column("modifications", sa.String(length=256), nullable=True),
        sa.Column("systemnormal", sa.String(length=1), nullable=True),
        sa.Column("outage", sa.String(length=256), nullable=True),
        sa.PrimaryKeyConstraint("genconsetid", "effectivedate", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_genconsettrk_lastchanged"),
        "genconsettrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "genericconstraintrhs",
        sa.Column("genconid", sa.String(length=20), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=22, scale=0), nullable=False),
        sa.Column("scope", sa.String(length=2), nullable=False),
        sa.Column("termid", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("groupid", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("spd_id", sa.String(length=21), nullable=True),
        sa.Column("spd_type", sa.String(length=1), nullable=True),
        sa.Column("factor", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("operation", sa.String(length=10), nullable=True),
        sa.Column("defaultvalue", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("parameterterm1", sa.String(length=12), nullable=True),
        sa.Column("parameterterm2", sa.String(length=12), nullable=True),
        sa.Column("parameterterm3", sa.String(length=12), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("genconid", "effectivedate", "versionno", "scope", "termid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_genericconstraintrhs_lastchanged"),
        "genericconstraintrhs",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "genericequationdesc",
        sa.Column("equationid", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=256), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("impact", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=128), nullable=True),
        sa.Column("limittype", sa.String(length=64), nullable=True),
        sa.Column("reason", sa.String(length=256), nullable=True),
        sa.Column("modifications", sa.String(length=256), nullable=True),
        sa.Column("additionalnotes", sa.String(length=256), nullable=True),
        sa.PrimaryKeyConstraint("equationid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_genericequationdesc_lastchanged"),
        "genericequationdesc",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "genericequationrhs",
        sa.Column("equationid", sa.String(length=20), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("termid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("groupid", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("spd_id", sa.String(length=21), nullable=True),
        sa.Column("spd_type", sa.String(length=1), nullable=True),
        sa.Column("factor", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("operation", sa.String(length=10), nullable=True),
        sa.Column("defaultvalue", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("parameterterm1", sa.String(length=12), nullable=True),
        sa.Column("parameterterm2", sa.String(length=12), nullable=True),
        sa.Column("parameterterm3", sa.String(length=12), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("equationid", "effectivedate", "versionno", "termid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_genericequationrhs_lastchanged"),
        "genericequationrhs",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "genmeter",
        sa.Column("meterid", sa.String(length=12), nullable=False),
        sa.Column("gensetid", sa.String(length=20), nullable=True),
        sa.Column("connectionpointid", sa.String(length=10), nullable=True),
        sa.Column("stationid", sa.String(length=10), nullable=True),
        sa.Column("metertype", sa.String(length=20), nullable=True),
        sa.Column("meterclass", sa.String(length=10), nullable=True),
        sa.Column("voltagelevel", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("applydate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("authorisedby", sa.String(length=10), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("comdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("decomdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("meterid", "applydate", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_genmeter_lastchanged"),
        "genmeter",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_genmeter_stationid"),
        "genmeter",
        ["stationid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "genunitmtrinperiod",
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=6, scale=0), nullable=False),
        sa.Column("connectionpointid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("genunitid", sa.String(length=10), nullable=True),
        sa.Column("stationid", sa.String(length=10), nullable=True),
        sa.Column(
            "importenergyvalue",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "exportenergyvalue",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "importreactivevalue",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "exportreactivevalue",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("mda", sa.String(length=10), nullable=False),
        sa.Column(
            "local_retailer",
            sa.String(length=10),
            server_default=sa.text("'POOLNSW'::character varying"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "participantid",
            "settlementdate",
            "versionno",
            "connectionpointid",
            "periodid",
            "mda",
            "local_retailer",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_genunitmtrinperiod_lastchanged"),
        "genunitmtrinperiod",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_genunitmtrinperiod_stationid"),
        "genunitmtrinperiod",
        ["stationid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "genunits",
        sa.Column("gensetid", sa.String(length=20), nullable=False),
        sa.Column("stationid", sa.String(length=10), nullable=True),
        sa.Column("setlossfactor", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("cdindicator", sa.String(length=10), nullable=True),
        sa.Column("agcflag", sa.String(length=2), nullable=True),
        sa.Column("spinningflag", sa.String(length=2), nullable=True),
        sa.Column("voltlevel", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column(
            "registeredcapacity",
            sa.Numeric(precision=6, scale=0),
            nullable=True,
        ),
        sa.Column("dispatchtype", sa.String(length=10), nullable=True),
        sa.Column("starttype", sa.String(length=20), nullable=True),
        sa.Column("mktgeneratorind", sa.String(length=10), nullable=True),
        sa.Column("normalstatus", sa.String(length=10), nullable=True),
        sa.Column("maxcapacity", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("gensettype", sa.String(length=15), nullable=True),
        sa.Column("gensetname", sa.String(length=40), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "co2e_emissions_factor",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("co2e_energy_source", sa.String(length=100), nullable=True),
        sa.Column("co2e_data_source", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("gensetid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_genunits_lastchanged"),
        "genunits",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "genunits_unit",
        sa.Column("gensetid", sa.String(length=20), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=6, scale=0), nullable=False),
        sa.Column("unit_grouping_label", sa.String(length=20), nullable=False),
        sa.Column("unit_count", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("unit_size", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column("unit_max_size", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column("aggregation_flag", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("gensetid", "effectivedate", "versionno", "unit_grouping_label"),
        schema="mms",
    )
    op.create_table(
        "gst_bas_class",
        sa.Column("bas_class", sa.String(length=30), nullable=False),
        sa.Column("description", sa.String(length=100), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("bas_class"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_gst_bas_class_lastchanged"),
        "gst_bas_class",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "gst_rate",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("bas_class", sa.String(length=30), nullable=False),
        sa.Column("gst_rate", sa.Numeric(precision=8, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno", "bas_class"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_gst_rate_lastchanged"),
        "gst_rate",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "gst_transaction_class",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("transaction_type", sa.String(length=30), nullable=False),
        sa.Column("bas_class", sa.String(length=30), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno", "transaction_type", "bas_class"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_gst_transaction_class_lastchanged"),
        "gst_transaction_class",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "gst_transaction_type",
        sa.Column("transaction_type", sa.String(length=30), nullable=False),
        sa.Column("description", sa.String(length=100), nullable=True),
        sa.Column("gl_financialcode", sa.String(length=10), nullable=True),
        sa.Column("gl_tcode", sa.String(length=15), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("transaction_type"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_gst_transaction_type_lastchanged"),
        "gst_transaction_type",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "instructionsubtype",
        sa.Column("instructiontypeid", sa.String(length=10), nullable=False),
        sa.Column("instructionsubtypeid", sa.String(length=10), nullable=False),
        sa.Column("description", sa.String(length=64), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("instructiontypeid", "instructionsubtypeid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_instructionsubtype_lastchanged"),
        "instructionsubtype",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "instructiontype",
        sa.Column("instructiontypeid", sa.String(length=10), nullable=False),
        sa.Column("description", sa.String(length=64), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("instructiontypeid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_instructiontype_lastchanged"),
        "instructiontype",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "intcontract",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("startperiod", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("endperiod", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column(
            "deregistrationdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "deregistrationperiod",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint("contractid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_intcontract_lastchanged"),
        "intcontract",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "intcontractamount",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("amount", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("rcf", sa.CHAR(length=1), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.PrimaryKeyConstraint("contractid", "versionno", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_intcontractamount_lastchanged"),
        "intcontractamount",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "intcontractamounttrk",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_intcontractamounttrk_lastchanged"),
        "intcontractamounttrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "interconnector",
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("regionfrom", sa.String(length=10), nullable=True),
        sa.Column("rsoid", sa.String(length=10), nullable=True),
        sa.Column("regionto", sa.String(length=10), nullable=True),
        sa.Column("description", sa.String(length=64), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("interconnectorid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_interconnector_lastchanged"),
        "interconnector",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "interconnectoralloc",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=5, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("allocation", sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "effectivedate",
            "versionno",
            "interconnectorid",
            "regionid",
            "participantid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_interconnectoralloc_lastchanged"),
        "interconnectoralloc",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "interconnectorconstraint",
        sa.Column(
            "reserveoverallloadfactor",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
        ),
        sa.Column(
            "fromregionlossshare",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
        ),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("maxmwin", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("maxmwout", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lossconstant", sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column(
            "lossflowcoefficient",
            sa.Numeric(precision=27, scale=17),
            nullable=True,
        ),
        sa.Column("emsmeasurand", sa.String(length=40), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("dynamicrhs", sa.String(length=1), nullable=True),
        sa.Column("importlimit", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("exportlimit", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column(
            "outagederationfactor",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "nonphysicallossfactor",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "overloadfactor60sec",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "overloadfactor6sec",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "fcassupportunavailable",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column("ictype", sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno", "interconnectorid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_interconnectorconstraint_lastchanged"),
        "interconnectorconstraint",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "interconnmwflow",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=6, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column(
            "importenergyvalue",
            sa.Numeric(precision=15, scale=6),
            nullable=True,
        ),
        sa.Column(
            "exportenergyvalue",
            sa.Numeric(precision=15, scale=6),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "versionno", "interconnectorid", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_interconnmwflow_lastchanged"),
        "interconnmwflow",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "intermittent_cluster_avail",
        sa.Column("tradingdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=20), nullable=False),
        sa.Column("offerdatetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("clusterid", sa.String(length=20), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column(
            "elements_unavailable",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("tradingdate", "duid", "offerdatetime", "clusterid", "periodid"),
        schema="mms",
    )
    op.create_table(
        "intermittent_cluster_avail_day",
        sa.Column("tradingdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=20), nullable=False),
        sa.Column("offerdatetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("clusterid", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("tradingdate", "duid", "offerdatetime", "clusterid"),
        schema="mms",
    )
    op.create_table(
        "intermittent_ds_pred",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=20), nullable=False),
        sa.Column("offerdatetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("origin", sa.String(length=20), nullable=False),
        sa.Column(
            "forecast_priority",
            sa.Numeric(precision=10, scale=0),
            nullable=False,
        ),
        sa.Column("forecast_mean", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("forecast_poe10", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("forecast_poe50", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("forecast_poe90", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint(
            "run_datetime",
            "duid",
            "offerdatetime",
            "interval_datetime",
            "origin",
            "forecast_priority",
        ),
        schema="mms",
    )
    op.create_table(
        "intermittent_ds_run",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=20), nullable=False),
        sa.Column("offerdatetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("origin", sa.String(length=20), nullable=False),
        sa.Column(
            "forecast_priority",
            sa.Numeric(precision=10, scale=0),
            nullable=False,
        ),
        sa.Column("authorisedby", sa.String(length=20), nullable=True),
        sa.Column("comments", sa.String(length=200), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("model", sa.String(length=30), nullable=True),
        sa.Column(
            "participant_timestamp",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("suppressed_aemo", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column(
            "suppressed_participant",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column("transaction_id", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint(
            "run_datetime",
            "duid",
            "offerdatetime",
            "origin",
            "forecast_priority",
        ),
        schema="mms",
    )
    op.create_table(
        "intermittent_forecast_trk",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=20), nullable=False),
        sa.Column("origin", sa.String(length=20), nullable=True),
        sa.Column(
            "forecast_priority",
            sa.Numeric(precision=10, scale=0),
            nullable=True,
        ),
        sa.Column("offerdatetime", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "duid"),
        schema="mms",
    )
    op.create_table(
        "intermittent_gen_fcst",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=20), nullable=False),
        sa.Column(
            "start_interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column(
            "end_interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("versionno", sa.Numeric(precision=10, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("run_datetime", "duid"),
        schema="mms",
    )
    op.create_table(
        "intermittent_gen_fcst_data",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=20), nullable=False),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("powermean", sa.Numeric(precision=9, scale=3), nullable=True),
        sa.Column("powerpoe50", sa.Numeric(precision=9, scale=3), nullable=True),
        sa.Column("powerpoelow", sa.Numeric(precision=9, scale=3), nullable=True),
        sa.Column("powerpoehigh", sa.Numeric(precision=9, scale=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("run_datetime", "duid", "interval_datetime"),
        schema="mms",
    )
    op.create_table(
        "intermittent_gen_limit",
        sa.Column("tradingdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=20), nullable=False),
        sa.Column("offerdatetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("uppermwlimit", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("tradingdate", "duid", "offerdatetime", "periodid"),
        schema="mms",
    )
    op.create_table(
        "intermittent_gen_limit_day",
        sa.Column("tradingdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=20), nullable=False),
        sa.Column("offerdatetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("participantid", sa.String(length=20), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedbyuser", sa.String(length=20), nullable=True),
        sa.Column("authorisedbyparticipantid", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("tradingdate", "duid", "offerdatetime"),
        schema="mms",
    )
    op.create_table(
        "intermittent_p5_pred",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=20), nullable=False),
        sa.Column("offerdatetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("origin", sa.String(length=20), nullable=False),
        sa.Column(
            "forecast_priority",
            sa.Numeric(precision=10, scale=0),
            nullable=False,
        ),
        sa.Column("forecast_mean", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("forecast_poe10", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("forecast_poe50", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("forecast_poe90", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint(
            "run_datetime",
            "duid",
            "offerdatetime",
            "interval_datetime",
            "origin",
            "forecast_priority",
        ),
        schema="mms",
    )
    op.create_table(
        "intermittent_p5_run",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=20), nullable=False),
        sa.Column("offerdatetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("origin", sa.String(length=20), nullable=False),
        sa.Column(
            "forecast_priority",
            sa.Numeric(precision=10, scale=0),
            nullable=False,
        ),
        sa.Column("authorisedby", sa.String(length=20), nullable=True),
        sa.Column("comments", sa.String(length=200), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("model", sa.String(length=30), nullable=True),
        sa.Column(
            "participant_timestamp",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("suppressed_aemo", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column(
            "suppressed_participant",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column("transaction_id", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint(
            "run_datetime",
            "duid",
            "offerdatetime",
            "origin",
            "forecast_priority",
        ),
        schema="mms",
    )
    op.create_table(
        "intraregionalloc",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=5, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("allocation", sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno", "regionid", "participantid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_intraregionalloc_lastchanged"),
        "intraregionalloc",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "irfmamount",
        sa.Column("irfmid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("irfmid", "versionno", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_irfmamount_lastchanged"),
        "irfmamount",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "irfmevents",
        sa.Column("irfmid", sa.String(length=10), nullable=False),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("startperiod", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("endperiod", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("irfmid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_irfmevents_lastchanged"),
        "irfmevents",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "lossfactormodel",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column(
            "demandcoefficient",
            sa.Numeric(precision=27, scale=17),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno", "interconnectorid", "regionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_lossfactormodel_lastchanged"),
        "lossfactormodel",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "lossmodel",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.String(length=20), nullable=True),
        sa.Column("losssegment", sa.Numeric(precision=6, scale=0), nullable=False),
        sa.Column("mwbreakpoint", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lossfactor", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno", "interconnectorid", "losssegment"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_lossmodel_lastchanged"),
        "lossmodel",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "market_fee_cat_excl",
        sa.Column("marketfeeid", sa.String(length=20), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "version_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("participant_categoryid", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint(
            "marketfeeid",
            "effectivedate",
            "version_datetime",
            "participant_categoryid",
        ),
        schema="mms",
    )
    op.create_table(
        "market_fee_cat_excl_trk",
        sa.Column("marketfeeid", sa.String(length=20), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "version_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("marketfeeid", "effectivedate", "version_datetime"),
        schema="mms",
    )
    op.create_table(
        "market_fee_exclusion",
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("marketfeeid", sa.String(length=10), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("participantid", "effectivedate", "versionno", "marketfeeid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_market_fee_exclusion_lastchanged"),
        "market_fee_exclusion",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "market_fee_exclusiontrk",
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("participantid", "effectivedate", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_market_fee_exclusiontrk_lastchanged"),
        "market_fee_exclusiontrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "market_price_thresholds",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("voll", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "marketpricefloor",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "administered_price_threshold",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_market_price_thresholds_lastchanged"),
        "market_price_thresholds",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "market_suspend_regime_sum",
        sa.Column("suspension_id", sa.String(length=20), nullable=False),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column("start_interval", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("end_interval", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("pricing_regime", sa.String(length=20), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("suspension_id", "regionid", "start_interval"),
        schema="mms",
    )
    op.create_table(
        "market_suspend_region_sum",
        sa.Column("suspension_id", sa.String(length=20), nullable=False),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column(
            "initial_interval",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "end_region_interval",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "end_suspension_interval",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("suspension_id", "regionid"),
        schema="mms",
    )
    op.create_table(
        "market_suspend_schedule",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("day_type", sa.String(length=20), nullable=False),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("energy_rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("r6_rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("r60_rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("r5_rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rreg_rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("l6_rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("l60_rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("l5_rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lreg_rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "day_type", "regionid", "periodid"),
        schema="mms",
    )
    op.create_table(
        "market_suspend_schedule_trk",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "source_start_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("source_end_date", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("comments", sa.String(length=1000), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate"),
        schema="mms",
    )
    op.create_table(
        "marketfee",
        sa.Column("marketfeeid", sa.String(length=10), nullable=False),
        sa.Column("marketfeeperiod", sa.String(length=20), nullable=True),
        sa.Column("marketfeetype", sa.String(length=12), nullable=True),
        sa.Column("description", sa.String(length=64), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("gl_tcode", sa.String(length=15), nullable=True),
        sa.Column("gl_financialcode", sa.String(length=10), nullable=True),
        sa.Column("fee_class", sa.String(length=40), nullable=True),
        sa.PrimaryKeyConstraint("marketfeeid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_marketfee_lastchanged"),
        "marketfee",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "marketfeedata",
        sa.Column("marketfeeid", sa.String(length=10), nullable=False),
        sa.Column(
            "marketfeeversionno",
            sa.Numeric(precision=3, scale=0),
            nullable=False,
        ),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("marketfeevalue", sa.Numeric(precision=22, scale=8), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("marketfeeid", "marketfeeversionno", "effectivedate"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_marketfeedata_lastchanged"),
        "marketfeedata",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "marketfeetrk",
        sa.Column(
            "marketfeeversionno",
            sa.Numeric(precision=3, scale=0),
            nullable=False,
        ),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("marketfeeversionno", "effectivedate"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_marketfeetrk_lastchanged"),
        "marketfeetrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "marketnoticedata",
        sa.Column("noticeid", sa.Numeric(precision=10, scale=0), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("typeid", sa.String(length=25), nullable=True),
        sa.Column("noticetype", sa.String(length=25), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("reason", sa.String(length=2000), nullable=True),
        sa.Column("externalreference", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("noticeid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_marketnoticedata_lastchanged"),
        "marketnoticedata",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "marketnoticetype",
        sa.Column("typeid", sa.String(length=25), nullable=False),
        sa.Column("description", sa.String(length=64), nullable=True),
        sa.Column("raisedby", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("typeid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_marketnoticetype_lastchanged"),
        "marketnoticetype",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "marketsuspension",
        sa.Column("suspensionid", sa.String(length=10), nullable=False),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("startperiod", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("endperiod", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("reason", sa.String(length=64), nullable=True),
        sa.Column("startauthorisedby", sa.String(length=15), nullable=True),
        sa.Column("endauthorisedby", sa.String(length=15), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("suspensionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_marketsuspension_lastchanged"),
        "marketsuspension",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "marketsusregion",
        sa.Column("suspensionid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("suspensionid", "regionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_marketsusregion_lastchanged"),
        "marketsusregion",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mas_cp_change",
        sa.Column("nmi", sa.String(length=10), nullable=False),
        sa.Column("status_flag", sa.String(length=1), nullable=True),
        sa.Column("cp_old_security_code", sa.String(length=4), nullable=True),
        sa.Column("cp_new_security_code", sa.String(length=4), nullable=True),
        sa.Column("old_local_network_provider", sa.String(length=10), nullable=True),
        sa.Column("old_local_retailer", sa.String(length=10), nullable=True),
        sa.Column("old_financial_participant", sa.String(length=10), nullable=True),
        sa.Column("old_metering_data_agent", sa.String(length=10), nullable=True),
        sa.Column("old_retailer_of_last_resort", sa.String(length=10), nullable=True),
        sa.Column("old_responsible_person", sa.String(length=10), nullable=True),
        sa.Column("new_local_network_provider", sa.String(length=10), nullable=True),
        sa.Column("new_local_retailer", sa.String(length=10), nullable=True),
        sa.Column("new_financial_participant", sa.String(length=10), nullable=True),
        sa.Column("new_metering_data_agent", sa.String(length=10), nullable=True),
        sa.Column("new_retailer_of_last_resort", sa.String(length=10), nullable=True),
        sa.Column("new_responsible_person", sa.String(length=10), nullable=True),
        sa.Column("old_lnsp_ok", sa.String(length=1), nullable=True),
        sa.Column("old_lr_ok", sa.String(length=1), nullable=True),
        sa.Column("old_frmp_ok", sa.String(length=1), nullable=True),
        sa.Column("old_mda_ok", sa.String(length=1), nullable=True),
        sa.Column("old_rolr_ok", sa.String(length=1), nullable=True),
        sa.Column("old_rp_ok", sa.String(length=1), nullable=True),
        sa.Column("new_lnsp_ok", sa.String(length=1), nullable=True),
        sa.Column("new_lr_ok", sa.String(length=1), nullable=True),
        sa.Column("new_frmp_ok", sa.String(length=1), nullable=True),
        sa.Column("new_mda_ok", sa.String(length=1), nullable=True),
        sa.Column("new_rolr_ok", sa.String(length=1), nullable=True),
        sa.Column("new_rp_ok", sa.String(length=1), nullable=True),
        sa.Column("prudential_ok", sa.String(length=1), nullable=True),
        sa.Column(
            "initial_change_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "current_change_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("cp_name", sa.String(length=30), nullable=True),
        sa.Column("cp_detail_1", sa.String(length=30), nullable=True),
        sa.Column("cp_detail_2", sa.String(length=30), nullable=True),
        sa.Column("city_suburb", sa.String(length=30), nullable=True),
        sa.Column("state", sa.String(length=3), nullable=True),
        sa.Column("post_code", sa.String(length=4), nullable=True),
        sa.Column("tx_node", sa.String(length=4), nullable=True),
        sa.Column("aggregate_data", sa.String(length=1), nullable=True),
        sa.Column(
            "average_daily_load_kwh",
            sa.Numeric(precision=8, scale=0),
            nullable=True,
        ),
        sa.Column(
            "distribution_loss",
            sa.Numeric(precision=5, scale=4),
            nullable=True,
        ),
        sa.Column("old_lsnp_text", sa.String(length=30), nullable=True),
        sa.Column("old_lr_text", sa.String(length=30), nullable=True),
        sa.Column("old_frmp_text", sa.String(length=30), nullable=True),
        sa.Column("old_mda_text", sa.String(length=30), nullable=True),
        sa.Column("old_rolr_text", sa.String(length=30), nullable=True),
        sa.Column("old_rp_text", sa.String(length=30), nullable=True),
        sa.Column("new_lsnp_text", sa.String(length=30), nullable=True),
        sa.Column("new_lr_text", sa.String(length=30), nullable=True),
        sa.Column("new_frmp_text", sa.String(length=30), nullable=True),
        sa.Column("new_mda_text", sa.String(length=30), nullable=True),
        sa.Column("new_rolr_text", sa.String(length=30), nullable=True),
        sa.Column("new_rp_text", sa.String(length=30), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("nmi_class", sa.String(length=9), nullable=True),
        sa.Column("metering_type", sa.String(length=9), nullable=True),
        sa.Column("jurisdiction", sa.String(length=3), nullable=True),
        sa.Column("create_date", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("expiry_date", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("meter_read_date", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("nmi"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mas_cp_change_lastchanged"),
        "mas_cp_change",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mas_cp_master",
        sa.Column("nmi", sa.String(length=10), nullable=False),
        sa.Column("cp_security_code", sa.String(length=4), nullable=True),
        sa.Column("in_use", sa.String(length=1), nullable=True),
        sa.Column(
            "valid_from_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("valid_to_date", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("local_network_provider", sa.String(length=10), nullable=True),
        sa.Column("local_retailer", sa.String(length=10), nullable=True),
        sa.Column("financial_participant", sa.String(length=10), nullable=True),
        sa.Column("metering_data_agent", sa.String(length=10), nullable=True),
        sa.Column("retailer_of_last_resort", sa.String(length=10), nullable=True),
        sa.Column("responsible_person", sa.String(length=10), nullable=True),
        sa.Column("cp_name", sa.String(length=30), nullable=True),
        sa.Column("cp_detail_1", sa.String(length=30), nullable=True),
        sa.Column("cp_detail_2", sa.String(length=30), nullable=True),
        sa.Column("city_suburb", sa.String(length=30), nullable=True),
        sa.Column("state", sa.String(length=3), nullable=True),
        sa.Column("post_code", sa.String(length=4), nullable=True),
        sa.Column("tx_node", sa.String(length=4), nullable=True),
        sa.Column("aggregate_data", sa.String(length=1), nullable=True),
        sa.Column(
            "average_daily_load_kwh",
            sa.Numeric(precision=8, scale=0),
            nullable=True,
        ),
        sa.Column(
            "distribution_loss",
            sa.Numeric(precision=5, scale=4),
            nullable=True,
        ),
        sa.Column("lsnp_text", sa.String(length=30), nullable=True),
        sa.Column("lr_text", sa.String(length=30), nullable=True),
        sa.Column("frmp_text", sa.String(length=30), nullable=True),
        sa.Column("mda_text", sa.String(length=30), nullable=True),
        sa.Column("rolr_text", sa.String(length=30), nullable=True),
        sa.Column("rp_text", sa.String(length=30), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("nmi_class", sa.String(length=9), nullable=True),
        sa.Column("metering_type", sa.String(length=9), nullable=True),
        sa.Column("jurisdiction", sa.String(length=3), nullable=True),
        sa.PrimaryKeyConstraint("nmi", "valid_from_date"),
        sa.UniqueConstraint("nmi", "valid_to_date"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mas_cp_master_lastchanged"),
        "mas_cp_master",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mcc_casesolution",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.PrimaryKeyConstraint("run_datetime"),
        schema="mms",
    )
    op.create_table(
        "mcc_constraintsolution",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("constraintid", sa.String(length=20), nullable=False),
        sa.Column("rhs", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("marginalvalue", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.PrimaryKeyConstraint("run_datetime", "constraintid"),
        schema="mms",
    )
    op.create_table(
        "meterdata",
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("meterrunno", sa.Numeric(precision=6, scale=0), nullable=False),
        sa.Column("connectionpointid", sa.String(length=10), nullable=False),
        sa.Column(
            "importenergyvalue",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "exportenergyvalue",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "importreactivevalue",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column(
            "exportreactivevalue",
            sa.Numeric(precision=9, scale=6),
            nullable=True,
        ),
        sa.Column("hostdistributor", sa.String(length=10), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("mda", sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint(
            "participantid",
            "periodid",
            "settlementdate",
            "meterrunno",
            "connectionpointid",
            "hostdistributor",
            "mda",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_meterdata_lastchanged"),
        "meterdata",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "meterdata_aggregate_reads",
        sa.Column("case_id", sa.Numeric(precision=15, scale=0), nullable=False),
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("connectionpointid", sa.String(length=20), nullable=False),
        sa.Column("meter_type", sa.String(length=20), nullable=False),
        sa.Column("frmp", sa.String(length=20), nullable=False),
        sa.Column("lr", sa.String(length=20), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("importvalue", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column("exportvalue", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "case_id",
            "settlementdate",
            "connectionpointid",
            "meter_type",
            "frmp",
            "lr",
            "periodid",
        ),
        schema="mms",
    )
    op.create_table(
        "meterdata_gen_duid",
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("mwh_reading", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("interval_datetime", "duid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_meterdata_gen_duid_lastchanged"),
        "meterdata_gen_duid",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "meterdata_individual_reads",
        sa.Column("case_id", sa.Numeric(precision=15, scale=0), nullable=False),
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("meter_id", sa.String(length=20), nullable=False),
        sa.Column("meter_id_suffix", sa.String(length=20), nullable=False),
        sa.Column("frmp", sa.String(length=20), nullable=False),
        sa.Column("lr", sa.String(length=20), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("connectionpointid", sa.String(length=20), nullable=False),
        sa.Column("meter_type", sa.String(length=20), nullable=False),
        sa.Column("importvalue", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column("exportvalue", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "case_id",
            "settlementdate",
            "meter_id",
            "meter_id_suffix",
            "periodid",
        ),
        schema="mms",
    )
    op.create_table(
        "meterdata_interconnector",
        sa.Column("case_id", sa.Numeric(precision=15, scale=0), nullable=False),
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("interconnectorid", sa.String(length=20), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("importvalue", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("exportvalue", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("case_id", "settlementdate", "interconnectorid", "periodid"),
        schema="mms",
    )
    op.create_table(
        "meterdata_trk",
        sa.Column("case_id", sa.Numeric(precision=15, scale=0), nullable=False),
        sa.Column(
            "aggregate_reads_load_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "individual_reads_load_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("case_id"),
        schema="mms",
    )
    op.create_table(
        "meterdatatrk",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("meterrunno", sa.Numeric(precision=6, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("filename", sa.String(length=40), nullable=True),
        sa.Column("ackfilename", sa.String(length=40), nullable=True),
        sa.Column("connectionpointid", sa.String(length=10), nullable=False),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("meteringdataagent", sa.String(length=10), nullable=False),
        sa.Column("hostdistributor", sa.String(length=10), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "meterrunno",
            "participantid",
            "connectionpointid",
            "meteringdataagent",
            "hostdistributor",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_meterdatatrk_lastchanged"),
        "meterdatatrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mms_data_model_audit",
        sa.Column(
            "installation_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("mmsdm_version", sa.String(length=20), nullable=False),
        sa.Column("install_type", sa.String(length=10), nullable=False),
        sa.Column("script_version", sa.String(length=20), nullable=True),
        sa.Column("nem_change_notice", sa.String(length=20), nullable=True),
        sa.Column("project_title", sa.String(length=200), nullable=True),
        sa.Column("username", sa.String(length=40), nullable=True),
        sa.Column("status", sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint("installation_date", "mmsdm_version", "install_type"),
        schema="mms",
    )
    op.create_table(
        "mnsp_dayoffer",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("linkid", sa.String(length=10), nullable=False),
        sa.Column("entrytype", sa.String(length=20), nullable=True),
        sa.Column("rebidexplanation", sa.String(length=500), nullable=True),
        sa.Column("priceband1", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband2", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband3", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband4", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband5", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband6", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband7", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband8", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband9", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("priceband10", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("mr_factor", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "offerdate",
            "versionno",
            "participantid",
            "linkid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mnsp_dayoffer_lastchanged"),
        "mnsp_dayoffer",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mnsp_filetrk",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("filename", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=True),
        sa.Column("ackfilename", sa.String(length=40), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "offerdate", "participantid", "filename"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mnsp_filetrk_lastchanged"),
        "mnsp_filetrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mnsp_interconnector",
        sa.Column("linkid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=True),
        sa.Column("fromregion", sa.String(length=10), nullable=True),
        sa.Column("toregion", sa.String(length=10), nullable=True),
        sa.Column("maxcapacity", sa.Numeric(precision=5, scale=0), nullable=True),
        sa.Column("tlf", sa.Numeric(precision=12, scale=7), nullable=True),
        sa.Column("lhsfactor", sa.Numeric(precision=12, scale=7), nullable=True),
        sa.Column(
            "meterflowconstant",
            sa.Numeric(precision=12, scale=7),
            nullable=True,
        ),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("from_region_tlf", sa.Numeric(precision=12, scale=7), nullable=True),
        sa.Column("to_region_tlf", sa.Numeric(precision=12, scale=7), nullable=True),
        sa.PrimaryKeyConstraint("linkid", "effectivedate", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mnsp_interconnector_lastchanged"),
        "mnsp_interconnector",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mnsp_offertrk",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("filename", sa.String(length=40), nullable=False),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "offerdate",
            "versionno",
            "participantid",
            "filename",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mnsp_offertrk_lastchanged"),
        "mnsp_offertrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mnsp_participant",
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("interconnectorid", "effectivedate", "versionno", "participantid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mnsp_participant_lastchanged"),
        "mnsp_participant",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mnsp_peroffer",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("linkid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=22, scale=0), nullable=False),
        sa.Column("maxavail", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail1", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail2", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail3", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail4", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail5", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail6", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail7", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail8", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail9", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail10", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("fixedload", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("rampuprate", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column(
            "pasaavailability",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.Column("mr_capacity", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "offerdate",
            "versionno",
            "participantid",
            "linkid",
            "periodid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mnsp_peroffer_lastchanged"),
        "mnsp_peroffer",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mr_dayoffer_stack",
        sa.Column("mr_date", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column(
            "version_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("stack_position", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column("authorised", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column(
            "offer_settlementdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("offer_offerdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("offer_versionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("offer_type", sa.String(length=20), nullable=True),
        sa.Column("laof", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("mr_date", "regionid", "version_datetime", "stack_position"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mr_dayoffer_stack_lastchanged"),
        "mr_dayoffer_stack",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mr_event",
        sa.Column("mr_date", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=20), nullable=True),
        sa.Column(
            "offer_cut_off_time",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "settlement_complete",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("mr_date", "regionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mr_event_lastchanged"),
        "mr_event",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mr_event_schedule",
        sa.Column("mr_date", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column(
            "version_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column(
            "demand_effectivedate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "demand_offerdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("demand_versionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("authorisedby", sa.String(length=20), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("mr_date", "regionid", "version_datetime"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mr_event_schedule_lastchanged"),
        "mr_event_schedule",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mr_peroffer_stack",
        sa.Column("mr_date", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column(
            "version_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("stack_position", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column(
            "accepted_capacity",
            sa.Numeric(precision=6, scale=0),
            nullable=True,
        ),
        sa.Column(
            "deducted_capacity",
            sa.Numeric(precision=6, scale=0),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "mr_date",
            "regionid",
            "version_datetime",
            "stack_position",
            "periodid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mr_peroffer_stack_lastchanged"),
        "mr_peroffer_stack",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mtpasa_case_set",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("run_no", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("casesetid", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("runtypeid", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("run_datetime", "run_no"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mtpasa_case_set_lastchanged"),
        "mtpasa_case_set",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mtpasa_caseresult",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("run_no", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("plexos_version", sa.String(length=20), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("run_datetime", "run_no"),
        schema="mms",
    )
    op.create_table(
        "mtpasa_casesolution",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("run_no", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("pasaversion", sa.String(length=10), nullable=True),
        sa.Column("reservecondition", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("lorcondition", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column(
            "capacityobjfunction",
            sa.Numeric(precision=12, scale=3),
            nullable=True,
        ),
        sa.Column("capacityoption", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column(
            "maxsurplusreserveoption",
            sa.Numeric(precision=12, scale=3),
            nullable=True,
        ),
        sa.Column(
            "maxsparecapacityoption",
            sa.Numeric(precision=12, scale=3),
            nullable=True,
        ),
        sa.Column(
            "interconnectorflowpenalty",
            sa.Numeric(precision=12, scale=3),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("runtype", sa.String(length=50), nullable=True),
        sa.Column(
            "reliabilitylrcdemandoption",
            sa.Numeric(precision=12, scale=3),
            nullable=True,
        ),
        sa.Column(
            "outagelrcdemandoption",
            sa.Numeric(precision=12, scale=3),
            nullable=True,
        ),
        sa.Column("lordemandoption", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("reliabilitylrccapacityoption", sa.String(length=10), nullable=True),
        sa.Column("outagelrccapacityoption", sa.String(length=10), nullable=True),
        sa.Column("lorcapacityoption", sa.String(length=10), nullable=True),
        sa.Column("loruigfoption", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column(
            "reliabilitylrcuigfoption",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column(
            "outagelrcuigfoption",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("run_datetime", "run_no"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mtpasa_casesolution_lastchanged"),
        "mtpasa_casesolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mtpasa_constraintresult",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("run_no", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("runtype", sa.String(length=20), nullable=False),
        sa.Column("demand_poe_type", sa.String(length=20), nullable=False),
        sa.Column("day", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("constraintid", sa.String(length=20), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column(
            "probabilityofbinding",
            sa.Numeric(precision=8, scale=5),
            nullable=True,
        ),
        sa.Column(
            "probabilityofviolation",
            sa.Numeric(precision=8, scale=5),
            nullable=True,
        ),
        sa.Column(
            "constraintviolation90",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "constraintviolation50",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "constraintviolation10",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "run_datetime",
            "run_no",
            "runtype",
            "demand_poe_type",
            "day",
            "constraintid",
        ),
        schema="mms",
    )
    op.create_table(
        "mtpasa_constraintsolution",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("run_no", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("energyblock", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("day", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("ldcblock", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("constraintid", sa.String(length=20), nullable=False),
        sa.Column("capacityrhs", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "capacitymarginalvalue",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "capacityviolationdegree",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "runtype",
            sa.String(length=20),
            server_default=sa.text("'OUTAGE_LRC'::character varying"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "run_datetime",
            "run_no",
            "energyblock",
            "day",
            "ldcblock",
            "constraintid",
            "runtype",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mtpasa_constraintsolution_lastchanged"),
        "mtpasa_constraintsolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mtpasa_constraintsummary",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("run_no", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("runtype", sa.String(length=20), nullable=False),
        sa.Column("demand_poe_type", sa.String(length=20), nullable=False),
        sa.Column("day", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("constraintid", sa.String(length=20), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("aggregation_period", sa.String(length=20), nullable=False),
        sa.Column(
            "constrainthoursbinding",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "run_datetime",
            "run_no",
            "runtype",
            "demand_poe_type",
            "day",
            "constraintid",
            "aggregation_period",
        ),
        schema="mms",
    )
    op.create_table(
        "mtpasa_interconnectorresult",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("run_no", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("runtype", sa.String(length=20), nullable=False),
        sa.Column("demand_poe_type", sa.String(length=20), nullable=False),
        sa.Column("day", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("interconnectorid", sa.String(length=20), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("flow90", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("flow50", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("flow10", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "probabilityofbindingexport",
            sa.Numeric(precision=8, scale=5),
            nullable=True,
        ),
        sa.Column(
            "probabilityofbindingimport",
            sa.Numeric(precision=8, scale=5),
            nullable=True,
        ),
        sa.Column(
            "calculatedexportlimit",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "calculatedimportlimit",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "run_datetime",
            "run_no",
            "runtype",
            "demand_poe_type",
            "day",
            "interconnectorid",
        ),
        schema="mms",
    )
    op.create_table(
        "mtpasa_interconnectorsolution",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("run_no", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("energyblock", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("day", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("ldcblock", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("capacitymwflow", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "capacitymarginalvalue",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "capacityviolationdegree",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "calculatedexportlimit",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "calculatedimportlimit",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "runtype",
            sa.String(length=20),
            server_default=sa.text("'OUTAGE_LRC'::character varying"),
            nullable=False,
        ),
        sa.Column("exportlimitconstraintid", sa.String(length=20), nullable=True),
        sa.Column("importlimitconstraintid", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint(
            "run_datetime",
            "run_no",
            "energyblock",
            "day",
            "ldcblock",
            "interconnectorid",
            "runtype",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mtpasa_interconnectorsolution_lastchanged"),
        "mtpasa_interconnectorsolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mtpasa_intermittent_avail",
        sa.Column("tradingdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=20), nullable=False),
        sa.Column("offerdatetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("clusterid", sa.String(length=20), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "elements_unavailable",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("tradingdate", "duid", "offerdatetime", "clusterid"),
        schema="mms",
    )
    op.create_table(
        "mtpasa_intermittent_limit",
        sa.Column("tradingdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=20), nullable=False),
        sa.Column("offerdatetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("uppermwlimit", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("authorisedbyuser", sa.String(length=20), nullable=True),
        sa.Column("authorisedbyparticipantid", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("tradingdate", "duid", "offerdatetime"),
        schema="mms",
    )
    op.create_table(
        "mtpasa_lolpresult",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("run_no", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("runtype", sa.String(length=20), nullable=False),
        sa.Column("day", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column(
            "worst_interval_periodid",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column(
            "worst_interval_demand",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "worst_interval_intgen",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "worst_interval_dsp",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "lossofloadprobability",
            sa.Numeric(precision=8, scale=5),
            nullable=True,
        ),
        sa.Column("lossofloadmagnitude", sa.String(length=20), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("run_datetime", "run_no", "runtype", "day", "regionid"),
        schema="mms",
    )
    op.create_table(
        "mtpasa_offerdata",
        sa.Column("participantid", sa.String(length=20), nullable=False),
        sa.Column("offerdatetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("unitid", sa.String(length=20), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("energy", sa.Numeric(precision=9, scale=0), nullable=True),
        sa.Column("capacity1", sa.Numeric(precision=9, scale=0), nullable=True),
        sa.Column("capacity2", sa.Numeric(precision=9, scale=0), nullable=True),
        sa.Column("capacity3", sa.Numeric(precision=9, scale=0), nullable=True),
        sa.Column("capacity4", sa.Numeric(precision=9, scale=0), nullable=True),
        sa.Column("capacity5", sa.Numeric(precision=9, scale=0), nullable=True),
        sa.Column("capacity6", sa.Numeric(precision=9, scale=0), nullable=True),
        sa.Column("capacity7", sa.Numeric(precision=9, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("participantid", "offerdatetime", "unitid", "effectivedate"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mtpasa_offerdata_lastchanged"),
        "mtpasa_offerdata",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mtpasa_offerfiletrk",
        sa.Column("participantid", sa.String(length=20), nullable=False),
        sa.Column("offerdatetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("filename", sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint("participantid", "offerdatetime"),
        schema="mms",
    )
    op.create_table(
        "mtpasa_regionavail_trk",
        sa.Column(
            "publish_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "latest_offer_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("publish_datetime"),
        schema="mms",
    )
    op.create_table(
        "mtpasa_regionavailability",
        sa.Column(
            "publish_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("day", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column(
            "pasaavailability_scheduled",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.Column(
            "latest_offer_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "energyunconstrainedcapacity",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.Column(
            "energyconstrainedcapacity",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.Column(
            "nonscheduledgeneration",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("demand10", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("demand50", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "energyreqdemand10",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "energyreqdemand50",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("publish_datetime", "day", "regionid"),
        schema="mms",
    )
    op.create_table(
        "mtpasa_regioniteration",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("run_no", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("runtype", sa.String(length=20), nullable=False),
        sa.Column("demand_poe_type", sa.String(length=20), nullable=False),
        sa.Column("aggregation_period", sa.String(length=20), nullable=False),
        sa.Column("period_ending", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column(
            "use_iteration_id",
            sa.Numeric(precision=5, scale=0),
            nullable=False,
        ),
        sa.Column(
            "use_iteration_event_number",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "use_iteration_event_average",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "run_datetime",
            "run_no",
            "runtype",
            "demand_poe_type",
            "aggregation_period",
            "period_ending",
            "regionid",
            "use_iteration_id",
        ),
        schema="mms",
    )
    op.create_table(
        "mtpasa_regionresult",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("run_no", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("runtype", sa.String(length=20), nullable=False),
        sa.Column("demand_poe_type", sa.String(length=20), nullable=False),
        sa.Column("day", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("demand", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "aggregateinstalledcapacity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "numberofiterations",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "use_numberofiterations",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("use_max", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "use_upperquartile",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("use_median", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "use_lowerquartile",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("use_min", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("use_average", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "use_event_average",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "totalscheduledgen90",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "totalscheduledgen50",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "totalscheduledgen10",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "totalintermittentgen90",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "totalintermittentgen50",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "totalintermittentgen10",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "demandsideparticipation90",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "demandsideparticipation50",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "demandsideparticipation10",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "totalsemischedulegen90",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "totalsemischedulegen50",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "totalsemischedulegen10",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "run_datetime",
            "run_no",
            "runtype",
            "demand_poe_type",
            "day",
            "regionid",
        ),
        schema="mms",
    )
    op.create_table(
        "mtpasa_regionsolution",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("run_no", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("energyblock", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("day", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("ldcblock", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("demand10", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("reservereq", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("capacityreq", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "energyreqdemand10",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "unconstrainedcapacity",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.Column(
            "constrainedcapacity",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.Column(
            "netinterchangeunderscarcity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("surpluscapacity", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("surplusreserve", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("reservecondition", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column(
            "maxsurplusreserve",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "maxsparecapacity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("lorcondition", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column(
            "aggregatecapacityavailable",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "aggregatescheduledload",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "aggregatepasaavailability",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.Column(
            "runtype",
            sa.String(length=20),
            server_default=sa.text("'OUTAGE_LRC'::character varying"),
            nullable=False,
        ),
        sa.Column(
            "calculatedlor1level",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "calculatedlor2level",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "msrnetinterchangeunderscarcity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "lornetinterchangeunderscarcity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "totalintermittentgeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("demand50", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "demand_and_nonschedgen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("uigf", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "semischeduledcapacity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "lor_semischeduledcapacity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("deficitreserve", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column(
            "maxusefulresponse",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "murnetinterchangeunderscarcity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "lortotalintermittentgeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "energyreqdemand50",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "run_datetime",
            "run_no",
            "energyblock",
            "day",
            "ldcblock",
            "regionid",
            "runtype",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mtpasa_regionsolution_lastchanged"),
        "mtpasa_regionsolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mtpasa_regionsummary",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("run_no", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("runtype", sa.String(length=20), nullable=False),
        sa.Column("demand_poe_type", sa.String(length=20), nullable=False),
        sa.Column("aggregation_period", sa.String(length=20), nullable=False),
        sa.Column("period_ending", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column("nativedemand", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "use_percentile10",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "use_percentile20",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "use_percentile30",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "use_percentile40",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "use_percentile50",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "use_percentile60",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "use_percentile70",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "use_percentile80",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "use_percentile90",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "use_percentile100",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("use_average", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "numberofiterations",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "use_numberofiterations",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("use_event_max", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "use_event_upperquartile",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "use_event_median",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "use_event_lowerquartile",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("use_event_min", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("weight", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column(
            "use_weighted_avg",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("lrc", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "run_datetime",
            "run_no",
            "runtype",
            "demand_poe_type",
            "aggregation_period",
            "period_ending",
            "regionid",
        ),
        schema="mms",
    )
    op.create_table(
        "mtpasa_reservelimit",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "version_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("reservelimitid", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("rhs", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "version_datetime", "reservelimitid"),
        schema="mms",
    )
    op.create_table(
        "mtpasa_reservelimit_region",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "version_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("reservelimitid", sa.String(length=20), nullable=False),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column("coef", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "version_datetime", "reservelimitid", "regionid"),
        schema="mms",
    )
    op.create_table(
        "mtpasa_reservelimit_set",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "version_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("reservelimit_set_id", sa.String(length=20), nullable=True),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=20), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "version_datetime"),
        schema="mms",
    )
    op.create_table(
        "mtpasa_reservelimitsolution",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("run_no", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("runtype", sa.String(length=20), nullable=False),
        sa.Column("energyblock", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("day", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("ldcblock", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("reservelimitid", sa.String(length=20), nullable=False),
        sa.Column("marginalvalue", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "run_datetime",
            "run_no",
            "runtype",
            "energyblock",
            "day",
            "ldcblock",
            "reservelimitid",
        ),
        schema="mms",
    )
    op.create_table(
        "mtpasaconstraintsolution_d",
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("constraint_id", sa.String(length=20), nullable=False),
        sa.Column(
            "degree_of_violation",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("datetime", "constraint_id"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mtpasaconstraintsolution_d_lastchanged"),
        "mtpasaconstraintsolution_d",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mtpasainterconnectorsolution_d",
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("interconnector_id", sa.String(length=12), nullable=False),
        sa.Column(
            "positive_interconnector_flow",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "positive_transfer_limits",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("positive_binding", sa.String(length=10), nullable=True),
        sa.Column(
            "negative_interconnector_flow",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "negative_transfer_limits",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("negative_binding", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("datetime", "interconnector_id"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mtpasainterconnectorsolution_d_lastchanged"),
        "mtpasainterconnectorsolution_d",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "mtpasaregionsolution_d",
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("region_id", sa.String(length=12), nullable=False),
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("reserve_condition", sa.String(length=50), nullable=True),
        sa.Column("reserve_surplus", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column(
            "capacity_requirement",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "minimum_reserve_requirement",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "region_demand_10poe",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "demand_minus_scheduled_load",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "constrained_capacity",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "unconstrained_capacity",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("net_interchange", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column(
            "energy_requirement_10poe",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "reported_block_id",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("datetime", "region_id"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_mtpasaregionsolution_d_lastchanged"),
        "mtpasaregionsolution_d",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "negative_residue",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("nrm_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "directional_interconnectorid",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "nrm_activated_flag",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column(
            "cumul_negresidue_amount",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "cumul_negresidue_prev_ti",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "negresidue_current_ti",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "negresidue_pd_next_ti",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("price_revision", sa.String(length=30), nullable=True),
        sa.Column("predispatchseqno", sa.String(length=20), nullable=True),
        sa.Column(
            "event_activated_di",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "event_deactivated_di",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "di_notbinding_count",
            sa.Numeric(precision=2, scale=0),
            nullable=True,
        ),
        sa.Column(
            "di_violated_count",
            sa.Numeric(precision=2, scale=0),
            nullable=True,
        ),
        sa.Column(
            "nrmconstraint_blocked_flag",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("settlementdate", "nrm_datetime", "directional_interconnectorid"),
        schema="mms",
    )
    op.create_table(
        "network_equipmentdetail",
        sa.Column("substationid", sa.String(length=30), nullable=False),
        sa.Column("equipmenttype", sa.String(length=10), nullable=False),
        sa.Column("equipmentid", sa.String(length=30), nullable=False),
        sa.Column("validfrom", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("validto", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("voltage", sa.String(length=20), nullable=True),
        sa.Column("description", sa.String(length=100), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("substationid", "equipmenttype", "equipmentid", "validfrom"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_network_equipmentdetail_lastchanged"),
        "network_equipmentdetail",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "network_outageconstraintset",
        sa.Column("outageid", sa.Numeric(precision=15, scale=0), nullable=False),
        sa.Column("genconsetid", sa.String(length=50), nullable=False),
        sa.Column("startinterval", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("endinterval", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("outageid", "genconsetid"),
        schema="mms",
    )
    op.create_table(
        "network_outagedetail",
        sa.Column("outageid", sa.Numeric(precision=15, scale=0), nullable=False),
        sa.Column("substationid", sa.String(length=30), nullable=False),
        sa.Column("equipmenttype", sa.String(length=10), nullable=False),
        sa.Column("equipmentid", sa.String(length=30), nullable=False),
        sa.Column("starttime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("endtime", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("submitteddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("outagestatuscode", sa.String(length=10), nullable=True),
        sa.Column("resubmitreason", sa.String(length=50), nullable=True),
        sa.Column(
            "resubmitoutageid",
            sa.Numeric(precision=15, scale=0),
            nullable=True,
        ),
        sa.Column("recalltimeday", sa.Numeric(precision=10, scale=0), nullable=True),
        sa.Column("recalltimenight", sa.Numeric(precision=10, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("reason", sa.String(length=100), nullable=True),
        sa.Column("issecondary", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column(
            "actual_starttime",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("actual_endtime", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("companyrefcode", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint(
            "outageid",
            "substationid",
            "equipmenttype",
            "equipmentid",
            "starttime",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_network_outagedetail_lastchanged"),
        "network_outagedetail",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "network_outagestatuscode",
        sa.Column("outagestatuscode", sa.String(length=10), nullable=False),
        sa.Column("description", sa.String(length=100), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("outagestatuscode"),
        schema="mms",
    )
    op.create_table(
        "network_rating",
        sa.Column("spd_id", sa.String(length=21), nullable=False),
        sa.Column("validfrom", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("validto", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("substationid", sa.String(length=30), nullable=True),
        sa.Column("equipmenttype", sa.String(length=10), nullable=True),
        sa.Column("equipmentid", sa.String(length=30), nullable=True),
        sa.Column("ratinglevel", sa.String(length=10), nullable=True),
        sa.Column("isdynamic", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("spd_id", "validfrom"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_network_rating_lastchanged"),
        "network_rating",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "network_realtimerating",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("spd_id", sa.String(length=21), nullable=False),
        sa.Column("ratingvalue", sa.Numeric(precision=16, scale=6), nullable=False),
        sa.PrimaryKeyConstraint("settlementdate", "spd_id"),
        schema="mms",
    )
    op.create_table(
        "network_staticrating",
        sa.Column("substationid", sa.String(length=30), nullable=False),
        sa.Column("equipmenttype", sa.String(length=10), nullable=False),
        sa.Column("equipmentid", sa.String(length=30), nullable=False),
        sa.Column("ratinglevel", sa.String(length=10), nullable=False),
        sa.Column("applicationid", sa.String(length=20), nullable=False),
        sa.Column("validfrom", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("validto", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("ratingvalue", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "substationid",
            "equipmenttype",
            "equipmentid",
            "ratinglevel",
            "applicationid",
            "validfrom",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_network_staticrating_lastchanged"),
        "network_staticrating",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "network_substationdetail",
        sa.Column("substationid", sa.String(length=30), nullable=False),
        sa.Column("validfrom", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("validto", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("description", sa.String(length=100), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("ownerid", sa.String(length=30), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("substationid", "validfrom"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_network_substationdetail_lastchanged"),
        "network_substationdetail",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "oartrack",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("filename", sa.String(length=40), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "offerdate", "versionno", "participantid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_oartrack_lastchanged"),
        "oartrack",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_oartrack_participantid"),
        "oartrack",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "offeragcdata",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("availability", sa.Numeric(precision=4, scale=0), nullable=True),
        sa.Column("upperlimit", sa.Numeric(precision=4, scale=0), nullable=True),
        sa.Column("lowerlimit", sa.Numeric(precision=4, scale=0), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("filename", sa.String(length=40), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("agcup", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("agcdown", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("contractid", "effectivedate", "versionno", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_offeragcdata_contractid"),
        "offeragcdata",
        ["contractid"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_offeragcdata_lastchanged"),
        "offeragcdata",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "offerastrk",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("filename", sa.String(length=40), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno", "participantid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_offerastrk_lastchanged"),
        "offerastrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "offerfiletrk",
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=True),
        sa.Column("ackfilename", sa.String(length=40), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("filename", sa.String(length=40), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("offerdate", "participantid", "filename"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_offerfiletrk_lastchanged"),
        "offerfiletrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_offerfiletrk_participantid"),
        "offerfiletrk",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "offergovdata",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("sec6availup", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("sec6availdown", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("sec60availup", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("sec60availdown", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("filename", sa.String(length=40), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractid", "effectivedate", "versionno", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_offergovdata_contractid"),
        "offergovdata",
        ["contractid"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_offergovdata_lastchanged"),
        "offergovdata",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "offerlsheddata",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("availableload", sa.Numeric(precision=4, scale=0), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("filename", sa.String(length=40), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.PrimaryKeyConstraint("contractid", "effectivedate", "versionno", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_offerlsheddata_lastchanged"),
        "offerlsheddata",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "offerrestartdata",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("availability", sa.String(length=3), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("filename", sa.String(length=40), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.PrimaryKeyConstraint("contractid", "offerdate", "versionno", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_offerrestartdata_lastchanged"),
        "offerrestartdata",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "offerrpowerdata",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("availability", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("mta", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("mtg", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("filename", sa.String(length=40), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractid", "effectivedate", "versionno", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_offerrpowerdata_contractid"),
        "offerrpowerdata",
        ["contractid"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_offerrpowerdata_lastchanged"),
        "offerrpowerdata",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "offeruloadingdata",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("availableload", sa.Numeric(precision=4, scale=0), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("filename", sa.String(length=40), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.PrimaryKeyConstraint("contractid", "effectivedate", "versionno", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_offeruloadingdata_contractid"),
        "offeruloadingdata",
        ["contractid"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_offeruloadingdata_lastchanged"),
        "offeruloadingdata",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "offerunloadingdata",
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("availableload", sa.Numeric(precision=4, scale=0), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("filename", sa.String(length=40), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.PrimaryKeyConstraint("contractid", "effectivedate", "versionno", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_offerunloadingdata_contractid"),
        "offerunloadingdata",
        ["contractid"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_offerunloadingdata_lastchanged"),
        "offerunloadingdata",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "overriderrp",
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("startperiod", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("endperiod", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("rrp", sa.Numeric(precision=15, scale=0), nullable=True),
        sa.Column("description", sa.String(length=128), nullable=True),
        sa.Column("authorisestart", sa.String(length=15), nullable=True),
        sa.Column("authoriseend", sa.String(length=15), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("regionid", "startdate", "startperiod"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_overriderrp_lastchanged"),
        "overriderrp",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "p5min_blockedconstraint",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("constraintid", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("run_datetime", "constraintid"),
        schema="mms",
    )
    op.create_table(
        "p5min_casesolution",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("startinterval_datetime", sa.String(length=20), nullable=True),
        sa.Column("totalobjective", sa.Numeric(precision=27, scale=10), nullable=True),
        sa.Column(
            "nonphysicallosses",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column(
            "totalareagenviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalinterconnectorviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalgenericviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalramprateviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalunitmwcapacityviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "total5minviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalregviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "total6secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "total60secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalenergyconstrviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalenergyofferviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalasprofileviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalfaststartviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("run_datetime"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_p5min_casesolution_lastchanged"),
        "p5min_casesolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "p5min_constraintsolution",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("constraintid", sa.String(length=20), nullable=False),
        sa.Column("rhs", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("marginalvalue", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("violationdegree", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("duid", sa.String(length=20), nullable=True),
        sa.Column(
            "genconid_effectivedate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "genconid_versionno",
            sa.Numeric(precision=22, scale=0),
            nullable=True,
        ),
        sa.Column("lhs", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("run_datetime", "interval_datetime", "constraintid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_p5min_constraintsolution_lastchanged"),
        "p5min_constraintsolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "p5min_interconnectorsoln",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("meteredmwflow", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwlosses", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("marginalvalue", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("violationdegree", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mnsp", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("exportlimit", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("importlimit", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("marginalloss", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("exportgenconid", sa.String(length=20), nullable=True),
        sa.Column("importgenconid", sa.String(length=20), nullable=True),
        sa.Column("fcasexportlimit", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("fcasimportlimit", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "local_price_adjustment_export",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.Column(
            "locally_constrained_export",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column(
            "local_price_adjustment_import",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.Column(
            "locally_constrained_import",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("run_datetime", "interconnectorid", "interval_datetime"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_p5min_interconnectorsoln_lastchanged"),
        "p5min_interconnectorsoln",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "p5min_local_price",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("duid", sa.String(length=20), nullable=False),
        sa.Column(
            "local_price_adjustment",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.Column(
            "locally_constrained",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("run_datetime", "interval_datetime", "duid"),
        schema="mms",
    )
    op.create_table(
        "p5min_regionsolution",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "excessgeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise6secrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise6secrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise60secrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise60secrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise5minrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise5minrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raiseregrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raiseregrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower6secrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower6secrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower60secrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower60secrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower5minrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower5minrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lowerregrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lowerregrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("totaldemand", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "availablegeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("availableload", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("demandforecast", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "dispatchablegeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "dispatchableload",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("netinterchange", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower5mindispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower5minimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower5minlocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower5minlocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower5minreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower60secdispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60secimport",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60seclocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60seclocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower60secreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower6secdispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower6secimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower6seclocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower6seclocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower6secreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise5mindispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise5minimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise5minlocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise5minlocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise5minreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise60secdispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60secimport",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60seclocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60seclocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise60secreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise6secdispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise6secimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise6seclocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6seclocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise6secreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "aggregatedispatcherror",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("initialsupply", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("clearedsupply", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lowerregimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lowerregdispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lowerreglocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lowerreglocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lowerregreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raiseregimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raiseregdispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raisereglocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raisereglocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raiseregreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise5minlocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raisereglocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60seclocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6seclocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower5minlocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lowerreglocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60seclocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower6seclocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise5minviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raiseregviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower5minviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lowerregviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower6secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "totalintermittentgeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "demand_and_nonschedgen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("uigf", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "semischedule_clearedmw",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "semischedule_compliancemw",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("ss_solar_uigf", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("ss_wind_uigf", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "ss_solar_clearedmw",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "ss_wind_clearedmw",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "ss_solar_compliancemw",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "ss_wind_compliancemw",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("run_datetime", "interval_datetime", "regionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_p5min_regionsolution_lastchanged"),
        "p5min_regionsolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "p5min_unitsolution",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("connectionpointid", sa.String(length=12), nullable=True),
        sa.Column("tradetype", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("agcstatus", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("initialmw", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("totalcleared", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rampdownrate", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rampuprate", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower5min", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower60sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower6sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise5min", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise60sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise6sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lowerreg", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raisereg", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("availability", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise6secflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("raise60secflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("raise5minflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("raiseregflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lower6secflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lower60secflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lower5minflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lowerregflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("semidispatchcap", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("run_datetime", "interval_datetime", "duid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_p5min_unitsolution_lastchanged"),
        "p5min_unitsolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "participant",
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("participantclassid", sa.String(length=20), nullable=True),
        sa.Column("name", sa.String(length=80), nullable=True),
        sa.Column("description", sa.String(length=64), nullable=True),
        sa.Column("acn", sa.String(length=9), nullable=True),
        sa.Column("primarybusiness", sa.String(length=40), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("participantid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_participant_lastchanged"),
        "participant",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "participant_bandfee_alloc",
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("marketfeeid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantcategoryid", sa.String(length=10), nullable=False),
        sa.Column("marketfeevalue", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "participantid",
            "marketfeeid",
            "effectivedate",
            "versionno",
            "participantcategoryid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_participant_bandfee_alloc_lastchanged"),
        "participant_bandfee_alloc",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "participantaccount",
        sa.Column("accountname", sa.String(length=80), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("accountnumber", sa.String(length=16), nullable=True),
        sa.Column("bankname", sa.String(length=16), nullable=True),
        sa.Column("banknumber", sa.Numeric(precision=10, scale=0), nullable=True),
        sa.Column("branchname", sa.String(length=16), nullable=True),
        sa.Column("branchnumber", sa.Numeric(precision=10, scale=0), nullable=True),
        sa.Column("bsbnumber", sa.String(length=20), nullable=True),
        sa.Column(
            "nemmcocreditaccountnumber",
            sa.Numeric(precision=10, scale=0),
            nullable=True,
        ),
        sa.Column(
            "nemmcodebitaccountnumber",
            sa.Numeric(precision=10, scale=0),
            nullable=True,
        ),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("abn", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("participantid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_participantaccount_lastchanged"),
        "participantaccount",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "participantcategory",
        sa.Column("participantcategoryid", sa.String(length=10), nullable=False),
        sa.Column("description", sa.String(length=64), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("participantcategoryid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_participantcategory_lastchanged"),
        "participantcategory",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "participantcategoryalloc",
        sa.Column("participantcategoryid", sa.String(length=10), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("participantcategoryid", "participantid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_participantcategoryalloc_lastchanged"),
        "participantcategoryalloc",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "participantclass",
        sa.Column("participantclassid", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=64), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("participantclassid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_participantclass_lastchanged"),
        "participantclass",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "participantcreditdetail",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("creditlimit", sa.Numeric(precision=10, scale=0), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "participantid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_participantcreditdetail_lastchanged"),
        "participantcreditdetail",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_participantcreditdetail_participantid"),
        "participantcreditdetail",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "participantnoticetrk",
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("noticeid", sa.Numeric(precision=10, scale=0), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("participantid", "noticeid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_participantnoticetrk_lastchanged"),
        "participantnoticetrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_participantnoticetrk_participantid"),
        "participantnoticetrk",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "pasacasesolution",
        sa.Column("caseid", sa.String(length=20), nullable=False),
        sa.Column(
            "solutioncomplete",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("pasaversion", sa.Numeric(precision=27, scale=10), nullable=True),
        sa.Column(
            "excessgeneration",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("deficitcapacity", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("caseid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_pasacasesolution_lastchanged"),
        "pasacasesolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "pasaconstraintsolution",
        sa.Column("caseid", sa.String(length=20), nullable=False),
        sa.Column("constraintid", sa.String(length=20), nullable=False),
        sa.Column("periodid", sa.String(length=20), nullable=False),
        sa.Column(
            "capacitymarginalvalue",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "capacityviolationdegree",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "excessgenmarginalvalue",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "excessgenviolationdegree",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("constraintid", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_pasaconstraintsolution_lastchanged"),
        "pasaconstraintsolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "pasainterconnectorsolution",
        sa.Column("caseid", sa.String(length=20), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.String(length=20), nullable=False),
        sa.Column("capacitymwflow", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column(
            "capacitymarginalvalue",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "capacityviolationdegree",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("excessgenmwflow", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column(
            "excessgenmarginalvalue",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "excessgenviolationdegree",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("importlimit", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("exportlimit", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("interconnectorid", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_pasainterconnectorsolution_lastchanged"),
        "pasainterconnectorsolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "pasaregionsolution",
        sa.Column("caseid", sa.String(length=20), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.String(length=20), nullable=False),
        sa.Column("demand10", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("demand50", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("demand90", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column(
            "unconstrainedcapacity",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "constrainedcapacity",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("capacitysurplus", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("reservereq", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column(
            "reservecondition",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("reservesurplus", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column(
            "loadrejectionreservereq",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "loadrejectionreservesurplus",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "netinterchangeunderexcess",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "netinterchangeunderscarcity",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "excessgeneration",
            sa.Numeric(precision=22, scale=0),
            nullable=True,
        ),
        sa.Column("energyrequired", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "capacityrequired",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("regionid", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_pasaregionsolution_lastchanged"),
        "pasaregionsolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "pdpasa_casesolution",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("pasaversion", sa.String(length=10), nullable=True),
        sa.Column("reservecondition", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("lorcondition", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column(
            "capacityobjfunction",
            sa.Numeric(precision=12, scale=3),
            nullable=True,
        ),
        sa.Column("capacityoption", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column(
            "maxsurplusreserveoption",
            sa.Numeric(precision=12, scale=3),
            nullable=True,
        ),
        sa.Column(
            "maxsparecapacityoption",
            sa.Numeric(precision=12, scale=3),
            nullable=True,
        ),
        sa.Column(
            "interconnectorflowpenalty",
            sa.Numeric(precision=12, scale=3),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "reliabilitylrcdemandoption",
            sa.Numeric(precision=12, scale=3),
            nullable=True,
        ),
        sa.Column(
            "outagelrcdemandoption",
            sa.Numeric(precision=12, scale=3),
            nullable=True,
        ),
        sa.Column("lordemandoption", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("reliabilitylrccapacityoption", sa.String(length=10), nullable=True),
        sa.Column("outagelrccapacityoption", sa.String(length=10), nullable=True),
        sa.Column("lorcapacityoption", sa.String(length=10), nullable=True),
        sa.Column("loruigfoption", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column(
            "reliabilitylrcuigfoption",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column(
            "outagelrcuigfoption",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("run_datetime"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_pdpasa_casesolution_lastchanged"),
        "pdpasa_casesolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "pdpasa_regionsolution",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("demand10", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("demand50", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("demand90", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("reservereq", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("capacityreq", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "energyreqdemand50",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "unconstrainedcapacity",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.Column(
            "constrainedcapacity",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.Column(
            "netinterchangeunderscarcity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("surpluscapacity", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("surplusreserve", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("reservecondition", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column(
            "maxsurplusreserve",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "maxsparecapacity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("lorcondition", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column(
            "aggregatecapacityavailable",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "aggregatescheduledload",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "aggregatepasaavailability",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.Column(
            "runtype",
            sa.String(length=20),
            server_default=sa.text("'OUTAGE_LRC'::character varying"),
            nullable=False,
        ),
        sa.Column(
            "energyreqdemand10",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "calculatedlor1level",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "calculatedlor2level",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "msrnetinterchangeunderscarcity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "lornetinterchangeunderscarcity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "totalintermittentgeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "demand_and_nonschedgen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("uigf", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "semischeduledcapacity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "lor_semischeduledcapacity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("lcr", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lcr2", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("fum", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("ss_solar_uigf", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("ss_wind_uigf", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "ss_solar_capacity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "ss_wind_capacity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "ss_solar_cleared",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("ss_wind_cleared", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.PrimaryKeyConstraint("run_datetime", "interval_datetime", "regionid", "runtype"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_pdpasa_regionsolution_lastchanged"),
        "pdpasa_regionsolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "perdemand",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("resdemand", sa.Numeric(precision=10, scale=0), nullable=True),
        sa.Column(
            "demand90probability",
            sa.Numeric(precision=10, scale=0),
            nullable=True,
        ),
        sa.Column(
            "demand10probability",
            sa.Numeric(precision=10, scale=0),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("mr_schedule", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate", "regionid", "offerdate", "periodid", "versionno"
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_perdemand_lastchanged"),
        "perdemand",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "peroffer",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("selfdispatch", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("maxavail", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("fixedload", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("rocup", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("rocdown", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail1", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail2", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail3", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail4", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail5", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail6", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail7", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail8", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail9", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail10", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "pasaavailability",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.Column("mr_capacity", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "duid", "offerdate", "periodid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_peroffer_lastchanged"),
        "peroffer",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        "peroffer_ndx2",
        "peroffer",
        ["duid", "lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "peroffer_d",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("selfdispatch", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("maxavail", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("fixedload", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("rocup", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("rocdown", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail1", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail2", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail3", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail4", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail5", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail6", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail7", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail8", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail9", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("bandavail10", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "pasaavailability",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.Column("mr_capacity", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "duid", "offerdate", "periodid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_peroffer_d_lastchanged"),
        "peroffer_d",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        "peroffer_d_ndx2",
        "peroffer_d",
        ["duid", "lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "predispatch_fcas_req",
        sa.Column("predispatchseqno", sa.String(length=20), nullable=True),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("periodid", sa.String(length=20), nullable=True),
        sa.Column("genconid", sa.String(length=20), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("bidtype", sa.String(length=10), nullable=False),
        sa.Column(
            "genconeffectivedate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("genconversionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("marginalvalue", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("base_cost", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("adjusted_cost", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("estimated_cmpf", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("estimated_crmpf", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "recovery_factor_cmpf",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "recovery_factor_crmpf",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("genconid", "regionid", "bidtype", "datetime"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatch_fcas_req_lastchanged"),
        "predispatch_fcas_req",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "predispatch_local_price",
        sa.Column("predispatchseqno", sa.String(length=20), nullable=False),
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=20), nullable=False),
        sa.Column("periodid", sa.String(length=20), nullable=True),
        sa.Column(
            "local_price_adjustment",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.Column(
            "locally_constrained",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("datetime", "duid"),
        schema="mms",
    )
    op.create_table(
        "predispatch_mnspbidtrk",
        sa.Column("predispatchseqno", sa.String(length=20), nullable=False),
        sa.Column("linkid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.String(length=20), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("predispatchseqno", "linkid", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatch_mnspbidtrk_lastchanged"),
        "predispatch_mnspbidtrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "predispatchbidtrk",
        sa.Column("predispatchseqno", sa.String(length=20), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.String(length=20), nullable=False),
        sa.Column("bidtype", sa.String(length=10), nullable=True),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("predispatchseqno", "duid", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatchbidtrk_lastchanged"),
        "predispatchbidtrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        "predispatchbidtrk_ndx2",
        "predispatchbidtrk",
        ["duid", "lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        "predispatchbidtrk_ndx3",
        "predispatchbidtrk",
        ["duid", "settlementdate"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "predispatchblockedconstraint",
        sa.Column("predispatchseqno", sa.String(length=20), nullable=False),
        sa.Column("constraintid", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("predispatchseqno", "constraintid"),
        schema="mms",
    )
    op.create_table(
        "predispatchcasesolution",
        sa.Column("predispatchseqno", sa.String(length=20), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("solutionstatus", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("spdversion", sa.String(length=20), nullable=True),
        sa.Column(
            "nonphysicallosses",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column("totalobjective", sa.Numeric(precision=27, scale=10), nullable=True),
        sa.Column(
            "totalareagenviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalinterconnectorviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalgenericviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalramprateviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalunitmwcapacityviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "total5minviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalregviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "total6secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "total60secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalasprofileviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalenergyconstrviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalenergyofferviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("predispatchseqno", "runno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatchcasesolution_lastchanged"),
        "predispatchcasesolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "predispatchconstraint",
        sa.Column("predispatchseqno", sa.String(length=20), nullable=True),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("constraintid", sa.String(length=20), nullable=False),
        sa.Column("periodid", sa.String(length=20), nullable=True),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("rhs", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("marginalvalue", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("violationdegree", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("duid", sa.String(length=20), nullable=True),
        sa.Column(
            "genconid_effectivedate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "genconid_versionno",
            sa.Numeric(precision=22, scale=0),
            nullable=True,
        ),
        sa.Column("lhs", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.PrimaryKeyConstraint("constraintid", "datetime"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatchconstraint_lastchanged"),
        "predispatchconstraint",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatchconstraint_predispatchseqno"),
        "predispatchconstraint",
        ["predispatchseqno"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "predispatchinterconnectorres",
        sa.Column("predispatchseqno", sa.String(length=20), nullable=True),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.String(length=20), nullable=True),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("meteredmwflow", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwlosses", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("marginalvalue", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("violationdegree", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("exportlimit", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("importlimit", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("marginalloss", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("exportgenconid", sa.String(length=20), nullable=True),
        sa.Column("importgenconid", sa.String(length=20), nullable=True),
        sa.Column("fcasexportlimit", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("fcasimportlimit", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "local_price_adjustment_export",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.Column(
            "locally_constrained_export",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column(
            "local_price_adjustment_import",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.Column(
            "locally_constrained_import",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("interconnectorid", "datetime"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatchinterconnectorres_lastchanged"),
        "predispatchinterconnectorres",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatchinterconnectorres_predispatchseqno"),
        "predispatchinterconnectorres",
        ["predispatchseqno"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "predispatchintersensitivities",
        sa.Column("predispatchseqno", sa.String(length=20), nullable=True),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.String(length=20), nullable=True),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "intervention_active",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column("mwflow1", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow2", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow3", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow4", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow5", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow6", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow7", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow8", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow9", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow10", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow11", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow12", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow13", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow14", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow15", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow16", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow17", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow18", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow19", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow20", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow21", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow22", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow23", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow24", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow25", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow26", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow27", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow28", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow29", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow30", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow31", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow32", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow33", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow34", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow35", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow36", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow37", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow38", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow39", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow40", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow41", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow42", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow43", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("interconnectorid", "datetime"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatchintersensitivities_lastchanged"),
        "predispatchintersensitivities",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "predispatchload",
        sa.Column("predispatchseqno", sa.String(length=20), nullable=True),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("tradetype", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("periodid", sa.String(length=20), nullable=True),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("connectionpointid", sa.String(length=12), nullable=True),
        sa.Column("agcstatus", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("dispatchmode", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("initialmw", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("totalcleared", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower5min", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower60sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower6sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise5min", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise60sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise6sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rampdownrate", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rampuprate", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("downepf", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("upepf", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "marginal5minvalue",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "marginal60secvalue",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "marginal6secvalue",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("marginalvalue", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "violation5mindegree",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "violation60secdegree",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "violation6secdegree",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("violationdegree", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("lowerreg", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raisereg", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("availability", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise6secflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("raise60secflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("raise5minflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("raiseregflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lower6secflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lower60secflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lower5minflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lowerregflags", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column(
            "raise6secactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "raise60secactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "raise5minactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "raiseregactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "lower6secactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "lower60secactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "lower5minactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "lowerregactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("semidispatchcap", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("duid", "datetime"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatchload_lastchanged"),
        "predispatchload",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatchload_predispatchseqno"),
        "predispatchload",
        ["predispatchseqno"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        "predispatchload_ndx2",
        "predispatchload",
        ["duid", "lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "predispatchoffertrk",
        sa.Column("predispatchseqno", sa.String(length=20), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("bidtype", sa.String(length=20), nullable=False),
        sa.Column("periodid", sa.String(length=20), nullable=False),
        sa.Column(
            "bidsettlementdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column("bidofferdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("predispatchseqno", "duid", "bidtype", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatchoffertrk_lastchanged"),
        "predispatchoffertrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "predispatchprice",
        sa.Column("predispatchseqno", sa.String(length=20), nullable=True),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.String(length=20), nullable=True),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("eep", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrp1", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("eep1", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrp2", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("eep2", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrp3", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("eep3", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrp4", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("eep4", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrp5", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("eep5", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrp6", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("eep6", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrp7", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("eep7", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrp8", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("eep8", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("raise6secrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise60secrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise5minrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raiseregrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower6secrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower60secrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower5minrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lowerregrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.PrimaryKeyConstraint("regionid", "datetime"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatchprice_lastchanged"),
        "predispatchprice",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatchprice_predispatchseqno"),
        "predispatchprice",
        ["predispatchseqno"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "predispatchpricesensitivities",
        sa.Column("predispatchseqno", sa.String(length=20), nullable=True),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.String(length=20), nullable=True),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("rrpeep1", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep2", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep3", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep4", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep5", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep6", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep7", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep8", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep9", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep10", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep11", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep12", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep13", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep14", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep15", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep16", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep17", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep18", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep19", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep20", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep21", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep22", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep23", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep24", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep25", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep26", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep27", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep28", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("rrpeep29", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep30", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep31", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep32", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep33", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep34", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep35", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "intervention_active",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column("rrpeep36", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep37", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep38", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep39", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep40", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep41", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep42", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrpeep43", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.PrimaryKeyConstraint("regionid", "datetime"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatchpricesensitivities_lastchanged"),
        "predispatchpricesensitivities",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatchpricesensitivities_predispatchseqno"),
        "predispatchpricesensitivities",
        ["predispatchseqno"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "predispatchregionsum",
        sa.Column("predispatchseqno", sa.String(length=20), nullable=True),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.String(length=20), nullable=True),
        sa.Column("intervention", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("totaldemand", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "availablegeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("availableload", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("demandforecast", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "dispatchablegeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "dispatchableload",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("netinterchange", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "excessgeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower5mindispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower5minimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower5minlocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower5minlocalprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower5minlocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower5minprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower5minreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower5minsupplyprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60secdispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60secimport",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60seclocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60seclocalprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60seclocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower60secprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower60secreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower60secsupplyprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower6secdispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower6secimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower6seclocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower6seclocalprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower6seclocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower6secprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower6secreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower6secsupplyprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise5mindispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise5minimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise5minlocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise5minlocalprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise5minlocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise5minprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise5minreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise5minsupplyprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60secdispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60secimport",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60seclocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60seclocalprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60seclocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise60secprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise60secreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise60secsupplyprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6secdispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise6secimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise6seclocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6seclocalprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6seclocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise6secprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise6secreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise6secsupplyprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("initialsupply", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("clearedsupply", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lowerregimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lowerreglocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lowerreglocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lowerregreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raiseregimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raisereglocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raisereglocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raiseregreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise5minlocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raisereglocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60seclocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6seclocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower5minlocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lowerreglocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60seclocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower6seclocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise5minviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raiseregviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower5minviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lowerregviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower6secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6secactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "raise60secactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "raise5minactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "raiseregactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "lower6secactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "lower60secactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "lower5minactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "lowerregactualavailability",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("decavailability", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lorsurplus", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lrcsurplus", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column(
            "totalintermittentgeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "demand_and_nonschedgen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("uigf", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "semischedule_clearedmw",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "semischedule_compliancemw",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("ss_solar_uigf", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("ss_wind_uigf", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "ss_solar_clearedmw",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "ss_wind_clearedmw",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "ss_solar_compliancemw",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "ss_wind_compliancemw",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("regionid", "datetime"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatchregionsum_lastchanged"),
        "predispatchregionsum",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatchregionsum_predispatchseqno"),
        "predispatchregionsum",
        ["predispatchseqno"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "predispatchscenariodemand",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("scenario", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column("deltamw", sa.Numeric(precision=4, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno", "scenario", "regionid"),
        schema="mms",
    )
    op.create_table(
        "predispatchscenariodemandtrk",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_predispatchscenariodemandtrk_lastchanged"),
        "predispatchscenariodemandtrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "prudentialcompanyposition",
        sa.Column(
            "prudential_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("company_id", sa.String(length=20), nullable=False),
        sa.Column("mcl", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("credit_support", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("trading_limit", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column(
            "current_amount_balance",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "security_deposit_provision",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "security_deposit_offset",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "security_deposit_balance",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "expost_realloc_balance",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("default_balance", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("outstandings", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("trading_margin", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("typical_accrual", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column(
            "prudential_margin",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "early_payment_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "percentage_outstandings",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("prudential_date", "runno", "company_id"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_prudentialcompanyposition_lastchanged"),
        "prudentialcompanyposition",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "prudentialruntrk",
        sa.Column(
            "prudential_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("prudential_date", "runno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_prudentialruntrk_lastchanged"),
        "prudentialruntrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "reallocation",
        sa.Column("reallocationid", sa.String(length=20), nullable=False),
        sa.Column("creditparticipantid", sa.String(length=10), nullable=True),
        sa.Column("debitparticipantid", sa.String(length=10), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("agreementtype", sa.String(length=10), nullable=True),
        sa.Column("creditreference", sa.String(length=400), nullable=True),
        sa.Column("debitreference", sa.String(length=400), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("current_stepid", sa.String(length=20), nullable=True),
        sa.Column("daytype", sa.String(length=20), nullable=True),
        sa.Column("reallocation_type", sa.String(length=1), nullable=True),
        sa.Column("calendarid", sa.String(length=30), nullable=True),
        sa.Column("intervallength", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("reallocationid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_reallocation_lastchanged"),
        "reallocation",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "reallocationdetails",
        sa.Column("reallocationid", sa.String(length=20), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("reallocationid", "effectivedate", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_reallocationdetails_lastchanged"),
        "reallocationdetails",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "reallocationinterval",
        sa.Column("reallocationid", sa.String(length=20), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("value", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("nrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.PrimaryKeyConstraint("reallocationid", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_reallocationinterval_lastchanged"),
        "reallocationinterval",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "reallocationintervals",
        sa.Column("reallocationid", sa.String(length=20), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column(
            "reallocationvalue",
            sa.Numeric(precision=6, scale=2),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("reallocationid", "effectivedate", "versionno", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_reallocationintervals_lastchanged"),
        "reallocationintervals",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "reallocations",
        sa.Column("reallocationid", sa.String(length=20), nullable=False),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("startperiod", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("endperiod", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("participanttoid", sa.String(length=10), nullable=True),
        sa.Column("participantfromid", sa.String(length=10), nullable=True),
        sa.Column("agreementtype", sa.String(length=10), nullable=True),
        sa.Column(
            "deregistrationdate",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "deregistrationperiod",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("reallocationid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_reallocations_lastchanged"),
        "reallocations",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "region",
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("description", sa.String(length=64), nullable=True),
        sa.Column("regionstatus", sa.String(length=8), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("regionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_region_lastchanged"),
        "region",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "regionapc",
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("regionid", "effectivedate", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_regionapc_lastchanged"),
        "regionapc",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "regionapcintervals",
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("apcvalue", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("apctype", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("fcasapcvalue", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("apfvalue", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.PrimaryKeyConstraint("regionid", "effectivedate", "versionno", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_regionapcintervals_lastchanged"),
        "regionapcintervals",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "regionfcasrelaxation_ocd",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("servicetype", sa.String(length=10), nullable=False),
        sa.Column("global", sa.Numeric(precision=1, scale=0), nullable=False),
        sa.Column("requirement", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "runno", "regionid", "servicetype", "global"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_regionfcasrelaxation_ocd_lastchanged"),
        "regionfcasrelaxation_ocd",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "regionstandingdata",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("rsoid", sa.String(length=10), nullable=True),
        sa.Column("regionalreferencepointid", sa.String(length=10), nullable=True),
        sa.Column(
            "peaktradingperiod",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("scalingfactor", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno", "regionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_regionstandingdata_lastchanged"),
        "regionstandingdata",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "resdemandtrk",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("filename", sa.String(length=40), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "regionid", "offerdate", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_resdemandtrk_lastchanged"),
        "resdemandtrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "reserve",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=12), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("lower5min", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lower60sec", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lower6sec", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("raise5min", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("raise60sec", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("raise6sec", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("pasareserve", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column(
            "loadrejectionreservereq",
            sa.Numeric(precision=10, scale=0),
            nullable=True,
        ),
        sa.Column("raisereg", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lowerreg", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lor1level", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("lor2level", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "versionno", "regionid", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_reserve_lastchanged"),
        "reserve",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "residue_bid_trk",
        sa.Column("contractid", sa.String(length=30), nullable=True),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("bidloaddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("auctionid", sa.String(length=30), nullable=False),
        sa.PrimaryKeyConstraint("versionno", "participantid", "auctionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_residue_bid_trk_lastchanged"),
        "residue_bid_trk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "residue_con_data",
        sa.Column("contractid", sa.String(length=30), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("unitspurchased", sa.Numeric(precision=17, scale=5), nullable=True),
        sa.Column("linkpayment", sa.Numeric(precision=17, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "secondary_units_sold",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "contractid",
            "versionno",
            "participantid",
            "interconnectorid",
            "fromregionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_residue_con_data_lastchanged"),
        "residue_con_data",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "residue_con_estimates_trk",
        sa.Column("contractid", sa.String(length=30), nullable=False),
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("quarter", sa.Numeric(precision=1, scale=0), nullable=False),
        sa.Column("valuationid", sa.String(length=15), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractid", "contractyear", "quarter", "valuationid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_residue_con_estimates_trk_lastchanged"),
        "residue_con_estimates_trk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "residue_con_funds",
        sa.Column("contractid", sa.String(length=30), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("defaultunits", sa.Numeric(precision=5, scale=0), nullable=True),
        sa.Column("rolloverunits", sa.Numeric(precision=5, scale=0), nullable=True),
        sa.Column("reallocatedunits", sa.Numeric(precision=5, scale=0), nullable=True),
        sa.Column("unitsoffered", sa.Numeric(precision=5, scale=0), nullable=True),
        sa.Column("meanreserveprice", sa.Numeric(precision=9, scale=2), nullable=True),
        sa.Column("scalefactor", sa.Numeric(precision=8, scale=5), nullable=True),
        sa.Column(
            "actualreserveprice",
            sa.Numeric(precision=9, scale=2),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractid", "interconnectorid", "fromregionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_residue_con_funds_lastchanged"),
        "residue_con_funds",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "residue_contracts",
        sa.Column("contractyear", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("quarter", sa.Numeric(precision=1, scale=0), nullable=False),
        sa.Column("tranche", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("contractid", sa.String(length=30), nullable=True),
        sa.Column("startdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("notifydate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("auctiondate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("calcmethod", sa.String(length=20), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("notifypostdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("notifyby", sa.String(length=15), nullable=True),
        sa.Column("postdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("postedby", sa.String(length=15), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("description", sa.String(length=80), nullable=True),
        sa.Column("auctionid", sa.String(length=30), nullable=True),
        sa.PrimaryKeyConstraint("contractyear", "quarter", "tranche"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_residue_contracts_lastchanged"),
        "residue_contracts",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "residue_funds_bid",
        sa.Column("contractid", sa.String(length=30), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("loaddate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("optionid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("units", sa.Numeric(precision=5, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractid",
            "participantid",
            "loaddate",
            "optionid",
            "interconnectorid",
            "fromregionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_residue_funds_bid_lastchanged"),
        "residue_funds_bid",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "residue_price_bid",
        sa.Column("contractid", sa.String(length=30), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("loaddate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("optionid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("bidprice", sa.Numeric(precision=17, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("auctionid", sa.String(length=30), nullable=False),
        sa.PrimaryKeyConstraint("participantid", "loaddate", "optionid", "auctionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_residue_price_bid_lastchanged"),
        "residue_price_bid",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "residue_price_funds_bid",
        sa.Column("contractid", sa.String(length=30), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("units", sa.Numeric(precision=5, scale=0), nullable=True),
        sa.Column("bidprice", sa.Numeric(precision=17, scale=5), nullable=True),
        sa.Column("linkedbidflag", sa.Numeric(precision=6, scale=0), nullable=False),
        sa.Column("auctionid", sa.String(length=30), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "contractid",
            "interconnectorid",
            "fromregionid",
            "linkedbidflag",
            "auctionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_residue_price_funds_bid_lastchanged"),
        "residue_price_funds_bid",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "residue_public_data",
        sa.Column("contractid", sa.String(length=30), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("unitsoffered", sa.Numeric(precision=5, scale=0), nullable=True),
        sa.Column("unitssold", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("clearingprice", sa.Numeric(precision=17, scale=5), nullable=True),
        sa.Column("reserveprice", sa.Numeric(precision=17, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractid", "versionno", "interconnectorid", "fromregionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_residue_public_data_lastchanged"),
        "residue_public_data",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "residue_trk",
        sa.Column("contractid", sa.String(length=30), nullable=True),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("rundate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("postdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("postedby", sa.String(length=15), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("status", sa.String(length=15), nullable=True),
        sa.Column("auctionid", sa.String(length=30), nullable=False),
        sa.PrimaryKeyConstraint("versionno", "auctionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_residue_trk_lastchanged"),
        "residue_trk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "residuecontractpayments",
        sa.Column("contractid", sa.String(length=30), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("contractid", "participantid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_residuecontractpayments_lastchanged"),
        "residuecontractpayments",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "residuefiletrk",
        sa.Column("contractid", sa.String(length=30), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("loaddate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("filename", sa.String(length=40), nullable=True),
        sa.Column("ackfilename", sa.String(length=40), nullable=True),
        sa.Column("status", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("auctionid", sa.String(length=30), nullable=False),
        sa.PrimaryKeyConstraint("participantid", "loaddate", "auctionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_residuefiletrk_lastchanged"),
        "residuefiletrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "rooftop_pv_actual",
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column("power", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("qi", sa.Numeric(precision=2, scale=1), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("interval_datetime", "type", "regionid"),
        schema="mms",
    )
    op.create_table(
        "rooftop_pv_forecast",
        sa.Column(
            "version_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("powermean", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("powerpoe50", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("powerpoelow", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("powerpoehigh", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("version_datetime", "regionid", "interval_datetime"),
        schema="mms",
    )
    op.create_table(
        "secdeposit_interest_rate",
        sa.Column("interest_acct_id", sa.String(length=20), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "version_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("interest_rate", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint("interest_acct_id", "effectivedate", "version_datetime"),
        schema="mms",
    )
    op.create_table(
        "secdeposit_provision",
        sa.Column("security_deposit_id", sa.String(length=20), nullable=False),
        sa.Column("participantid", sa.String(length=20), nullable=False),
        sa.Column(
            "transaction_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "maturity_contractyear",
            sa.Numeric(precision=4, scale=0),
            nullable=True,
        ),
        sa.Column("maturity_weekno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("interest_rate", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("interest_calc_type", sa.String(length=20), nullable=True),
        sa.Column("interest_acct_id", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("security_deposit_id", "participantid"),
        schema="mms",
    )
    op.create_table(
        "set_ancillary_summary",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("service", sa.String(length=20), nullable=False),
        sa.Column("paymenttype", sa.String(length=20), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("paymentamount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "service",
            "paymenttype",
            "regionid",
            "periodid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_set_ancillary_summary_lastchanged"),
        "set_ancillary_summary",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "set_apc_compensation",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("apeventid", sa.Numeric(precision=6, scale=0), nullable=False),
        sa.Column("claimid", sa.Numeric(precision=6, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=20), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column(
            "compensation_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "apeventid",
            "claimid",
            "participantid",
            "periodid",
        ),
        schema="mms",
    )
    op.create_table(
        "set_apc_recovery",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("apeventid", sa.Numeric(precision=6, scale=0), nullable=False),
        sa.Column("claimid", sa.Numeric(precision=6, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=20), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=20), nullable=False),
        sa.Column("recovery_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "region_recovery_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "apeventid",
            "claimid",
            "participantid",
            "periodid",
            "regionid",
        ),
        schema="mms",
    )
    op.create_table(
        "set_csp_derogation_amount",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("amount_id", sa.String(length=20), nullable=False),
        sa.Column(
            "derogation_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "periodid",
            "participantid",
            "amount_id",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_set_csp_derogation_amount_lastchanged"),
        "set_csp_derogation_amount",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "set_csp_supportdata_constraint",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("constraintid", sa.String(length=20), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("marginalvalue", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("rhs", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "lowertumut_factor",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "uppertumut_factor",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "lowertumut_cspa_coeff",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "uppertumut_cspa_coeff",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("abs_x", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("abs_y", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "interval_datetime",
            "constraintid",
            "periodid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_set_csp_supportdata_constraint_lastchanged"),
        "set_csp_supportdata_constraint",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "set_csp_supportdata_energydiff",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("lowertumut_spdp", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("uppertumut_spdp", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("lowertumut_evdp", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("uppertumut_evdp", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("flow_direction", sa.String(length=20), nullable=True),
        sa.Column("total_x", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("total_y", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("lowertumut_age", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("uppertumut_age", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("eva", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "versionno", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_set_csp_supportdata_energydiff_lastchanged"),
        "set_csp_supportdata_energydiff",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "set_csp_supportdata_subprice",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("rrp", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("is_csp_interval", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("lowertumut_tlf", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("uppertumut_tlf", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "lowertumut_price",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "uppertumut_price",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "lowertumut_cspa_coeff",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "uppertumut_cspa_coeff",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "lowertumut_spdp_uncapped",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "uppertumut_spdp_uncapped",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("lowertumut_spdp", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("uppertumut_spdp", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("interval_abs_x", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("interval_abs_y", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "versionno", "interval_datetime"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_set_csp_supportdata_subprice_lastchanged"),
        "set_csp_supportdata_subprice",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "set_fcas_payment",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column(
            "lower6sec_payment",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "raise6sec_payment",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "lower60sec_payment",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "raise60sec_payment",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "lower5min_payment",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "raise5min_payment",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "lowerreg_payment",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "raisereg_payment",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "versionno", "duid", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_set_fcas_payment_lastchanged"),
        "set_fcas_payment",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "set_fcas_recovery",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.String(length=3), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column(
            "lower6sec_recovery",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "raise6sec_recovery",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "lower60sec_recovery",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "raise60sec_recovery",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "lower5min_recovery",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "raise5min_recovery",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "lowerreg_recovery",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "raisereg_recovery",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "lower6sec_recovery_gen",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "raise6sec_recovery_gen",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "lower60sec_recovery_gen",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "raise60sec_recovery_gen",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "lower5min_recovery_gen",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "raise5min_recovery_gen",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "lowerreg_recovery_gen",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "raisereg_recovery_gen",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "participantid",
            "regionid",
            "periodid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_set_fcas_recovery_lastchanged"),
        "set_fcas_recovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "set_fcas_regulation_trk",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("constraintid", sa.String(length=20), nullable=False),
        sa.Column("cmpf", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("crmpf", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "recovery_factor_cmpf",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "recovery_factor_crmpf",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate", "versionno", "interval_datetime", "constraintid"
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_set_fcas_regulation_trk_lastchanged"),
        "set_fcas_regulation_trk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "set_mr_payment",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("mr_capacity", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column(
            "uncapped_payment",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("capped_payment", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "versionno", "regionid", "duid", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_set_mr_payment_lastchanged"),
        "set_mr_payment",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "set_mr_recovery",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("arodef", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("nta", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "versionno", "regionid", "duid", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_set_mr_recovery_lastchanged"),
        "set_mr_recovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "set_nmas_recovery",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=20), nullable=False),
        sa.Column("service", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("paymenttype", sa.String(length=20), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("rbf", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("payment_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "participant_energy",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("region_energy", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("recovery_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "participant_generation",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "region_generation",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "recovery_amount_customer",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "recovery_amount_generator",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "periodid",
            "participantid",
            "service",
            "contractid",
            "paymenttype",
            "regionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_set_nmas_recovery_lastchanged"),
        "set_nmas_recovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "set_nmas_recovery_rbf",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("service", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("paymenttype", sa.String(length=20), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("rbf", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("payment_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("recovery_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "periodid",
            "service",
            "contractid",
            "paymenttype",
            "regionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_set_nmas_recovery_rbf_lastchanged"),
        "set_nmas_recovery_rbf",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "set_run_parameter",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("parameterid", sa.String(length=20), nullable=False),
        sa.Column("numvalue", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "versionno", "parameterid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_set_run_parameter_lastchanged"),
        "set_run_parameter",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setagcpayment",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("tlf", sa.Numeric(precision=7, scale=5), nullable=True),
        sa.Column("ebp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("clearedmw", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("initialmw", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("enablingpayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "contractversionno",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("offerversionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "participantid",
            "contractid",
            "periodid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setagcpayment_lastchanged"),
        "setagcpayment",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setagcpayment_participantid"),
        "setagcpayment",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setagcrecovery",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=True),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("enablingpayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "participantdemand",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("regiondemand", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "enablingrecovery",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "enablingrecovery_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "participantdemand_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "regiondemand_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "participantid",
            "periodid",
            "regionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setagcrecovery_lastchanged"),
        "setagcrecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setapccompensation",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("apccompensation", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "participantid",
            "regionid",
            "periodid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setapccompensation_lastchanged"),
        "setapccompensation",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setapcrecovery",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column(
            "totalcompensation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "participantdemand",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("regiondemand", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("apcrecovery", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "participantid",
            "regionid",
            "periodid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setapcrecovery_lastchanged"),
        "setapcrecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setcfg_participant_mpf",
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantcategoryid", sa.String(length=10), nullable=False),
        sa.Column("connectionpointid", sa.String(length=10), nullable=False),
        sa.Column("mpf", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "participantid",
            "effectivedate",
            "versionno",
            "participantcategoryid",
            "connectionpointid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setcfg_participant_mpf_lastchanged"),
        "setcfg_participant_mpf",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setcfg_participant_mpftrk",
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("participantid", "effectivedate", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setcfg_participant_mpftrk_lastchanged"),
        "setcfg_participant_mpftrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setcpdata",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=10, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=10, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("tcpid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("igenergy", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("xgenergy", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("inenergy", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("xnenergy", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("ipower", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("xpower", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("rrp", sa.Numeric(precision=20, scale=5), nullable=True),
        sa.Column("eep", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("tlf", sa.Numeric(precision=7, scale=5), nullable=True),
        sa.Column("cprrp", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("cpeep", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("ta", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("ep", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("apc", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("resc", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("resp", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("meterrunno", sa.Numeric(precision=10, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("hostdistributor", sa.String(length=10), nullable=True),
        sa.Column("mda", sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "periodid",
            "participantid",
            "tcpid",
            "mda",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setcpdata_lastchanged"),
        "setcpdata",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setcpdata_participantid"),
        "setcpdata",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setcpdataregion",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=22, scale=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=22, scale=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("sumigenergy", sa.Numeric(precision=27, scale=5), nullable=True),
        sa.Column("sumxgenergy", sa.Numeric(precision=27, scale=5), nullable=True),
        sa.Column("suminenergy", sa.Numeric(precision=27, scale=5), nullable=True),
        sa.Column("sumxnenergy", sa.Numeric(precision=27, scale=5), nullable=True),
        sa.Column("sumipower", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("sumxpower", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("sumep", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "versionno", "periodid", "regionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setcpdataregion_lastchanged"),
        "setcpdataregion",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setfcascomp",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("ccprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("clearedmw", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("unconstrainedmw", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("ebp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("tlf", sa.Numeric(precision=7, scale=5), nullable=True),
        sa.Column("rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("excessgen", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("fcascomp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate", "versionno", "participantid", "duid", "periodid"
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setfcascomp_lastchanged"),
        "setfcascomp",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setfcasrecovery",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("fcascomp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "participantdemand",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("regiondemand", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("fcasrecovery", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "fcasrecovery_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "participantdemand_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "regiondemand_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "participantid",
            "regionid",
            "periodid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setfcasrecovery_lastchanged"),
        "setfcasrecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setfcasregionrecovery",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("bidtype", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column(
            "generatorregionenergy",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "customerregionenergy",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("regionrecovery", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "versionno", "bidtype", "regionid", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setfcasregionrecovery_lastchanged"),
        "setfcasregionrecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setgendata",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=10, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=10, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("stationid", sa.String(length=10), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("gensetid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("genergy", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("aenergy", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("gpower", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("apower", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("rrp", sa.Numeric(precision=20, scale=5), nullable=True),
        sa.Column("eep", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("tlf", sa.Numeric(precision=7, scale=5), nullable=True),
        sa.Column("cprrp", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("cpeep", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("netenergy", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("energycost", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column(
            "excessenergycost",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column("apc", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("resc", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("resp", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("expenergy", sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column("expenergycost", sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column("meterrunno", sa.Numeric(precision=6, scale=0), nullable=True),
        sa.Column("mda", sa.String(length=10), nullable=True),
        sa.Column("secondary_tlf", sa.Numeric(precision=7, scale=5), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "periodid",
            "stationid",
            "duid",
            "gensetid",
            "regionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setgendata_lastchanged"),
        "setgendata",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setgendata_participantid"),
        "setgendata",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setgendataregion",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=22, scale=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=22, scale=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("genergy", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("aenergy", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("gpower", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("apower", sa.Numeric(precision=22, scale=0), nullable=True),
        sa.Column("netenergy", sa.Numeric(precision=27, scale=5), nullable=True),
        sa.Column("energycost", sa.Numeric(precision=27, scale=5), nullable=True),
        sa.Column(
            "excessenergycost",
            sa.Numeric(precision=27, scale=5),
            nullable=True,
        ),
        sa.Column("expenergy", sa.Numeric(precision=27, scale=6), nullable=True),
        sa.Column("expenergycost", sa.Numeric(precision=27, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "versionno", "periodid", "regionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setgendataregion_lastchanged"),
        "setgendataregion",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setgovpayment",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("tlf", sa.Numeric(precision=7, scale=5), nullable=True),
        sa.Column("rl6secraise", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rl60secraise", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rl6seclower", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rl60seclower", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("deadbandup", sa.Numeric(precision=7, scale=5), nullable=True),
        sa.Column("deadbanddown", sa.Numeric(precision=7, scale=5), nullable=True),
        sa.Column("r6", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("r60", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("l6", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("l60", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rl6", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rl60", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("ll6", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("ll60", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "enabling6rpayment",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "enabling60rpayment",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "enabling6lpayment",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "enabling60lpayment",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "contractversionno",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("offerversionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "participantid",
            "contractid",
            "periodid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setgovpayment_lastchanged"),
        "setgovpayment",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setgovpayment_participantid"),
        "setgovpayment",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setgovrecovery",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=True),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column(
            "enabling6rpayment",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "enabling60rpayment",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "enabling6lpayment",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "enabling60lpayment",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "participantdemand",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("regiondemand", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "enabling6rrecovery",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "enabling60rrecovery",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "enabling6lrecovery",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "enabling60lrecovery",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "enabling6lrecovery_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "enabling6rrecovery_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "enabling60lrecovery_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "enabling60rrecovery_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "participantdemand_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "regiondemand_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "participantid",
            "periodid",
            "regionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setgovrecovery_lastchanged"),
        "setgovrecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setintervention",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=True),
        sa.Column("contractversion", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("rcf", sa.CHAR(length=1), nullable=True),
        sa.Column(
            "interventionpayment",
            sa.Numeric(precision=12, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "versionno", "periodid", "duid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setintervention_lastchanged"),
        "setintervention",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setinterventionrecovery",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("rcf", sa.CHAR(length=1), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column(
            "participantdemand",
            sa.Numeric(precision=12, scale=5),
            nullable=True,
        ),
        sa.Column("totaldemand", sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column(
            "interventionpayment",
            sa.Numeric(precision=12, scale=5),
            nullable=True,
        ),
        sa.Column(
            "interventionamount",
            sa.Numeric(precision=12, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "periodid",
            "contractid",
            "participantid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setinterventionrecovery_lastchanged"),
        "setinterventionrecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setintraregionresidues",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("ep", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("ec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("exp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("irss", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "runno", "periodid", "regionid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setintraregionresidues_lastchanged"),
        "setintraregionresidues",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setiraucsurplus",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("settlementrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("totalsurplus", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "contractallocation",
            sa.Numeric(precision=8, scale=5),
            nullable=True,
        ),
        sa.Column("surplusvalue", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "csp_derogation_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("unadjusted_irsr", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "settlementrunno",
            "contractid",
            "periodid",
            "participantid",
            "interconnectorid",
            "fromregionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setiraucsurplus_lastchanged"),
        "setiraucsurplus",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setirfmrecovery",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("irfmid", sa.String(length=10), nullable=False),
        sa.Column("irmfversion", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column(
            "participantdemand",
            sa.Numeric(precision=12, scale=5),
            nullable=True,
        ),
        sa.Column("totaltcd", sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column("totaltfd", sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column("irfmamount", sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column("irfmpayment", sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "periodid",
            "irfmid",
            "participantid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setirfmrecovery_lastchanged"),
        "setirfmrecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setirnspsurplus",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("settlementrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("totalsurplus", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "contractallocation",
            sa.Numeric(precision=8, scale=5),
            nullable=True,
        ),
        sa.Column("surplusvalue", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "csp_derogation_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("unadjusted_irsr", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "settlementrunno",
            "contractid",
            "periodid",
            "participantid",
            "interconnectorid",
            "fromregionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setirnspsurplus_lastchanged"),
        "setirnspsurplus",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setirpartsurplus",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("settlementrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("totalsurplus", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "contractallocation",
            sa.Numeric(precision=8, scale=5),
            nullable=True,
        ),
        sa.Column("surplusvalue", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "csp_derogation_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("unadjusted_irsr", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "settlementrunno",
            "contractid",
            "periodid",
            "participantid",
            "interconnectorid",
            "fromregionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setirpartsurplus_lastchanged"),
        "setirpartsurplus",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setirsurplus",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("settlementrunno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("mwflow", sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column("lossfactor", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("surplusvalue", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "csp_derogation_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("unadjusted_irsr", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "settlementrunno",
            "periodid",
            "interconnectorid",
            "regionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setirsurplus_lastchanged"),
        "setirsurplus",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setlshedpayment",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("tlf", sa.Numeric(precision=7, scale=5), nullable=True),
        sa.Column("rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lseprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mcpprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lscr", sa.Numeric(precision=4, scale=0), nullable=True),
        sa.Column("lsepayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("ccpayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("constrainedmw", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("unconstrainedmw", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("als", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("initialdemand", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("finaldemand", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "contractversionno",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("offerversionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "availabilitypayment",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "participantid",
            "contractid",
            "periodid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setlshedpayment_lastchanged"),
        "setlshedpayment",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setlshedpayment_participantid"),
        "setlshedpayment",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setlshedrecovery",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=True),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("lsepayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("ccpayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "participantdemand",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("regiondemand", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lserecovery", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("ccrecovery", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lserecovery_gen", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("ccrecovery_gen", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "participantdemand_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "regiondemand_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "availabilityrecovery",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "availabilityrecovery_gen",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "participantid",
            "periodid",
            "regionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setlshedrecovery_lastchanged"),
        "setlshedrecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setluloadpayment",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("tlf", sa.Numeric(precision=7, scale=5), nullable=True),
        sa.Column("ebp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("enablingprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("usageprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("ccprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("blocksize", sa.Numeric(precision=4, scale=0), nullable=True),
        sa.Column("acr", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("unitoutput", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("unitexcessgen", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("enablingpayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("usagepayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "compensationpayment",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "contractversionno",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("offerversionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "participantid",
            "contractid",
            "periodid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setluloadpayment_lastchanged"),
        "setluloadpayment",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setluloadpayment_participantid"),
        "setluloadpayment",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setluloadrecovery",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=True),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("enablingpayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("usagepayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "compensationpayment",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "participantdemand",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("regiondemand", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "enablingrecovery",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("usagerecovery", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "compensationrecovery",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "enablingrecovery_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "usagerecovery_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "compensationrecovery_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "participantdemand_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "regiondemand_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "participantid",
            "periodid",
            "regionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setluloadrecovery_lastchanged"),
        "setluloadrecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setlunloadpayment",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("tlf", sa.Numeric(precision=7, scale=5), nullable=True),
        sa.Column("ebp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("enablingprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("usageprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("ccprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("clearedmw", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("unconstrainedmw", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("controlrange", sa.Numeric(precision=4, scale=0), nullable=True),
        sa.Column("enablingpayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("usagepayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "compensationpayment",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "contractversionno",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("offerversionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "participantid",
            "contractid",
            "periodid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setlunloadpayment_lastchanged"),
        "setlunloadpayment",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setlunloadpayment_participantid"),
        "setlunloadpayment",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setlunloadrecovery",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=True),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("enablingpayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("usagepayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "compensationpayment",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "participantdemand",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("regiondemand", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "enablingrecovery",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("usagerecovery", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "compensationrecovery",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "enablingrecovery_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "usagerecovery_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "compensationrecovery_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "participantdemand_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "regiondemand_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "participantid",
            "periodid",
            "regionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setlunloadrecovery_lastchanged"),
        "setlunloadrecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setmarketfees",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("marketfeeid", sa.String(length=10), nullable=False),
        sa.Column("marketfeevalue", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("energy", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("participantcategoryid", sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "runno",
            "participantid",
            "periodid",
            "marketfeeid",
            "participantcategoryid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setmarketfees_lastchanged"),
        "setmarketfees",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setreallocations",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("reallocationid", sa.String(length=20), nullable=False),
        sa.Column(
            "reallocationvalue",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("energy", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "runno",
            "periodid",
            "participantid",
            "reallocationid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setreallocations_lastchanged"),
        "setreallocations",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setreserverecovery",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("rcf", sa.CHAR(length=1), nullable=True),
        sa.Column("spotpayment", sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column(
            "participantdemand",
            sa.Numeric(precision=12, scale=5),
            nullable=True,
        ),
        sa.Column("totaldemand", sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column("reservepayment", sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column("reserveamount", sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "periodid",
            "contractid",
            "participantid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setreserverecovery_lastchanged"),
        "setreserverecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setreservetrader",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=True),
        sa.Column("contractversion", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("rcf", sa.CHAR(length=1), nullable=True),
        sa.Column("unitavail", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("cpa", sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column("cpe", sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column("cpu", sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column("cptotal", sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column("capdifference", sa.Numeric(precision=12, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "versionno", "periodid", "duid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setreservetrader_lastchanged"),
        "setreservetrader",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setrestartpayment",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("restarttype", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("avaflag", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column(
            "availabilityprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("tcf", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column(
            "availabilitypayment",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "contractversionno",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("offerversionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("enablingpayment", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "participantid",
            "contractid",
            "periodid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setrestartpayment_lastchanged"),
        "setrestartpayment",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setrestartpayment_participantid"),
        "setrestartpayment",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setrestartrecovery",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=True),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column(
            "availabilitypayment",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "participantdemand",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("regiondemand", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "availabilityrecovery",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "availabilityrecovery_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "participantdemand_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "regiondemand_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("enablingpayment", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "enablingrecovery",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "enablingrecovery_gen",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "participantid",
            "periodid",
            "regionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setrestartrecovery_lastchanged"),
        "setrestartrecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setrpowerpayment",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=True),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("tlf", sa.Numeric(precision=7, scale=5), nullable=True),
        sa.Column("ebp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mvaraprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mvareprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mvargprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("ccprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("synccompensation", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("mta", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mtg", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("blocksize", sa.Numeric(precision=4, scale=0), nullable=True),
        sa.Column("avaflag", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("clearedmw", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("unconstrainedmw", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "availabilitypayment",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("enablingpayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("ccpayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "contractversionno",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column("offerdate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("offerversionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "availabilitypayment_rebate",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "participantid",
            "contractid",
            "periodid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setrpowerpayment_lastchanged"),
        "setrpowerpayment",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setrpowerrecovery",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=True),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column(
            "availabilitypayment",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("enablingpayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("ccpayment", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "participantdemand",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("regiondemand", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "availabilityrecovery",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "enablingrecovery",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("ccrecovery", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "availabilityrecovery_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "enablingrecovery_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("ccrecovery_gen", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "participantdemand_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "regiondemand_gen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "participantid",
            "periodid",
            "regionid",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setrpowerrecovery_lastchanged"),
        "setrpowerrecovery",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setsmallgendata",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("connectionpointid", sa.String(length=20), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=20), nullable=False),
        sa.Column("regionid", sa.String(length=20), nullable=True),
        sa.Column("importenergy", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("exportenergy", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("rrp", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("tlf", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("impenergycost", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("expenergycost", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "settlementdate",
            "versionno",
            "connectionpointid",
            "periodid",
            "participantid",
        ),
        schema="mms",
    )
    op.create_table(
        "setvicboundaryenergy",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("boundaryenergy", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "versionno", "participantid", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setvicboundaryenergy_lastchanged"),
        "setvicboundaryenergy",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setvicenergyfigures",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("totalgenoutput", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("totalpcsd", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("tlr", sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column("mlf", sa.Numeric(precision=15, scale=6), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "versionno", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setvicenergyfigures_lastchanged"),
        "setvicenergyfigures",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "setvicenergyflow",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("netflow", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "versionno", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_setvicenergyflow_lastchanged"),
        "setvicenergyflow",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "spdconnectionpointconstraint",
        sa.Column("connectionpointid", sa.String(length=12), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("genconid", sa.String(length=20), nullable=False),
        sa.Column("factor", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("bidtype", sa.String(length=12), nullable=False),
        sa.PrimaryKeyConstraint(
            "connectionpointid",
            "effectivedate",
            "versionno",
            "genconid",
            "bidtype",
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_spdconnectionpointconstraint_lastchanged"),
        "spdconnectionpointconstraint",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "spdinterconnectorconstraint",
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("genconid", sa.String(length=20), nullable=False),
        sa.Column("factor", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("interconnectorid", "effectivedate", "versionno", "genconid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_spdinterconnectorconstraint_lastchanged"),
        "spdinterconnectorconstraint",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "spdregionconstraint",
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("genconid", sa.String(length=20), nullable=False),
        sa.Column("factor", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("bidtype", sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint("regionid", "effectivedate", "versionno", "genconid", "bidtype"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_spdregionconstraint_lastchanged"),
        "spdregionconstraint",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "sra_cash_security",
        sa.Column("cash_security_id", sa.String(length=36), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=True),
        sa.Column("provision_date", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("cash_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("interest_acct_id", sa.String(length=20), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("finalreturndate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "cash_security_returned",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("deletiondate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("cash_security_id"),
        schema="mms",
    )
    op.create_table(
        "sra_financial_auc_mardetail",
        sa.Column("sra_year", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("sra_quarter", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("sra_runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("cash_security_id", sa.String(length=36), nullable=False),
        sa.Column("returned_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "returned_interest",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "sra_year",
            "sra_quarter",
            "sra_runno",
            "participantid",
            "cash_security_id",
        ),
        schema="mms",
    )
    op.create_table(
        "sra_financial_auc_margin",
        sa.Column("sra_year", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("sra_quarter", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("sra_runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column(
            "total_cash_security",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("required_margin", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("returned_margin", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "returned_margin_interest",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("sra_year", "sra_quarter", "sra_runno", "participantid"),
        schema="mms",
    )
    op.create_table(
        "sra_financial_auc_receipts",
        sa.Column("sra_year", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("sra_quarter", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("sra_runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("units_purchased", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("clearing_price", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("receipt_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("proceeds_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("units_sold", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint(
            "sra_year",
            "sra_quarter",
            "sra_runno",
            "participantid",
            "interconnectorid",
            "fromregionid",
            "contractid",
        ),
        schema="mms",
    )
    op.create_table(
        "sra_financial_aucpay_detail",
        sa.Column("sra_year", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("sra_quarter", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("sra_runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("contractid", sa.String(length=10), nullable=False),
        sa.Column("maximum_units", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("units_sold", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("shortfall_units", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("reserve_price", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("clearing_price", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("payment_amount", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "shortfall_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("allocation", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "net_payment_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint(
            "sra_year",
            "sra_quarter",
            "sra_runno",
            "participantid",
            "interconnectorid",
            "fromregionid",
            "contractid",
        ),
        schema="mms",
    )
    op.create_table(
        "sra_financial_aucpay_sum",
        sa.Column("sra_year", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("sra_quarter", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("sra_runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column(
            "gross_proceeds_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "total_gross_proceeds_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "shortfall_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "total_shortfall_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "net_payment_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("sra_year", "sra_quarter", "sra_runno", "participantid"),
        schema="mms",
    )
    op.create_table(
        "sra_financial_runtrk",
        sa.Column("sra_year", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("sra_quarter", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("sra_runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("runtype", sa.String(length=20), nullable=True),
        sa.Column("rundate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("posteddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "interest_versionno",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column("makeup_versionno", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("sra_year", "sra_quarter", "sra_runno"),
        schema="mms",
    )
    op.create_table(
        "sra_offer_product",
        sa.Column("auctionid", sa.String(length=30), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("loaddate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("optionid", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=True),
        sa.Column("fromregionid", sa.String(length=10), nullable=True),
        sa.Column("offer_quantity", sa.Numeric(precision=5, scale=0), nullable=True),
        sa.Column("offer_price", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("trancheid", sa.String(length=30), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("auctionid", "participantid", "loaddate", "optionid"),
        schema="mms",
    )
    op.create_table(
        "sra_offer_profile",
        sa.Column("auctionid", sa.String(length=30), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("loaddate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("filename", sa.String(length=40), nullable=True),
        sa.Column("ackfilename", sa.String(length=40), nullable=True),
        sa.Column("transactionid", sa.String(length=100), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("auctionid", "participantid", "loaddate"),
        schema="mms",
    )
    op.create_table(
        "sra_prudential_cash_security",
        sa.Column(
            "prudential_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column(
            "prudential_runno",
            sa.Numeric(precision=8, scale=0),
            nullable=False,
        ),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("cash_security_id", sa.String(length=36), nullable=False),
        sa.Column(
            "cash_security_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "prudential_date",
            "prudential_runno",
            "participantid",
            "cash_security_id",
        ),
        schema="mms",
    )
    op.create_table(
        "sra_prudential_comp_position",
        sa.Column(
            "prudential_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column(
            "prudential_runno",
            sa.Numeric(precision=8, scale=0),
            nullable=False,
        ),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("trading_limit", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column(
            "prudential_exposure_amount",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column("trading_margin", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint("prudential_date", "prudential_runno", "participantid"),
        schema="mms",
    )
    op.create_table(
        "sra_prudential_exposure",
        sa.Column(
            "prudential_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column(
            "prudential_runno",
            sa.Numeric(precision=8, scale=0),
            nullable=False,
        ),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("sra_year", sa.Numeric(precision=4, scale=0), nullable=False),
        sa.Column("sra_quarter", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("fromregionid", sa.String(length=10), nullable=False),
        sa.Column("max_tranche", sa.Numeric(precision=2, scale=0), nullable=True),
        sa.Column("auctionid", sa.String(length=30), nullable=True),
        sa.Column(
            "offer_submissiontime",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.Column(
            "average_purchase_price",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "average_cancellation_price",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "cancellation_volume",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.Column(
            "trading_position",
            sa.Numeric(precision=18, scale=8),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "prudential_date",
            "prudential_runno",
            "participantid",
            "sra_year",
            "sra_quarter",
            "interconnectorid",
            "fromregionid",
        ),
        schema="mms",
    )
    op.create_table(
        "sra_prudential_run",
        sa.Column(
            "prudential_date",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column(
            "prudential_runno",
            sa.Numeric(precision=8, scale=0),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("prudential_date", "prudential_runno"),
        schema="mms",
    )
    op.create_table(
        "stadualloc",
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("stationid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("duid", "effectivedate", "stationid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_stadualloc_duid"),
        "stadualloc",
        ["duid"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_stadualloc_lastchanged"),
        "stadualloc",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        "stadualloc_ndx2",
        "stadualloc",
        ["stationid", "effectivedate", "versionno"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "station",
        sa.Column("stationid", sa.String(length=10), nullable=False),
        sa.Column("stationname", sa.String(length=80), nullable=True),
        sa.Column("address1", sa.String(length=80), nullable=True),
        sa.Column("address2", sa.String(length=80), nullable=True),
        sa.Column("address3", sa.String(length=80), nullable=True),
        sa.Column("address4", sa.String(length=80), nullable=True),
        sa.Column("city", sa.String(length=40), nullable=True),
        sa.Column("state", sa.String(length=10), nullable=True),
        sa.Column("postcode", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("connectionpointid", sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint("stationid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_station_lastchanged"),
        "station",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "stationoperatingstatus",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("stationid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "stationid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_stationoperatingstatus_lastchanged"),
        "stationoperatingstatus",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "stationowner",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("stationid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "participantid", "stationid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_stationowner_lastchanged"),
        "stationowner",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_stationowner_participantid"),
        "stationowner",
        ["participantid"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        "stationowner_ndx2",
        "stationowner",
        ["stationid", "effectivedate", "versionno"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "stationownertrk",
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("participantid", sa.String(length=10), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("authorisedby", sa.String(length=15), nullable=True),
        sa.Column("authoriseddate", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "participantid", "versionno"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_stationownertrk_lastchanged"),
        "stationownertrk",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "stpasa_casesolution",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("pasaversion", sa.String(length=10), nullable=True),
        sa.Column("reservecondition", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("lorcondition", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column(
            "capacityobjfunction",
            sa.Numeric(precision=12, scale=3),
            nullable=True,
        ),
        sa.Column("capacityoption", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column(
            "maxsurplusreserveoption",
            sa.Numeric(precision=12, scale=3),
            nullable=True,
        ),
        sa.Column(
            "maxsparecapacityoption",
            sa.Numeric(precision=12, scale=3),
            nullable=True,
        ),
        sa.Column(
            "interconnectorflowpenalty",
            sa.Numeric(precision=12, scale=3),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "reliabilitylrcdemandoption",
            sa.Numeric(precision=12, scale=3),
            nullable=True,
        ),
        sa.Column(
            "outagelrcdemandoption",
            sa.Numeric(precision=12, scale=3),
            nullable=True,
        ),
        sa.Column("lordemandoption", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("reliabilitylrccapacityoption", sa.String(length=10), nullable=True),
        sa.Column("outagelrccapacityoption", sa.String(length=10), nullable=True),
        sa.Column("lorcapacityoption", sa.String(length=10), nullable=True),
        sa.Column("loruigfoption", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.Column(
            "reliabilitylrcuigfoption",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.Column(
            "outagelrcuigfoption",
            sa.Numeric(precision=3, scale=0),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("run_datetime"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_stpasa_casesolution_lastchanged"),
        "stpasa_casesolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "stpasa_constraintsolution",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("constraintid", sa.String(length=20), nullable=False),
        sa.Column("capacityrhs", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "capacitymarginalvalue",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "capacityviolationdegree",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "runtype",
            sa.String(length=20),
            server_default=sa.text("'OUTAGE_LRC'::character varying"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("run_datetime", "interval_datetime", "constraintid", "runtype"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_stpasa_constraintsolution_lastchanged"),
        "stpasa_constraintsolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "stpasa_interconnectorsoln",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("capacitymwflow", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "capacitymarginalvalue",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "capacityviolationdegree",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "calculatedexportlimit",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "calculatedimportlimit",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "runtype",
            sa.String(length=20),
            server_default=sa.text("'OUTAGE_LRC'::character varying"),
            nullable=False,
        ),
        sa.Column("exportlimitconstraintid", sa.String(length=20), nullable=True),
        sa.Column("importlimitconstraintid", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint(
            "run_datetime", "interval_datetime", "interconnectorid", "runtype"
        ),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_stpasa_interconnectorsoln_lastchanged"),
        "stpasa_interconnectorsoln",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "stpasa_regionsolution",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("demand10", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("demand50", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("demand90", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("reservereq", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("capacityreq", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "energyreqdemand50",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "unconstrainedcapacity",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.Column(
            "constrainedcapacity",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.Column(
            "netinterchangeunderscarcity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("surpluscapacity", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("surplusreserve", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("reservecondition", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column(
            "maxsurplusreserve",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "maxsparecapacity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("lorcondition", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column(
            "aggregatecapacityavailable",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "aggregatescheduledload",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "aggregatepasaavailability",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.Column(
            "runtype",
            sa.String(length=20),
            server_default=sa.text("'OUTAGE_LRC'::character varying"),
            nullable=False,
        ),
        sa.Column(
            "energyreqdemand10",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "calculatedlor1level",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "calculatedlor2level",
            sa.Numeric(precision=16, scale=6),
            nullable=True,
        ),
        sa.Column(
            "msrnetinterchangeunderscarcity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "lornetinterchangeunderscarcity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "totalintermittentgeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "demand_and_nonschedgen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("uigf", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "semischeduledcapacity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "lor_semischeduledcapacity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("lcr", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("lcr2", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("fum", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column("ss_solar_uigf", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("ss_wind_uigf", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "ss_solar_capacity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "ss_wind_capacity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "ss_solar_cleared",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("ss_wind_cleared", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.PrimaryKeyConstraint("run_datetime", "interval_datetime", "regionid", "runtype"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_stpasa_regionsolution_lastchanged"),
        "stpasa_regionsolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "stpasa_systemsolution",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("systemdemand50", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("reservereq", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "unconstrainedcapacity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "constrainedcapacity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column("surpluscapacity", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("surplusreserve", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("reservecondition", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("interval_datetime"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_stpasa_systemsolution_lastchanged"),
        "stpasa_systemsolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_stpasa_systemsolution_run_datetime"),
        "stpasa_systemsolution",
        ["run_datetime"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "stpasa_unitsolution",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column(
            "interval_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("connectionpointid", sa.String(length=10), nullable=True),
        sa.Column(
            "expectedmaxcapacity",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "capacitymarginalvalue",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "capacityviolationdegree",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "capacityavailable",
            sa.Numeric(precision=12, scale=2),
            nullable=True,
        ),
        sa.Column(
            "energyconstrained",
            sa.Numeric(precision=1, scale=0),
            nullable=True,
        ),
        sa.Column("energyavailable", sa.Numeric(precision=10, scale=0), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "pasaavailability",
            sa.Numeric(precision=12, scale=0),
            nullable=True,
        ),
        sa.Column(
            "runtype",
            sa.String(length=20),
            server_default=sa.text("'OUTAGE_LRC'::character varying"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("run_datetime", "interval_datetime", "duid", "runtype"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_stpasa_unitsolution_lastchanged"),
        "stpasa_unitsolution",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "tradinginterconnect",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("interconnectorid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("meteredmwflow", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwflow", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("mwlosses", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "runno", "interconnectorid", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_tradinginterconnect_lastchanged"),
        "tradinginterconnect",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "tradingload",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("duid", sa.String(length=10), nullable=False),
        sa.Column("tradetype", sa.Numeric(precision=2, scale=0), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("initialmw", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("totalcleared", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rampdownrate", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("rampuprate", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower5min", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower60sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower6sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise5min", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise60sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise6sec", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("lowerreg", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raisereg", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("availability", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("semidispatchcap", sa.Numeric(precision=3, scale=0), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "runno", "duid", "tradetype", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_tradingload_lastchanged"),
        "tradingload",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_index(
        "tradingload_ndx2",
        "tradingload",
        ["duid", "lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "tradingprice",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("rrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("eep", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("invalidflag", sa.String(length=1), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("rop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise6secrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise6secrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise60secrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise60secrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise5minrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise5minrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raiseregrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raiseregrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower6secrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower6secrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower60secrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower60secrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower5minrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower5minrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lowerregrrp", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lowerregrop", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("price_status", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "runno", "regionid", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_tradingprice_lastchanged"),
        "tradingprice",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "tradingregionsum",
        sa.Column("settlementdate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("runno", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=False),
        sa.Column("periodid", sa.Numeric(precision=3, scale=0), nullable=False),
        sa.Column("totaldemand", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "availablegeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("availableload", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("demandforecast", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "dispatchablegeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "dispatchableload",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("netinterchange", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "excessgeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower5mindispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower5minimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower5minlocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower5minlocalprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower5minlocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower5minprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower5minreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower5minsupplyprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60secdispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60secimport",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60seclocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60seclocalprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60seclocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower60secprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower60secreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower60secsupplyprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower6secdispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower6secimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower6seclocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower6seclocalprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower6seclocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lower6secprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lower6secreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lower6secsupplyprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise5mindispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise5minimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise5minlocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise5minlocalprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise5minlocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise5minprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise5minreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise5minsupplyprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60secdispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60secimport",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60seclocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60seclocalprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60seclocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise60secprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise60secreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise60secsupplyprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6secdispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise6secimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise6seclocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6seclocalprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6seclocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raise6secprice", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raise6secreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise6secsupplyprice",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("initialsupply", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("clearedsupply", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("lowerregimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "lowerreglocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lowerreglocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("lowerregreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column("raiseregimport", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raisereglocaldispatch",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raisereglocalreq",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("raiseregreq", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.Column(
            "raise5minlocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raisereglocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60seclocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6seclocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower5minlocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lowerreglocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60seclocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower6seclocalviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise5minviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raiseregviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise60secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "raise6secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower5minviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lowerregviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower60secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "lower6secviolation",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "totalintermittentgeneration",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column(
            "demand_and_nonschedgen",
            sa.Numeric(precision=15, scale=5),
            nullable=True,
        ),
        sa.Column("uigf", sa.Numeric(precision=15, scale=5), nullable=True),
        sa.PrimaryKeyConstraint("settlementdate", "runno", "regionid", "periodid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_tradingregionsum_lastchanged"),
        "tradingregionsum",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "transmissionlossfactor",
        sa.Column(
            "transmissionlossfactor",
            sa.Numeric(precision=15, scale=5),
            nullable=False,
        ),
        sa.Column("effectivedate", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("versionno", sa.Numeric(precision=22, scale=0), nullable=False),
        sa.Column("connectionpointid", sa.String(length=10), nullable=False),
        sa.Column("regionid", sa.String(length=10), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("secondary_tlf", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.PrimaryKeyConstraint("effectivedate", "versionno", "connectionpointid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_transmissionlossfactor_lastchanged"),
        "transmissionlossfactor",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "valuationid",
        sa.Column("valuationid", sa.String(length=15), nullable=False),
        sa.Column("description", sa.String(length=80), nullable=True),
        sa.Column("lastchanged", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.PrimaryKeyConstraint("valuationid"),
        schema="mms",
    )
    op.create_index(
        op.f("ix_mms_valuationid_lastchanged"),
        "valuationid",
        ["lastchanged"],
        unique=False,
        schema="mms",
    )
    op.create_table(
        "voltage_instruction",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("ems_id", sa.String(length=60), nullable=False),
        sa.Column("participantid", sa.String(length=20), nullable=True),
        sa.Column("station_id", sa.String(length=60), nullable=True),
        sa.Column("device_id", sa.String(length=60), nullable=True),
        sa.Column("device_type", sa.String(length=20), nullable=True),
        sa.Column("control_type", sa.String(length=20), nullable=True),
        sa.Column("target", sa.Numeric(precision=15, scale=0), nullable=True),
        sa.Column("conforming", sa.Numeric(precision=1, scale=0), nullable=True),
        sa.Column("instruction_summary", sa.String(length=400), nullable=True),
        sa.Column(
            "version_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column(
            "instruction_sequence",
            sa.Numeric(precision=4, scale=0),
            nullable=True,
        ),
        sa.Column("additional_notes", sa.String(length=60), nullable=True),
        sa.PrimaryKeyConstraint("run_datetime", "ems_id", "version_datetime"),
        schema="mms",
    )
    op.create_table(
        "voltage_instruction_trk",
        sa.Column("run_datetime", postgresql.TIMESTAMP(precision=3), nullable=False),
        sa.Column("file_type", sa.String(length=20), nullable=True),
        sa.Column(
            "version_datetime",
            postgresql.TIMESTAMP(precision=3),
            nullable=False,
        ),
        sa.Column("se_datetime", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column("solution_category", sa.String(length=60), nullable=True),
        sa.Column("solution_status", sa.String(length=60), nullable=True),
        sa.Column("operating_mode", sa.String(length=60), nullable=True),
        sa.Column("operating_status", sa.String(length=100), nullable=True),
        sa.Column("est_expiry", postgresql.TIMESTAMP(precision=3), nullable=True),
        sa.Column(
            "est_next_instruction",
            postgresql.TIMESTAMP(precision=3),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("run_datetime", "version_datetime"),
        schema="mms",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.execute("drop schema mms cascade;")

    op.drop_table("voltage_instruction_trk", schema="mms")
    op.drop_table("voltage_instruction", schema="mms")
    op.drop_index(
        op.f("ix_mms_valuationid_lastchanged"),
        table_name="valuationid",
        schema="mms",
    )
    op.drop_table("valuationid", schema="mms")
    op.drop_index(
        op.f("ix_mms_transmissionlossfactor_lastchanged"),
        table_name="transmissionlossfactor",
        schema="mms",
    )
    op.drop_table("transmissionlossfactor", schema="mms")
    op.drop_index(
        op.f("ix_mms_tradingregionsum_lastchanged"),
        table_name="tradingregionsum",
        schema="mms",
    )
    op.drop_table("tradingregionsum", schema="mms")
    op.drop_index(
        op.f("ix_mms_tradingprice_lastchanged"),
        table_name="tradingprice",
        schema="mms",
    )
    op.drop_table("tradingprice", schema="mms")
    op.drop_index("tradingload_ndx2", table_name="tradingload", schema="mms")
    op.drop_index(
        op.f("ix_mms_tradingload_lastchanged"),
        table_name="tradingload",
        schema="mms",
    )
    op.drop_table("tradingload", schema="mms")
    op.drop_index(
        op.f("ix_mms_tradinginterconnect_lastchanged"),
        table_name="tradinginterconnect",
        schema="mms",
    )
    op.drop_table("tradinginterconnect", schema="mms")
    op.drop_index(
        op.f("ix_mms_stpasa_unitsolution_lastchanged"),
        table_name="stpasa_unitsolution",
        schema="mms",
    )
    op.drop_table("stpasa_unitsolution", schema="mms")
    op.drop_index(
        op.f("ix_mms_stpasa_systemsolution_run_datetime"),
        table_name="stpasa_systemsolution",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_stpasa_systemsolution_lastchanged"),
        table_name="stpasa_systemsolution",
        schema="mms",
    )
    op.drop_table("stpasa_systemsolution", schema="mms")
    op.drop_index(
        op.f("ix_mms_stpasa_regionsolution_lastchanged"),
        table_name="stpasa_regionsolution",
        schema="mms",
    )
    op.drop_table("stpasa_regionsolution", schema="mms")
    op.drop_index(
        op.f("ix_mms_stpasa_interconnectorsoln_lastchanged"),
        table_name="stpasa_interconnectorsoln",
        schema="mms",
    )
    op.drop_table("stpasa_interconnectorsoln", schema="mms")
    op.drop_index(
        op.f("ix_mms_stpasa_constraintsolution_lastchanged"),
        table_name="stpasa_constraintsolution",
        schema="mms",
    )
    op.drop_table("stpasa_constraintsolution", schema="mms")
    op.drop_index(
        op.f("ix_mms_stpasa_casesolution_lastchanged"),
        table_name="stpasa_casesolution",
        schema="mms",
    )
    op.drop_table("stpasa_casesolution", schema="mms")
    op.drop_index(
        op.f("ix_mms_stationownertrk_lastchanged"),
        table_name="stationownertrk",
        schema="mms",
    )
    op.drop_table("stationownertrk", schema="mms")
    op.drop_index("stationowner_ndx2", table_name="stationowner", schema="mms")
    op.drop_index(
        op.f("ix_mms_stationowner_participantid"),
        table_name="stationowner",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_stationowner_lastchanged"),
        table_name="stationowner",
        schema="mms",
    )
    op.drop_table("stationowner", schema="mms")
    op.drop_index(
        op.f("ix_mms_stationoperatingstatus_lastchanged"),
        table_name="stationoperatingstatus",
        schema="mms",
    )
    op.drop_table("stationoperatingstatus", schema="mms")
    op.drop_index(op.f("ix_mms_station_lastchanged"), table_name="station", schema="mms")
    op.drop_table("station", schema="mms")
    op.drop_index("stadualloc_ndx2", table_name="stadualloc", schema="mms")
    op.drop_index(
        op.f("ix_mms_stadualloc_lastchanged"),
        table_name="stadualloc",
        schema="mms",
    )
    op.drop_index(op.f("ix_mms_stadualloc_duid"), table_name="stadualloc", schema="mms")
    op.drop_table("stadualloc", schema="mms")
    op.drop_table("sra_prudential_run", schema="mms")
    op.drop_table("sra_prudential_exposure", schema="mms")
    op.drop_table("sra_prudential_comp_position", schema="mms")
    op.drop_table("sra_prudential_cash_security", schema="mms")
    op.drop_table("sra_offer_profile", schema="mms")
    op.drop_table("sra_offer_product", schema="mms")
    op.drop_table("sra_financial_runtrk", schema="mms")
    op.drop_table("sra_financial_aucpay_sum", schema="mms")
    op.drop_table("sra_financial_aucpay_detail", schema="mms")
    op.drop_table("sra_financial_auc_receipts", schema="mms")
    op.drop_table("sra_financial_auc_margin", schema="mms")
    op.drop_table("sra_financial_auc_mardetail", schema="mms")
    op.drop_table("sra_cash_security", schema="mms")
    op.drop_index(
        op.f("ix_mms_spdregionconstraint_lastchanged"),
        table_name="spdregionconstraint",
        schema="mms",
    )
    op.drop_table("spdregionconstraint", schema="mms")
    op.drop_index(
        op.f("ix_mms_spdinterconnectorconstraint_lastchanged"),
        table_name="spdinterconnectorconstraint",
        schema="mms",
    )
    op.drop_table("spdinterconnectorconstraint", schema="mms")
    op.drop_index(
        op.f("ix_mms_spdconnectionpointconstraint_lastchanged"),
        table_name="spdconnectionpointconstraint",
        schema="mms",
    )
    op.drop_table("spdconnectionpointconstraint", schema="mms")
    op.drop_index(
        op.f("ix_mms_setvicenergyflow_lastchanged"),
        table_name="setvicenergyflow",
        schema="mms",
    )
    op.drop_table("setvicenergyflow", schema="mms")
    op.drop_index(
        op.f("ix_mms_setvicenergyfigures_lastchanged"),
        table_name="setvicenergyfigures",
        schema="mms",
    )
    op.drop_table("setvicenergyfigures", schema="mms")
    op.drop_index(
        op.f("ix_mms_setvicboundaryenergy_lastchanged"),
        table_name="setvicboundaryenergy",
        schema="mms",
    )
    op.drop_table("setvicboundaryenergy", schema="mms")
    op.drop_table("setsmallgendata", schema="mms")
    op.drop_index(
        op.f("ix_mms_setrpowerrecovery_lastchanged"),
        table_name="setrpowerrecovery",
        schema="mms",
    )
    op.drop_table("setrpowerrecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_setrpowerpayment_lastchanged"),
        table_name="setrpowerpayment",
        schema="mms",
    )
    op.drop_table("setrpowerpayment", schema="mms")
    op.drop_index(
        op.f("ix_mms_setrestartrecovery_lastchanged"),
        table_name="setrestartrecovery",
        schema="mms",
    )
    op.drop_table("setrestartrecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_setrestartpayment_participantid"),
        table_name="setrestartpayment",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_setrestartpayment_lastchanged"),
        table_name="setrestartpayment",
        schema="mms",
    )
    op.drop_table("setrestartpayment", schema="mms")
    op.drop_index(
        op.f("ix_mms_setreservetrader_lastchanged"),
        table_name="setreservetrader",
        schema="mms",
    )
    op.drop_table("setreservetrader", schema="mms")
    op.drop_index(
        op.f("ix_mms_setreserverecovery_lastchanged"),
        table_name="setreserverecovery",
        schema="mms",
    )
    op.drop_table("setreserverecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_setreallocations_lastchanged"),
        table_name="setreallocations",
        schema="mms",
    )
    op.drop_table("setreallocations", schema="mms")
    op.drop_index(
        op.f("ix_mms_setmarketfees_lastchanged"),
        table_name="setmarketfees",
        schema="mms",
    )
    op.drop_table("setmarketfees", schema="mms")
    op.drop_index(
        op.f("ix_mms_setlunloadrecovery_lastchanged"),
        table_name="setlunloadrecovery",
        schema="mms",
    )
    op.drop_table("setlunloadrecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_setlunloadpayment_participantid"),
        table_name="setlunloadpayment",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_setlunloadpayment_lastchanged"),
        table_name="setlunloadpayment",
        schema="mms",
    )
    op.drop_table("setlunloadpayment", schema="mms")
    op.drop_index(
        op.f("ix_mms_setluloadrecovery_lastchanged"),
        table_name="setluloadrecovery",
        schema="mms",
    )
    op.drop_table("setluloadrecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_setluloadpayment_participantid"),
        table_name="setluloadpayment",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_setluloadpayment_lastchanged"),
        table_name="setluloadpayment",
        schema="mms",
    )
    op.drop_table("setluloadpayment", schema="mms")
    op.drop_index(
        op.f("ix_mms_setlshedrecovery_lastchanged"),
        table_name="setlshedrecovery",
        schema="mms",
    )
    op.drop_table("setlshedrecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_setlshedpayment_participantid"),
        table_name="setlshedpayment",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_setlshedpayment_lastchanged"),
        table_name="setlshedpayment",
        schema="mms",
    )
    op.drop_table("setlshedpayment", schema="mms")
    op.drop_index(
        op.f("ix_mms_setirsurplus_lastchanged"),
        table_name="setirsurplus",
        schema="mms",
    )
    op.drop_table("setirsurplus", schema="mms")
    op.drop_index(
        op.f("ix_mms_setirpartsurplus_lastchanged"),
        table_name="setirpartsurplus",
        schema="mms",
    )
    op.drop_table("setirpartsurplus", schema="mms")
    op.drop_index(
        op.f("ix_mms_setirnspsurplus_lastchanged"),
        table_name="setirnspsurplus",
        schema="mms",
    )
    op.drop_table("setirnspsurplus", schema="mms")
    op.drop_index(
        op.f("ix_mms_setirfmrecovery_lastchanged"),
        table_name="setirfmrecovery",
        schema="mms",
    )
    op.drop_table("setirfmrecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_setiraucsurplus_lastchanged"),
        table_name="setiraucsurplus",
        schema="mms",
    )
    op.drop_table("setiraucsurplus", schema="mms")
    op.drop_index(
        op.f("ix_mms_setintraregionresidues_lastchanged"),
        table_name="setintraregionresidues",
        schema="mms",
    )
    op.drop_table("setintraregionresidues", schema="mms")
    op.drop_index(
        op.f("ix_mms_setinterventionrecovery_lastchanged"),
        table_name="setinterventionrecovery",
        schema="mms",
    )
    op.drop_table("setinterventionrecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_setintervention_lastchanged"),
        table_name="setintervention",
        schema="mms",
    )
    op.drop_table("setintervention", schema="mms")
    op.drop_index(
        op.f("ix_mms_setgovrecovery_lastchanged"),
        table_name="setgovrecovery",
        schema="mms",
    )
    op.drop_table("setgovrecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_setgovpayment_participantid"),
        table_name="setgovpayment",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_setgovpayment_lastchanged"),
        table_name="setgovpayment",
        schema="mms",
    )
    op.drop_table("setgovpayment", schema="mms")
    op.drop_index(
        op.f("ix_mms_setgendataregion_lastchanged"),
        table_name="setgendataregion",
        schema="mms",
    )
    op.drop_table("setgendataregion", schema="mms")
    op.drop_index(
        op.f("ix_mms_setgendata_participantid"),
        table_name="setgendata",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_setgendata_lastchanged"),
        table_name="setgendata",
        schema="mms",
    )
    op.drop_table("setgendata", schema="mms")
    op.drop_index(
        op.f("ix_mms_setfcasregionrecovery_lastchanged"),
        table_name="setfcasregionrecovery",
        schema="mms",
    )
    op.drop_table("setfcasregionrecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_setfcasrecovery_lastchanged"),
        table_name="setfcasrecovery",
        schema="mms",
    )
    op.drop_table("setfcasrecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_setfcascomp_lastchanged"),
        table_name="setfcascomp",
        schema="mms",
    )
    op.drop_table("setfcascomp", schema="mms")
    op.drop_index(
        op.f("ix_mms_setcpdataregion_lastchanged"),
        table_name="setcpdataregion",
        schema="mms",
    )
    op.drop_table("setcpdataregion", schema="mms")
    op.drop_index(
        op.f("ix_mms_setcpdata_participantid"),
        table_name="setcpdata",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_setcpdata_lastchanged"),
        table_name="setcpdata",
        schema="mms",
    )
    op.drop_table("setcpdata", schema="mms")
    op.drop_index(
        op.f("ix_mms_setcfg_participant_mpftrk_lastchanged"),
        table_name="setcfg_participant_mpftrk",
        schema="mms",
    )
    op.drop_table("setcfg_participant_mpftrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_setcfg_participant_mpf_lastchanged"),
        table_name="setcfg_participant_mpf",
        schema="mms",
    )
    op.drop_table("setcfg_participant_mpf", schema="mms")
    op.drop_index(
        op.f("ix_mms_setapcrecovery_lastchanged"),
        table_name="setapcrecovery",
        schema="mms",
    )
    op.drop_table("setapcrecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_setapccompensation_lastchanged"),
        table_name="setapccompensation",
        schema="mms",
    )
    op.drop_table("setapccompensation", schema="mms")
    op.drop_index(
        op.f("ix_mms_setagcrecovery_lastchanged"),
        table_name="setagcrecovery",
        schema="mms",
    )
    op.drop_table("setagcrecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_setagcpayment_participantid"),
        table_name="setagcpayment",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_setagcpayment_lastchanged"),
        table_name="setagcpayment",
        schema="mms",
    )
    op.drop_table("setagcpayment", schema="mms")
    op.drop_index(
        op.f("ix_mms_set_run_parameter_lastchanged"),
        table_name="set_run_parameter",
        schema="mms",
    )
    op.drop_table("set_run_parameter", schema="mms")
    op.drop_index(
        op.f("ix_mms_set_nmas_recovery_rbf_lastchanged"),
        table_name="set_nmas_recovery_rbf",
        schema="mms",
    )
    op.drop_table("set_nmas_recovery_rbf", schema="mms")
    op.drop_index(
        op.f("ix_mms_set_nmas_recovery_lastchanged"),
        table_name="set_nmas_recovery",
        schema="mms",
    )
    op.drop_table("set_nmas_recovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_set_mr_recovery_lastchanged"),
        table_name="set_mr_recovery",
        schema="mms",
    )
    op.drop_table("set_mr_recovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_set_mr_payment_lastchanged"),
        table_name="set_mr_payment",
        schema="mms",
    )
    op.drop_table("set_mr_payment", schema="mms")
    op.drop_index(
        op.f("ix_mms_set_fcas_regulation_trk_lastchanged"),
        table_name="set_fcas_regulation_trk",
        schema="mms",
    )
    op.drop_table("set_fcas_regulation_trk", schema="mms")
    op.drop_index(
        op.f("ix_mms_set_fcas_recovery_lastchanged"),
        table_name="set_fcas_recovery",
        schema="mms",
    )
    op.drop_table("set_fcas_recovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_set_fcas_payment_lastchanged"),
        table_name="set_fcas_payment",
        schema="mms",
    )
    op.drop_table("set_fcas_payment", schema="mms")
    op.drop_index(
        op.f("ix_mms_set_csp_supportdata_subprice_lastchanged"),
        table_name="set_csp_supportdata_subprice",
        schema="mms",
    )
    op.drop_table("set_csp_supportdata_subprice", schema="mms")
    op.drop_index(
        op.f("ix_mms_set_csp_supportdata_energydiff_lastchanged"),
        table_name="set_csp_supportdata_energydiff",
        schema="mms",
    )
    op.drop_table("set_csp_supportdata_energydiff", schema="mms")
    op.drop_index(
        op.f("ix_mms_set_csp_supportdata_constraint_lastchanged"),
        table_name="set_csp_supportdata_constraint",
        schema="mms",
    )
    op.drop_table("set_csp_supportdata_constraint", schema="mms")
    op.drop_index(
        op.f("ix_mms_set_csp_derogation_amount_lastchanged"),
        table_name="set_csp_derogation_amount",
        schema="mms",
    )
    op.drop_table("set_csp_derogation_amount", schema="mms")
    op.drop_table("set_apc_recovery", schema="mms")
    op.drop_table("set_apc_compensation", schema="mms")
    op.drop_index(
        op.f("ix_mms_set_ancillary_summary_lastchanged"),
        table_name="set_ancillary_summary",
        schema="mms",
    )
    op.drop_table("set_ancillary_summary", schema="mms")
    op.drop_table("secdeposit_provision", schema="mms")
    op.drop_table("secdeposit_interest_rate", schema="mms")
    op.drop_table("rooftop_pv_forecast", schema="mms")
    op.drop_table("rooftop_pv_actual", schema="mms")
    op.drop_index(
        op.f("ix_mms_residuefiletrk_lastchanged"),
        table_name="residuefiletrk",
        schema="mms",
    )
    op.drop_table("residuefiletrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_residuecontractpayments_lastchanged"),
        table_name="residuecontractpayments",
        schema="mms",
    )
    op.drop_table("residuecontractpayments", schema="mms")
    op.drop_index(
        op.f("ix_mms_residue_trk_lastchanged"),
        table_name="residue_trk",
        schema="mms",
    )
    op.drop_table("residue_trk", schema="mms")
    op.drop_index(
        op.f("ix_mms_residue_public_data_lastchanged"),
        table_name="residue_public_data",
        schema="mms",
    )
    op.drop_table("residue_public_data", schema="mms")
    op.drop_index(
        op.f("ix_mms_residue_price_funds_bid_lastchanged"),
        table_name="residue_price_funds_bid",
        schema="mms",
    )
    op.drop_table("residue_price_funds_bid", schema="mms")
    op.drop_index(
        op.f("ix_mms_residue_price_bid_lastchanged"),
        table_name="residue_price_bid",
        schema="mms",
    )
    op.drop_table("residue_price_bid", schema="mms")
    op.drop_index(
        op.f("ix_mms_residue_funds_bid_lastchanged"),
        table_name="residue_funds_bid",
        schema="mms",
    )
    op.drop_table("residue_funds_bid", schema="mms")
    op.drop_index(
        op.f("ix_mms_residue_contracts_lastchanged"),
        table_name="residue_contracts",
        schema="mms",
    )
    op.drop_table("residue_contracts", schema="mms")
    op.drop_index(
        op.f("ix_mms_residue_con_funds_lastchanged"),
        table_name="residue_con_funds",
        schema="mms",
    )
    op.drop_table("residue_con_funds", schema="mms")
    op.drop_index(
        op.f("ix_mms_residue_con_estimates_trk_lastchanged"),
        table_name="residue_con_estimates_trk",
        schema="mms",
    )
    op.drop_table("residue_con_estimates_trk", schema="mms")
    op.drop_index(
        op.f("ix_mms_residue_con_data_lastchanged"),
        table_name="residue_con_data",
        schema="mms",
    )
    op.drop_table("residue_con_data", schema="mms")
    op.drop_index(
        op.f("ix_mms_residue_bid_trk_lastchanged"),
        table_name="residue_bid_trk",
        schema="mms",
    )
    op.drop_table("residue_bid_trk", schema="mms")
    op.drop_index(op.f("ix_mms_reserve_lastchanged"), table_name="reserve", schema="mms")
    op.drop_table("reserve", schema="mms")
    op.drop_index(
        op.f("ix_mms_resdemandtrk_lastchanged"),
        table_name="resdemandtrk",
        schema="mms",
    )
    op.drop_table("resdemandtrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_regionstandingdata_lastchanged"),
        table_name="regionstandingdata",
        schema="mms",
    )
    op.drop_table("regionstandingdata", schema="mms")
    op.drop_index(
        op.f("ix_mms_regionfcasrelaxation_ocd_lastchanged"),
        table_name="regionfcasrelaxation_ocd",
        schema="mms",
    )
    op.drop_table("regionfcasrelaxation_ocd", schema="mms")
    op.drop_index(
        op.f("ix_mms_regionapcintervals_lastchanged"),
        table_name="regionapcintervals",
        schema="mms",
    )
    op.drop_table("regionapcintervals", schema="mms")
    op.drop_index(
        op.f("ix_mms_regionapc_lastchanged"),
        table_name="regionapc",
        schema="mms",
    )
    op.drop_table("regionapc", schema="mms")
    op.drop_index(op.f("ix_mms_region_lastchanged"), table_name="region", schema="mms")
    op.drop_table("region", schema="mms")
    op.drop_index(
        op.f("ix_mms_reallocations_lastchanged"),
        table_name="reallocations",
        schema="mms",
    )
    op.drop_table("reallocations", schema="mms")
    op.drop_index(
        op.f("ix_mms_reallocationintervals_lastchanged"),
        table_name="reallocationintervals",
        schema="mms",
    )
    op.drop_table("reallocationintervals", schema="mms")
    op.drop_index(
        op.f("ix_mms_reallocationinterval_lastchanged"),
        table_name="reallocationinterval",
        schema="mms",
    )
    op.drop_table("reallocationinterval", schema="mms")
    op.drop_index(
        op.f("ix_mms_reallocationdetails_lastchanged"),
        table_name="reallocationdetails",
        schema="mms",
    )
    op.drop_table("reallocationdetails", schema="mms")
    op.drop_index(
        op.f("ix_mms_reallocation_lastchanged"),
        table_name="reallocation",
        schema="mms",
    )
    op.drop_table("reallocation", schema="mms")
    op.drop_index(
        op.f("ix_mms_prudentialruntrk_lastchanged"),
        table_name="prudentialruntrk",
        schema="mms",
    )
    op.drop_table("prudentialruntrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_prudentialcompanyposition_lastchanged"),
        table_name="prudentialcompanyposition",
        schema="mms",
    )
    op.drop_table("prudentialcompanyposition", schema="mms")
    op.drop_index(
        op.f("ix_mms_predispatchscenariodemandtrk_lastchanged"),
        table_name="predispatchscenariodemandtrk",
        schema="mms",
    )
    op.drop_table("predispatchscenariodemandtrk", schema="mms")
    op.drop_table("predispatchscenariodemand", schema="mms")
    op.drop_index(
        op.f("ix_mms_predispatchregionsum_predispatchseqno"),
        table_name="predispatchregionsum",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_predispatchregionsum_lastchanged"),
        table_name="predispatchregionsum",
        schema="mms",
    )
    op.drop_table("predispatchregionsum", schema="mms")
    op.drop_index(
        op.f("ix_mms_predispatchpricesensitivities_predispatchseqno"),
        table_name="predispatchpricesensitivities",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_predispatchpricesensitivities_lastchanged"),
        table_name="predispatchpricesensitivities",
        schema="mms",
    )
    op.drop_table("predispatchpricesensitivities", schema="mms")
    op.drop_index(
        op.f("ix_mms_predispatchprice_predispatchseqno"),
        table_name="predispatchprice",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_predispatchprice_lastchanged"),
        table_name="predispatchprice",
        schema="mms",
    )
    op.drop_table("predispatchprice", schema="mms")
    op.drop_index(
        op.f("ix_mms_predispatchoffertrk_lastchanged"),
        table_name="predispatchoffertrk",
        schema="mms",
    )
    op.drop_table("predispatchoffertrk", schema="mms")
    op.drop_index("predispatchload_ndx2", table_name="predispatchload", schema="mms")
    op.drop_index(
        op.f("ix_mms_predispatchload_predispatchseqno"),
        table_name="predispatchload",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_predispatchload_lastchanged"),
        table_name="predispatchload",
        schema="mms",
    )
    op.drop_table("predispatchload", schema="mms")
    op.drop_index(
        op.f("ix_mms_predispatchintersensitivities_lastchanged"),
        table_name="predispatchintersensitivities",
        schema="mms",
    )
    op.drop_table("predispatchintersensitivities", schema="mms")
    op.drop_index(
        op.f("ix_mms_predispatchinterconnectorres_predispatchseqno"),
        table_name="predispatchinterconnectorres",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_predispatchinterconnectorres_lastchanged"),
        table_name="predispatchinterconnectorres",
        schema="mms",
    )
    op.drop_table("predispatchinterconnectorres", schema="mms")
    op.drop_index(
        op.f("ix_mms_predispatchconstraint_predispatchseqno"),
        table_name="predispatchconstraint",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_predispatchconstraint_lastchanged"),
        table_name="predispatchconstraint",
        schema="mms",
    )
    op.drop_table("predispatchconstraint", schema="mms")
    op.drop_index(
        op.f("ix_mms_predispatchcasesolution_lastchanged"),
        table_name="predispatchcasesolution",
        schema="mms",
    )
    op.drop_table("predispatchcasesolution", schema="mms")
    op.drop_table("predispatchblockedconstraint", schema="mms")
    op.drop_index("predispatchbidtrk_ndx3", table_name="predispatchbidtrk", schema="mms")
    op.drop_index("predispatchbidtrk_ndx2", table_name="predispatchbidtrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_predispatchbidtrk_lastchanged"),
        table_name="predispatchbidtrk",
        schema="mms",
    )
    op.drop_table("predispatchbidtrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_predispatch_mnspbidtrk_lastchanged"),
        table_name="predispatch_mnspbidtrk",
        schema="mms",
    )
    op.drop_table("predispatch_mnspbidtrk", schema="mms")
    op.drop_table("predispatch_local_price", schema="mms")
    op.drop_index(
        op.f("ix_mms_predispatch_fcas_req_lastchanged"),
        table_name="predispatch_fcas_req",
        schema="mms",
    )
    op.drop_table("predispatch_fcas_req", schema="mms")
    op.drop_index("peroffer_d_ndx2", table_name="peroffer_d", schema="mms")
    op.drop_index(
        op.f("ix_mms_peroffer_d_lastchanged"),
        table_name="peroffer_d",
        schema="mms",
    )
    op.drop_table("peroffer_d", schema="mms")
    op.drop_index("peroffer_ndx2", table_name="peroffer", schema="mms")
    op.drop_index(
        op.f("ix_mms_peroffer_lastchanged"),
        table_name="peroffer",
        schema="mms",
    )
    op.drop_table("peroffer", schema="mms")
    op.drop_index(
        op.f("ix_mms_perdemand_lastchanged"),
        table_name="perdemand",
        schema="mms",
    )
    op.drop_table("perdemand", schema="mms")
    op.drop_index(
        op.f("ix_mms_pdpasa_regionsolution_lastchanged"),
        table_name="pdpasa_regionsolution",
        schema="mms",
    )
    op.drop_table("pdpasa_regionsolution", schema="mms")
    op.drop_index(
        op.f("ix_mms_pdpasa_casesolution_lastchanged"),
        table_name="pdpasa_casesolution",
        schema="mms",
    )
    op.drop_table("pdpasa_casesolution", schema="mms")
    op.drop_index(
        op.f("ix_mms_pasaregionsolution_lastchanged"),
        table_name="pasaregionsolution",
        schema="mms",
    )
    op.drop_table("pasaregionsolution", schema="mms")
    op.drop_index(
        op.f("ix_mms_pasainterconnectorsolution_lastchanged"),
        table_name="pasainterconnectorsolution",
        schema="mms",
    )
    op.drop_table("pasainterconnectorsolution", schema="mms")
    op.drop_index(
        op.f("ix_mms_pasaconstraintsolution_lastchanged"),
        table_name="pasaconstraintsolution",
        schema="mms",
    )
    op.drop_table("pasaconstraintsolution", schema="mms")
    op.drop_index(
        op.f("ix_mms_pasacasesolution_lastchanged"),
        table_name="pasacasesolution",
        schema="mms",
    )
    op.drop_table("pasacasesolution", schema="mms")
    op.drop_index(
        op.f("ix_mms_participantnoticetrk_participantid"),
        table_name="participantnoticetrk",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_participantnoticetrk_lastchanged"),
        table_name="participantnoticetrk",
        schema="mms",
    )
    op.drop_table("participantnoticetrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_participantcreditdetail_participantid"),
        table_name="participantcreditdetail",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_participantcreditdetail_lastchanged"),
        table_name="participantcreditdetail",
        schema="mms",
    )
    op.drop_table("participantcreditdetail", schema="mms")
    op.drop_index(
        op.f("ix_mms_participantclass_lastchanged"),
        table_name="participantclass",
        schema="mms",
    )
    op.drop_table("participantclass", schema="mms")
    op.drop_index(
        op.f("ix_mms_participantcategoryalloc_lastchanged"),
        table_name="participantcategoryalloc",
        schema="mms",
    )
    op.drop_table("participantcategoryalloc", schema="mms")
    op.drop_index(
        op.f("ix_mms_participantcategory_lastchanged"),
        table_name="participantcategory",
        schema="mms",
    )
    op.drop_table("participantcategory", schema="mms")
    op.drop_index(
        op.f("ix_mms_participantaccount_lastchanged"),
        table_name="participantaccount",
        schema="mms",
    )
    op.drop_table("participantaccount", schema="mms")
    op.drop_index(
        op.f("ix_mms_participant_bandfee_alloc_lastchanged"),
        table_name="participant_bandfee_alloc",
        schema="mms",
    )
    op.drop_table("participant_bandfee_alloc", schema="mms")
    op.drop_index(
        op.f("ix_mms_participant_lastchanged"),
        table_name="participant",
        schema="mms",
    )
    op.drop_table("participant", schema="mms")
    op.drop_index(
        op.f("ix_mms_p5min_unitsolution_lastchanged"),
        table_name="p5min_unitsolution",
        schema="mms",
    )
    op.drop_table("p5min_unitsolution", schema="mms")
    op.drop_index(
        op.f("ix_mms_p5min_regionsolution_lastchanged"),
        table_name="p5min_regionsolution",
        schema="mms",
    )
    op.drop_table("p5min_regionsolution", schema="mms")
    op.drop_table("p5min_local_price", schema="mms")
    op.drop_index(
        op.f("ix_mms_p5min_interconnectorsoln_lastchanged"),
        table_name="p5min_interconnectorsoln",
        schema="mms",
    )
    op.drop_table("p5min_interconnectorsoln", schema="mms")
    op.drop_index(
        op.f("ix_mms_p5min_constraintsolution_lastchanged"),
        table_name="p5min_constraintsolution",
        schema="mms",
    )
    op.drop_table("p5min_constraintsolution", schema="mms")
    op.drop_index(
        op.f("ix_mms_p5min_casesolution_lastchanged"),
        table_name="p5min_casesolution",
        schema="mms",
    )
    op.drop_table("p5min_casesolution", schema="mms")
    op.drop_table("p5min_blockedconstraint", schema="mms")
    op.drop_index(
        op.f("ix_mms_overriderrp_lastchanged"),
        table_name="overriderrp",
        schema="mms",
    )
    op.drop_table("overriderrp", schema="mms")
    op.drop_index(
        op.f("ix_mms_offerunloadingdata_lastchanged"),
        table_name="offerunloadingdata",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_offerunloadingdata_contractid"),
        table_name="offerunloadingdata",
        schema="mms",
    )
    op.drop_table("offerunloadingdata", schema="mms")
    op.drop_index(
        op.f("ix_mms_offeruloadingdata_lastchanged"),
        table_name="offeruloadingdata",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_offeruloadingdata_contractid"),
        table_name="offeruloadingdata",
        schema="mms",
    )
    op.drop_table("offeruloadingdata", schema="mms")
    op.drop_index(
        op.f("ix_mms_offerrpowerdata_lastchanged"),
        table_name="offerrpowerdata",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_offerrpowerdata_contractid"),
        table_name="offerrpowerdata",
        schema="mms",
    )
    op.drop_table("offerrpowerdata", schema="mms")
    op.drop_index(
        op.f("ix_mms_offerrestartdata_lastchanged"),
        table_name="offerrestartdata",
        schema="mms",
    )
    op.drop_table("offerrestartdata", schema="mms")
    op.drop_index(
        op.f("ix_mms_offerlsheddata_lastchanged"),
        table_name="offerlsheddata",
        schema="mms",
    )
    op.drop_table("offerlsheddata", schema="mms")
    op.drop_index(
        op.f("ix_mms_offergovdata_lastchanged"),
        table_name="offergovdata",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_offergovdata_contractid"),
        table_name="offergovdata",
        schema="mms",
    )
    op.drop_table("offergovdata", schema="mms")
    op.drop_index(
        op.f("ix_mms_offerfiletrk_participantid"),
        table_name="offerfiletrk",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_offerfiletrk_lastchanged"),
        table_name="offerfiletrk",
        schema="mms",
    )
    op.drop_table("offerfiletrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_offerastrk_lastchanged"),
        table_name="offerastrk",
        schema="mms",
    )
    op.drop_table("offerastrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_offeragcdata_lastchanged"),
        table_name="offeragcdata",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_offeragcdata_contractid"),
        table_name="offeragcdata",
        schema="mms",
    )
    op.drop_table("offeragcdata", schema="mms")
    op.drop_index(
        op.f("ix_mms_oartrack_participantid"),
        table_name="oartrack",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_oartrack_lastchanged"),
        table_name="oartrack",
        schema="mms",
    )
    op.drop_table("oartrack", schema="mms")
    op.drop_index(
        op.f("ix_mms_network_substationdetail_lastchanged"),
        table_name="network_substationdetail",
        schema="mms",
    )
    op.drop_table("network_substationdetail", schema="mms")
    op.drop_index(
        op.f("ix_mms_network_staticrating_lastchanged"),
        table_name="network_staticrating",
        schema="mms",
    )
    op.drop_table("network_staticrating", schema="mms")
    op.drop_table("network_realtimerating", schema="mms")
    op.drop_index(
        op.f("ix_mms_network_rating_lastchanged"),
        table_name="network_rating",
        schema="mms",
    )
    op.drop_table("network_rating", schema="mms")
    op.drop_table("network_outagestatuscode", schema="mms")
    op.drop_index(
        op.f("ix_mms_network_outagedetail_lastchanged"),
        table_name="network_outagedetail",
        schema="mms",
    )
    op.drop_table("network_outagedetail", schema="mms")
    op.drop_table("network_outageconstraintset", schema="mms")
    op.drop_index(
        op.f("ix_mms_network_equipmentdetail_lastchanged"),
        table_name="network_equipmentdetail",
        schema="mms",
    )
    op.drop_table("network_equipmentdetail", schema="mms")
    op.drop_table("negative_residue", schema="mms")
    op.drop_index(
        op.f("ix_mms_mtpasaregionsolution_d_lastchanged"),
        table_name="mtpasaregionsolution_d",
        schema="mms",
    )
    op.drop_table("mtpasaregionsolution_d", schema="mms")
    op.drop_index(
        op.f("ix_mms_mtpasainterconnectorsolution_d_lastchanged"),
        table_name="mtpasainterconnectorsolution_d",
        schema="mms",
    )
    op.drop_table("mtpasainterconnectorsolution_d", schema="mms")
    op.drop_index(
        op.f("ix_mms_mtpasaconstraintsolution_d_lastchanged"),
        table_name="mtpasaconstraintsolution_d",
        schema="mms",
    )
    op.drop_table("mtpasaconstraintsolution_d", schema="mms")
    op.drop_table("mtpasa_reservelimitsolution", schema="mms")
    op.drop_table("mtpasa_reservelimit_set", schema="mms")
    op.drop_table("mtpasa_reservelimit_region", schema="mms")
    op.drop_table("mtpasa_reservelimit", schema="mms")
    op.drop_table("mtpasa_regionsummary", schema="mms")
    op.drop_index(
        op.f("ix_mms_mtpasa_regionsolution_lastchanged"),
        table_name="mtpasa_regionsolution",
        schema="mms",
    )
    op.drop_table("mtpasa_regionsolution", schema="mms")
    op.drop_table("mtpasa_regionresult", schema="mms")
    op.drop_table("mtpasa_regioniteration", schema="mms")
    op.drop_table("mtpasa_regionavailability", schema="mms")
    op.drop_table("mtpasa_regionavail_trk", schema="mms")
    op.drop_table("mtpasa_offerfiletrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_mtpasa_offerdata_lastchanged"),
        table_name="mtpasa_offerdata",
        schema="mms",
    )
    op.drop_table("mtpasa_offerdata", schema="mms")
    op.drop_table("mtpasa_lolpresult", schema="mms")
    op.drop_table("mtpasa_intermittent_limit", schema="mms")
    op.drop_table("mtpasa_intermittent_avail", schema="mms")
    op.drop_index(
        op.f("ix_mms_mtpasa_interconnectorsolution_lastchanged"),
        table_name="mtpasa_interconnectorsolution",
        schema="mms",
    )
    op.drop_table("mtpasa_interconnectorsolution", schema="mms")
    op.drop_table("mtpasa_interconnectorresult", schema="mms")
    op.drop_table("mtpasa_constraintsummary", schema="mms")
    op.drop_index(
        op.f("ix_mms_mtpasa_constraintsolution_lastchanged"),
        table_name="mtpasa_constraintsolution",
        schema="mms",
    )
    op.drop_table("mtpasa_constraintsolution", schema="mms")
    op.drop_table("mtpasa_constraintresult", schema="mms")
    op.drop_index(
        op.f("ix_mms_mtpasa_casesolution_lastchanged"),
        table_name="mtpasa_casesolution",
        schema="mms",
    )
    op.drop_table("mtpasa_casesolution", schema="mms")
    op.drop_table("mtpasa_caseresult", schema="mms")
    op.drop_index(
        op.f("ix_mms_mtpasa_case_set_lastchanged"),
        table_name="mtpasa_case_set",
        schema="mms",
    )
    op.drop_table("mtpasa_case_set", schema="mms")
    op.drop_index(
        op.f("ix_mms_mr_peroffer_stack_lastchanged"),
        table_name="mr_peroffer_stack",
        schema="mms",
    )
    op.drop_table("mr_peroffer_stack", schema="mms")
    op.drop_index(
        op.f("ix_mms_mr_event_schedule_lastchanged"),
        table_name="mr_event_schedule",
        schema="mms",
    )
    op.drop_table("mr_event_schedule", schema="mms")
    op.drop_index(
        op.f("ix_mms_mr_event_lastchanged"),
        table_name="mr_event",
        schema="mms",
    )
    op.drop_table("mr_event", schema="mms")
    op.drop_index(
        op.f("ix_mms_mr_dayoffer_stack_lastchanged"),
        table_name="mr_dayoffer_stack",
        schema="mms",
    )
    op.drop_table("mr_dayoffer_stack", schema="mms")
    op.drop_index(
        op.f("ix_mms_mnsp_peroffer_lastchanged"),
        table_name="mnsp_peroffer",
        schema="mms",
    )
    op.drop_table("mnsp_peroffer", schema="mms")
    op.drop_index(
        op.f("ix_mms_mnsp_participant_lastchanged"),
        table_name="mnsp_participant",
        schema="mms",
    )
    op.drop_table("mnsp_participant", schema="mms")
    op.drop_index(
        op.f("ix_mms_mnsp_offertrk_lastchanged"),
        table_name="mnsp_offertrk",
        schema="mms",
    )
    op.drop_table("mnsp_offertrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_mnsp_interconnector_lastchanged"),
        table_name="mnsp_interconnector",
        schema="mms",
    )
    op.drop_table("mnsp_interconnector", schema="mms")
    op.drop_index(
        op.f("ix_mms_mnsp_filetrk_lastchanged"),
        table_name="mnsp_filetrk",
        schema="mms",
    )
    op.drop_table("mnsp_filetrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_mnsp_dayoffer_lastchanged"),
        table_name="mnsp_dayoffer",
        schema="mms",
    )
    op.drop_table("mnsp_dayoffer", schema="mms")
    op.drop_table("mms_data_model_audit", schema="mms")
    op.drop_index(
        op.f("ix_mms_meterdatatrk_lastchanged"),
        table_name="meterdatatrk",
        schema="mms",
    )
    op.drop_table("meterdatatrk", schema="mms")
    op.drop_table("meterdata_trk", schema="mms")
    op.drop_table("meterdata_interconnector", schema="mms")
    op.drop_table("meterdata_individual_reads", schema="mms")
    op.drop_index(
        op.f("ix_mms_meterdata_gen_duid_lastchanged"),
        table_name="meterdata_gen_duid",
        schema="mms",
    )
    op.drop_table("meterdata_gen_duid", schema="mms")
    op.drop_table("meterdata_aggregate_reads", schema="mms")
    op.drop_index(
        op.f("ix_mms_meterdata_lastchanged"),
        table_name="meterdata",
        schema="mms",
    )
    op.drop_table("meterdata", schema="mms")
    op.drop_table("mcc_constraintsolution", schema="mms")
    op.drop_table("mcc_casesolution", schema="mms")
    op.drop_index(
        op.f("ix_mms_mas_cp_master_lastchanged"),
        table_name="mas_cp_master",
        schema="mms",
    )
    op.drop_table("mas_cp_master", schema="mms")
    op.drop_index(
        op.f("ix_mms_mas_cp_change_lastchanged"),
        table_name="mas_cp_change",
        schema="mms",
    )
    op.drop_table("mas_cp_change", schema="mms")
    op.drop_index(
        op.f("ix_mms_marketsusregion_lastchanged"),
        table_name="marketsusregion",
        schema="mms",
    )
    op.drop_table("marketsusregion", schema="mms")
    op.drop_index(
        op.f("ix_mms_marketsuspension_lastchanged"),
        table_name="marketsuspension",
        schema="mms",
    )
    op.drop_table("marketsuspension", schema="mms")
    op.drop_index(
        op.f("ix_mms_marketnoticetype_lastchanged"),
        table_name="marketnoticetype",
        schema="mms",
    )
    op.drop_table("marketnoticetype", schema="mms")
    op.drop_index(
        op.f("ix_mms_marketnoticedata_lastchanged"),
        table_name="marketnoticedata",
        schema="mms",
    )
    op.drop_table("marketnoticedata", schema="mms")
    op.drop_index(
        op.f("ix_mms_marketfeetrk_lastchanged"),
        table_name="marketfeetrk",
        schema="mms",
    )
    op.drop_table("marketfeetrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_marketfeedata_lastchanged"),
        table_name="marketfeedata",
        schema="mms",
    )
    op.drop_table("marketfeedata", schema="mms")
    op.drop_index(
        op.f("ix_mms_marketfee_lastchanged"),
        table_name="marketfee",
        schema="mms",
    )
    op.drop_table("marketfee", schema="mms")
    op.drop_table("market_suspend_schedule_trk", schema="mms")
    op.drop_table("market_suspend_schedule", schema="mms")
    op.drop_table("market_suspend_region_sum", schema="mms")
    op.drop_table("market_suspend_regime_sum", schema="mms")
    op.drop_index(
        op.f("ix_mms_market_price_thresholds_lastchanged"),
        table_name="market_price_thresholds",
        schema="mms",
    )
    op.drop_table("market_price_thresholds", schema="mms")
    op.drop_index(
        op.f("ix_mms_market_fee_exclusiontrk_lastchanged"),
        table_name="market_fee_exclusiontrk",
        schema="mms",
    )
    op.drop_table("market_fee_exclusiontrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_market_fee_exclusion_lastchanged"),
        table_name="market_fee_exclusion",
        schema="mms",
    )
    op.drop_table("market_fee_exclusion", schema="mms")
    op.drop_table("market_fee_cat_excl_trk", schema="mms")
    op.drop_table("market_fee_cat_excl", schema="mms")
    op.drop_index(
        op.f("ix_mms_lossmodel_lastchanged"),
        table_name="lossmodel",
        schema="mms",
    )
    op.drop_table("lossmodel", schema="mms")
    op.drop_index(
        op.f("ix_mms_lossfactormodel_lastchanged"),
        table_name="lossfactormodel",
        schema="mms",
    )
    op.drop_table("lossfactormodel", schema="mms")
    op.drop_index(
        op.f("ix_mms_irfmevents_lastchanged"),
        table_name="irfmevents",
        schema="mms",
    )
    op.drop_table("irfmevents", schema="mms")
    op.drop_index(
        op.f("ix_mms_irfmamount_lastchanged"),
        table_name="irfmamount",
        schema="mms",
    )
    op.drop_table("irfmamount", schema="mms")
    op.drop_index(
        op.f("ix_mms_intraregionalloc_lastchanged"),
        table_name="intraregionalloc",
        schema="mms",
    )
    op.drop_table("intraregionalloc", schema="mms")
    op.drop_table("intermittent_p5_run", schema="mms")
    op.drop_table("intermittent_p5_pred", schema="mms")
    op.drop_table("intermittent_gen_limit_day", schema="mms")
    op.drop_table("intermittent_gen_limit", schema="mms")
    op.drop_table("intermittent_gen_fcst_data", schema="mms")
    op.drop_table("intermittent_gen_fcst", schema="mms")
    op.drop_table("intermittent_forecast_trk", schema="mms")
    op.drop_table("intermittent_ds_run", schema="mms")
    op.drop_table("intermittent_ds_pred", schema="mms")
    op.drop_table("intermittent_cluster_avail_day", schema="mms")
    op.drop_table("intermittent_cluster_avail", schema="mms")
    op.drop_index(
        op.f("ix_mms_interconnmwflow_lastchanged"),
        table_name="interconnmwflow",
        schema="mms",
    )
    op.drop_table("interconnmwflow", schema="mms")
    op.drop_index(
        op.f("ix_mms_interconnectorconstraint_lastchanged"),
        table_name="interconnectorconstraint",
        schema="mms",
    )
    op.drop_table("interconnectorconstraint", schema="mms")
    op.drop_index(
        op.f("ix_mms_interconnectoralloc_lastchanged"),
        table_name="interconnectoralloc",
        schema="mms",
    )
    op.drop_table("interconnectoralloc", schema="mms")
    op.drop_index(
        op.f("ix_mms_interconnector_lastchanged"),
        table_name="interconnector",
        schema="mms",
    )
    op.drop_table("interconnector", schema="mms")
    op.drop_index(
        op.f("ix_mms_intcontractamounttrk_lastchanged"),
        table_name="intcontractamounttrk",
        schema="mms",
    )
    op.drop_table("intcontractamounttrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_intcontractamount_lastchanged"),
        table_name="intcontractamount",
        schema="mms",
    )
    op.drop_table("intcontractamount", schema="mms")
    op.drop_index(
        op.f("ix_mms_intcontract_lastchanged"),
        table_name="intcontract",
        schema="mms",
    )
    op.drop_table("intcontract", schema="mms")
    op.drop_index(
        op.f("ix_mms_instructiontype_lastchanged"),
        table_name="instructiontype",
        schema="mms",
    )
    op.drop_table("instructiontype", schema="mms")
    op.drop_index(
        op.f("ix_mms_instructionsubtype_lastchanged"),
        table_name="instructionsubtype",
        schema="mms",
    )
    op.drop_table("instructionsubtype", schema="mms")
    op.drop_index(
        op.f("ix_mms_gst_transaction_type_lastchanged"),
        table_name="gst_transaction_type",
        schema="mms",
    )
    op.drop_table("gst_transaction_type", schema="mms")
    op.drop_index(
        op.f("ix_mms_gst_transaction_class_lastchanged"),
        table_name="gst_transaction_class",
        schema="mms",
    )
    op.drop_table("gst_transaction_class", schema="mms")
    op.drop_index(
        op.f("ix_mms_gst_rate_lastchanged"),
        table_name="gst_rate",
        schema="mms",
    )
    op.drop_table("gst_rate", schema="mms")
    op.drop_index(
        op.f("ix_mms_gst_bas_class_lastchanged"),
        table_name="gst_bas_class",
        schema="mms",
    )
    op.drop_table("gst_bas_class", schema="mms")
    op.drop_table("genunits_unit", schema="mms")
    op.drop_index(
        op.f("ix_mms_genunits_lastchanged"),
        table_name="genunits",
        schema="mms",
    )
    op.drop_table("genunits", schema="mms")
    op.drop_index(
        op.f("ix_mms_genunitmtrinperiod_stationid"),
        table_name="genunitmtrinperiod",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_genunitmtrinperiod_lastchanged"),
        table_name="genunitmtrinperiod",
        schema="mms",
    )
    op.drop_table("genunitmtrinperiod", schema="mms")
    op.drop_index(op.f("ix_mms_genmeter_stationid"), table_name="genmeter", schema="mms")
    op.drop_index(
        op.f("ix_mms_genmeter_lastchanged"),
        table_name="genmeter",
        schema="mms",
    )
    op.drop_table("genmeter", schema="mms")
    op.drop_index(
        op.f("ix_mms_genericequationrhs_lastchanged"),
        table_name="genericequationrhs",
        schema="mms",
    )
    op.drop_table("genericequationrhs", schema="mms")
    op.drop_index(
        op.f("ix_mms_genericequationdesc_lastchanged"),
        table_name="genericequationdesc",
        schema="mms",
    )
    op.drop_table("genericequationdesc", schema="mms")
    op.drop_index(
        op.f("ix_mms_genericconstraintrhs_lastchanged"),
        table_name="genericconstraintrhs",
        schema="mms",
    )
    op.drop_table("genericconstraintrhs", schema="mms")
    op.drop_index(
        op.f("ix_mms_genconsettrk_lastchanged"),
        table_name="genconsettrk",
        schema="mms",
    )
    op.drop_table("genconsettrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_genconsetinvoke_lastchanged"),
        table_name="genconsetinvoke",
        schema="mms",
    )
    op.drop_table("genconsetinvoke", schema="mms")
    op.drop_index(
        op.f("ix_mms_genconset_lastchanged"),
        table_name="genconset",
        schema="mms",
    )
    op.drop_table("genconset", schema="mms")
    op.drop_index(
        op.f("ix_mms_gencondata_lastchanged"),
        table_name="gencondata",
        schema="mms",
    )
    op.drop_table("gencondata", schema="mms")
    op.drop_index(
        op.f("ix_mms_gdinstruct_targettime"),
        table_name="gdinstruct",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_gdinstruct_lastchanged"),
        table_name="gdinstruct",
        schema="mms",
    )
    op.drop_index(op.f("ix_mms_gdinstruct_duid"), table_name="gdinstruct", schema="mms")
    op.drop_table("gdinstruct", schema="mms")
    op.drop_index(
        op.f("ix_mms_forcemajeureregion_lastchanged"),
        table_name="forcemajeureregion",
        schema="mms",
    )
    op.drop_table("forcemajeureregion", schema="mms")
    op.drop_index(
        op.f("ix_mms_forcemajeure_lastchanged"),
        table_name="forcemajeure",
        schema="mms",
    )
    op.drop_table("forcemajeure", schema="mms")
    op.drop_index(
        op.f("ix_mms_emsmaster_lastchanged"),
        table_name="emsmaster",
        schema="mms",
    )
    op.drop_table("emsmaster", schema="mms")
    op.drop_index(
        op.f("ix_mms_dudetailsummary_lastchanged"),
        table_name="dudetailsummary",
        schema="mms",
    )
    op.drop_table("dudetailsummary", schema="mms")
    op.drop_index(
        op.f("ix_mms_dudetail_lastchanged"),
        table_name="dudetail",
        schema="mms",
    )
    op.drop_table("dudetail", schema="mms")
    op.drop_index(op.f("ix_mms_dualloc_lastchanged"), table_name="dualloc", schema="mms")
    op.drop_index(op.f("ix_mms_dualloc_duid"), table_name="dualloc", schema="mms")
    op.drop_table("dualloc", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatchtrk_lastchanged"),
        table_name="dispatchtrk",
        schema="mms",
    )
    op.drop_table("dispatchtrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatchregionsum_lastchanged"),
        table_name="dispatchregionsum",
        schema="mms",
    )
    op.drop_table("dispatchregionsum", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatchprice_lastchanged"),
        table_name="dispatchprice",
        schema="mms",
    )
    op.drop_table("dispatchprice", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatchoffertrk_lastchanged"),
        table_name="dispatchoffertrk",
        schema="mms",
    )
    op.drop_index("dispatchoffertrk_ndx2", table_name="dispatchoffertrk", schema="mms")
    op.drop_table("dispatchoffertrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatchload_bnc_lastchanged"),
        table_name="dispatchload_bnc",
        schema="mms",
    )
    op.drop_index("dispatchload_bnc_ndx2", table_name="dispatchload_bnc", schema="mms")
    op.drop_table("dispatchload_bnc", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatchload_lastchanged"),
        table_name="dispatchload",
        schema="mms",
    )
    op.drop_index("dispatchload_ndx2", table_name="dispatchload", schema="mms")
    op.drop_table("dispatchload", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatchinterconnectorres_lastchanged"),
        table_name="dispatchinterconnectorres",
        schema="mms",
    )
    op.drop_table("dispatchinterconnectorres", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatchconstraint_settlementdate"),
        table_name="dispatchconstraint",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_dispatchconstraint_lastchanged"),
        table_name="dispatchconstraint",
        schema="mms",
    )
    op.drop_table("dispatchconstraint", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatchcasesolution_bnc_lastchanged"),
        table_name="dispatchcasesolution_bnc",
        schema="mms",
    )
    op.drop_table("dispatchcasesolution_bnc", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatchcasesolution_lastchanged"),
        table_name="dispatchcasesolution",
        schema="mms",
    )
    op.drop_table("dispatchcasesolution", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatchcase_ocd_lastchanged"),
        table_name="dispatchcase_ocd",
        schema="mms",
    )
    op.drop_table("dispatchcase_ocd", schema="mms")
    op.drop_table("dispatchblockedconstraint", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatchbidtrk_lastchanged"),
        table_name="dispatchbidtrk",
        schema="mms",
    )
    op.drop_index("dispatchbidtrk_ndx2", table_name="dispatchbidtrk", schema="mms")
    op.drop_table("dispatchbidtrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatchableunit_lastchanged"),
        table_name="dispatchableunit",
        schema="mms",
    )
    op.drop_table("dispatchableunit", schema="mms")
    op.drop_table("dispatch_unit_scada", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatch_unit_conformance_lastchanged"),
        table_name="dispatch_unit_conformance",
        schema="mms",
    )
    op.drop_table("dispatch_unit_conformance", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatch_price_revision_lastchanged"),
        table_name="dispatch_price_revision",
        schema="mms",
    )
    op.drop_table("dispatch_price_revision", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatch_mr_schedule_trk_lastchanged"),
        table_name="dispatch_mr_schedule_trk",
        schema="mms",
    )
    op.drop_table("dispatch_mr_schedule_trk", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatch_mnspbidtrk_lastchanged"),
        table_name="dispatch_mnspbidtrk",
        schema="mms",
    )
    op.drop_table("dispatch_mnspbidtrk", schema="mms")
    op.drop_table("dispatch_local_price", schema="mms")
    op.drop_table("dispatch_interconnection", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatch_fcas_req_lastchanged"),
        table_name="dispatch_fcas_req",
        schema="mms",
    )
    op.drop_table("dispatch_fcas_req", schema="mms")
    op.drop_index(
        op.f("ix_mms_dispatch_constraint_fcas_ocd_lastchanged"),
        table_name="dispatch_constraint_fcas_ocd",
        schema="mms",
    )
    op.drop_table("dispatch_constraint_fcas_ocd", schema="mms")
    op.drop_table("demandoperationalforecast", schema="mms")
    op.drop_table("demandoperationalactual", schema="mms")
    op.drop_index(op.f("ix_mms_deltamw_lastchanged"), table_name="deltamw", schema="mms")
    op.drop_table("deltamw", schema="mms")
    op.drop_index(
        op.f("ix_mms_defaultperoffer_lastchanged"),
        table_name="defaultperoffer",
        schema="mms",
    )
    op.drop_table("defaultperoffer", schema="mms")
    op.drop_index(
        op.f("ix_mms_defaultoffertrk_lastchanged"),
        table_name="defaultoffertrk",
        schema="mms",
    )
    op.drop_table("defaultoffertrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_defaultdayoffer_lastchanged"),
        table_name="defaultdayoffer",
        schema="mms",
    )
    op.drop_table("defaultdayoffer", schema="mms")
    op.drop_index(
        op.f("ix_mms_daytrack_lastchanged"),
        table_name="daytrack",
        schema="mms",
    )
    op.drop_table("daytrack", schema="mms")
    op.drop_index(
        op.f("ix_mms_dayoffer_d_lastchanged"),
        table_name="dayoffer_d",
        schema="mms",
    )
    op.drop_index("dayoffer_d_ndx2", table_name="dayoffer_d", schema="mms")
    op.drop_table("dayoffer_d", schema="mms")
    op.drop_index(
        op.f("ix_mms_dayoffer_lastchanged"),
        table_name="dayoffer",
        schema="mms",
    )
    op.drop_index("dayoffer_ndx2", table_name="dayoffer", schema="mms")
    op.drop_table("dayoffer", schema="mms")
    op.drop_index(
        op.f("ix_mms_contractunitunloading_participantid"),
        table_name="contractunitunloading",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_contractunitunloading_lastchanged"),
        table_name="contractunitunloading",
        schema="mms",
    )
    op.drop_table("contractunitunloading", schema="mms")
    op.drop_index(
        op.f("ix_mms_contractunitloading_participantid"),
        table_name="contractunitloading",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_contractunitloading_lastchanged"),
        table_name="contractunitloading",
        schema="mms",
    )
    op.drop_table("contractunitloading", schema="mms")
    op.drop_index(
        op.f("ix_mms_contractrestartunits_lastchanged"),
        table_name="contractrestartunits",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_contractrestartunits_contractid"),
        table_name="contractrestartunits",
        schema="mms",
    )
    op.drop_table("contractrestartunits", schema="mms")
    op.drop_index(
        op.f("ix_mms_contractrestartservices_participantid"),
        table_name="contractrestartservices",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_contractrestartservices_lastchanged"),
        table_name="contractrestartservices",
        schema="mms",
    )
    op.drop_table("contractrestartservices", schema="mms")
    op.drop_index(
        op.f("ix_mms_contractreservetrader_lastchanged"),
        table_name="contractreservetrader",
        schema="mms",
    )
    op.drop_table("contractreservetrader", schema="mms")
    op.drop_index(
        op.f("ix_mms_contractreservethreshold_lastchanged"),
        table_name="contractreservethreshold",
        schema="mms",
    )
    op.drop_table("contractreservethreshold", schema="mms")
    op.drop_index(
        op.f("ix_mms_contractreserveflag_lastchanged"),
        table_name="contractreserveflag",
        schema="mms",
    )
    op.drop_table("contractreserveflag", schema="mms")
    op.drop_index(
        op.f("ix_mms_contractreactivepower_participantid"),
        table_name="contractreactivepower",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_contractreactivepower_lastchanged"),
        table_name="contractreactivepower",
        schema="mms",
    )
    op.drop_table("contractreactivepower", schema="mms")
    op.drop_index(
        op.f("ix_mms_contractloadshed_participantid"),
        table_name="contractloadshed",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_contractloadshed_lastchanged"),
        table_name="contractloadshed",
        schema="mms",
    )
    op.drop_table("contractloadshed", schema="mms")
    op.drop_index(
        op.f("ix_mms_contractgovernor_participantid"),
        table_name="contractgovernor",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_contractgovernor_lastchanged"),
        table_name="contractgovernor",
        schema="mms",
    )
    op.drop_table("contractgovernor", schema="mms")
    op.drop_index(
        op.f("ix_mms_contractagc_lastchanged"),
        table_name="contractagc",
        schema="mms",
    )
    op.drop_index("contractagc_ndx2", table_name="contractagc", schema="mms")
    op.drop_table("contractagc", schema="mms")
    op.drop_index(
        op.f("ix_mms_constraintrelaxation_ocd_lastchanged"),
        table_name="constraintrelaxation_ocd",
        schema="mms",
    )
    op.drop_table("constraintrelaxation_ocd", schema="mms")
    op.drop_index(
        op.f("ix_mms_connectionpointoperatingsta_lastchanged"),
        table_name="connectionpointoperatingsta",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_connectionpointoperatingsta_connectionpointid"),
        table_name="connectionpointoperatingsta",
        schema="mms",
    )
    op.drop_table("connectionpointoperatingsta", schema="mms")
    op.drop_index(
        op.f("ix_mms_connectionpointdetails_lastchanged"),
        table_name="connectionpointdetails",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_connectionpointdetails_connectionpointid"),
        table_name="connectionpointdetails",
        schema="mms",
    )
    op.drop_index(
        "connectionpointdetai_ndx2",
        table_name="connectionpointdetails",
        schema="mms",
    )
    op.drop_table("connectionpointdetails", schema="mms")
    op.drop_index(
        op.f("ix_mms_connectionpoint_lastchanged"),
        table_name="connectionpoint",
        schema="mms",
    )
    op.drop_table("connectionpoint", schema="mms")
    op.drop_index(
        op.f("ix_mms_billwhitehole_lastchanged"),
        table_name="billwhitehole",
        schema="mms",
    )
    op.drop_table("billwhitehole", schema="mms")
    op.drop_index(
        op.f("ix_mms_billsmelterrate_lastchanged"),
        table_name="billsmelterrate",
        schema="mms",
    )
    op.drop_table("billsmelterrate", schema="mms")
    op.drop_index(
        op.f("ix_mms_billinterventionregionrecovery_lastchanged"),
        table_name="billinterventionregionrecovery",
        schema="mms",
    )
    op.drop_table("billinterventionregionrecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_billinterventionrecovery_lastchanged"),
        table_name="billinterventionrecovery",
        schema="mms",
    )
    op.drop_table("billinterventionrecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingsmelterreduction_participantid"),
        table_name="billingsmelterreduction",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_billingsmelterreduction_lastchanged"),
        table_name="billingsmelterreduction",
        schema="mms",
    )
    op.drop_table("billingsmelterreduction", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingruntrk_lastchanged"),
        table_name="billingruntrk",
        schema="mms",
    )
    op.drop_table("billingruntrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingreservetraderregion_lastchanged"),
        table_name="billingreservetraderregion",
        schema="mms",
    )
    op.drop_table("billingreservetraderregion", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingreservetrader_lastchanged"),
        table_name="billingreservetrader",
        schema="mms",
    )
    op.drop_table("billingreservetrader", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingreserveregionrecovery_lastchanged"),
        table_name="billingreserveregionrecovery",
        schema="mms",
    )
    op.drop_table("billingreserveregionrecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingreserverecovery_lastchanged"),
        table_name="billingreserverecovery",
        schema="mms",
    )
    op.drop_table("billingreserverecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingregionimports_lastchanged"),
        table_name="billingregionimports",
        schema="mms",
    )
    op.drop_table("billingregionimports", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingregionfigures_lastchanged"),
        table_name="billingregionfigures",
        schema="mms",
    )
    op.drop_table("billingregionfigures", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingregionexports_lastchanged"),
        table_name="billingregionexports",
        schema="mms",
    )
    op.drop_table("billingregionexports", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingrealloc_detail_lastchanged"),
        table_name="billingrealloc_detail",
        schema="mms",
    )
    op.drop_table("billingrealloc_detail", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingrealloc_participantid"),
        table_name="billingrealloc",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_billingrealloc_lastchanged"),
        table_name="billingrealloc",
        schema="mms",
    )
    op.drop_table("billingrealloc", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingprioradjustments_lastchanged"),
        table_name="billingprioradjustments",
        schema="mms",
    )
    op.drop_index(
        "billingprioradjustments_ndx2",
        table_name="billingprioradjustments",
        schema="mms",
    )
    op.drop_table("billingprioradjustments", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingirpartsurplussum_lastchanged"),
        table_name="billingirpartsurplussum",
        schema="mms",
    )
    op.drop_index(
        "billingirpartsurplussum_i01",
        table_name="billingirpartsurplussum",
        schema="mms",
    )
    op.drop_table("billingirpartsurplussum", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingirpartsurplus_lastchanged"),
        table_name="billingirpartsurplus",
        schema="mms",
    )
    op.drop_table("billingirpartsurplus", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingirnspsurplussum_lastchanged"),
        table_name="billingirnspsurplussum",
        schema="mms",
    )
    op.drop_table("billingirnspsurplussum", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingirnspsurplus_lastchanged"),
        table_name="billingirnspsurplus",
        schema="mms",
    )
    op.drop_table("billingirnspsurplus", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingirfm_lastchanged"),
        table_name="billingirfm",
        schema="mms",
    )
    op.drop_table("billingirfm", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingiraucsurplussum_lastchanged"),
        table_name="billingiraucsurplussum",
        schema="mms",
    )
    op.drop_table("billingiraucsurplussum", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingiraucsurplus_lastchanged"),
        table_name="billingiraucsurplus",
        schema="mms",
    )
    op.drop_table("billingiraucsurplus", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingintraresidues_lastchanged"),
        table_name="billingintraresidues",
        schema="mms",
    )
    op.drop_table("billingintraresidues", schema="mms")
    op.drop_index(
        op.f("ix_mms_billinginterventionregion_lastchanged"),
        table_name="billinginterventionregion",
        schema="mms",
    )
    op.drop_table("billinginterventionregion", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingintervention_lastchanged"),
        table_name="billingintervention",
        schema="mms",
    )
    op.drop_table("billingintervention", schema="mms")
    op.drop_index(
        op.f("ix_mms_billinginterresidues_lastchanged"),
        table_name="billinginterresidues",
        schema="mms",
    )
    op.drop_table("billinginterresidues", schema="mms")
    op.drop_index(
        op.f("ix_mms_billinggendata_participantid"),
        table_name="billinggendata",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_billinggendata_lastchanged"),
        table_name="billinggendata",
        schema="mms",
    )
    op.drop_table("billinggendata", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingfinancialadjustments_lastchanged"),
        table_name="billingfinancialadjustments",
        schema="mms",
    )
    op.drop_table("billingfinancialadjustments", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingfees_participantid"),
        table_name="billingfees",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_billingfees_lastchanged"),
        table_name="billingfees",
        schema="mms",
    )
    op.drop_table("billingfees", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingexcessgen_participantid"),
        table_name="billingexcessgen",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_billingexcessgen_lastchanged"),
        table_name="billingexcessgen",
        schema="mms",
    )
    op.drop_table("billingexcessgen", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingdaytrk_lastchanged"),
        table_name="billingdaytrk",
        schema="mms",
    )
    op.drop_table("billingdaytrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingcustexcessgen_lastchanged"),
        table_name="billingcustexcessgen",
        schema="mms",
    )
    op.drop_table("billingcustexcessgen", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingcpsum_participantid"),
        table_name="billingcpsum",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_billingcpsum_lastchanged"),
        table_name="billingcpsum",
        schema="mms",
    )
    op.drop_table("billingcpsum", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingcpdata_participantid"),
        table_name="billingcpdata",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_billingcpdata_lastchanged"),
        table_name="billingcpdata",
        schema="mms",
    )
    op.drop_table("billingcpdata", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingcalendar_lastchanged"),
        table_name="billingcalendar",
        schema="mms",
    )
    op.drop_table("billingcalendar", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingasrecovery_lastchanged"),
        table_name="billingasrecovery",
        schema="mms",
    )
    op.drop_table("billingasrecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingaspayments_lastchanged"),
        table_name="billingaspayments",
        schema="mms",
    )
    op.drop_table("billingaspayments", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingapcrecovery_lastchanged"),
        table_name="billingapcrecovery",
        schema="mms",
    )
    op.drop_table("billingapcrecovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_billingapccompensation_lastchanged"),
        table_name="billingapccompensation",
        schema="mms",
    )
    op.drop_table("billingapccompensation", schema="mms")
    op.drop_table("billing_secdeposit_application", schema="mms")
    op.drop_table("billing_secdep_interest_rate", schema="mms")
    op.drop_table("billing_secdep_interest_pay", schema="mms")
    op.drop_table("billing_res_trader_recovery", schema="mms")
    op.drop_table("billing_res_trader_payment", schema="mms")
    op.drop_table("billing_nmas_tst_recvry_trk", schema="mms")
    op.drop_index(
        op.f("ix_mms_billing_nmas_tst_recvry_rbf_lastchanged"),
        table_name="billing_nmas_tst_recvry_rbf",
        schema="mms",
    )
    op.drop_table("billing_nmas_tst_recvry_rbf", schema="mms")
    op.drop_index(
        op.f("ix_mms_billing_nmas_tst_recovery_lastchanged"),
        table_name="billing_nmas_tst_recovery",
        schema="mms",
    )
    op.drop_table("billing_nmas_tst_recovery", schema="mms")
    op.drop_table("billing_nmas_tst_payments", schema="mms")
    op.drop_index(
        op.f("ix_mms_billing_mr_summary_lastchanged"),
        table_name="billing_mr_summary",
        schema="mms",
    )
    op.drop_table("billing_mr_summary", schema="mms")
    op.drop_index(
        op.f("ix_mms_billing_mr_shortfall_lastchanged"),
        table_name="billing_mr_shortfall",
        schema="mms",
    )
    op.drop_table("billing_mr_shortfall", schema="mms")
    op.drop_index(
        op.f("ix_mms_billing_mr_recovery_lastchanged"),
        table_name="billing_mr_recovery",
        schema="mms",
    )
    op.drop_table("billing_mr_recovery", schema="mms")
    op.drop_index(
        op.f("ix_mms_billing_mr_payment_lastchanged"),
        table_name="billing_mr_payment",
        schema="mms",
    )
    op.drop_table("billing_mr_payment", schema="mms")
    op.drop_index(
        op.f("ix_mms_billing_gst_summary_lastchanged"),
        table_name="billing_gst_summary",
        schema="mms",
    )
    op.drop_table("billing_gst_summary", schema="mms")
    op.drop_index(
        op.f("ix_mms_billing_gst_detail_lastchanged"),
        table_name="billing_gst_detail",
        schema="mms",
    )
    op.drop_table("billing_gst_detail", schema="mms")
    op.drop_table("billing_eftshortfall_detail", schema="mms")
    op.drop_table("billing_eftshortfall_amount", schema="mms")
    op.drop_index(
        op.f("ix_mms_billing_direction_reconciliatn_lastchanged"),
        table_name="billing_direction_reconciliatn",
        schema="mms",
    )
    op.drop_table("billing_direction_reconciliatn", schema="mms")
    op.drop_table("billing_direction_recon_other", schema="mms")
    op.drop_table("billing_daily_energy_summary", schema="mms")
    op.drop_index(
        op.f("ix_mms_billing_csp_derogation_amount_lastchanged"),
        table_name="billing_csp_derogation_amount",
        schema="mms",
    )
    op.drop_table("billing_csp_derogation_amount", schema="mms")
    op.drop_table("billing_co2e_publication_trk", schema="mms")
    op.drop_table("billing_co2e_publication", schema="mms")
    op.drop_table("billing_apc_recovery", schema="mms")
    op.drop_table("billing_apc_compensation", schema="mms")
    op.drop_index(
        op.f("ix_mms_billadjustments_participantid"),
        table_name="billadjustments",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_billadjustments_lastchanged"),
        table_name="billadjustments",
        schema="mms",
    )
    op.drop_table("billadjustments", schema="mms")
    op.drop_index(
        op.f("ix_mms_bidtypestrk_lastchanged"),
        table_name="bidtypestrk",
        schema="mms",
    )
    op.drop_table("bidtypestrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_bidtypes_lastchanged"),
        table_name="bidtypes",
        schema="mms",
    )
    op.drop_table("bidtypes", schema="mms")
    op.drop_index(
        op.f("ix_mms_bidperoffer_d_lastchanged"),
        table_name="bidperoffer_d",
        schema="mms",
    )
    op.drop_table("bidperoffer_d", schema="mms")
    op.drop_index(
        op.f("ix_mms_bidperoffer_lastchanged"),
        table_name="bidperoffer",
        schema="mms",
    )
    op.drop_table("bidperoffer", schema="mms")
    op.drop_index(
        op.f("ix_mms_bidofferfiletrk_lastchanged"),
        table_name="bidofferfiletrk",
        schema="mms",
    )
    op.drop_table("bidofferfiletrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_bidduiddetailstrk_lastchanged"),
        table_name="bidduiddetailstrk",
        schema="mms",
    )
    op.drop_table("bidduiddetailstrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_bidduiddetails_lastchanged"),
        table_name="bidduiddetails",
        schema="mms",
    )
    op.drop_table("bidduiddetails", schema="mms")
    op.drop_index(
        op.f("ix_mms_biddayoffer_d_participantid"),
        table_name="biddayoffer_d",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_biddayoffer_d_lastchanged"),
        table_name="biddayoffer_d",
        schema="mms",
    )
    op.drop_table("biddayoffer_d", schema="mms")
    op.drop_index(
        op.f("ix_mms_biddayoffer_participantid"),
        table_name="biddayoffer",
        schema="mms",
    )
    op.drop_index(
        op.f("ix_mms_biddayoffer_lastchanged"),
        table_name="biddayoffer",
        schema="mms",
    )
    op.drop_table("biddayoffer", schema="mms")
    op.drop_index(
        op.f("ix_mms_auction_tranche_lastchanged"),
        table_name="auction_tranche",
        schema="mms",
    )
    op.drop_table("auction_tranche", schema="mms")
    op.drop_index(
        op.f("ix_mms_auction_rp_estimate_lastchanged"),
        table_name="auction_rp_estimate",
        schema="mms",
    )
    op.drop_table("auction_rp_estimate", schema="mms")
    op.drop_index(
        op.f("ix_mms_auction_revenue_track_lastchanged"),
        table_name="auction_revenue_track",
        schema="mms",
    )
    op.drop_table("auction_revenue_track", schema="mms")
    op.drop_index(
        op.f("ix_mms_auction_revenue_estimate_lastchanged"),
        table_name="auction_revenue_estimate",
        schema="mms",
    )
    op.drop_table("auction_revenue_estimate", schema="mms")
    op.drop_index(
        op.f("ix_mms_auction_ic_allocations_lastchanged"),
        table_name="auction_ic_allocations",
        schema="mms",
    )
    op.drop_table("auction_ic_allocations", schema="mms")
    op.drop_index(
        op.f("ix_mms_auction_calendar_lastchanged"),
        table_name="auction_calendar",
        schema="mms",
    )
    op.drop_table("auction_calendar", schema="mms")
    op.drop_index(op.f("ix_mms_auction_lastchanged"), table_name="auction", schema="mms")
    op.drop_table("auction", schema="mms")
    op.drop_index(
        op.f("ix_mms_apeventregion_lastchanged"),
        table_name="apeventregion",
        schema="mms",
    )
    op.drop_table("apeventregion", schema="mms")
    op.drop_index(op.f("ix_mms_apevent_lastchanged"), table_name="apevent", schema="mms")
    op.drop_table("apevent", schema="mms")
    op.drop_index(
        op.f("ix_mms_apccompamounttrk_lastchanged"),
        table_name="apccompamounttrk",
        schema="mms",
    )
    op.drop_table("apccompamounttrk", schema="mms")
    op.drop_index(
        op.f("ix_mms_apccompamount_lastchanged"),
        table_name="apccompamount",
        schema="mms",
    )
    op.drop_table("apccompamount", schema="mms")
    op.drop_index(op.f("ix_mms_apccomp_lastchanged"), table_name="apccomp", schema="mms")
    op.drop_table("apccomp", schema="mms")
    op.drop_index(
        op.f("ix_mms_ancillary_recovery_split_lastchanged"),
        table_name="ancillary_recovery_split",
        schema="mms",
    )
    op.drop_table("ancillary_recovery_split", schema="mms")
    # ### end Alembic commands ###
