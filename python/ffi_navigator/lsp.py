"""Data structures for language server protocol."""
import attr

@attr.s
class Position:
    line : int = attr.ib()
    character : int = attr.ib()

@attr.s
class Range:
    start : Position = attr.ib()
    end : Position = attr.ib()

@attr.s
class Location:
    uri : str = attr.ib()
    range : Range = attr.ib()
