# utils.py

"""Utility functions for jgchess."""

import config

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


