"""Pre-computed movement tables for jgchess.

All tables are generated once at module import time.
Squares are indexed 0-63: a1=0, b1=1, ..., h8=63.
File (column): square % 8  (0=a, 7=h)
Rank (row):    square // 8 (0=rank1, 7=rank8)

Sliding pieces (bishop, rook, queen) use lists of rays.
Each ray is an ordered list of squares from the piece outward.
Non-sliding pieces (knight, king) use flat lists.
"""

def _build_knight_moves() -> dict[int, list[int]]:
    """Builds the knight movement table.

    Returns:
        Mapping from square index to list of reachable squares.
    """
    offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
               (1, -2),  (1, 2),  (2, -1),  (2, 1)]
    table: dict[int, list[int]] = {}
    for sq in range(64):
        rank, file = divmod(sq, 8)
        targets = []
        for dr, df in offsets:
            r, f = rank + dr, file + df
            if 0 <= r <= 7 and 0 <= f <= 7:
                targets.append(r * 8 + f)
        table[sq] = targets
    return table

def _build_king_moves() -> dict[int, list[int]]:
    """Builds the king movement table (excluding castling).

    Returns:
        Mapping from square index to list of reachable squares.
    """
    offsets = [(-1, -1), (-1, 0), (-1, 1),
               (0,  -1),          (0,  1),
               (1,  -1), (1,  0), (1,  1)]
    table: dict[int, list[int]] = {}
    for sq in range(64):
        rank, file = divmod(sq, 8)
        targets = []
        for dr, df in offsets:
            r, f = rank + dr, file + df
            if 0 <= r <= 7 and 0 <= f <= 7:
                targets.append(r * 8 + f)
        table[sq] = targets
    return table

def _build_bishop_moves() -> dict[int, list[list[int]]]:
    """Builds the bishop movement table as diagonal rays.

    Each square maps to a list of 2-4 rays. Each ray is an ordered
    list of squares from the piece outward along one diagonal.

    Returns:
        Mapping from square index to list of rays.
    """
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    table: dict[int, list[list[int]]] = {}
    for sq in range(64):
        rank, file = divmod(sq, 8)
        rays = []
        for dr, df in directions:
            ray = []
            r, f = rank + dr, file + df
            while 0 <= r <= 7 and 0 <= f <= 7:
                ray.append(r * 8 + f)
                r += dr
                f += df
            if ray:
                rays.append(ray)
        table[sq] = rays
    return table

def _build_rook_moves() -> dict[int, list[list[int]]]:
    """Builds the rook movement table as orthogonal rays.

    Each square maps to a list of 2-4 rays. Each ray is an ordered
    list of squares from the piece outward along one file or rank.

    Returns:
        Mapping from square index to list of rays.
    """
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    table: dict[int, list[list[int]]] = {}
    for sq in range(64):
        rank, file = divmod(sq, 8)
        rays = []
        for dr, df in directions:
            ray = []
            r, f = rank + dr, file + df
            while 0 <= r <= 7 and 0 <= f <= 7:
                ray.append(r * 8 + f)
                r += dr
                f += df
            if ray:
                rays.append(ray)
        table[sq] = rays
    return table

def _build_queen_moves() -> dict[int, list[list[int]]]:
    """Builds the queen movement table as combined rays.

    The queen combines all bishop and rook rays from the same square.

    Returns:
        Mapping from square index to list of rays.
    """
    bishop = _build_bishop_moves()
    rook = _build_rook_moves()
    return {sq: bishop[sq] + rook[sq] for sq in range(64)}


# ---------------------------------------------------------------------------
# Module-level constants — computed once at import time
# ---------------------------------------------------------------------------

KNIGHT_MOVES: dict[int, list[int]]       = _build_knight_moves()
KING_MOVES:   dict[int, list[int]]       = _build_king_moves()
BISHOP_MOVES: dict[int, list[list[int]]] = _build_bishop_moves()
ROOK_MOVES:   dict[int, list[list[int]]] = _build_rook_moves()
QUEEN_MOVES:  dict[int, list[list[int]]] = _build_queen_moves()
