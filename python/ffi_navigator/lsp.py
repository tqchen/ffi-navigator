"""Data structures for language server protocol."""
import attr

@attr.s
class Position:
    line : int = attr.ib()
    character : int = attr.ib()

    def __lt__(self, other):
        if self.line < other.line:
            return True
        if self.line > other.line:
            return False
        if self.line > other.line:
            return False

@attr.s
class Range:
    start : Position = attr.ib()
    end : Position = attr.ib()

@attr.s
class Location:
    uri : str = attr.ib()
    range : Range = attr.ib()
