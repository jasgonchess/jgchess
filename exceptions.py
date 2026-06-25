# exceptions.py

class ChessDBException(Exception):
    """Base exception for the entire chess database ecosystem."""
    pass

class InvalidFENException(ChessDBException):
    """Raised when the provided FEN string is malformed or corrupted."""
    pass

class DatabaseException(Exception):
    """Raised when a database operation fails."""
    pass

class InvalidMoveException(ChessDBException):
    """Raised when the provided move is invalid."""
    pass

class InvalidPositionException(ChessDBException):
    """Raised when the provided position is invalid."""
    pass
