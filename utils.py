# utils.py

"""Utility functions for jgchess."""

import config
from models import Position

def square_to_index(square: str) -> int:
    """Converts an algebraic square name to a 0-63 board index.

    Args:
        square: Algebraic square name (e.g. 'e3'). Use '-' for no square.

    Returns:
        Integer index in range 0-63, or -1 for '-' or invalid input.
    """
    if square == '-':
        return -1
    return config.SQUARE_TO_INDEX.get(square, -1)

# ---------------------------------------------------------------------------
# CRITICAL FUNCTION: Converts a Position Object to the database format
# ---------------------------------------------------------------------------


def position_to_db(position: Position) -> tuple[int, bytes]:
    """Converts a Position object to the (bitboard, pieces) database format.

    The bitboard is a 64-bit unsigned integer where bit N is set if a piece
    occupies square N (a1=bit0, h8=bit63).

    The pieces BLOB stores one nibble (4 bits) per piece, in the same order
    as the set bits in the bitboard (ascending square index). Two nibbles are
    packed into each byte: the first piece occupies the high nibble, the
    second occupies the low nibble. If the piece count is odd, the last byte
    has the final nibble in the high position and zeros in the low nibble.

    Args:
        position: A fully populated Position instance.

    Returns:
        A tuple of (bitboard, pieces) where bitboard is an unsigned 64-bit
        integer and pieces is a bytes object.

    Raises:
        ValueError: If position.squares contains an invalid square index
            or nibble value.
    """

    if not isinstance(position, Position):
        raise ValueError("Expected a Position instance.")

    bitboard: int = 0
    nibble_list: list[int] = []

    # position.squares is a dict square:piece where only square with pieces are keys.
    for sq in sorted(position.squares):
        if not (0 <= sq <= 63):
            raise ValueError(f"Invalid square index: {sq}")

        nibble = position.squares[sq]
        if nibble not in config.VALID_NIBBLES:
            raise ValueError(f"Invalid nibble value {nibble} at square {sq}.")

        bitboard |= (1 << sq)  # Each occupied square gets 1. Unoccupied squares remain 0.
        nibble_list.append(nibble)  # Creates a list of pieces in the correct order

    # Pack nibbles into bytes: two nibbles per byte, high nibble first
    blob = _pack_nibbles(nibble_list)

    return to_signed_64(bitboard), blob


def _pack_nibbles(nibbles: list[int]) -> bytes:
    """Packs a list of nibble values (0-15) into a bytes object.

    Two nibbles are packed per byte. The first nibble occupies bits 7-4
    (high nibble) and the second occupies bits 3-0 (low nibble). If the
    list length is odd, the last byte has zeros in the low nibble.
    See which nibble represent which piece in config.py file

    Args:
        nibbles: List of integers in range 0-15.

    Returns:bytes([72, 101, 108, 108, 111])
        Packed bytes object.
    """
    result: list[int] = []
    for i in range(0, len(nibbles), 2):
        high = nibbles[i]
        low = nibbles[i + 1] if i + 1 < len(nibbles) else 0
        result.append((high << 4) | low)
    return bytes(result)


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

