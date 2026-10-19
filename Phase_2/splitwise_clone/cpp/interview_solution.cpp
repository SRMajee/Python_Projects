/*
 * Splitwise Clone - Interview Solution (C++)
 *
 * 1. Primary Capabilities:
 *   - EQUAL, EXACT, PERCENT split strategies with balance ledger
 *   - Pairwise balance tracking via nested unordered_map
 *   - Concurrency Extension: mutex guards add_expense for thread-safe balance updates
 *
 * 2. Error Handling:
 *   - runtime_error if exact amounts don't sum to total or percentages don't sum to 100
 *
 * 3. Out Of Scope:
 *   - Min-cash-flow simplification, persistent storage, multi-currency support
 */
#include<bits/stdc++.h>
using namespace std;

enum class SplitType { EQUAL, EXACT, PERCENT };

class ExpenseManager {
    unordered_map<string, unordered_map<string, double>> balances;
    mutex mtx;
public:
    void add_expense(const string& paid_by, double total, SplitType type,
                     const vector<string>& participants,
                     const vector<double>& values = {}) {
        map<string, double> shares;
        if (type == SplitType::EQUAL) {
            double share = round(total / participants.size() * 100) / 100.0;
            for (auto& p : participants) shares[p] = share;
        } else if (type == SplitType::EXACT) {
            double sum = 0; for (auto v : values) sum += v;
            if (abs(sum - total) > 0.01) throw runtime_error("Sum mismatch");
            for (int i = 0; i < (int)participants.size(); ++i) shares[participants[i]] = values[i];
        } else {
            double sum = 0; for (auto v : values) sum += v;
            if (abs(sum - 100) > 0.01) throw runtime_error("Pct mismatch");
            for (int i = 0; i < (int)participants.size(); ++i)
                shares[participants[i]] = round(total * values[i] / 100.0 * 100) / 100.0;
        }
        lock_guard<mutex> lk(mtx);
        for (auto& [uid, amt] : shares) {
            if (uid == paid_by) continue;
            balances[uid][paid_by] += amt;
        }
    }
    double get_balance(const string& from, const string& to) { return balances[from][to]; }
};

int main() {
    ExpenseManager mgr;
    mgr.add_expense("u1", 300, SplitType::EQUAL, {"u1","u2","u3"});
    assert(abs(mgr.get_balance("u2","u1") - 100) < 0.01);
    mgr.add_expense("u1", 100, SplitType::PERCENT, {"u1","u2"}, {60, 40});
    assert(abs(mgr.get_balance("u2","u1") - 140) < 0.01);
    cout << "Interview C++ Splitwise passed!" << endl;
}
