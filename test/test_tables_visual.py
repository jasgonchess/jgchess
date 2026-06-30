"""Quick visual test for tables.py — prints all movement tables."""

import tables

INDEX_TO_SQUARE = {
    sq: f"{'abcdefgh'[sq % 8]}{sq // 8 + 1}"
    for sq in range(64)
}


def print_flat_table(name: str, table: dict[int, list[int]]) -> None:
    """Prints a flat movement table (knight or king).

    Args:
        name: Display name for the table.
        table: Mapping from square index to list of target squares.
    """
    print(f"\n{'=' * 60}")
    print(f"  {name}")
    print(f"{'=' * 60}")
    for sq in range(64):
        targets = [INDEX_TO_SQUARE[t] for t in table[sq]]
        print(f"  {INDEX_TO_SQUARE[sq]:>3} ({sq:>2}): {targets}")


def print_ray_table(name: str, table: dict[int, list[list[int]]]) -> None:
    """Prints a ray-based movement table (bishop, rook, or queen).

    Args:
        name: Display name for the table.
        table: Mapping from square index to list of rays.
    """
    print(f"\n{'=' * 60}")
    print(f"  {name}")
    print(f"{'=' * 60}")
    for sq in range(64):
        rays = [[INDEX_TO_SQUARE[t] for t in ray] for ray in table[sq]]
        print(f"  {INDEX_TO_SQUARE[sq]:>3} ({sq:>2}): {rays}")


if __name__ == "__main__":
    print_flat_table("KNIGHT_MOVES", tables.KNIGHT_MOVES)
    print_flat_table("KING_MOVES",   tables.KING_MOVES)
    print_ray_table ("BISHOP_MOVES", tables.BISHOP_MOVES)
    print_ray_table ("ROOK_MOVES",   tables.ROOK_MOVES)
    print_ray_table ("QUEEN_MOVES",  tables.QUEEN_MOVES)
