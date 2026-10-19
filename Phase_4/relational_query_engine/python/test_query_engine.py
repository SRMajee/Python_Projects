"""Tests for Relational Query Engine."""
import unittest
from query_engine import (Table, TableScan, IndexScan, Filter, Project,
                          GroupBy, OrderBy, Limit, NestedLoopJoin, Row)


class TestQueryEngine(unittest.TestCase):
    def setUp(self):
        self.employees = Table("employees", ["id", "name", "dept", "salary"])
        data = [
            {"id": 1, "name": "Alice", "dept": "eng", "salary": 90000},
            {"id": 2, "name": "Bob", "dept": "eng", "salary": 85000},
            {"id": 3, "name": "Carol", "dept": "sales", "salary": 70000},
            {"id": 4, "name": "Dave", "dept": "sales", "salary": 75000},
            {"id": 5, "name": "Eve", "dept": "eng", "salary": 95000},
        ]
        self.employees.insert_many(data)
        self.employees.create_index("dept")
        self.employees.create_index("salary")

    def test_table_scan(self):
        rows = list(TableScan(self.employees))
        self.assertEqual(len(rows), 5)

    def test_filter(self):
        q = Filter(TableScan(self.employees), "dept", "=", "eng")
        rows = list(q)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(r["dept"] == "eng" for r in rows))

    def test_index_scan_eq(self):
        rows = list(IndexScan(self.employees, "dept", "=", "eng"))
        self.assertEqual(len(rows), 3)

    def test_index_scan_range(self):
        rows = list(IndexScan(self.employees, "salary", ">", 80000))
        self.assertEqual(len(rows), 3)  # Alice(90k), Bob(85k), Eve(95k)

    def test_project(self):
        q = Project(TableScan(self.employees), ["name", "salary"])
        rows = list(q)
        self.assertEqual(set(rows[0].keys()), {"name", "salary"})

    def test_group_by(self):
        q = GroupBy(
            TableScan(self.employees),
            group_cols=["dept"],
            aggregations={"total_salary": ("SUM", "salary"), "count": ("COUNT", "id")}
        )
        rows = list(q)
        eng = next(r for r in rows if r["dept"] == "eng")
        self.assertEqual(eng["total_salary"], 270000)
        self.assertEqual(eng["count"], 3)

    def test_order_by(self):
        q = OrderBy(TableScan(self.employees), [("salary", False)])
        rows = list(q)
        self.assertEqual(rows[0]["name"], "Eve")
        self.assertEqual(rows[-1]["name"], "Carol")

    def test_limit(self):
        q = Limit(TableScan(self.employees), 2)
        rows = list(q)
        self.assertEqual(len(rows), 2)

    def test_join(self):
        depts = Table("depts", ["dept_name", "floor"])
        depts.insert(dept_name="eng", floor=3)
        depts.insert(dept_name="sales", floor=1)
        q = NestedLoopJoin(
            TableScan(self.employees), TableScan(depts),
            "dept", "dept_name"
        )
        rows = list(q)
        self.assertEqual(len(rows), 5)
        eng_rows = [r for r in rows if r["dept"] == "eng"]
        self.assertTrue(all(r["floor"] == 3 for r in eng_rows))

    def test_complex_query(self):
        """SELECT dept, AVG(salary) as avg_sal FROM employees
           WHERE salary > 70000 GROUP BY dept ORDER BY avg_sal DESC LIMIT 1"""
        q = Limit(
            OrderBy(
                GroupBy(
                    Filter(TableScan(self.employees), "salary", ">", 70000),
                    ["dept"],
                    {"avg_sal": ("AVG", "salary")}
                ),
                [("avg_sal", False)]
            ),
            1
        )
        rows = list(q)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["dept"], "eng")

    def test_invalid_filter_op(self):
        with self.assertRaises(ValueError):
            Filter(TableScan(self.employees), "salary", "LIKE", 100)

    def test_index_not_found(self):
        with self.assertRaises(KeyError):
            list(IndexScan(self.employees, "name", "=", "Alice"))


if __name__ == "__main__":
    unittest.main()
