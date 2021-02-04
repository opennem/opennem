"""
Queries to drop views and create primary key indexes

"""

from textwrap import dedent
from typing import Optional

from opennem.db.views.utils import get_index_name

from .schema import ViewDefinition


def query_materialized(viewdef: ViewDefinition) -> str:
    return "materialized" if viewdef.materialized else ""


def get_query_drop_view(viewdef: ViewDefinition) -> Optional[str]:

    __query = "drop {materialized} view if exists {view_name} cascade;"

    query = __query.format(
        view_name=viewdef.name,
        materialized=query_materialized(viewdef),
    )

    return dedent(query)


def get_view_unique_index_query(viewdef: ViewDefinition) -> Optional[str]:

    if not viewdef.primary_key:
        return None

    __query = "CREATE UNIQUE INDEX IF NOT EXISTS {index_name} ON {view_name} ({index_keys});"

    index_keys = ", ".join(viewdef.primary_key)

    query = __query.format(
        index_name=get_index_name(viewdef.name, unique=True),
        view_name=viewdef.name,
        index_keys=index_keys,
    )

    return dedent(query)


def get_all_views_query() -> str:
    """ doc """
    # There is a better way to do this to get out deps
    return "select table_name from INFORMATION_SCHEMA.views where table_schema='public';"


def get_all_views_deps() -> str:
    """ doc """

    query = """
    with view_oids as (
        select
            distinct(dependent_view.oid) as view_oid

        from pg_depend
        JOIN pg_rewrite ON pg_depend.objid = pg_rewrite.oid
        JOIN pg_class as dependent_view ON pg_rewrite.ev_class = dependent_view.oid
        JOIN pg_namespace dependent_ns ON dependent_ns.oid = dependent_view.relnamespace
        WHERE
        dependent_ns.nspname = 'public'
    ), view_dependencies as (
        select
            dependent_view.oid as dependent_oid,
            dependent_ns.nspname as dependent_schema,
            dependent_view.relname as dependent_view,
            source_table.oid as dependency_oid,
            source_ns.nspname as source_schema,
            source_table.relname as source_view
        from pg_depend
        JOIN pg_rewrite ON pg_depend.objid = pg_rewrite.oid
        JOIN pg_class as dependent_view ON pg_rewrite.ev_class = dependent_view.oid
        JOIN pg_class as source_table ON pg_depend.refobjid = source_table.oid
        JOIN view_oids on source_table.oid = view_oids.view_oid
        JOIN pg_namespace dependent_ns ON dependent_ns.oid = dependent_view.relnamespace
        JOIN pg_namespace source_ns ON source_ns.oid = source_table.relnamespace
        WHERE
            source_ns.nspname = 'public'
        group by
            dependent_view.oid,
            dependent_ns.nspname,
            dependent_view.relname,
            source_table.oid,
            source_ns.nspname,
            source_table.relname
    )
    select
        view_dependencies.*
    from view_dependencies
    ;
    """

    return dedent(query)
