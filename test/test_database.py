# test_databases.py

"""Unit tests for databases.py."""

import math
import pytest
import sqlite3
import tempfile
import os

import config
import utils
from models import Position
from databases import insert_position
from exceptions import DatabaseException


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_db() -> str:
    """Creates a temporary SQLite database with the position table.

    The database is deleted automatically after each test.

    Yields:
        Full path to the temporary database file.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE position (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            bitboard INTEGER NOT NULL,
            pieces   BLOB NOT NULL,
            eval     INTEGER DEFAULT NULL,
            comment  INTEGER DEFAULT NULL,
            eco      INTEGER DEFAULT NULL
        )
    """)
    conn.execute("""
        CREATE UNIQUE INDEX idx_position_unique ON position (bitboard, pieces)
    """)
    conn.commit()
    conn.close()

    yield db_path

    os.unlink(db_path)  # deletes the temporary file after each test


@pytest.fixture
def starting_position() -> tuple[int, bytes]:
    """Returns (bitboard, pieces) for the chess starting position."""
    pos = Position.from_fen(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    )
    return utils.position_to_db(pos)


@pytest.fixture
def after_1_e4() -> tuple[int, bytes]:
    """Returns (bitboard, pieces) for the position after 1.e4."""
    pos = Position.from_fen(
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    )
    return utils.position_to_db(pos)


# ---------------------------------------------------------------------------
# Tests: insert_position
# ---------------------------------------------------------------------------

def test_insert_starting_position_returns_id(temp_db, starting_position):
    """Inserting the starting position must return a valid row id."""
    bitboard, pieces = starting_position
    row_id = insert_position(temp_db, bitboard, pieces)
    assert row_id is not None
    assert row_id >= 1


def test_insert_duplicate_returns_none(temp_db, starting_position):
    """Inserting the same position twice must return None on the second call."""
    bitboard, pieces = starting_position
    insert_position(temp_db, bitboard, pieces)
    row_id = insert_position(temp_db, bitboard, pieces)
    assert row_id is None


def test_insert_two_positions_db_has_two_records(temp_db, starting_position, after_1_e4):
    """After inserting two distinct positions, the DB must contain exactly 2 records."""
    bb1, p1 = starting_position
    bb2, p2 = after_1_e4
    insert_position(temp_db, bb1, p1)
    insert_position(temp_db, bb2, p2)

    conn = sqlite3.connect(temp_db)
    count = conn.execute("SELECT COUNT(*) FROM position").fetchone()[0]
    conn.close()
    assert count == 2


def test_insert_with_optional_fields(temp_db, starting_position):
    """Insert with eval, comment and eco must persist all values correctly."""
    bitboard, pieces = starting_position
    row_id = insert_position(
        temp_db, bitboard, pieces,
        eval=-30,
        comment=0b00000011,
        eco=1
    )
    assert row_id is not None

    conn = sqlite3.connect(temp_db)
    row = conn.execute(
        "SELECT eval, comment, eco FROM position WHERE id = ?", (row_id,)
    ).fetchone()
    conn.close()

    assert row == (-30, 0b00000011, 1)


def test_insert_optional_fields_default_null(temp_db, starting_position):
    """Insert without optional fields must store NULL for eval, comment, eco."""
    bitboard, pieces = starting_position
    row_id = insert_position(temp_db, bitboard, pieces)

    conn = sqlite3.connect(temp_db)
    row = conn.execute(
        "SELECT eval, comment, eco FROM position WHERE id = ?", (row_id,)
    ).fetchone()
    conn.close()

    assert row == (None, None, None)


def test_insert_invalid_db_path_raises():
    """Inserting into a non-existent database path must raise DatabaseException."""
    with pytest.raises(DatabaseException):
        insert_position("/invalid/path/chess.db", 0, b'\x00')