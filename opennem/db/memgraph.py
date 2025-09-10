"""
Memgraph database connection utilities.

Provides connection management for Memgraph graph database.
"""

import logging
from contextlib import contextmanager

from mgclient import connect

logger = logging.getLogger("opennem.db.memgraph")


class MemgraphConnection:
    """Manages connection to Memgraph database."""

    def __init__(self, host: str = "localhost", port: int = 7687):
        self.host = host
        self.port = port
        self._connection = None

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


# Global connection instance
_memgraph_connection: MemgraphConnection | None = None


def get_memgraph_connection() -> MemgraphConnection:
    """Get the global Memgraph connection instance."""
    global _memgraph_connection
    if _memgraph_connection is None:
        _memgraph_connection = MemgraphConnection()
    return _memgraph_connection


@contextmanager
def memgraph_session():
    """Context manager for Memgraph sessions."""
    conn = get_memgraph_connection()
    cursor = conn.connection.cursor()
    try:
        yield cursor
        conn.connection.commit()
    except Exception as e:
        conn.connection.rollback()
        raise e
    finally:
        cursor.close()


def init_memgraph_schema():
    """Initialize Memgraph schema with indexes for performance."""
    conn = get_memgraph_connection()

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


def clear_memgraph_data():
    """Clear all data from Memgraph (useful for testing)."""
    conn = get_memgraph_connection()
    conn.execute_and_commit("MATCH (n) DETACH DELETE n")
    logger.info("Cleared all Memgraph data")
