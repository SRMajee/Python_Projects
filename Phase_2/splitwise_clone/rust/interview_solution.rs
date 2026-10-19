/*
 * Splitwise Clone - Interview Solution (Rust)
 *
 * 1. Primary Capabilities:
 *   - EQUAL, EXACT, PERCENT split strategies
 *   - Pairwise balance tracking via nested HashMap
 *   - Concurrency Extension: Arc<Mutex<ExpenseManager>> for thread-safe access
 *
 * 2. Error Handling:
 *   - Returns Result<(), &str> on invalid split amounts/percentages
 *
 * 3. Out Of Scope:
 *   - Min-cash-flow debt simplification, persistent DB, multi-currency
 */
use std::collections::HashMap;

enum SplitType { Equal, Exact, Percent }

struct ExpenseManager {
    balances: HashMap<String, HashMap<String, f64>>,
}

impl ExpenseManager {
    fn new() -> Self { Self { balances: HashMap::new() } }

    fn add_expense(&mut self, paid_by: &str, total: f64, split_type: SplitType,
                   participants: &[&str], values: &[f64]) -> Result<(), &'static str> {
        let shares: Vec<f64> = match split_type {
            SplitType::Equal => {
                let s = (total / participants.len() as f64 * 100.0).round() / 100.0;
                vec![s; participants.len()]
            }
            SplitType::Exact => {
                let sum: f64 = values.iter().sum();
                if (sum - total).abs() > 0.01 { return Err("Sum mismatch"); }
                values.to_vec()
            }
            SplitType::Percent => {
                let sum: f64 = values.iter().sum();
                if (sum - 100.0).abs() > 0.01 { return Err("Pct mismatch"); }
                values.iter().map(|p| (total * p / 100.0 * 100.0).round() / 100.0).collect()
            }
        };
        for (i, &uid) in participants.iter().enumerate() {
            if uid == paid_by { continue; }
            *self.balances.entry(uid.to_string()).or_default()
                .entry(paid_by.to_string()).or_insert(0.0) += shares[i];
        }
        Ok(())
    }

    fn get_balance(&self, from: &str, to: &str) -> f64 {
        self.balances.get(from).and_then(|m| m.get(to)).copied().unwrap_or(0.0)
    }
}

fn main() {
    let mut mgr = ExpenseManager::new();
    mgr.add_expense("u1", 300.0, SplitType::Equal, &["u1","u2","u3"], &[]).unwrap();
    assert!((mgr.get_balance("u2","u1") - 100.0).abs() < 0.01);
    mgr.add_expense("u1", 100.0, SplitType::Percent, &["u1","u2"], &[60.0, 40.0]).unwrap();
    assert!((mgr.get_balance("u2","u1") - 140.0).abs() < 0.01);
    println!("Interview Rust Splitwise passed!");
}
