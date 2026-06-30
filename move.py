"""Chess move representation for jgchess.

A Move object represents a fully resolved chess move: piece type, origin
square, destination square, and any special flags (castling, en passant,
promotion). It does not carry color information — color is determined by
the Position context in which the move is applied.
"""

import config
import tables
from exceptions import InvalidMoveException


class Move:
    """Represents a single fully resolved chess move.

    A Move is considered complete only when all fields are known:
    piece type, origin square, and destination square. Special flags
    (castling, en passant, promotion) default to their inactive values.

    Color is not stored — it is inferred from the Position in which
    the move occurs.

    Attributes:
        piece: The piece type that moves, as an uppercase letter:
            'P' (pawn), 'N' (knight), 'B' (bishop),
            'R' (rook), 'Q' (queen), 'K' (king).
        square_from: Origin square index (0-63, a1=0, h8=63).
        square_to: Destination square index (0-63, a1=0, h8=63).
        is_castling: True if the move is a castling move. The specific
            castling type (short/long, white/black) is fully determined
            by square_from and square_to.
        is_en_passant: True if the move is an en passant capture.
        promotion_piece: The piece type the pawn promotes to
            ('N', 'B', 'R' or 'Q'), or None if not a promotion.
    """

    VALID_PIECES:     frozenset[str] = frozenset({'P', 'N', 'B', 'R', 'Q', 'K'})
    PROMOTION_PIECES: frozenset[str] = frozenset({'N', 'B', 'R', 'Q'})

    def __init__(
        self,
        piece: str,
        square_from: int,
        square_to: int,
        is_castling: bool = False,
        is_en_passant: bool = False,
        promotion_piece: str | None = None,
    ) -> None:
        """Initialises a Move object.

        Args:
            piece: Piece type as an uppercase letter
                ('P', 'N', 'B', 'R', 'Q' or 'K').
            square_from: Origin square index (0-63).
            square_to: Destination square index (0-63).
            is_castling: True if this is a castling move.
            is_en_passant: True if this is an en passant capture.
            promotion_piece: Promotion target piece type
                ('N', 'B', 'R' or 'Q'), or None.

        Raises:
            InvalidMoveException: If any argument is outside its valid range.
        """
        if piece not in self.VALID_PIECES:
            raise InvalidMoveException(
                f"Invalid piece '{piece}'. Must be one of {sorted(self.VALID_PIECES)}."
            )
        if not (0 <= square_from <= 63):
            raise InvalidMoveException(
                f"Invalid square_from {square_from}. Must be between 0 and 63."
            )
        if not (0 <= square_to <= 63):
            raise InvalidMoveException(
                f"Invalid square_to {square_to}. Must be between 0 and 63."
            )
        if square_from == square_to:
            raise InvalidMoveException(
                f"square_from and square_to must be different (got {square_from})."
            )
        if promotion_piece is not None and promotion_piece not in self.PROMOTION_PIECES:
            raise InvalidMoveException(
                f"Invalid promotion_piece '{promotion_piece}'. "
                f"Must be one of {sorted(self.PROMOTION_PIECES)} or None."
            )
        if promotion_piece is not None and piece != 'P':
            raise InvalidMoveException(
                f"Only pawns can promote, but piece is '{piece}'."
            )

        self.piece:           str        = piece
        self.square_from:     int        = square_from
        self.square_to:       int        = square_to
        self.is_castling:     bool       = is_castling
        self.is_en_passant:   bool       = is_en_passant
        self.promotion_piece: str | None = promotion_piece

    # -----------------------------------------------------------------------
    # Alternative constructors
    # -----------------------------------------------------------------------

    @classmethod
    def from_short_algebraic(cls, text: str, position: "Position") -> "Move":
        """Creates a Move object from algebraic notation and a Position.

        Parses standard algebraic notation (SAN) as found in PGN files,
        resolves the origin square by querying the position, and returns
        a fully resolved Move object.

        Handles: normal moves, captures, castling (O-O / 0-0 / O-O-O /
        0-0-0), en passant, promotion (e8=Q), and explicit disambiguation
        (Nbd7, R1e4). Trailing '+' and '#' are ignored.

        Args:
            text: A move string in standard algebraic notation,
                e.g. 'Nf3', 'e4', 'O-O', 'exd8=Q', 'Nbd7'.
            position: The current Position from which the move is made.

        Returns:
            A fully resolved Move instance.

        Raises:
            InvalidMoveException: If the move string cannot be parsed,
                if no piece can reach the destination, or if more than
                one piece can reach the destination (ambiguous PGN).
        """
        from models import Position  # local import to avoid circular dependency

        text = text.strip().rstrip('+#')

        # -------------------------------------------------------------------
        # Castling
        # -------------------------------------------------------------------
        if text in ('O-O', '0-0'):
            return cls._resolve_castling(position, kingside=True)
        if text in ('O-O-O', '0-0-0'):
            return cls._resolve_castling(position, kingside=False)

        # -------------------------------------------------------------------
        # Promotion — detect and strip '=X' suffix
        # -------------------------------------------------------------------
        promotion_piece: str | None = None
        if '=' in text:
            eq_idx = text.index('=')
            promotion_piece = text[eq_idx + 1:]
            text = text[:eq_idx]
            if promotion_piece not in cls.PROMOTION_PIECES:
                raise InvalidMoveException(
                    f"Invalid promotion piece '{promotion_piece}'."
                )

        # -------------------------------------------------------------------
        # Identify destination square — always the last two characters
        # -------------------------------------------------------------------
        if len(text) < 2:
            raise InvalidMoveException(
                f"Move string too short to parse: '{text}'."
            )
        dest_str = text[-2:]
        if dest_str not in config.SQUARE_TO_INDEX:
            raise InvalidMoveException(
                f"Invalid destination square '{dest_str}' in move '{text}'."
            )
        square_to = config.SQUARE_TO_INDEX[dest_str]

        # -------------------------------------------------------------------
        # Identify piece type and disambiguation hint
        # -------------------------------------------------------------------
        if text[0] in 'NBRQK':
            piece = text[0]
            hint  = text[1:-2]   # e.g. 'b' in 'Nbd7', '1' in 'R1e4', '' in 'Nf3'
        else:
            piece = 'P'
            hint  = text[:-2]    # e.g. 'e' in 'exd5', '' in 'e4'
            hint  = hint.rstrip('x')

        # -------------------------------------------------------------------
        # Resolve origin square
        # -------------------------------------------------------------------
        square_from, is_en_passant = cls._resolve_origin(
            piece, square_to, hint, position
        )

        return cls(
            piece=piece,
            square_from=square_from,
            square_to=square_to,
            is_castling=False,
            is_en_passant=is_en_passant,
            promotion_piece=promotion_piece,
        )

    @classmethod
    def from_full_algebraic(cls, text: str, position: "Position") -> "Move":
        """Creates a Move from full algebraic notation (e.g. 'Ne4-f6', 'Pe2-e4').

        Full algebraic notation always specifies both origin and destination
        squares explicitly, so no position lookup is needed for disambiguation.
        Castling and promotion are also supported.

        Args:
            text: A move string in full algebraic notation,
                e.g. 'Ne4-f6', 'Pe2-e4', 'O-O', 'Pe7-e8=Q'.
            position: The current Position (used only for en passant detection).

        Returns:
            A fully resolved Move instance.

        Raises:
            InvalidMoveException: If the string cannot be parsed or the
                origin/destination squares are invalid.
        """
        text = text.strip().rstrip('+#')

        # Castling — identical to from_short_algebraic
        if text in ('O-O', '0-0'):
            return cls._resolve_castling(position, kingside=True)
        if text in ('O-O-O', '0-0-0'):
            return cls._resolve_castling(position, kingside=False)

        # Promotion — strip '=X' suffix
        promotion_piece: str | None = None
        if '=' in text:
            eq_idx = text.index('=')
            promotion_piece = text[eq_idx + 1:]
            text = text[:eq_idx]
            if promotion_piece not in cls.PROMOTION_PIECES:
                raise InvalidMoveException(
                    f"Invalid promotion piece '{promotion_piece}'."
                )

        # Expected format: <Piece><sq_from>-<sq_to>  e.g. 'Ne4-f6' or 'Pe2-e4'
        # Piece letter is optional for pawns in some implementations
        if len(text) < 5:
            raise InvalidMoveException(
                f"Move string too short for full algebraic notation: '{text}'."
            )

        if text[0] in 'NBRQKP':
            piece = text[0]
            rest = text[1:]  # 'e4-f6'
        else:
            piece = 'P'
            rest = text  # 'e2-e4' without piece letter

        if '-' not in rest:
            raise InvalidMoveException(
                f"Missing '-' separator in full algebraic notation: '{text}'."
            )

        parts = rest.split('-')
        if len(parts) != 2:
            raise InvalidMoveException(
                f"Expected exactly one '-' separator in '{text}'."
            )

        from_str, to_str = parts
        if from_str not in config.SQUARE_TO_INDEX:
            raise InvalidMoveException(
                f"Invalid origin square '{from_str}' in '{text}'."
            )
        if to_str not in config.SQUARE_TO_INDEX:
            raise InvalidMoveException(
                f"Invalid destination square '{to_str}' in '{text}'."
            )

        square_from = config.SQUARE_TO_INDEX[from_str]
        square_to = config.SQUARE_TO_INDEX[to_str]

        # En passant detection — pawn captures diagonally onto empty square
        is_en_passant = False
        if piece == 'P' and square_from % 8 != square_to % 8:
            if position.squares.get(square_to) is None:
                captured_sq = (square_from // 8) * 8 + (square_to % 8)
                if position.squares.get(captured_sq) == config.NIBBLE_EN_PASSANT_TARGET:
                    is_en_passant = True

        return cls(
            piece=piece,
            square_from=square_from,
            square_to=square_to,
            is_castling=False,
            is_en_passant=is_en_passant,
            promotion_piece=promotion_piece,
        )

    # -----------------------------------------------------------------------
    # Private resolution helpers
    # -----------------------------------------------------------------------

    @classmethod
    def _resolve_castling(cls, position: "Position", kingside: bool) -> "Move":
        """Resolves a castling move into a fully specified Move.

        Args:
            position: The current Position.
            kingside: True for kingside (O-O), False for queenside (O-O-O).

        Returns:
            A Move with is_castling=True.

        Raises:
            InvalidMoveException: If the castling right is not available
                in the current position.
        """
        if position.turn == 'w':
            square_from  = config.SQUARE_TO_INDEX['e1']
            square_to    = config.SQUARE_TO_INDEX['g1'] if kingside else config.SQUARE_TO_INDEX['c1']
            rook_sq      = config.SQUARE_TO_INDEX['h1'] if kingside else config.SQUARE_TO_INDEX['a1']
            right_nibble = config.NIBBLE_WHITE_ROOK_CAN_CASTLE
        else:
            square_from  = config.SQUARE_TO_INDEX['e8']
            square_to    = config.SQUARE_TO_INDEX['g8'] if kingside else config.SQUARE_TO_INDEX['c8']
            rook_sq      = config.SQUARE_TO_INDEX['h8'] if kingside else config.SQUARE_TO_INDEX['a8']
            right_nibble = config.NIBBLE_BLACK_ROOK_CAN_CASTLE

        if position.squares.get(rook_sq) != right_nibble:
            side  = 'kingside' if kingside else 'queenside'
            color = 'White' if position.turn == 'w' else 'Black'
            raise InvalidMoveException(
                f"{color} does not have {side} castling rights in this position."
            )

        return cls(
            piece='K',
            square_from=square_from,
            square_to=square_to,
            is_castling=True,
        )

    @classmethod
    def _resolve_origin(
        cls,
        piece: str,
        square_to: int,
        hint: str,
        position: "Position",
    ) -> tuple[int, bool]:
        """Finds the origin square for a move given piece type and destination.

        Searches the position for pieces of the correct type and color that
        can legally reach square_to, using movement tables and ray blocking.

        Args:
            piece: Piece type ('P', 'N', 'B', 'R', 'Q' or 'K').
            square_to: Destination square index (0-63).
            hint: Disambiguation string from the PGN token, e.g. 'b', '1',
                'b1', or '' if none.
            position: The current Position.

        Returns:
            A tuple (square_from, is_en_passant).

        Raises:
            InvalidMoveException: If no candidate or more than one candidate
                is found after applying the disambiguation hint.
        """
        is_en_passant = False

        if piece == 'P':
            candidates, is_en_passant = cls._pawn_origins(square_to, hint, position)
        elif piece == 'N':
            candidates = cls._knight_origins(square_to, position)
        elif piece == 'B':
            candidates = cls._sliding_origins(square_to, position, tables.BISHOP_MOVES)
        elif piece == 'R':
            candidates = cls._sliding_origins(square_to, position, tables.ROOK_MOVES)
        elif piece == 'Q':
            candidates = cls._sliding_origins(square_to, position, tables.QUEEN_MOVES)
        else:  # 'K'
            candidates = cls._king_origins(square_to, position)

        # Apply disambiguation hint for non-pawn pieces
        if hint and piece != 'P':
            candidates = cls._apply_hint(candidates, hint)

        if len(candidates) == 0:
            raise InvalidMoveException(
                f"No {piece} can reach {config.INDEX_TO_SQUARE[square_to]} "
                f"in this position."
            )
        if len(candidates) > 1:
            squares_str = ', '.join(
                config.INDEX_TO_SQUARE[sq] for sq in candidates
            )
            raise InvalidMoveException(
                f"Ambiguous move: {piece} on {squares_str} can all reach "
                f"{config.INDEX_TO_SQUARE[square_to]}. PGN disambiguation "
                f"is missing or incorrect."
            )

        return candidates[0], is_en_passant

    @classmethod
    def _knight_origins(cls, square_to: int, position: "Position") -> list[int]:
        """Returns squares with a friendly knight that can reach square_to.

        Args:
            square_to: Destination square index.
            position: The current Position.

        Returns:
            List of candidate origin square indices.
        """
        friendly_nibbles = (
            config.WHITE_NIBBLES if position.turn == 'w' else config.BLACK_NIBBLES
        )
        # Destination must not be occupied by a friendly piece
        if position.squares.get(square_to) in friendly_nibbles:
            return []
        friendly_knight = (
            config.NIBBLE_WHITE_KNIGHT
            if position.turn == 'w'
            else config.NIBBLE_BLACK_KNIGHT
        )
        return [
            sq for sq in tables.KNIGHT_MOVES[square_to]
            if position.squares.get(sq) == friendly_knight
        ]

    @classmethod
    def _king_origins(cls, square_to: int, position: "Position") -> list[int]:
        """Returns squares with the friendly king that can reach square_to.

        Args:
            square_to: Destination square index.
            position: The current Position.

        Returns:
            List of candidate origin square indices (0 or 1 elements).
        """
        friendly_nibbles = (
            config.WHITE_NIBBLES if position.turn == 'w' else config.BLACK_NIBBLES
        )
        # Destination must not be occupied by a friendly piece
        if position.squares.get(square_to) in friendly_nibbles:
            return []
        friendly_king = (
            config.WHITE_KING_NIBBLES
            if position.turn == 'w'
            else frozenset({config.NIBBLE_BLACK_KING})
        )
        return [
            sq for sq in tables.KING_MOVES[square_to]
            if position.squares.get(sq) in friendly_king
        ]

    @classmethod
    def _sliding_origins(
        cls,
        square_to: int,
        position: "Position",
        move_table: dict[int, list[list[int]]],
    ) -> list[int]:
        """Returns squares with a friendly sliding piece that can reach square_to.

        Traverses each ray from square_to outward. Stops at the first
        occupied square per ray — if that square holds a friendly piece
        of the correct type (implied by the caller's choice of move_table),
        it is a candidate origin.

        Args:
            square_to: Destination square index.
            position: The current Position.
            move_table: One of BISHOP_MOVES, ROOK_MOVES, or QUEEN_MOVES.

        Returns:
            List of candidate origin square indices.
        """
        if move_table is tables.BISHOP_MOVES:
            valid_friendly: frozenset[int] = frozenset({
                config.NIBBLE_WHITE_BISHOP
                if position.turn == 'w'
                else config.NIBBLE_BLACK_BISHOP
            })
        elif move_table is tables.ROOK_MOVES:
            valid_friendly = (
                frozenset({
                    config.NIBBLE_WHITE_ROOK_NO_CASTLE,
                    config.NIBBLE_WHITE_ROOK_CAN_CASTLE,
                })
                if position.turn == 'w'
                else frozenset({
                    config.NIBBLE_BLACK_ROOK_NO_CASTLE,
                    config.NIBBLE_BLACK_ROOK_CAN_CASTLE,
                })
            )
        else:  # QUEEN_MOVES
            valid_friendly = frozenset({
                config.NIBBLE_WHITE_QUEEN
                if position.turn == 'w'
                else config.NIBBLE_BLACK_QUEEN
            })

        # Destination must not be occupied by a friendly piece
        friendly_nibbles = (
            config.WHITE_NIBBLES if position.turn == 'w' else config.BLACK_NIBBLES
        )
        if position.squares.get(square_to) in friendly_nibbles:
            return []

        candidates: list[int] = []
        for ray in move_table[square_to]:
            for sq in ray:
                nibble = position.squares.get(sq)
                if nibble is None:
                    continue          # empty square — keep going along ray
                if nibble in valid_friendly:
                    candidates.append(sq)
                break                 # ray blocked by any piece

        return candidates

    @classmethod
    def _pawn_origins(
        cls,
        square_to: int,
        hint: str,
        position: "Position",
    ) -> tuple[list[int], bool]:
        """Returns candidate origin squares for a pawn move.

        Handles single advance, double advance from starting rank,
        diagonal captures, and en passant.

        Args:
            square_to: Destination square index.
            hint: File of the capturing pawn (e.g. 'e' for 'exd5'),
                or '' for straight advances.
            position: The current Position.

        Returns:
            A tuple (candidates, is_en_passant).
        """
        is_en_passant  = False
        candidates: list[int] = []
        rank_to        = square_to // 8
        file_to        = square_to % 8

        if position.turn == 'w':
            friendly_pawn = config.NIBBLE_WHITE_PAWN
            direction     = -1    # white pawns move up; origin is one rank below dest
            starting_rank = 1
        else:
            friendly_pawn = config.NIBBLE_BLACK_PAWN
            direction     = 1    # black pawns move down; origin is one rank above dest
            starting_rank = 6

        if hint:
            # Diagonal capture — origin file given by hint
            file_from = ord(hint) - ord('a')
            sq_from   = (rank_to + direction) * 8 + file_from
            if 0 <= sq_from <= 63:
                if position.squares.get(sq_from) == friendly_pawn:
                    dest_nibble = position.squares.get(square_to)
                    if dest_nibble is None:
                        # Destination is empty — could be en passant
                        ep_pawn_sq = sq_from // 8 * 8 + file_to
                        if position.squares.get(ep_pawn_sq) == config.NIBBLE_EN_PASSANT_TARGET:
                            is_en_passant = True
                            candidates.append(sq_from)
                    else:
                        # Normal diagonal capture
                        candidates.append(sq_from)
        else:
            # Straight advance — destination must not be occupied
            if position.squares.get(square_to) is not None:
                return candidates, is_en_passant

            sq_one = (rank_to + direction) * 8 + file_to       # one step back
            sq_two = (rank_to + direction * 2) * 8 + file_to   # two steps back

            if 0 <= sq_one <= 63 and position.squares.get(sq_one) == friendly_pawn:
                # Single advance
                candidates.append(sq_one)
            elif (0 <= sq_two <= 63
                    and sq_two // 8 == starting_rank
                    and position.squares.get(sq_two) == friendly_pawn
                    and position.squares.get(sq_one) is None):
                # Double advance from starting rank — intermediate square must be empty
                candidates.append(sq_two)

        return candidates, is_en_passant

    @staticmethod
    def _apply_hint(candidates: list[int], hint: str) -> list[int]:
        """Filters candidates using a PGN disambiguation hint.

        Args:
            candidates: List of candidate origin square indices.
            hint: A file letter ('a'-'h'), a rank digit ('1'-'8'),
                or a full square name ('a1'-'h8').

        Returns:
            Filtered list of candidate square indices.
        """
        if len(hint) == 2:
            sq = config.SQUARE_TO_INDEX.get(hint)
            return [c for c in candidates if c == sq]
        if hint.isalpha():
            file_idx = ord(hint) - ord('a')
            return [c for c in candidates if c % 8 == file_idx]
        if hint.isdigit():
            rank_idx = int(hint) - 1
            return [c for c in candidates if c // 8 == rank_idx]
        return candidates

    # -----------------------------------------------------------------------
    # String representations
    # -----------------------------------------------------------------------

    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the move.

        Returns:
            A string showing all move fields.
        """
        return (
            f"Move(piece={self.piece!r}, "
            f"square_from={self.square_from}, "
            f"square_to={self.square_to}, "
            f"is_castling={self.is_castling}, "
            f"is_en_passant={self.is_en_passant}, "
            f"promotion_piece={self.promotion_piece!r})"
        )

    def __str__(self) -> str:
        """Returns a compact human-readable string in coordinate notation.

        Returns:
            A string such as 'Ne4-f6' or 'Pe7-e8=Q'.
        """
        files = "abcdefgh"

        def sq(index: int) -> str:
            return f"{files[index % 8]}{index // 8 + 1}"

        text = f"{self.piece}{sq(self.square_from)}-{sq(self.square_to)}"
        if self.promotion_piece:
            text += f"={self.promotion_piece}"
        if self.is_castling:
            text += " (castling)"
        if self.is_en_passant:
            text += " (e.p.)"
        return text
