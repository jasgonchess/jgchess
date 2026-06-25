# databases.py

"""SQLite database operations for jgchess."""

import sqlite3
from contextlib import contextmanager
from collections.abc import Generator
import config
from exceptions import DatabaseException
from dataclasses import dataclass

@contextmanager
def open_database(db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """Opens a connection to the SQLite database.

    Intended for use as a context manager when performing multiple
    operations in a single session. The connection is closed automatically
    on exit, even if an exception occurs.

    Args:
        db_path: Full path to the SQLite database file.

    Yields:
        An open sqlite3.Connection object.

    Raises:
        DatabaseException: If the database file cannot be opened.

    Example:
        with open_database(db_path) as conn:
            insert_position(conn, bitboard, pieces)
            insert_position(conn, bitboard2, pieces2)
    """
    try:
        conn = sqlite3.connect(db_path)
        yield conn
    except sqlite3.OperationalError as exc:
        raise DatabaseException(f"Could not open database: {exc}") from exc
    finally:
        conn.close()

@dataclass
class PositionRecord:
    """Raw database record for a chess position.

    Attributes:
        id: Primary key from the database.
        bitboard: Signed 64-bit integer representing occupied squares.
        pieces: BLOB with one nibble per piece in bitboard order.
        eval: Optional position evaluation in centipawns.
        comment: Optional bitmask of positional characteristics.
        eco: Optional ECO opening code identifier.
    """
    id: int
    bitboard: int
    pieces: bytes
    eval: int | None
    comment: int | None
    eco: int | None

def fetch_position(
    conn: sqlite3.Connection,
    position_id: int,
) -> PositionRecord | None:
    """Fetches a chess position from the database by its primary key.

    Args:
        conn: An open sqlite3.Connection, obtained via open_database().
        position_id: The primary key (id) of the position to retrieve.

    Returns:
        A PositionRecord with the row data, or None if not found.

    Raises:
        DatabaseException: If a database error occurs during the query.
    """
    sql = """
        SELECT id, bitboard, pieces, eval, comment, eco
        FROM position
        WHERE id = ?
    """
    try:
        cursor = conn.execute(sql, (position_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return PositionRecord(
            id=row[0],
            bitboard=row[1],
            pieces=row[2],
            eval=row[3],
            comment=row[4],
            eco=row[5],
        )

    except sqlite3.OperationalError as exc:
        raise DatabaseException(f"Database error on fetch: {exc}") from exc
    except sqlite3.DatabaseError as exc:
        raise DatabaseException(f"Unexpected database error: {exc}") from exc

def insert_position(
    conn: sqlite3.Connection,
    bitboard: int,
    pieces: bytes,
    eval: int | None = None,
    comment: int | None = None,
    eco: int | None = None,
) -> int | None:
    """Inserts a chess position into the database.

    If the position already exists (same bitboard and pieces), the insertion
    is silently ignored and None is returned.

    Args:
        conn: An open sqlite3.Connection, obtained via open_database().
        bitboard: Signed 64-bit integer representing occupied squares.
        pieces: BLOB with one nibble per piece in bitboard order.
        eval: Optional position evaluation in centipawns.
        comment: Optional bitmask of positional characteristics.
        eco: Optional ECO opening code identifier.

    Returns:
        The row id of the inserted record, or None if the position already
        existed in the database.

    Raises:
        DatabaseException: If a database error occurs during insertion.
    """
    sql = """
        INSERT OR IGNORE INTO position (bitboard, pieces, eval, comment, eco)
        VALUES (?, ?, ?, ?, ?)
    """
    try:
        cursor = conn.execute("BEGIN")
        cursor = conn.execute(sql, (bitboard, pieces, eval, comment, eco))
        conn.commit()
        if cursor.rowcount == 0:
            return None
        return cursor.lastrowid

    except sqlite3.OperationalError as exc:
        raise DatabaseException(f"Database error on insert: {exc}") from exc
    except sqlite3.DatabaseError as exc:
        raise DatabaseException(f"Unexpected database error: {exc}") from exc