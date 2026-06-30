# models.py

import config
from exceptions import InvalidFENException
from validators import is_valid_fen


class Position:
    """Represents a chess position in the jgchess internal format.

    Attributes:
        squares: Mapping of board index (0-63) to nibble value (0-15).
        turn: Active color, 'w' for White or 'b' for Black.
        castling: Castling availability string (e.g. 'KQkq' or '-').
        en_passant: En passant target square in algebraic notation or '-'.
        halfmove: Halfmove clock for the fifty-move rule.
        fullmove: Fullmove number.
    """

    def __init__(self) -> None:
        self.squares: dict[int, int] = {}
        self.turn: str = 'w'
        self.castling: str = '-'
        self.en_passant: str = '-'

    @classmethod
    def from_fen(cls, fen_string: str) -> "Position":
        """Creates a Position object from a FEN string.

        Args:
            fen_string: A valid FEN string representing a chess position.

        Returns:
            A fully populated Position instance.

        Raises:
            InvalidFENException: If the FEN string is malformed.
        """
        if not is_valid_fen(fen_string):
            raise InvalidFENException(f"Malformed FEN string: '{fen_string}'")

        parts = fen_string.split()
        obj = cls()
        obj.turn       = parts[1]
        obj.castling   = parts[2]
        obj.en_passant = parts[3]

        ep_sq = config.SQUARE_TO_INDEX.get(obj.en_passant, -1)

        ranks = parts[0].split('/')
        for rank_idx, rank_fen in enumerate(ranks):
            rank = 7 - rank_idx  # FEN starts at rank 8; index 0 = rank 1
            file = 0

            for char in rank_fen:
                if char.isdigit():
                    file += int(char)
                    continue

                nibble = config.FEN_TO_NIBBLE.get(char)
                if nibble is None:
                    raise InvalidFENException(
                        f"Unknown piece character '{char}' in FEN."
                    )

                sq = rank * 8 + file

                # En passant: mark the pawn that just moved two squares
                if ep_sq != -1:
                    if obj.turn == 'b' and nibble == config.NIBBLE_WHITE_PAWN and sq == ep_sq + 8:
                        nibble = config.NIBBLE_EN_PASSANT_TARGET
                    elif obj.turn == 'w' and nibble == config.NIBBLE_BLACK_PAWN and sq == ep_sq - 8:
                        nibble = config.NIBBLE_EN_PASSANT_TARGET

                # White king encodes the side to move
                if nibble == config.NIBBLE_WHITE_KING_WHITE_TO_MOVE and obj.turn == 'b':
                    nibble = config.NIBBLE_WHITE_KING_BLACK_TO_MOVE

                # Castling rights encoded in the rook nibble
                if nibble == config.NIBBLE_WHITE_ROOK_NO_CASTLE:
                    if (sq == 0 and 'Q' in obj.castling) or (sq == 7 and 'K' in obj.castling):
                        nibble = config.NIBBLE_WHITE_ROOK_CAN_CASTLE
                elif nibble == config.NIBBLE_BLACK_ROOK_NO_CASTLE:
                    if (sq == 56 and 'q' in obj.castling) or (sq == 63 and 'k' in obj.castling):
                        nibble = config.NIBBLE_BLACK_ROOK_CAN_CASTLE

                obj.squares[sq] = nibble
                file += 1

        return obj

    @classmethod
    def from_squares(cls, squares: dict[int, int]) -> "Position":
        """Creates a Position object from a squares dict.

        Intended for use by apply_move() after a move has been applied
        to a copy of the squares dict. Derives turn, castling, and
        en_passant by inspecting nibble values directly.

        Args:
            squares: Mapping of board index (0-63) to nibble value (0-15),
                representing the complete board state including all
                special nibbles (castling rights, side to move,
                en passant target).

        Returns:
            A fully populated Position instance.

        Raises:
            InvalidFENException: If the squares dict contains no White King,
                which would make the position structurally invalid.
        """
        obj = cls()
        obj.squares = dict(squares)  # defensive copy

        castling_rights: list[str] = []

        for sq, nibble in squares.items():

            # Side to move — encoded in White King nibble
            if nibble == config.NIBBLE_WHITE_KING_WHITE_TO_MOVE:
                obj.turn = 'w'
            elif nibble == config.NIBBLE_WHITE_KING_BLACK_TO_MOVE:
                obj.turn = 'b'

            # Castling rights — encoded in Rook nibbles
            elif nibble == config.NIBBLE_WHITE_ROOK_CAN_CASTLE:
                castling_rights.append('Q' if sq == config.SQUARE_TO_INDEX['a1'] else 'K')
            elif nibble == config.NIBBLE_BLACK_ROOK_CAN_CASTLE:
                castling_rights.append('q' if sq == config.SQUARE_TO_INDEX['a8'] else 'k')

            # En passant target — encoded as special pawn nibble
            elif nibble == config.NIBBLE_EN_PASSANT_TARGET:
                obj.en_passant = config.INDEX_TO_SQUARE[sq]

        # Normalise castling string to standard order KQkq
        order = 'KQkq'
        sorted_rights = sorted(castling_rights, key=lambda r: order.index(r))
        obj.castling = ''.join(sorted_rights) if sorted_rights else '-'

        return obj

