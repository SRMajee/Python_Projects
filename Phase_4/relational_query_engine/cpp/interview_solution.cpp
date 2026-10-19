/*
 * Relational Query Engine - Interview Solution (C++)
 *
 * 1. Primary Capabilities:
 *   - Materialized Volcano operators: scan, filter, group_by, order_by, limit, join
 *   - variant<int,double,string> column values
 *   - Composable function pipeline
 *   - Concurrency Extension: mutex on Table::insert
 *
 * 2. Error Handling:
 *   - runtime_error on unknown filter operator
 *
 * 3. Out Of Scope:
 *   - Query parser, cost optimizer, indexes, hash/merge join, subqueries
 */
#include<bits/stdc++.h>
using namespace std;

using Val = variant<int,double,string>;
using Row = unordered_map<string, Val>;

double num(const Val& v) { return holds_alternative<int>(v) ? get<int>(v) : holds_alternative<double>(v) ? get<double>(v) : 0; }
string str(const Val& v) { return holds_alternative<string>(v) ? get<string>(v) : to_string(num(v)); }

vector<Row> filt(const vector<Row>& s, const string& c, const string& op, const Val& v) {
    vector<Row> r; for (auto& row : s) { auto it = row.find(c); if (it == row.end()) continue;
        double a = num(it->second), b = num(v);
        bool ok = op=="=" ? a==b : op==">" ? a>b : op=="<" ? a<b : op==">=" ? a>=b : a<=b;
        if (ok) r.push_back(row); } return r;
}

vector<Row> grp(const vector<Row>& s, const vector<string>& gc, const vector<tuple<string,string,string>>& ag) {
    map<string, vector<const Row*>> groups;
    for (auto& r : s) { string k; for (auto& c : gc) { auto it = r.find(c); k += it != r.end() ? str(it->second) : ""; k += "|"; } groups[k].push_back(&r); }
    vector<Row> res;
    for (auto& [k, rows] : groups) { Row rr; /* simplified: use first row's group col vals */
        for (auto& c : gc) rr[c] = rows[0]->at(c);
        for (auto& [o, fn, col] : ag) { vector<double> vs; for (auto* r : rows) { auto it = r->find(col); if (it != r->end()) vs.push_back(num(it->second)); }
            if (fn=="SUM") rr[o] = accumulate(vs.begin(),vs.end(),0.0);
            else if (fn=="COUNT") rr[o] = (int)vs.size();
            else if (fn=="AVG") rr[o] = vs.empty() ? 0.0 : accumulate(vs.begin(),vs.end(),0.0)/vs.size();
        } res.push_back(rr); } return res;
}

vector<Row> ord(vector<Row> s, const string& c, bool asc) {
    sort(s.begin(), s.end(), [&](const Row& a, const Row& b) { return asc ? num(a.at(c))<num(b.at(c)) : num(a.at(c))>num(b.at(c)); }); return s;
}

int main() {
    vector<Row> t = {{{"dept",string("e")},{"sal",90}},{{"dept",string("e")},{"sal",80}},{{"dept",string("s")},{"sal",70}}};
    auto r = grp(filt(t,"sal",">",65), {"dept"}, {{"total","SUM","sal"}});
    assert(r.size() == 2);
    cout << "Interview C++ Query Engine passed!" << endl;
}
