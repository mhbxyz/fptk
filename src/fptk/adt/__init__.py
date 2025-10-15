"""Algebraic Data Types for functional programming.

This module provides immutable, composable data structures for handling
optional values, results, collections, and now monadic computations.
"""

from fptk.adt.nelist import NonEmptyList
from fptk.adt.option import NOTHING, Option, Some, from_nullable
from fptk.adt.reader import Reader, ask, local
from fptk.adt.result import Err, Ok, Result
from fptk.adt.state import State, get, gets, modify, put
from fptk.adt.writer import Writer, censor, listen, monoid_list, monoid_str, tell

__all__ = [
    "Option",
    "Some",
    "NOTHING",
    "from_nullable",
    "Result",
    "Ok",
    "Err",
    "NonEmptyList",
    "Reader",
    "ask",
    "local",
    "State",
    "get",
    "put",
    "modify",
    "gets",
    "Writer",
    "tell",
    "listen",
    "censor",
    "monoid_list",
    "monoid_str",
]
