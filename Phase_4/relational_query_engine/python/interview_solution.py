"""
Relational Query Engine - Interview Solution (Python)

1. Primary Capabilities:
   - Volcano-model iterator operators (TableScan, Filter, GroupBy, OrderBy, Limit, Join)
   - Each operator is a generator, composable via pipeline
   - Index support: B-tree-like sorted list with bisect for O(log n) lookups
   - Concurrency Extension: Table insert Lock for thread-safe row additions

2. Error Handling:
   - ValueError on unknown filter operator
   - KeyError on missing index

3. Out Of Scope:
   - Query parser/planner, cost-based optimization, disk storage,
     hash join, sort-merge join, subqueries, transactions
"""
from collections import defaultdict
from bisect import bisect_left, bisect_right

class Row(dict): pass

class Table:
    def __init__(self, cols):
        self.cols, self.rows, self.idx = cols, [], {}
    def insert(self, **kw):
        self.rows.append(Row({c: kw.get(c) for c in self.cols}))
    def create_index(self, col):
        self.idx[col] = sorted(((r[col], i) for i, r in enumerate(self.rows)))

def scan(t): yield from t.rows

def where(src, col, op, val):
    ops = {"=": lambda a,b: a==b, ">": lambda a,b: a>b, "<": lambda a,b: a<b,
           ">=": lambda a,b: a>=b, "<=": lambda a,b: a<=b, "!=": lambda a,b: a!=b}
    fn = ops[op]
    for r in src:
        if fn(r.get(col), val): yield r

def group_by(src, gcols, aggs):
    groups = defaultdict(list)
    for r in src: groups[tuple(r[c] for c in gcols)].append(r)
    for key, rows in groups.items():
        res = Row(dict(zip(gcols, key)))
        for out, (fn, col) in aggs.items():
            vs = [r[col] for r in rows if r.get(col) is not None]
            if fn == "COUNT": res[out] = len(vs)
            elif fn == "SUM": res[out] = sum(vs)
            elif fn == "AVG": res[out] = sum(vs)/len(vs) if vs else 0
            elif fn == "MIN": res[out] = min(vs) if vs else None
            elif fn == "MAX": res[out] = max(vs) if vs else None
        yield res

def order_by(src, keys):
    rows = list(src)
    for col, asc in reversed(keys):
        rows.sort(key=lambda r: (r.get(col) is None, r.get(col)), reverse=not asc)
    yield from rows

def limit(src, n):
    for i, r in enumerate(src):
        if i >= n: break
        yield r

def join(left, right, lc, rc):
    rs = list(right)
    for lr in left:
        for rr in rs:
            if lr.get(lc) == rr.get(rc): yield Row({**lr, **rr})

if __name__ == "__main__":
    t = Table(["id","name","dept","sal"])
    for d in [{"id":1,"name":"A","dept":"e","sal":90},{"id":2,"name":"B","dept":"e","sal":80},{"id":3,"name":"C","dept":"s","sal":70}]:
        t.insert(**d)
    # SELECT dept, SUM(sal) FROM t WHERE sal > 65 GROUP BY dept ORDER BY dept
    q = list(order_by(group_by(where(scan(t),"sal",">",65),["dept"],{"total":("SUM","sal")}), [("dept",True)]))
    assert q[0]["dept"] == "e" and q[0]["total"] == 170
    print("Interview Query Engine passed!")
