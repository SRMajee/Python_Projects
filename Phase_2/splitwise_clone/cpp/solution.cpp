#include<bits/stdc++.h>
using namespace std;

enum class SplitType { EQUAL, EXACT, PERCENT };

struct User { string id, name; };

class ExpenseManager {
    unordered_map<string, User> users;
    unordered_map<string, unordered_map<string, double>> balances;
    mutex mtx;
public:
    void add_user(const string& id, const string& name) { users[id] = {id, name}; }

    void add_expense(const string& paid_by, double total, SplitType type,
                     const vector<string>& parts, const vector<double>& vals = {}) {
        map<string,double> shares;
        if (type == SplitType::EQUAL) {
            double s = round(total / parts.size() * 100) / 100.0;
            for (auto& p : parts) shares[p] = s;
        } else if (type == SplitType::EXACT) {
            double sum=0; for (auto v:vals) sum+=v;
            if (abs(sum-total)>0.01) throw runtime_error("Sum mismatch");
            for (int i=0;i<(int)parts.size();++i) shares[parts[i]]=vals[i];
        } else {
            double sum=0; for (auto v:vals) sum+=v;
            if (abs(sum-100)>0.01) throw runtime_error("Pct mismatch");
            for (int i=0;i<(int)parts.size();++i) shares[parts[i]]=round(total*vals[i]/100*100)/100.0;
        }
        lock_guard<mutex> lk(mtx);
        for (auto& [uid,amt] : shares) {
            if (uid==paid_by) continue;
            balances[uid][paid_by] += amt;
            balances[paid_by][uid] -= amt;
        }
    }

    unordered_map<string,double> get_balances(const string& uid) {
        unordered_map<string,double> res;
        for (auto& [k,v] : balances[uid]) if (abs(v) > 0.01) res[k] = v;
        return res;
    }

    vector<tuple<string,string,double>> simplify_debts() {
        map<string,double> net;
        for (auto& uid : users) {
            double total=0; for (auto& [_,v]:balances[uid.first]) total+=v;
            if (abs(total)>0.01) net[uid.first]=total;
        }
        vector<pair<double,string>> creditors, debtors;
        for (auto& [k,v]:net) { if (v>0.01) debtors.push_back({v,k}); if (v<-0.01) creditors.push_back({v,k}); }
        sort(debtors.rbegin(), debtors.rend());
        sort(creditors.begin(), creditors.end());
        vector<tuple<string,string,double>> result;
        int i=0,j=0;
        while (i<(int)debtors.size() && j<(int)creditors.size()) {
            double settle = min(debtors[i].first, -creditors[j].first);
            result.push_back({debtors[i].second, creditors[j].second, round(settle*100)/100.0});
            debtors[i].first -= settle; creditors[j].first += settle;
            if (debtors[i].first<0.01) i++;
            if (creditors[j].first>-0.01) j++;
        }
        return result;
    }
};

int main() {
    ExpenseManager mgr;
    mgr.add_user("u1","Alice"); mgr.add_user("u2","Bob"); mgr.add_user("u3","Charlie");
    mgr.add_expense("u1", 300, SplitType::EQUAL, {"u1","u2","u3"});
    assert(abs(mgr.get_balances("u2")["u1"] - 100) < 0.01);
    mgr.add_expense("u2", 90, SplitType::EXACT, {"u1","u2","u3"}, {30,30,30});
    auto debts = mgr.simplify_debts();
    assert(!debts.empty());
    cout << "Complete C++ Splitwise tests passed!" << endl;
}
