"""Global configuration, constants, and paths for jgchess.

This module centralises every magic number and project-wide setting so that
all other modules import from here rather than defining their own literals.
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

#: Root directory that contains all SQLite database files.
DB_DIR: str = "/home/jasg/pybin/chess/chessdb/"

#: Default database file name.
DB_DEFAULT: str = "chessdb01.db"

#: Full path to the default database.
DB_DEFAULT_PATH: str = os.path.join(DB_DIR, DB_DEFAULT)

# ---------------------------------------------------------------------------
# Nibble encoding table
# Each piece occupies exactly 4 bits (one nibble) inside the ``pieces`` BLOB.
# Nibbles are stored in the same order as the bits in the bitboard
# (bit 0 = a1, bit 63 = h8).
#
# Encoding:
#   0000 (0)  : White Pawn
#   0001 (1)  : Black Pawn
#   0010 (2)  : White Knight
#   0011 (3)  : Black Knight
#   0100 (4)  : White Bishop
#   0101 (5)  : Black Bishop
#   0110 (6)  : White Rook  (no castling right)
#   0111 (7)  : Black Rook  (no castling right)
#   1000 (8)  : White Rook  (has castling right)
#   1001 (9)  : Black Rook  (has castling right)
#   1010 (10) : White Queen
#   1011 (11) : Black Queen
#   1100 (12) : White King  (White to move)
#   1101 (13) : White King  (Black to move)
#   1110 (14) : Black King
#   1111 (15) : Pawn that just moved two squares (en passant target)
# ---------------------------------------------------------------------------

NIBBLE_WHITE_PAWN:              int = 0   # 0000
NIBBLE_BLACK_PAWN:              int = 1   # 0001
NIBBLE_WHITE_KNIGHT:            int = 2   # 0010
NIBBLE_BLACK_KNIGHT:            int = 3   # 0011
NIBBLE_WHITE_BISHOP:            int = 4   # 0100
NIBBLE_BLACK_BISHOP:            int = 5   # 0101
NIBBLE_WHITE_ROOK_NO_CASTLE:    int = 6   # 0110
NIBBLE_BLACK_ROOK_NO_CASTLE:    int = 7   # 0111
NIBBLE_WHITE_ROOK_CAN_CASTLE:   int = 8   # 1000
NIBBLE_BLACK_ROOK_CAN_CASTLE:   int = 9   # 1001
NIBBLE_WHITE_QUEEN:             int = 10  # 1010
NIBBLE_BLACK_QUEEN:             int = 11  # 1011
NIBBLE_WHITE_KING_WHITE_TO_MOVE: int = 12  # 1100
NIBBLE_WHITE_KING_BLACK_TO_MOVE: int = 13  # 1101
NIBBLE_BLACK_KING:              int = 14  # 1110
NIBBLE_EN_PASSANT_TARGET:       int = 15  # 1111

#: Convenience tuple with all valid nibble values.
VALID_NIBBLES: tuple[int, ...] = tuple(range(16))

# ---------------------------------------------------------------------------
# Bitboard constants
# ---------------------------------------------------------------------------

#: Number of squares on the board.
BOARD_SQUARES: int = 64

#: Mask for a fully occupied board (all 64 bits set).
FULL_BOARD_MASK: int = (1 << BOARD_SQUARES) - 1

# ---------------------------------------------------------------------------
# Square name to index lookup (algebraic notation → 0-63)
# a1=0, b1=1, ..., h1=7, a2=8, ..., h8=63
# ---------------------------------------------------------------------------
SQUARE_TO_INDEX: dict[str, int] = {
    f"{file}{rank}": (rank_idx * 8 + file_idx)
    for rank_idx, rank in enumerate("12345678")
    for file_idx, file in enumerate("abcdefgh")
}

#: Reverse mapping: 0-63 index → algebraic notation
INDEX_TO_SQUARE: dict[int, str] = {v: k for k, v in SQUARE_TO_INDEX.items()}

# FEN piece character to nibble value
FEN_TO_NIBBLE: dict[str, int] = {
    'P': NIBBLE_WHITE_PAWN,
    'p': NIBBLE_BLACK_PAWN,
    'N': NIBBLE_WHITE_KNIGHT,
    'n': NIBBLE_BLACK_KNIGHT,
    'B': NIBBLE_WHITE_BISHOP,
    'b': NIBBLE_BLACK_BISHOP,
    'R': NIBBLE_WHITE_ROOK_NO_CASTLE,
    'r': NIBBLE_BLACK_ROOK_NO_CASTLE,
    'Q': NIBBLE_WHITE_QUEEN,
    'q': NIBBLE_BLACK_QUEEN,
    'K': NIBBLE_WHITE_KING_WHITE_TO_MOVE,
    'k': NIBBLE_BLACK_KING,
}

# ---------------------------------------------------------------------------
# Nibble sets by color
# Useful for quickly determining the color of a piece on a given square
# without a chain of comparisons.
# ---------------------------------------------------------------------------

#: All nibble values that represent a White piece.
WHITE_NIBBLES: frozenset[int] = frozenset({
    NIBBLE_WHITE_PAWN,
    NIBBLE_WHITE_KNIGHT,
    NIBBLE_WHITE_BISHOP,
    NIBBLE_WHITE_ROOK_NO_CASTLE,
    NIBBLE_WHITE_ROOK_CAN_CASTLE,
    NIBBLE_WHITE_QUEEN,
    NIBBLE_WHITE_KING_WHITE_TO_MOVE,
    NIBBLE_WHITE_KING_BLACK_TO_MOVE,
})

#: All nibble values that represent a Black piece.
BLACK_NIBBLES: frozenset[int] = frozenset({
    NIBBLE_BLACK_PAWN,
    NIBBLE_BLACK_KNIGHT,
    NIBBLE_BLACK_BISHOP,
    NIBBLE_BLACK_ROOK_NO_CASTLE,
    NIBBLE_BLACK_ROOK_CAN_CASTLE,
    NIBBLE_BLACK_QUEEN,
    NIBBLE_BLACK_KING,
})

WHITE_KING_NIBBLES: frozenset[int] = frozenset({
    NIBBLE_WHITE_KING_WHITE_TO_MOVE,
    NIBBLE_WHITE_KING_BLACK_TO_MOVE,
})