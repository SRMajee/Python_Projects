"""
Relational Query Engine - Complete Solution (Python)
Volcano-model iterator-based SQL query engine with:
- Table scan and index scan operators
- WHERE filter with comparison operators
- GROUP BY with aggregation (COUNT, SUM, AVG, MIN, MAX)
- ORDER BY with multi-key sorting
- LIMIT operator
- Simple INNER JOIN (nested-loop)
- B-Tree-like index for accelerated lookups
Concurrency: Not applicable (single-query executor), but Table insert uses Lock.
"""
import threading
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Iterator
from bisect import insort, bisect_left, bisect_right


class Row(dict):
    """A row is a dictionary of column_name -> value."""
    pass


class Operator(ABC):
    """Volcano-model iterator base."""
    @abstractmethod
    def __iter__(self) -> Iterator[Row]:
        ...


class Table:
    """In-memory columnar-ish table with optional B-tree indexes."""
    def __init__(self, name: str, columns: list[str]):
        self.name = name
        self.columns = columns
        self._rows: list[Row] = []
        self._indexes: dict[str, list[tuple[Any, int]]] = {}  # col -> sorted (val, row_idx)
        self._lock = threading.Lock()

    def insert(self, **kwargs) -> None:
        with self._lock:
            row = Row({c: kwargs.get(c) for c in self.columns})
            idx = len(self._rows)
            self._rows.append(row)
            for col, index_list in self._indexes.items():
                insort(index_list, (row[col], idx))

    def insert_many(self, rows: list[dict]) -> None:
        for r in rows:
            self.insert(**r)

    def create_index(self, column: str) -> None:
        if column not in self.columns:
            raise ValueError(f"Column '{column}' not in table")
        with self._lock:
            idx_list = [(self._rows[i][column], i) for i in range(len(self._rows))]
            idx_list.sort()
            self._indexes[column] = idx_list

    def scan(self) -> list[Row]:
        return list(self._rows)

    def index_scan(self, column: str, op: str, value: Any) -> list[Row]:
        if column not in self._indexes:
            raise KeyError(f"No index on '{column}'")
        idx = self._indexes[column]
        keys = [k for k, _ in idx]
        if op == "=":
            lo = bisect_left(keys, value)
            hi = bisect_right(keys, value)
            return [self._rows[idx[i][1]] for i in range(lo, hi)]
        elif op == ">":
            lo = bisect_right(keys, value)
            return [self._rows[idx[i][1]] for i in range(lo, len(idx))]
        elif op == ">=":
            lo = bisect_left(keys, value)
            return [self._rows[idx[i][1]] for i in range(lo, len(idx))]
        elif op == "<":
            hi = bisect_left(keys, value)
            return [self._rows[idx[i][1]] for i in range(0, hi)]
        elif op == "<=":
            hi = bisect_right(keys, value)
            return [self._rows[idx[i][1]] for i in range(0, hi)]
        raise ValueError(f"Unsupported operator: {op}")


class TableScan(Operator):
    def __init__(self, table: Table):
        self.table = table
    def __iter__(self):
        yield from self.table.scan()


class IndexScan(Operator):
    def __init__(self, table: Table, column: str, op: str, value: Any):
        self.table, self.column, self.op, self.value = table, column, op, value
    def __iter__(self):
        yield from self.table.index_scan(self.column, self.op, self.value)


class Filter(Operator):
    """WHERE clause: filter rows by predicate."""
    OPS = {"=": lambda a, b: a == b, "!=": lambda a, b: a != b,
           ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
           "<": lambda a, b: a < b, "<=": lambda a, b: a <= b}

    def __init__(self, source: Operator, column: str, op: str, value: Any):
        self.source = source
        self.column = column
        self.comparator = self.OPS.get(op)
        if not self.comparator:
            raise ValueError(f"Unknown operator: {op}")
        self.value = value

    def __iter__(self):
        for row in self.source:
            if self.comparator(row.get(self.column), self.value):
                yield row


class Project(Operator):
    """SELECT specific columns."""
    def __init__(self, source: Operator, columns: list[str]):
        self.source = source
        self.columns = columns
    def __iter__(self):
        for row in self.source:
            yield Row({c: row.get(c) for c in self.columns})


class GroupBy(Operator):
    """GROUP BY with aggregation functions."""
    AGG_FNS = {"COUNT", "SUM", "AVG", "MIN", "MAX"}

    def __init__(self, source: Operator, group_cols: list[str],
                 aggregations: dict[str, tuple[str, str]]):
        """aggregations: {output_col: (fn_name, source_col)}"""
        self.source = source
        self.group_cols = group_cols
        self.aggregations = aggregations

    def __iter__(self):
        groups: dict[tuple, list[Row]] = defaultdict(list)
        for row in self.source:
            key = tuple(row.get(c) for c in self.group_cols)
            groups[key].append(row)
        for key, rows in groups.items():
            result = Row({c: v for c, v in zip(self.group_cols, key)})
            for out_col, (fn, src_col) in self.aggregations.items():
                vals = [r[src_col] for r in rows if r.get(src_col) is not None]
                if fn == "COUNT": result[out_col] = len(vals)
                elif fn == "SUM": result[out_col] = sum(vals)
                elif fn == "AVG": result[out_col] = sum(vals) / len(vals) if vals else 0
                elif fn == "MIN": result[out_col] = min(vals) if vals else None
                elif fn == "MAX": result[out_col] = max(vals) if vals else None
            yield result


class OrderBy(Operator):
    """ORDER BY with multi-key sorting."""
    def __init__(self, source: Operator, keys: list[tuple[str, bool]]):
        """keys: [(column, ascending), ...]"""
        self.source = source
        self.keys = keys
    def __iter__(self):
        rows = list(self.source)
        for col, asc in reversed(self.keys):
            rows.sort(key=lambda r: (r.get(col) is None, r.get(col)), reverse=not asc)
        yield from rows


class Limit(Operator):
    def __init__(self, source: Operator, n: int):
        self.source = source
        self.n = n
    def __iter__(self):
        for i, row in enumerate(self.source):
            if i >= self.n: break
            yield row


class NestedLoopJoin(Operator):
    """INNER JOIN using nested-loop strategy."""
    def __init__(self, left: Operator, right: Operator, left_col: str, right_col: str):
        self.left, self.right = left, right
        self.left_col, self.right_col = left_col, right_col
    def __iter__(self):
        right_rows = list(self.right)
        for lr in self.left:
            for rr in right_rows:
                if lr.get(self.left_col) == rr.get(self.right_col):
                    merged = Row({**lr, **rr})
                    yield merged
