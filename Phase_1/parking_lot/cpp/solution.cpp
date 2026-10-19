#include<bits/stdc++.h>
using namespace std;

enum class SpotSize { SMALL=1, MEDIUM=2, LARGE=3 };

class Vehicle {
protected: string license_plate;
public:
    Vehicle(string plate) : license_plate(move(plate)) {}
    virtual ~Vehicle() = default;
    const string& get_plate() const { return license_plate; }
    virtual SpotSize get_spot_size() const = 0;
    virtual double get_rate_multiplier() const = 0;
};

class Motorcycle : public Vehicle { public: using Vehicle::Vehicle;
    SpotSize get_spot_size() const override { return SpotSize::SMALL; }
    double get_rate_multiplier() const override { return 0.5; }
};
class Car : public Vehicle { public: using Vehicle::Vehicle;
    SpotSize get_spot_size() const override { return SpotSize::MEDIUM; }
    double get_rate_multiplier() const override { return 1.0; }
};
class Bus : public Vehicle { public: using Vehicle::Vehicle;
    SpotSize get_spot_size() const override { return SpotSize::LARGE; }
    double get_rate_multiplier() const override { return 2.0; }
};

struct Ticket { string id; int level; int spot_id; shared_ptr<Vehicle> vehicle; };

class ParkingSpot {
public:
    int id; SpotSize size; shared_ptr<Vehicle> vehicle{nullptr};
    ParkingSpot(int id_, SpotSize s) : id(id_), size(s) {}
    bool can_fit(const Vehicle& v) const { return !vehicle && (int)size >= (int)v.get_spot_size(); }
};

class ParkingLot {
    vector<vector<ParkingSpot>> levels;
    unordered_map<string, Ticket> tickets;
    double base_rate{20.0};
    mutex mtx;  // Concurrency: thread-safe park/unpark
public:
    ParkingLot(int num_levels, int sm, int md, int lg) {
        levels.resize(num_levels);
        for (int l=0; l<num_levels; ++l) {
            int id=1;
            for (int i=0;i<sm;++i) levels[l].emplace_back(id++, SpotSize::SMALL);
            for (int i=0;i<md;++i) levels[l].emplace_back(id++, SpotSize::MEDIUM);
            for (int i=0;i<lg;++i) levels[l].emplace_back(id++, SpotSize::LARGE);
        }
    }
    string park_vehicle(shared_ptr<Vehicle> v) {
        lock_guard<mutex> lk(mtx);
        ParkingSpot* best = nullptr; int best_lvl = -1;
        for (int l=0; l<(int)levels.size(); ++l)
            for (auto& s : levels[l])
                if (s.can_fit(*v) && (!best || s.size < best->size)) {
                    best = &s; best_lvl = l+1;
                    if (best->size == v->get_spot_size()) goto found;
                }
        found:
        if (!best) throw runtime_error("Parking lot full.");
        best->vehicle = v;
        string tid = "TICK-" + v->get_plate();
        tickets[tid] = {tid, best_lvl, best->id, v};
        return tid;
    }
    double unpark_vehicle(const string& tid, double hrs=2.0) {
        lock_guard<mutex> lk(mtx);
        auto it = tickets.find(tid);
        if (it == tickets.end()) throw runtime_error("Invalid ticket.");
        auto t = it->second; tickets.erase(it);
        levels[t.level-1][t.spot_id-1].vehicle = nullptr;
        return round(hrs * base_rate * t.vehicle->get_rate_multiplier() * 100.0) / 100.0;
    }
};

int main() {
    ParkingLot lot(1,1,1,1);
    auto car = make_shared<Car>("KA-01-1234");
    string t = lot.park_vehicle(car);
    assert(!t.empty());
    assert(lot.unpark_vehicle(t, 2.0) == 40.0);
    cout << "Complete C++ ParkingLot tests passed!" << endl;
}
