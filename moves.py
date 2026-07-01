"""Move execution for jgchess.

This module provides apply_move(), which takes a Position and a fully
resolved Move and returns the new Position after the move is made.

Responsibility boundary:
    - Move.from_algebraic() resolves *what* the move is.
    - apply_move()          resolves *what the board looks like after* it.
"""

import config
from position import Position
from move import Move


def apply_move(position: Position, move: Move) -> Position:
    """Applies a fully resolved move to a position and returns the new position.

    Does not validate move legality (e.g. leaving king in check). The move
    is assumed to be legal, as guaranteed by Move.from_algebraic() when
    called from a PGN parser.

    Handles all special cases: castling, en passant, promotion, loss of
    castling rights, and the en passant target nibble for double pawn advances.

    Args:
        position: The current Position before the move.
        move: A fully resolved Move object.

    Returns:
        A new Position reflecting the board state after the move.
    """
    # Work on a shallow copy of squares — Position is immutable after construction
    squares: dict[int, int] = dict(position.squares)

    # ------------------------------------------------------------------
    # Before anything else, clear any existing en passant target nibble.
    # A pawn that moved two squares last turn is no longer vulnerable.
    # ------------------------------------------------------------------
    ep_squares = [
        sq for sq, n in squares.items()
        if n == config.NIBBLE_EN_PASSANT_TARGET
    ]
    for sq in ep_squares:
        squares[sq] = (
            config.NIBBLE_WHITE_PAWN
            if position.turn == 'b'   # last mover was White
            else config.NIBBLE_BLACK_PAWN
        )

    if move.is_castling:
        squares = _apply_castling(squares, move, position.turn)
    elif move.is_en_passant:
        squares = _apply_en_passant(squares, move, position.turn)
    elif move.promotion_piece is not None:
        squares = _apply_promotion(squares, move, position.turn)
    else:
        squares = _apply_normal(squares, move, position.turn)

    # ------------------------------------------------------------------
    # Update the White King nibble to reflect the new side to move.
    # ------------------------------------------------------------------
    squares = _flip_side_to_move(squares, position.turn)

    return Position.from_squares(squares)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _apply_normal(
    squares: dict[int, int],
    move: Move,
    turn: str,
) -> dict[int, int]:
    """Handles a standard move (no castling, en passant, or promotion).

    Also handles:
    - Loss of castling rights when a rook or king moves.
    - En passant target nibble when a pawn advances two squares.

    Args:
        squares: Mutable copy of the current squares dict.
        move: The move to apply.
        turn: Side to move ('w' or 'b').

    Returns:
        Updated squares dict.
    """
    nibble = squares.pop(move.square_from)

    # Pawn double advance — mark as en passant target
    if move.piece == 'P':
        rank_diff = abs(move.square_to // 8 - move.square_from // 8)
        if rank_diff == 2:
            nibble = config.NIBBLE_EN_PASSANT_TARGET

    # Rook moves — lose castling right
    if move.piece == 'R':
        nibble = (
            config.NIBBLE_WHITE_ROOK_NO_CASTLE
            if turn == 'w'
            else config.NIBBLE_BLACK_ROOK_NO_CASTLE
        )

    # King moves — nibble will be corrected by _flip_side_to_move;
    # use a temporary neutral nibble for now
    if move.piece == 'K':
        nibble = (
            config.NIBBLE_WHITE_KING_WHITE_TO_MOVE
            if turn == 'w'
            else config.NIBBLE_BLACK_KING
        )

    squares[move.square_to] = nibble
    return squares


def _apply_castling(
    squares: dict[int, int],
    move: Move,
    turn: str,
) -> dict[int, int]:
    """Handles a castling move — moves both king and rook.

    Args:
        squares: Mutable copy of the current squares dict.
        move: The castling move (king's origin and destination).
        turn: Side to move ('w' or 'b').

    Returns:
        Updated squares dict.
    """
    # Determine rook squares from king destination
    kingside = move.square_to > move.square_from

    if turn == 'w':
        rook_from = config.SQUARE_TO_INDEX['h1'] if kingside else config.SQUARE_TO_INDEX['a1']
        rook_to   = config.SQUARE_TO_INDEX['f1'] if kingside else config.SQUARE_TO_INDEX['d1']
        king_nibble = config.NIBBLE_WHITE_KING_WHITE_TO_MOVE  # corrected by flip later
        rook_nibble = config.NIBBLE_WHITE_ROOK_NO_CASTLE
    else:
        rook_from = config.SQUARE_TO_INDEX['h8'] if kingside else config.SQUARE_TO_INDEX['a8']
        rook_to   = config.SQUARE_TO_INDEX['f8'] if kingside else config.SQUARE_TO_INDEX['d8']
        king_nibble = config.NIBBLE_BLACK_KING
        rook_nibble = config.NIBBLE_BLACK_ROOK_NO_CASTLE

    # Move king
    squares.pop(move.square_from)
    squares[move.square_to] = king_nibble

    # Move rook — remove castling right
    squares.pop(rook_from)
    squares[rook_to] = rook_nibble

    return squares


def _apply_en_passant(
    squares: dict[int, int],
    move: Move,
    turn: str,
) -> dict[int, int]:
    """Handles an en passant capture.

    Removes the capturing pawn from its origin, places it on the
    destination, and removes the captured pawn from its actual square
    (which differs from the destination).

    Args:
        squares: Mutable copy of the current squares dict.
        move: The en passant move.
        turn: Side to move ('w' or 'b').

    Returns:
        Updated squares dict.
    """
    # Move the capturing pawn
    squares.pop(move.square_from)
    squares[move.square_to] = (
        config.NIBBLE_WHITE_PAWN if turn == 'w' else config.NIBBLE_BLACK_PAWN
    )

    # Remove the captured pawn — same file as destination, same rank as origin
    captured_rank = move.square_from // 8
    captured_file = move.square_to % 8
    captured_sq   = captured_rank * 8 + captured_file
    squares.pop(captured_sq, None)

    return squares


def _apply_promotion(
    squares: dict[int, int],
    move: Move,
    turn: str,
) -> dict[int, int]:
    """Handles a pawn promotion.

    Removes the pawn from its origin and places the promoted piece
    on the destination square with the correct nibble.

    Args:
        squares: Mutable copy of the current squares dict.
        move: The promotion move (promotion_piece is not None).
        turn: Side to move ('w' or 'b').

    Returns:
        Updated squares dict.
    """
    squares.pop(move.square_from)

    piece_to_nibble: dict[str, tuple[int, int]] = {
        'N': (config.NIBBLE_WHITE_KNIGHT, config.NIBBLE_BLACK_KNIGHT),
        'B': (config.NIBBLE_WHITE_BISHOP, config.NIBBLE_BLACK_BISHOP),
        'R': (config.NIBBLE_WHITE_ROOK_NO_CASTLE, config.NIBBLE_BLACK_ROOK_NO_CASTLE),
        'Q': (config.NIBBLE_WHITE_QUEEN, config.NIBBLE_BLACK_QUEEN),
    }
    white_nibble, black_nibble = piece_to_nibble[move.promotion_piece]
    squares[move.square_to] = white_nibble if turn == 'w' else black_nibble

    return squares


def _flip_side_to_move(squares: dict[int, int], turn: str) -> dict[int, int]:
    """Updates the White King nibble to reflect the new side to move.

    After any move, the side to move changes. The White King encodes
    this information in its nibble (12 = White to move, 13 = Black to move).

    Args:
        squares: Mutable squares dict after the move has been applied.
        turn: The side that just moved ('w' or 'b').

    Returns:
        Updated squares dict.
    """
    new_king_nibble = (
        config.NIBBLE_WHITE_KING_BLACK_TO_MOVE  # White just moved → Black to move
        if turn == 'w'
        else config.NIBBLE_WHITE_KING_WHITE_TO_MOVE  # Black just moved → White to move
    )
    for sq, nibble in squares.items():
        if nibble in config.WHITE_KING_NIBBLES:
            squares[sq] = new_king_nibble
            break

    return squares
