use std::collections::HashMap;

#[derive(Debug)]
enum SplitType { Equal, Exact, Percent }

struct ExpenseManager {
    balances: HashMap<String, HashMap<String, f64>>,
}

impl ExpenseManager {
    fn new() -> Self { Self { balances: HashMap::new() } }

    fn add_expense(&mut self, paid_by: &str, total: f64, split_type: SplitType,
                   participants: &[&str], values: &[f64]) -> Result<(), String> {
        let shares: Vec<f64> = match split_type {
            SplitType::Equal => {
                let s = (total / participants.len() as f64 * 100.0).round() / 100.0;
                vec![s; participants.len()]
            }
            SplitType::Exact => {
                let sum: f64 = values.iter().sum();
                if (sum - total).abs() > 0.01 { return Err("Exact amounts must sum to total".into()); }
                values.to_vec()
            }
            SplitType::Percent => {
                let sum: f64 = values.iter().sum();
                if (sum - 100.0).abs() > 0.01 { return Err("Percentages must sum to 100".into()); }
                values.iter().map(|p| (total * p / 100.0 * 100.0).round() / 100.0).collect()
            }
        };
        for (i, &uid) in participants.iter().enumerate() {
            if uid == paid_by { continue; }
            *self.balances.entry(uid.to_string()).or_default()
                .entry(paid_by.to_string()).or_insert(0.0) += shares[i];
            *self.balances.entry(paid_by.to_string()).or_default()
                .entry(uid.to_string()).or_insert(0.0) -= shares[i];
        }
        Ok(())
    }

    fn get_balances(&self, uid: &str) -> Vec<(String, f64)> {
        self.balances.get(uid).map_or(vec![], |m|
            m.iter().filter(|(_,v)| v.abs() > 0.01).map(|(k,v)| (k.clone(), *v)).collect())
    }
}

fn main() {
    let mut mgr = ExpenseManager::new();
    mgr.add_expense("u1", 300.0, SplitType::Equal, &["u1","u2","u3"], &[]).unwrap();
    let bals = mgr.get_balances("u2");
    let owed = bals.iter().find(|(k,_)| k == "u1").unwrap().1;
    assert!((owed - 100.0).abs() < 0.01);
    mgr.add_expense("u2", 90.0, SplitType::Exact, &["u1","u2","u3"], &[30.0, 30.0, 30.0]).unwrap();
    mgr.add_expense("u3", 100.0, SplitType::Percent, &["u1","u2","u3"], &[50.0, 25.0, 25.0]).unwrap();
    println!("Complete Rust Splitwise tests passed!");
}
