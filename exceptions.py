# exceptions.py

"""Custom exception hierarchy for jgchess.

Every exception raised intentionally by jgchess inherits from
ChessDBException. This lets calling code choose its granularity:

    try:
        ...
    except InvalidFENException:
        # handle this specific failure
        ...
    except ChessDBException:
        # catch-all for any other jgchess-raised error
        ...

Each exception carries the contextual data relevant to its failure
(the offending FEN string, square index, position id, etc.) as plain
attributes, in addition to the human-readable message passed to
Exception. This keeps log messages informative and lets callers
inspect *what* failed programmatically, not just read a string.
"""


class ChessDBException(Exception):
    """Base exception for the entire jgchess ecosystem.

    All other jgchess exceptions inherit from this class. Catching
    ChessDBException distinguishes errors raised intentionally by
    jgchess from unrelated/unexpected errors (bugs, third-party
    failures) that should not be silently swallowed.
    """


class InvalidFENException(ChessDBException):
    """Raised when a FEN string is malformed or semantically invalid.

    Attributes:
        fen_string: The offending FEN string, if available.
    """

    def __init__(self, message: str, fen_string: str | None = None) -> None:
        super().__init__(message)
        self.fen_string = fen_string

    def __str__(self) -> str:
        base = super().__str__()
        if self.fen_string is not None:
            return f"{base} (fen_string={self.fen_string!r})"
        return base


class InvalidMoveException(ChessDBException):
    """Raised when a move cannot be parsed or resolved against a position.

    Covers unparsable algebraic notation, ambiguous PGN tokens lacking
    disambiguation, moves with no legal origin square, and castling
    requested without the corresponding right in the current position.

    Attributes:
        move_text: The original move string being parsed, if available.
    """

    def __init__(self, message: str, move_text: str | None = None) -> None:
        super().__init__(message)
        self.move_text = move_text

    def __str__(self) -> str:
        base = super().__str__()
        if self.move_text is not None:
            return f"{base} (move_text={self.move_text!r})"
        return base


class InvalidPositionException(ChessDBException):
    """Raised when a Position or its underlying data is structurally invalid.

    Examples: an out-of-range square index, a nibble value outside
    0-15, a squares dict with no White King, or any other internal
    inconsistency detected while building or encoding a Position.

    Attributes:
        square: The offending board square index (0-63), if applicable.
        nibble: The offending nibble value, if applicable.
    """

    def __init__(
        self,
        message: str,
        square: int | None = None,
        nibble: int | None = None,
    ) -> None:
        super().__init__(message)
        self.square = square
        self.nibble = nibble

    def __str__(self) -> str:
        base = super().__str__()
        details = []
        if self.square is not None:
            details.append(f"square={self.square}")
        if self.nibble is not None:
            details.append(f"nibble={self.nibble}")
        if details:
            return f"{base} ({', '.join(details)})"
        return base


class DatabaseException(ChessDBException):
    """Base class for all database-related errors.

    Raised directly for generic/unclassified database failures.
    Prefer the more specific subclasses below (DatabaseConnectionException,
    DatabaseIntegrityException) when the failure mode is known, so that
    callers can react differently to "could not reach the database" versus
    "the database returned corrupt data".
    """


class DatabaseConnectionException(DatabaseException):
    """Raised when the SQLite database file cannot be opened or connected to.

    Typically caused by an invalid path, missing permissions, or a
    locked/corrupted database file.

    Attributes:
        db_path: The path of the database that could not be opened.
    """

    def __init__(self, message: str, db_path: str | None = None) -> None:
        super().__init__(message)
        self.db_path = db_path

    def __str__(self) -> str:
        base = super().__str__()
        if self.db_path is not None:
            return f"{base} (db_path={self.db_path!r})"
        return base


class DatabaseIntegrityException(DatabaseException):
    """Raised when data read from the database is structurally corrupt.

    Example: a pieces BLOB whose length is inconsistent with the
    bitboard's population count for a given record.

    Attributes:
        position_id: The id of the offending position record, if known.
    """

    def __init__(self, message: str, position_id: int | None = None) -> None:
        super().__init__(message)
        self.position_id = position_id

    def __str__(self) -> str:
        base = super().__str__()
        if self.position_id is not None:
            return f"{base} (position_id={self.position_id})"
        return base
