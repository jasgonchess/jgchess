# test_models.py

"""Unit tests for models.py — Position class and from_fen constructor."""

import pytest
import config
import utils
from position import Position
from exceptions import InvalidFENException


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
FEN_AFTER_1_E4 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"


# ---------------------------------------------------------------------------
# Tests: FEN parsing — metadata fields
# ---------------------------------------------------------------------------

def test_turn_white():
    pos = Position.from_fen(STARTING_FEN)
    assert pos.turn == 'w'

def test_turn_black():
    pos = Position.from_fen(FEN_AFTER_1_E4)
    assert pos.turn == 'b'

def test_castling_full():
    pos = Position.from_fen(STARTING_FEN)
    assert pos.castling == 'KQkq'

def test_en_passant_none():
    pos = Position.from_fen(STARTING_FEN)
    assert pos.en_passant == '-'

def test_en_passant_e3():
    pos = Position.from_fen(FEN_AFTER_1_E4)
    assert pos.en_passant == 'e3'

def test_halfmove():
    pos = Position.from_fen(FEN_AFTER_1_E4)
    assert pos.halfmove == 0

def test_fullmove():
    pos = Position.from_fen(FEN_AFTER_1_E4)
    assert pos.fullmove == 1


# ---------------------------------------------------------------------------
# Tests: FEN parsing — piece placement and nibble encoding
# ---------------------------------------------------------------------------

def test_en_passant_target_nibble():
    """After 1.e4, the pawn on e4 is vulnerable to en passant — nibble must be 15."""
    pos = Position.from_fen(FEN_AFTER_1_E4)
    assert pos.squares[28] == config.NIBBLE_EN_PASSANT_TARGET

def test_white_king_black_to_move():
    """After 1.e4, it is Black's turn — White King nibble must be 13."""
    pos = Position.from_fen(FEN_AFTER_1_E4)
    white_king_sq = next(sq for sq, n in pos.squares.items()
                         if n in (config.NIBBLE_WHITE_KING_WHITE_TO_MOVE,
                                  config.NIBBLE_WHITE_KING_BLACK_TO_MOVE))
    assert pos.squares[white_king_sq] == config.NIBBLE_WHITE_KING_BLACK_TO_MOVE

def test_white_rook_can_castle_a1():
    """In starting position, rook on a1 (square 0) must have castling right."""
    pos = Position.from_fen(STARTING_FEN)
    assert pos.squares[0] == config.NIBBLE_WHITE_ROOK_CAN_CASTLE

def test_black_rook_can_castle_h8():
    """In starting position, rook on h8 (square 63) must have castling right."""
    pos = Position.from_fen(STARTING_FEN)
    assert pos.squares[63] == config.NIBBLE_BLACK_ROOK_CAN_CASTLE

def test_piece_count_starting_position():
    """Starting position must have exactly 32 pieces."""
    pos = Position.from_fen(STARTING_FEN)
    assert len(pos.squares) == 32

# ---------------------------------------------------------------------------
# Tests: invalid FEN — must raise InvalidFENException
# ---------------------------------------------------------------------------

def test_empty_fen_raises():
    with pytest.raises(InvalidFENException):
        Position.from_fen("")

def test_malformed_fen_raises():
    with pytest.raises(InvalidFENException):
        Position.from_fen("not_a_fen")

def test_non_integer_halfmove_raises():
    bad_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - X 1"
    with pytest.raises(InvalidFENException):
        Position.from_fen(bad_fen)

def test_missing_black_king():
    assert not is_valid_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1".replace('k','q'))

def test_invalid_turn():
    assert not is_valid_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR x KQkq - 0 1")

def test_en_passant_wrong_rank():
    assert not is_valid_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e4 0 1")

def test_negative_halfmove():
    assert not is_valid_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - -1 1")

# ---------------------------------------------------------------------------------------
# Tests: test the convertion of a Position object to a bitboard and BLOB for the database
# ---------------------------------------------------------------------------------------

def test_bitboard_e4_set():
    """After 1.e4, bit 28 must be set in the bitboard."""
    pos = Position.from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
    bitboard, _ = utils.position_to_db(pos)
    assert utils.to_unsigned_64(bitboard) & (1 << 28)

def test_piece_count_matches_blob_length():
    """BLOB length in bytes must be ceil(piece_count / 2)."""
    import math
    pos = Position.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    _, blob = utils.position_to_db(pos)
    assert len(blob) == math.ceil(32 / 2)  # 32 peças → 16 bytes

def test_round_trip():
    """Converting Position → DB → Position must produce identical squares."""
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    pos = Position.from_fen(fen)
    bitboard, blob = utils.position_to_db(pos)
    pos2 = utils.db_to_position(to_unsigned_64(bitboard), blob)  # função inversa, futura
    assert pos.squares == pos2.squares

# ---------------------------------------------------------------------------------------
# Tests:
# ---------------------------------------------------------------------------------------


