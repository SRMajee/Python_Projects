#include<bits/stdc++.h>
using namespace std;

enum class TripState { REQUESTED, MATCHED, IN_PROGRESS, COMPLETED, CANCELLED };
enum class DriverState { IDLE, ASSIGNED, ON_TRIP, OFFLINE };

struct Loc {
    double x, y;
    double dist(const Loc& o) const { return sqrt((x-o.x)*(x-o.x)+(y-o.y)*(y-o.y)); }
};

struct Driver { string id, name; Loc loc; DriverState state = DriverState::IDLE; };
struct Trip { string id, rider_id; Loc pickup, dropoff; string driver_id; TripState state = TripState::REQUESTED; double fare = 0; };

class SpatialGrid {
    double cell;
    map<pair<int,int>, set<string>> grid;
    map<string, pair<int,int>> driver_cells;
    mutex mtx;
    pair<int,int> cell_of(const Loc& l) { return {(int)floor(l.x/cell), (int)floor(l.y/cell)}; }
public:
    SpatialGrid(double c = 1.0) : cell(c) {}
    void update(const string& did, const Loc& loc) {
        lock_guard<mutex> lk(mtx);
        if (driver_cells.count(did)) grid[driver_cells[did]].erase(did);
        auto c = cell_of(loc); grid[c].insert(did); driver_cells[did] = c;
    }
    void remove(const string& did) {
        lock_guard<mutex> lk(mtx);
        if (driver_cells.count(did)) { grid[driver_cells[did]].erase(did); driver_cells.erase(did); }
    }
    vector<string> nearby(const Loc& loc, int radius = 3) {
        lock_guard<mutex> lk(mtx);
        auto [cx, cy] = cell_of(loc);
        vector<string> result;
        for (int dx = -radius; dx <= radius; dx++)
            for (int dy = -radius; dy <= radius; dy++)
                for (auto& id : grid[{cx+dx, cy+dy}]) result.push_back(id);
        return result;
    }
};

class RideEngine {
    map<string, Driver> drivers;
    map<string, Trip> trips;
    SpatialGrid grid;
    int trip_counter = 0;
    mutex mtx;
public:
    RideEngine(double cell = 1.0) : grid(cell) {}

    void register_driver(const string& id, const string& name, double x, double y) {
        lock_guard<mutex> lk(mtx);
        drivers[id] = {id, name, {x, y}, DriverState::IDLE};
        grid.update(id, {x, y});
    }

    string request_ride(const string& rider, double px, double py, double dx, double dy) {
        lock_guard<mutex> lk(mtx);
        string tid = "trip_" + to_string(++trip_counter);
        trips[tid] = {tid, rider, {px, py}, {dx, dy}, "", TripState::REQUESTED, 0};
        return tid;
    }

    string match_driver(const string& tid, double max_dist = 10.0) {
        lock_guard<mutex> lk(mtx);
        auto& trip = trips[tid];
        auto nearby = grid.nearby(trip.pickup);
        string best; double bd = 1e18;
        for (auto& did : nearby) {
            auto& d = drivers[did];
            if (d.state == DriverState::IDLE) {
                double dist = d.loc.dist(trip.pickup);
                if (dist <= max_dist && dist < bd) { best = did; bd = dist; }
            }
        }
        if (!best.empty()) {
            drivers[best].state = DriverState::ASSIGNED;
            trip.driver_id = best; trip.state = TripState::MATCHED;
            grid.remove(best);
        }
        return best;
    }

    void start_trip(const string& tid) {
        lock_guard<mutex> lk(mtx);
        auto& t = trips[tid]; t.state = TripState::IN_PROGRESS;
        drivers[t.driver_id].state = DriverState::ON_TRIP;
    }

    double complete_trip(const string& tid) {
        lock_guard<mutex> lk(mtx);
        auto& t = trips[tid]; t.state = TripState::COMPLETED;
        double dist = t.pickup.dist(t.dropoff);
        t.fare = 5.0 + dist * 2.0;
        auto& d = drivers[t.driver_id];
        d.state = DriverState::IDLE; d.loc = t.dropoff;
        grid.update(d.id, d.loc);
        return t.fare;
    }

    void cancel_trip(const string& tid) {
        lock_guard<mutex> lk(mtx);
        auto& t = trips[tid];
        if (!t.driver_id.empty()) { drivers[t.driver_id].state = DriverState::IDLE; grid.update(t.driver_id, drivers[t.driver_id].loc); }
        t.state = TripState::CANCELLED;
    }

    TripState get_trip_state(const string& tid) { lock_guard<mutex> lk(mtx); return trips[tid].state; }
};

int main() {
    RideEngine e;
    e.register_driver("d1", "Alice", 0, 0);
    e.register_driver("d2", "Bob", 5, 5);
    e.register_driver("d3", "Carol", 10, 10);

    // Request & match nearest
    auto tid = e.request_ride("r1", 0.5, 0.5, 8, 8);
    auto did = e.match_driver(tid);
    assert(did == "d1");
    assert(e.get_trip_state(tid) == TripState::MATCHED);

    // Full lifecycle
    e.start_trip(tid);
    assert(e.get_trip_state(tid) == TripState::IN_PROGRESS);
    double fare = e.complete_trip(tid);
    assert(fare > 0);
    assert(e.get_trip_state(tid) == TripState::COMPLETED);

    // No driver available
    auto tid2 = e.request_ride("r2", 100, 100, 200, 200);
    auto did2 = e.match_driver(tid2, 5.0);
    assert(did2.empty());

    // Cancel
    auto tid3 = e.request_ride("r3", 5, 5, 10, 10);
    e.match_driver(tid3);
    e.cancel_trip(tid3);
    assert(e.get_trip_state(tid3) == TripState::CANCELLED);

    // Thread safety
    {
        RideEngine e2;
        for (int i = 0; i < 20; i++)
            e2.register_driver("td" + to_string(i), "T", i * 1.0, i * 1.0);
        vector<thread> threads;
        atomic<int> matched{0};
        for (int i = 0; i < 10; i++) {
            threads.emplace_back([&e2, i, &matched] {
                auto t = e2.request_ride("r" + to_string(i), i * 1.0, i * 1.0, i + 5.0, i + 5.0);
                if (!e2.match_driver(t, 5.0).empty()) matched++;
            });
        }
        for (auto& t : threads) t.join();
        assert(matched > 0);
    }

    cout << "Complete C++ Ride Engine tests passed!" << endl;
}
