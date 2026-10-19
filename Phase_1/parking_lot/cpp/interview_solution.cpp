/*
 * Parking Lot - Interview Solution (C++)
 *
 * 1. Primary Capabilities:
 *   - Vehicle polymorphism (size + rate_multiplier)
 *   - Best-fit spot allocation (smallest compatible vacant spot)
 *   - Duration * base_rate * multiplier fee calculation
 *   - Concurrency Extension: mutex around park/unpark for thread-safe booking
 *
 * 2. Error Handling:
 *   - runtime_error on lot full or invalid ticket
 *
 * 3. Out Of Scope:
 *   - Barrier gates, payment gateways, slot reservations, persistent storage
 */
#include<bits/stdc++.h>
using namespace std;

enum class SpotSize { SMALL=1, MEDIUM=2, LARGE=3 };

struct Vehicle {
    string plate;
    virtual SpotSize size() const = 0;
    virtual double rate() const = 0;
    virtual ~Vehicle() = default;
};
struct Car : Vehicle { SpotSize size() const override { return SpotSize::MEDIUM; } double rate() const override { return 1.0; } };
struct Bike : Vehicle { SpotSize size() const override { return SpotSize::SMALL; } double rate() const override { return 0.5; } };
struct Bus : Vehicle { SpotSize size() const override { return SpotSize::LARGE; } double rate() const override { return 2.0; } };

class ParkingLot {
    vector<pair<SpotSize, shared_ptr<Vehicle>>> spots;
    unordered_map<string, pair<shared_ptr<Vehicle>, int>> tickets;
    double base{20.0};
    mutex mtx;  // Concurrency extension
public:
    ParkingLot(int sm, int md, int lg) {
        for (int i=0;i<sm;++i) spots.push_back({SpotSize::SMALL, nullptr});
        for (int i=0;i<md;++i) spots.push_back({SpotSize::MEDIUM, nullptr});
        for (int i=0;i<lg;++i) spots.push_back({SpotSize::LARGE, nullptr});
    }
    string park(shared_ptr<Vehicle> v) {
        lock_guard<mutex> lk(mtx);
        int best = -1;
        for (int i=0;i<(int)spots.size();++i)
            if (!spots[i].second && spots[i].first >= v->size())
                if (best<0 || spots[i].first < spots[best].first) { best=i; if (spots[i].first==v->size()) break; }
        if (best<0) throw runtime_error("Full");
        spots[best].second = v;
        string tid = "T-" + v->plate;
        tickets[tid] = {v, best};
        return tid;
    }
    double unpark(const string& tid, double hrs=1.0) {
        lock_guard<mutex> lk(mtx);
        auto it = tickets.find(tid);
        if (it==tickets.end()) throw runtime_error("Bad ticket");
        spots[it->second.second].second = nullptr;
        double fee = hrs * base * it->second.first->rate();
        tickets.erase(it);
        return fee;
    }
};

int main() {
    ParkingLot lot(1,1,1);
    auto c = make_shared<Car>(); c->plate = "KA01";
    string t = lot.park(c);
    assert(lot.unpark(t, 2.0) == 40.0);
    cout << "Interview C++ ParkingLot passed!" << endl;
}
