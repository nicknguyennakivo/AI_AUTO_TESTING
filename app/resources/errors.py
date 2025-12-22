from dataclasses import dataclass


@dataclass
class Errors:
    SOMETHING_WRONG: str = "An unexpected error"
    BAD_REQUEST: str = "Bad request"
    NOT_FOUND: str = "Not found"
