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
        self.halfmove: int = 0
        self.fullmove: int = 1

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

        try:
            obj.halfmove = int(parts[4])
            obj.fullmove = int(parts[5])
        except ValueError as exc:
            raise InvalidFENException(
                f"Non-integer move counters in FEN: '{fen_string}'"
            ) from exc

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


# --- Execução do Teste Principal ---
if __name__ == "__main__":
    import pytest, sys
    sys.exit(pytest.main(["test_models.py", "-v"]))


