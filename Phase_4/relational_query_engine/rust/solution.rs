//! Relational Query Engine - Complete Solution (Rust)
//! Volcano-model operators: scan, filter, group_by, order_by, limit, join.
//! Concurrency: Mutex on Table for thread-safe inserts.

use std::collections::HashMap;
use std::sync::Mutex;

#[derive(Debug, Clone, PartialEq, PartialOrd)]
enum Val { Int(i64), Float(f64), Str(String) }

impl Val {
    fn as_f64(&self) -> f64 {
        match self { Val::Int(i) => *i as f64, Val::Float(f) => *f, Val::Str(_) => 0.0 }
    }
    fn as_str(&self) -> String {
        match self { Val::Int(i) => i.to_string(), Val::Float(f) => f.to_string(), Val::Str(s) => s.clone() }
    }
}

type Row = HashMap<String, Val>;

struct Table {
    columns: Vec<String>,
    rows: Mutex<Vec<Row>>,
}
impl Table {
    fn new(cols: Vec<&str>) -> Self {
        Self { columns: cols.into_iter().map(|s| s.into()).collect(), rows: Mutex::new(Vec::new()) }
    }
    fn insert(&self, row: Row) { self.rows.lock().unwrap().push(row); }
    fn scan(&self) -> Vec<Row> { self.rows.lock().unwrap().clone() }
}

fn filter(src: Vec<Row>, col: &str, op: &str, val: &Val) -> Vec<Row> {
    src.into_iter().filter(|r| {
        r.get(col).map_or(false, |v| {
            let a = v.as_f64(); let b = val.as_f64();
            match op { "=" => a == b, ">" => a > b, "<" => a < b, ">=" => a >= b, "<=" => a <= b, "!=" => a != b, _ => false }
        })
    }).collect()
}

fn group_by(src: Vec<Row>, gcols: &[&str], aggs: &[(&str, &str, &str)]) -> Vec<Row> {
    let mut groups: HashMap<Vec<String>, Vec<Row>> = HashMap::new();
    for r in src {
        let key: Vec<String> = gcols.iter().map(|c| r.get(*c).map_or(String::new(), |v| v.as_str())).collect();
        groups.entry(key).or_default().push(r);
    }
    groups.into_iter().map(|(key, rows)| {
        let mut res = Row::new();
        for (i, c) in gcols.iter().enumerate() { res.insert(c.to_string(), Val::Str(key[i].clone())); }
        for &(out, func, col) in aggs {
            let vals: Vec<f64> = rows.iter().filter_map(|r| r.get(col).map(|v| v.as_f64())).collect();
            let v = match func {
                "COUNT" => Val::Int(vals.len() as i64),
                "SUM" => Val::Float(vals.iter().sum()),
                "AVG" => Val::Float(if vals.is_empty() { 0.0 } else { vals.iter().sum::<f64>() / vals.len() as f64 }),
                "MIN" => Val::Float(vals.iter().cloned().fold(f64::INFINITY, f64::min)),
                "MAX" => Val::Float(vals.iter().cloned().fold(f64::NEG_INFINITY, f64::max)),
                _ => Val::Int(0),
            };
            res.insert(out.to_string(), v);
        }
        res
    }).collect()
}

fn order_by(mut src: Vec<Row>, col: &str, asc: bool) -> Vec<Row> {
    src.sort_by(|a, b| {
        let va = a.get(col).map_or(0.0, |v| v.as_f64());
        let vb = b.get(col).map_or(0.0, |v| v.as_f64());
        if asc { va.partial_cmp(&vb).unwrap() } else { vb.partial_cmp(&va).unwrap() }
    });
    src
}

fn limit(src: Vec<Row>, n: usize) -> Vec<Row> { src.into_iter().take(n).collect() }

fn join(left: Vec<Row>, right: &[Row], lc: &str, rc: &str) -> Vec<Row> {
    let mut result = Vec::new();
    for lr in &left {
        for rr in right {
            if lr.get(lc).map(|v| v.as_str()) == rr.get(rc).map(|v| v.as_str()) {
                let mut merged = lr.clone();
                for (k, v) in rr { merged.insert(k.clone(), v.clone()); }
                result.push(merged);
            }
        }
    }
    result
}

fn row(pairs: Vec<(&str, Val)>) -> Row { pairs.into_iter().map(|(k,v)| (k.to_string(), v)).collect() }

fn main() {
    let t = Table::new(vec!["id","name","dept","salary"]);
    t.insert(row(vec![("id",Val::Int(1)),("name",Val::Str("Alice".into())),("dept",Val::Str("eng".into())),("salary",Val::Int(90000))]));
    t.insert(row(vec![("id",Val::Int(2)),("name",Val::Str("Bob".into())),("dept",Val::Str("eng".into())),("salary",Val::Int(85000))]));
    t.insert(row(vec![("id",Val::Int(3)),("name",Val::Str("Carol".into())),("dept",Val::Str("sales".into())),("salary",Val::Int(70000))]));
    t.insert(row(vec![("id",Val::Int(4)),("name",Val::Str("Dave".into())),("dept",Val::Str("sales".into())),("salary",Val::Int(75000))]));
    t.insert(row(vec![("id",Val::Int(5)),("name",Val::Str("Eve".into())),("dept",Val::Str("eng".into())),("salary",Val::Int(95000))]));

    let all = t.scan();
    assert_eq!(all.len(), 5);

    let eng = filter(all.clone(), "dept", "=", &Val::Str("eng".into()));
    assert_eq!(eng.len(), 3);

    let grouped = group_by(all.clone(), &["dept"], &[("total","SUM","salary"),("cnt","COUNT","id")]);
    assert_eq!(grouped.len(), 2);

    let sorted = order_by(all.clone(), "salary", false);
    assert_eq!(sorted[0].get("salary").unwrap().as_f64(), 95000.0);

    let lim = limit(all.clone(), 2);
    assert_eq!(lim.len(), 2);

    // Join
    let dept_t = Table::new(vec!["dept_name","floor"]);
    dept_t.insert(row(vec![("dept_name",Val::Str("eng".into())),("floor",Val::Int(3))]));
    dept_t.insert(row(vec![("dept_name",Val::Str("sales".into())),("floor",Val::Int(1))]));
    let joined = join(all.clone(), &dept_t.scan(), "dept", "dept_name");
    assert_eq!(joined.len(), 5);

    // Complex: WHERE salary>70000 GROUP BY dept ORDER BY total DESC LIMIT 1
    let q = limit(order_by(group_by(filter(all, "salary", ">", &Val::Int(70000)),
        &["dept"], &[("total","SUM","salary")]), "total", false), 1);
    assert_eq!(q.len(), 1);

    println!("Complete Rust Query Engine tests passed!");
}
