"""
Memgraph database connection utilities.

Provides connection management for Memgraph graph database. Each
``MemgraphConnection`` owns its own socket; the previous module-level
singleton was removed because it leaked across threads / event loops and
hid connection lifetime. Callers should either construct their own
instance or use :func:`get_memgraph_connection`, which returns a fresh
instance pre-configured from ``opennem.settings``.
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from mgclient import connect

from opennem import settings

logger = logging.getLogger("opennem.db.memgraph")


class MemgraphConnection:
    """Manages a single connection to Memgraph database."""

    def __init__(self, host: str | None = None, port: int | None = None):
        self.host = host if host is not None else settings.memgraph_host
        self.port = port if port is not None else settings.memgraph_port
        # mgclient is untyped; treat the connection handle as opaque.
        self._connection: Any = None

    def connect(self):
        """Establish connection to Memgraph."""
        try:
            self._connection = connect(host=self.host, port=self.port)
            logger.info(f"Connected to Memgraph at {self.host}:{self.port}")
            return self._connection
        except Exception as e:
            logger.error(f"Failed to connect to Memgraph: {e}")
            raise

    def close(self):
        """Close the Memgraph connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Closed Memgraph connection")

    @property
    def connection(self):
        """Get or create connection."""
        if not self._connection:
            self.connect()
        return self._connection

    def execute(self, query: str, params: dict | None = None):
        """Execute a query and return results."""
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()

    def execute_and_commit(self, query: str, params: dict | None = None):
        """Execute a query and commit the transaction."""
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor.fetchall()
        finally:
            cursor.close()

    @contextmanager
    def transaction(self) -> Iterator["MemgraphConnection"]:
        """
        Run a series of statements atomically.

        Yields the connection so callers can issue multiple ``execute(...)``
        calls; on exit the underlying transaction is committed, or rolled
        back if the block raises. Use this for any DELETE-then-CREATE
        sequence so the graph is never observably empty mid-build.
        """
        try:
            yield self
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise


def get_memgraph_connection() -> MemgraphConnection:
    """
    Return a new ``MemgraphConnection`` configured from settings.

    Each call returns a fresh instance to avoid shared mutable state
    across threads / tasks. Callers wanting a long-lived connection
    should hold the returned object for their own lifetime.
    """
    return MemgraphConnection()


@contextmanager
def memgraph_session():
    """Context manager for a Memgraph cursor wrapped in a transaction."""
    conn = get_memgraph_connection()
    cursor = conn.connection.cursor()
    try:
        yield cursor
        conn.connection.commit()
    except Exception:
        conn.connection.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def init_memgraph_schema(conn: MemgraphConnection | None = None) -> None:
    """Initialize Memgraph schema with indexes for performance."""
    conn = conn if conn is not None else get_memgraph_connection()

    # Create indexes for better query performance
    queries = [
        # Index on Region nodes
        "CREATE INDEX ON :Region(code)",
        "CREATE INDEX ON :Region(interval)",
        # Composite index for Region lookup
        "CREATE INDEX ON :Region(code, interval)",
    ]

    for query in queries:
        try:
            conn.execute_and_commit(query)
            logger.info(f"Created index: {query}")
        except Exception as e:
            # Index might already exist
            logger.debug(f"Index creation skipped (may already exist): {e}")


def clear_memgraph_data(conn: MemgraphConnection | None = None) -> None:
    """Clear all data from Memgraph (useful for testing)."""
    conn = conn if conn is not None else get_memgraph_connection()
    conn.execute_and_commit("MATCH (n) DETACH DELETE n")
    logger.info("Cleared all Memgraph data")
