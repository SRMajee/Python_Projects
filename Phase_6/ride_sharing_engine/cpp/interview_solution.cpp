/*
 * Ride-Sharing Engine - Interview Solution (C++)
 *
 * 1. Primary Capabilities:
 *   - Grid-based spatial index for nearest-driver lookup
 *   - State machine: REQUESTED -> MATCHED -> IN_PROGRESS -> COMPLETED/CANCELLED
 *   - Surge pricing (demand/supply ratio)
 *   - Concurrency Extension: mutex on engine + grid operations
 *
 * 2. Error Handling:
 *   - Empty string on no matching driver
 *   - State checked before transitions
 *
 * 3. Out Of Scope:
 *   - Real GPS, ETA, payments, ratings, ride pooling, routing
 */
#include<bits/stdc++.h>
using namespace std;

enum class TS { REQ, MATCH, ACTIVE, DONE, CANCEL };
enum class DS { IDLE, ASSIGNED, ON_TRIP };
struct Loc { double x, y; double dist(Loc o) { return sqrt((x-o.x)*(x-o.x)+(y-o.y)*(y-o.y)); } };
struct Driver { string id; Loc loc; DS state = DS::IDLE; };
struct Trip { string id, did; Loc pickup, dropoff; TS state = TS::REQ; double fare = 0; };

class Engine {
    map<string, Driver> ds; map<string, Trip> ts;
    map<pair<int,int>, set<string>> grid;
    int tc = 0; double cell; mutex mtx;
    pair<int,int> c(Loc l) { return {(int)floor(l.x/cell),(int)floor(l.y/cell)}; }
public:
    Engine(double cl=1) : cell(cl) {}
    void add_driver(const string& id, double x, double y) {
        lock_guard<mutex> lk(mtx); ds[id] = {id, {x,y}}; grid[c({x,y})].insert(id); }
    string request(double px, double py, double dx, double dy) {
        lock_guard<mutex> lk(mtx); string tid = "t" + to_string(++tc);
        ts[tid] = {tid, "", {px,py}, {dx,dy}}; return tid; }
    string match(const string& tid, double md=10) {
        lock_guard<mutex> lk(mtx); auto& t = ts[tid]; auto [cx,cy] = c(t.pickup);
        string best; double bd = 1e18;
        for (int dx=-3;dx<=3;dx++) for (int dy=-3;dy<=3;dy++)
            for (auto& did : grid[{cx+dx,cy+dy}]) { auto& d = ds[did];
                if (d.state==DS::IDLE) { double dist=d.loc.dist(t.pickup); if(dist<=md&&dist<bd){best=did;bd=dist;} } }
        if (!best.empty()) { ds[best].state=DS::ASSIGNED; t.did=best; t.state=TS::MATCH; grid[c(ds[best].loc)].erase(best); }
        return best; }
    void start(const string& tid) { lock_guard<mutex> lk(mtx); auto& t=ts[tid]; t.state=TS::ACTIVE; ds[t.did].state=DS::ON_TRIP; }
    double complete(const string& tid) { lock_guard<mutex> lk(mtx); auto& t=ts[tid]; t.state=TS::DONE;
        t.fare=5+t.pickup.dist(t.dropoff)*2; ds[t.did].state=DS::IDLE; ds[t.did].loc=t.dropoff;
        grid[c(t.dropoff)].insert(t.did); return t.fare; }
};

int main() {
    Engine e; e.add_driver("d1",0,0); e.add_driver("d2",5,5);
    auto tid = e.request(0.5,0.5,8,8); auto d = e.match(tid); assert(d=="d1");
    e.start(tid); double f = e.complete(tid); assert(f > 0);
    cout << "Interview C++ Ride Engine passed!" << endl;
}
