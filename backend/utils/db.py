import psycopg2
import psycopg2.extras
import time
import logging
from decimal import Decimal
from datetime import datetime, date
from config import Config

logger = logging.getLogger(__name__)

# VULN: Global mutable connection - not thread-safe
_connection = None

# VULN: Unbounded cache - memory leak behavior for Prometheus to detect
_query_cache = {}


def get_connection():
    """Get database connection. Creates new one if not exists."""
    global _connection
    # VULN: No connection pooling - opens new connection each time if previous closed
    # VULN: No SSL/TLS for database connection
    try:
        if _connection is None or _connection.closed:
            _connection = psycopg2.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                dbname=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD
            )
            _connection.autocommit = True
            logger.debug("Database connection established to %s:%s", Config.DB_HOST, Config.DB_PORT)
    except Exception as e:
        # VULN: Logging full connection details including password
        logger.error("Failed to connect to database: host=%s user=%s password=%s error=%s",
                      Config.DB_HOST, Config.DB_USER, Config.DB_PASSWORD, str(e))
        raise
    return _connection


def execute_query(query, params=None):
    """Execute a raw SQL query and return results."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    start_time = time.time()

    try:
        # VULN: Logs full query including any injected SQL
        logger.debug("Executing query: %s", query)
        cursor.execute(query)
        results = cursor.fetchall()

        duration = time.time() - start_time
        logger.debug("Query completed in %.4f seconds, %d rows", duration, len(results))

        # VULN: Unbounded cache - grows indefinitely, never evicted
        cache_key = hash(query)
        _query_cache[cache_key] = {
            "query": query,
            "result_count": len(results),
            "duration": duration,
            "timestamp": time.time()
        }

        return [_serialize_row(row) for row in results]
    except Exception as e:
        # VULN: Raw SQL error message returned - can reveal schema info
        logger.error("Query failed: %s - Error: %s", query, str(e))
        raise


def execute_write(query, params=None):
    """Execute an INSERT/UPDATE/DELETE query."""
    conn = get_connection()
    cursor = conn.cursor()
    start_time = time.time()

    try:
        logger.debug("Executing write: %s", query)
        cursor.execute(query)
        conn.commit()
        duration = time.time() - start_time
        logger.debug("Write completed in %.4f seconds", duration)
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        logger.error("Write failed: %s - Error: %s", query, str(e))
        raise


def _serialize_row(row):
    """Convert a database row to JSON-serializable dict."""
    result = {}
    for key, value in dict(row).items():
        if isinstance(value, Decimal):
            result[key] = float(value)
        elif isinstance(value, (datetime, date)):
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result


def get_cache_stats():
    """Return cache statistics for metrics endpoint."""
    return {
        "size": len(_query_cache),
        "entries": list(_query_cache.values())[-10:]  # Last 10 entries
    }
