# databases.py

"""SQLite database operations for jgchess."""

import sqlite3
from contextlib import contextmanager
from collections.abc import Generator
from exceptions import DatabaseConnectionException, DatabaseException
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Signed/unsigned 64-bit conversion helpers.
#
# The chess domain (Position, etc.) always works with bitboards as unsigned
# 64-bit integers — a plain occupancy mask. SQLite, however, stores INTEGER
# columns as signed 64-bit values. These two functions exist solely to
# bridge that storage detail, and are applied here, at the database
# boundary, rather than inside the domain model.
# ---------------------------------------------------------------------------

def to_signed_64(value: int) -> int:
    """Converts an unsigned 64-bit integer to a signed 64-bit integer.

    Required because SQLite stores integers as signed values.

    Args:
        value: Unsigned integer in range 0 to 2**64-1.

    Returns:
        Signed integer in range -2**63 to 2**63-1.
    """
    if value >= (1 << 63):
        return value - (1 << 64)
    return value


def to_unsigned_64(value: int) -> int:
    """Converts a signed 64-bit integer back to an unsigned 64-bit integer.

    Used when reading the bitboard from SQLite.

    Args:
        value: Signed integer in range -2**63 to 2**63-1.

    Returns:
        Unsigned integer in range 0 to 2**64-1.
    """
    if value < 0:
        return value + (1 << 64)
    return value


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
        DatabaseConnectionException: If the database file cannot be opened.

    Example:
        with open_database(db_path) as conn:
            insert_position(conn, bitboard, pieces)
            insert_position(conn, bitboard2, pieces2)
    """
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(db_path)
        yield conn
    except sqlite3.OperationalError as exc:
        raise DatabaseConnectionException(
            f"Could not open database: {exc}", db_path=db_path
        ) from exc
    finally:
        if conn is not None:
            conn.close()

@dataclass
class PositionRecord:
    """Raw database record for a chess position.

    Attributes:
        id: Primary key from the database.
        bitboard: Unsigned 64-bit integer representing occupied squares
            (bit N = square N, a1=bit0, h8=bit63). The signed/unsigned
            conversion required by SQLite's storage format is already
            applied by fetch_position() before this object is built.
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
            bitboard=to_unsigned_64(row[1]),
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
        bitboard: Unsigned 64-bit integer representing occupied squares
            (bit N = square N, a1=bit0, h8=bit63), e.g. as returned by
            Position.to_db_format(). The signed/unsigned conversion
            required by SQLite's storage format is applied internally.
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
        signed_bitboard = to_signed_64(bitboard)
        cursor = conn.execute("BEGIN")
        cursor = conn.execute(sql, (signed_bitboard, pieces, eval, comment, eco))
        conn.commit()
        if cursor.rowcount == 0:
            return None
        return cursor.lastrowid

    except sqlite3.OperationalError as exc:
        raise DatabaseException(f"Database error on insert: {exc}") from exc
    except sqlite3.DatabaseError as exc:
        raise DatabaseException(f"Unexpected database error: {exc}") from exc