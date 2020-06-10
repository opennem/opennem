"""
    OpenNEM primary schema adapted to support multiple energy sources

    Currently supported:

    - NEM
    - WEM
"""

from sqlalchemy import (
    NUMERIC,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Sequence,
    String,
    Table,
    Text,
    Time,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()
metadata = Base.metadata


class NemModel(object):
    """
        Base model for both NEM and WEM

        Each table has an overrid for update and additional meta fields

        @TODO - upsert support for postgresql and mysql dialects (see db/__init__)
    """

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key == "id" or key.endswith("_id"):
                continue

            # @TODO watch how we do updates so we don't overwrite data
            cur_val = getattr(self, key)
            if key not in [None, ""]:
                setattr(self, key, value)

    def __compile_query(self, query):
        """Via http://nicolascadou.com/blog/2014/01/printing-actual-sqlalchemy-queries"""
        compiler = (
            query.compile
            if not hasattr(query, "statement")
            else query.statement.compile
        )
        return compiler(dialect=postgresql.dialect())

    def __upsert(
        self,
        session,
        model,
        rows,
        as_of_date_col="report_date",
        no_update_cols=[],
    ):
        table = model.__table__

        stmt = self.insert(table).values(rows)

        update_cols = [
            c.name
            for c in table.c
            if c not in list(table.primary_key.columns)
            and c.name not in no_update_cols
        ]

        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=table.primary_key.columns,
            set_={k: getattr(stmt.excluded, k) for k in update_cols},
            index_where=(model.report_date < stmt.excluded.report_date),
        )

        print(self.compile_query(on_conflict_stmt))
        session.execute(on_conflict_stmt)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class NemDispatchUnitScada(Base, NemModel):
    __tablename__ = "nem_dispatch_unit_scada"
    __table_args__ = (
        Index(
            "nem_dispatch_unit_scada_uniq",
            "SETTLEMENTDATE",
            "DUID",
            unique=True,
        ),
    )

    id = Column(Integer, primary_key=True)
    SETTLEMENTDATE = Column(DateTime, index=True)
    DUID = Column(Text, index=True,)
    SCADAVALUE = Column(NUMERIC(10, 6))
