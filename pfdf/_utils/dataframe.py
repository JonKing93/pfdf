"""
Functions to help build pandas.DataFrame objects
----------
Functions:
    table   - Returns a DataFrame for a data table
"""

from __future__ import annotations

import typing

from pandas import DataFrame

if typing.TYPE_CHECKING:
    from typing import Sequence

    Table = Sequence[Sequence]


def table(table: Table, columns: Sequence[str]) -> DataFrame:
    "Returns a pandas DataFrame for a data table of row tuples"
    index = []
    data = []
    for row in table:
        index.append(row[0])
        data.append(row[1:])
    return DataFrame(data, index, columns)
