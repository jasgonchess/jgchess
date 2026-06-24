# databases.py

"""SQLite database operations for jgchess."""

import sqlite3
import config
from exceptions import DatabaseException


def insert_position(
    db_path: str,
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
        db_path: Full path to the SQLite database file.
        bitboard: Signed 64-bit integer representing occupied squares.
        pieces: BLOB with one nibble per piece in bitboard order.
        eval: Optional position evaluation in centipawns.
        comment: Optional bitmask of positional characteristics.
        eco: Optional ECO opening code identifier.

    Returns:
        The row id of the inserted record, or None if the position already
        existed in the database.

    Raises:
        DatabaseException: If the database file is not found or a database
            error occurs during insertion.
    """
    sql = """
        INSERT OR IGNORE INTO position (bitboard, pieces, eval, comment, eco)
        VALUES (?, ?, ?, ?, ?)
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("BEGIN")
            cursor = conn.execute(sql, (bitboard, pieces, eval, comment, eco))
            conn.commit()
            if cursor.rowcount == 0:
                return None  # Position already existed
            return cursor.lastrowid

    except sqlite3.OperationalError as exc:
        raise DatabaseException(f"Database error on insert: {exc}") from exc
    except sqlite3.DatabaseError as exc:
        raise DatabaseException(f"Unexpected database error: {exc}") from exc