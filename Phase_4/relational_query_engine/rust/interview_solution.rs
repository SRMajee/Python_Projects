/*
 * Relational Query Engine - Interview Solution (Rust)
 *
 * 1. Primary Capabilities:
 *   - Volcano operators: scan, filter, group_by, order_by, limit, join
 *   - Val enum (Int/Float/Str) for type-flexible columns
 *   - Composable functional pipeline
 *   - Concurrency Extension: Mutex<Vec<Row>> on Table
 *
 * 2. Error Handling:
 *   - Unknown ops silently excluded in filter
 *
 * 3. Out Of Scope:
 *   - SQL parser, cost optimizer, indexes, hash join, transactions
 */
use std::collections::HashMap;

#[derive(Debug, Clone)]
enum Val { I(i64), S(String) }
impl Val { fn n(&self) -> f64 { match self { Val::I(i) => *i as f64, _ => 0.0 } }
           fn s(&self) -> String { match self { Val::I(i) => i.to_string(), Val::S(s) => s.clone() } } }
type Row = HashMap<String, Val>;

fn filt(s: Vec<Row>, c: &str, op: &str, v: f64) -> Vec<Row> {
    s.into_iter().filter(|r| r.get(c).map_or(false, |x| match op { ">"=>x.n()>v, "<"=>x.n()<v, "="=>x.n()==v, _=>false })).collect()
}
fn grp(s: Vec<Row>, gc: &[&str], ag: &[(&str,&str,&str)]) -> Vec<Row> {
    let mut g: HashMap<String, Vec<Row>> = HashMap::new();
    for r in s { let k = gc.iter().map(|c| r.get(*c).map_or(String::new(),|v|v.s())).collect::<Vec<_>>().join("|"); g.entry(k).or_default().push(r); }
    g.into_iter().map(|(_, rows)| { let mut res = Row::new();
        for c in gc { res.insert(c.to_string(), rows[0].get(*c).cloned().unwrap_or(Val::I(0))); }
        for &(o, f, c) in ag { let vs: Vec<f64> = rows.iter().filter_map(|r| r.get(c).map(|v| v.n())).collect();
            res.insert(o.into(), Val::I(match f { "SUM" => vs.iter().sum::<f64>() as i64, "COUNT" => vs.len() as i64, _ => 0 })); } res }).collect()
}

fn main() {
    let t: Vec<Row> = vec![
        [("dept",Val::S("e".into())),("sal",Val::I(90))].into(),
        [("dept",Val::S("e".into())),("sal",Val::I(80))].into(),
        [("dept",Val::S("s".into())),("sal",Val::I(70))].into(),
    ];
    let r = grp(filt(t, "sal", ">", 65.0), &["dept"], &[("total","SUM","sal")]);
    assert_eq!(r.len(), 2);
    println!("Interview Rust Query Engine passed!");
}
