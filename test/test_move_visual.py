"""Visual test for Move.from_algebraic — run from the project directory.

Tests the first moves of Fischer vs Spassky (1992) from the starting
position, plus a few edge cases (disambiguation, invalid move, ambiguity).
"""

from models import Position
from move import Move
from exceptions import InvalidMoveException

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def test(label: str, token: str, pos: Position) -> None:
    """Attempts to parse a move and prints the result or the exception.

    Args:
        label: Description shown in the output line.
        token: Algebraic notation string to parse.
        pos: Current position.
    """
    try:
        move = Move.from_algebraic(token, pos)
        print(f"  OK  {label:30} {token:10} -> {move}")
    except InvalidMoveException as exc:
        print(f"  EX  {label:30} {token:10} -> InvalidMoveException: {exc}")
    except ValueError as exc:
        print(f"  EX  {label:30} {token:10} -> ValueError: {exc}")


if __name__ == "__main__":
    pos = Position.from_fen(STARTING_FEN)

    print("\n--- Valid moves from starting position (White to move) ---")
    test("pawn to e4",            "e4",    pos)
    test("pawn to d4",            "d4",    pos)
    test("knight g1 to f3",       "Nf3",   pos)
    test("knight b1 to c3",       "Nc3",   pos)
    test("pawn to e4 with check", "e4+",   pos)   # '+' must be stripped

    print("\n--- Invalid moves from starting position ---")
    test("bishop to b5 (blocked)", "Bb5",  pos)   # no path for bishop
    test("queen to e4 (blocked)",  "Qe4",  pos)   # queen blocked
    test("pawn to e5 (too far)",   "e5",   pos)   # white pawn cannot reach e5
    test("knight to d2 (no such)", "Nd2",  pos)   # no knight can go to d2

    print("\n--- Castling (not available from starting position) ---")
    test("kingside castling",      "O-O",  pos)   # rook nibble won't match
    test("queenside castling",     "O-O-O",pos)

    print("\n--- Malformed input ---")
    test("empty string",           "",     pos)
    test("garbage",                "Zx9",  pos)
