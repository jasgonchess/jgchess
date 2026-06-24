# validators.py

"""Input validation functions for jgchess."""


def is_valid_fen(fen_string: str) -> bool:
    """Performs robust syntactic and structural validation on a FEN string.

    Checks performed:
        - Correct type and non-empty string
        - Exactly 6 space-separated fields
        - Board field: exactly 8 ranks, each summing to 8 squares
        - Board field: only legal characters
        - Active color: 'w' or 'b'
        - Castling: valid characters, no duplicates
        - En passant: '-' or a valid target square for the active color
        - Halfmove and fullmove clocks: non-negative integers

    Args:
        fen_string: The FEN string to validate.

    Returns:
        True if the FEN string is structurally and semantically valid,
        False otherwise.
    """
    if not isinstance(fen_string, str) or not fen_string.strip():
        return False

    parts = fen_string.strip().split()
    if len(parts) != 6:
        return False

    board_fen, turn, castling, en_passant, halfmove, fullmove = parts

    # --- Field 1: board ranks ---
    ranks = board_fen.split('/')
    if len(ranks) != 8:
        return False

    valid_piece_chars = set("pnbrqkPNBRQK")
    white_kings = 0
    black_kings = 0

    for rank in ranks:
        square_count = 0
        for char in rank:
            if char.isdigit():
                digit = int(char)
                if digit < 1 or digit > 8:
                    return False
                square_count += digit
            elif char in valid_piece_chars:
                square_count += 1
                if char == 'K':
                    white_kings += 1
                elif char == 'k':
                    black_kings += 1
            else:
                return False
        if square_count != 8:
            return False

    if white_kings != 1 or black_kings != 1:
        return False

    # --- Field 2: active color ---
    if turn not in ('w', 'b'):
        return False

    # --- Field 3: castling availability ---
    if castling != '-':
        valid_castling_chars = set("KQkq")
        if not set(castling).issubset(valid_castling_chars):
            return False
        if len(castling) != len(set(castling)):  # no duplicate letters
            return False

    # --- Field 4: en passant target square ---
    if en_passant != '-':
        if len(en_passant) != 2:
            return False
        ep_file, ep_rank = en_passant[0], en_passant[1]
        if ep_file not in 'abcdefgh':
            return False
        # White just moved: en passant square must be on rank 3
        # Black just moved: en passant square must be on rank 6
        expected_rank = '3' if turn == 'b' else '6'
        if ep_rank != expected_rank:
            return False

    # --- Fields 5 and 6: move counters ---
    try:
        if int(halfmove) < 0 or int(fullmove) < 1:
            return False
    except ValueError:
        return False

    return True