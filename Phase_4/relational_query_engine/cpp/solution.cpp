#include<bits/stdc++.h>
using namespace std;

using Row = unordered_map<string, variant<int, double, string>>;

double to_double(const variant<int,double,string>& v) {
    if (holds_alternative<int>(v)) return get<int>(v);
    if (holds_alternative<double>(v)) return get<double>(v);
    return 0;
}

string to_string_val(const variant<int,double,string>& v) {
    if (holds_alternative<int>(v)) return to_string(get<int>(v));
    if (holds_alternative<double>(v)) return to_string(get<double>(v));
    return get<string>(v);
}

bool compare(const variant<int,double,string>& a, const variant<int,double,string>& b, const string& op) {
    double da = to_double(a), db = to_double(b);
    if (op == "=") return da == db;
    if (op == ">") return da > db;
    if (op == "<") return da < db;
    if (op == ">=") return da >= db;
    if (op == "<=") return da <= db;
    if (op == "!=") return da != db;
    throw runtime_error("Unknown op: " + op);
}

class Table {
    string name_;
    vector<string> columns_;
    vector<Row> rows_;
    mutex mtx;
public:
    Table(const string& name, vector<string> cols) : name_(name), columns_(move(cols)) {}
    void insert(Row row) { lock_guard<mutex> lk(mtx); rows_.push_back(move(row)); }
    const vector<Row>& rows() const { return rows_; }
    const vector<string>& columns() const { return columns_; }
};

// Operators return vector<Row> (materialized for simplicity in C++)
vector<Row> scan(Table& t) { return t.rows(); }

vector<Row> filter(const vector<Row>& src, const string& col, const string& op, const variant<int,double,string>& val) {
    vector<Row> result;
    for (auto& r : src) {
        auto it = r.find(col);
        if (it != r.end() && compare(it->second, val, op))
            result.push_back(r);
    }
    return result;
}

vector<Row> project(const vector<Row>& src, const vector<string>& cols) {
    vector<Row> result;
    for (auto& r : src) {
        Row nr;
        for (auto& c : cols) { auto it = r.find(c); if (it != r.end()) nr[c] = it->second; }
        result.push_back(move(nr));
    }
    return result;
}

vector<Row> group_by(const vector<Row>& src, const vector<string>& gcols,
                     const vector<tuple<string,string,string>>& aggs) {
    // aggs: (output_col, fn, source_col)
    map<vector<string>, vector<const Row*>> groups;
    for (auto& r : src) {
        vector<string> key;
        for (auto& c : gcols) { auto it = r.find(c); key.push_back(it != r.end() ? to_string_val(it->second) : ""); }
        groups[key].push_back(&r);
    }
    vector<Row> result;
    for (auto& [key, rows] : groups) {
        Row res;
        for (int i = 0; i < (int)gcols.size(); i++) res[gcols[i]] = key[i];
        for (auto& [out, fn, col] : aggs) {
            vector<double> vals;
            for (auto* r : rows) { auto it = r->find(col); if (it != r->end()) vals.push_back(to_double(it->second)); }
            if (fn == "COUNT") res[out] = (int)vals.size();
            else if (fn == "SUM") res[out] = accumulate(vals.begin(), vals.end(), 0.0);
            else if (fn == "AVG") res[out] = vals.empty() ? 0.0 : accumulate(vals.begin(), vals.end(), 0.0) / vals.size();
            else if (fn == "MIN") res[out] = *min_element(vals.begin(), vals.end());
            else if (fn == "MAX") res[out] = *max_element(vals.begin(), vals.end());
        }
        result.push_back(move(res));
    }
    return result;
}

vector<Row> order_by(vector<Row> src, const vector<pair<string,bool>>& keys) {
    for (auto it = keys.rbegin(); it != keys.rend(); ++it) {
        auto& [col, asc] = *it;
        sort(src.begin(), src.end(), [&](const Row& a, const Row& b) {
            auto ia = a.find(col), ib = b.find(col);
            if (ia == a.end()) return !asc;
            if (ib == b.end()) return asc;
            return asc ? to_double(ia->second) < to_double(ib->second)
                       : to_double(ia->second) > to_double(ib->second);
        });
    }
    return src;
}

vector<Row> limit_rows(const vector<Row>& src, int n) {
    return vector<Row>(src.begin(), src.begin() + min((int)src.size(), n));
}

vector<Row> nested_loop_join(const vector<Row>& left, const vector<Row>& right,
                              const string& lcol, const string& rcol) {
    vector<Row> result;
    for (auto& lr : left) {
        for (auto& rr : right) {
            auto il = lr.find(lcol), ir = rr.find(rcol);
            if (il != lr.end() && ir != rr.end() && to_string_val(il->second) == to_string_val(ir->second)) {
                Row merged = lr;
                for (auto& [k, v] : rr) merged[k] = v;
                result.push_back(move(merged));
            }
        }
    }
    return result;
}

int main() {
    Table emp("employees", {"id","name","dept","salary"});
    emp.insert({{"id",1},{"name",string("Alice")},{"dept",string("eng")},{"salary",90000}});
    emp.insert({{"id",2},{"name",string("Bob")},{"dept",string("eng")},{"salary",85000}});
    emp.insert({{"id",3},{"name",string("Carol")},{"dept",string("sales")},{"salary",70000}});
    emp.insert({{"id",4},{"name",string("Dave")},{"dept",string("sales")},{"salary",75000}});
    emp.insert({{"id",5},{"name",string("Eve")},{"dept",string("eng")},{"salary",95000}});

    // Table scan
    auto all = scan(emp);
    assert(all.size() == 5);

    // Filter: dept = eng
    auto eng = filter(all, "dept", "=", string("eng"));
    assert(eng.size() == 3);

    // GroupBy: dept, SUM(salary)
    auto grouped = group_by(all, {"dept"}, {{"total", "SUM", "salary"}, {"cnt", "COUNT", "id"}});
    assert(grouped.size() == 2);

    // OrderBy: salary DESC
    auto sorted_rows = order_by(all, {{"salary", false}});
    assert(to_double(sorted_rows[0]["salary"]) == 95000);

    // Limit
    auto limited = limit_rows(all, 2);
    assert(limited.size() == 2);

    // Join
    Table depts("depts", {"dept_name","floor"});
    depts.insert({{"dept_name",string("eng")},{"floor",3}});
    depts.insert({{"dept_name",string("sales")},{"floor",1}});
    auto joined = nested_loop_join(all, scan(depts), "dept", "dept_name");
    assert(joined.size() == 5);

    // Complex: WHERE sal>70000, GROUP BY dept, ORDER BY total DESC, LIMIT 1
    auto q = limit_rows(order_by(group_by(filter(all, "salary", ">", 70000),
        {"dept"}, {{"total", "SUM", "salary"}}), {{"total", false}}), 1);
    assert(q.size() == 1);
    assert(to_string_val(q[0]["dept"]) == "eng");

    cout << "Complete C++ Query Engine tests passed!" << endl;
}