@classmethod
def from_db(cls, record: "PositionRecord") -> "Position":
    """Creates a Position object from a raw database record.

    Reconstructs the full position state by decoding the bitboard
    and pieces BLOB back into the squares dict, and inferring turn,
    castling, and en passant from the nibble values.

    Args:
        record: A PositionRecord returned by databases.fetch_position().

    Returns:
        A fully populated Position instance.

    Raises:
        DatabaseIntegrityException: If the BLOB is malformed or the
            bitboard is inconsistent with the pieces data.
    """
    from exceptions import DatabaseIntegrityException
    from utils import to_unsigned_64

    obj = cls()
    bitboard = to_unsigned_64(record.bitboard)
    pieces = record.pieces

    # Unpack nibbles from the BLOB
    nibbles: list[int] = []
    for byte in pieces:
        nibbles.append(byte >> 4)
        nibbles.append(byte & 0x0F)

    # Walk the bitboard LSB-first, assigning one nibble per occupied square
    occupied_squares = [i for i in range(64) if (bitboard >> i) & 1]

    if len(occupied_squares) != len(nibbles):
        # The last nibble may be padding if piece count is odd
        if len(nibbles) - len(occupied_squares) != 1:
            raise DatabaseIntegrityException(
                f"BLOB length mismatch: {len(occupied_squares)} squares "
                f"but {len(nibbles)} nibbles in record id={record.id}",
                position_id=record.id,
            )

    castling_rights: list[str] = []

    for sq_idx, square in enumerate(occupied_squares):
        nibble = nibbles[sq_idx]
        obj.squares[square] = nibble

        # Infer turn from White King nibble
        if nibble == config.NIBBLE_WHITE_KING_WHITE_TO_MOVE:
            obj.turn = 'w'
        elif nibble == config.NIBBLE_WHITE_KING_BLACK_TO_MOVE:
            obj.turn = 'b'

        # Infer castling rights from Rook nibbles
        elif nibble == config.NIBBLE_WHITE_ROOK_CASTLING:
            castling_rights.append('Q' if square == 0 else 'K')
        elif nibble == config.NIBBLE_BLACK_ROOK_CASTLING:
            castling_rights.append('q' if square == 56 else 'k')

        # Infer en passant from the special pawn nibble
        elif nibble == config.NIBBLE_EN_PASSANT_TARGET:
            obj.en_passant = config.INDEX_TO_SQUARE[square]

    obj.castling = ''.join(castling_rights) if castling_rights else '-'

    return obj

# -----------------------------------
# Member functions
# -----------------------------------

def where_piece(self, nibble: int) -> list[int]:
    """Returns all squares occupied by a piece with the given nibble value.

    Args:
        nibble: The nibble value to search for (0-15).

    Returns:
        List of square indices (0-63) where that nibble is found,
        in ascending order. Empty list if none found.
    """
    return [sq for sq, n in self.squares.items() if n == nibble]



# --- Execução do Teste Principal ---
if __name__ == "__main__":
    import pytest, sys
    sys.exit(pytest.main(["test_models.py", "-v"]))


