"""Some type definitions for fixtures.

This should aid in the recognition of fixtures in the code.
"""
from pathlib import Path
from typing import Generic, TypeVar


T = TypeVar("T")


class Fixture(Generic[T]):
    """A generic fixture type."""


FixturePath = Fixture[Path]
