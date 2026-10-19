/**
 * Parking Lot Design - Concise Interview Solution (C++17)
 *
 * 1. Primary Capabilities:
 * - Class hierarchy with virtual methods for vehicle dimensions and rates.
 * - Best-fit spot assignment across multi-level structures.
 * - Dynamic fee calculation with rate multipliers.
 *
 * 2. Error Handling:
 * - Throws std::runtime_error("Parking lot full!") when no compatible spots are vacant.
 * - Throws std::runtime_error("Invalid ticket") on unparking unknown tickets.
 *
 * 3. Out Of Scope:
 * - Thread safety and barrier mutex synchronization.
 * - Persistent ticket database.
 */

#include <iostream>
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <cassert>
#include <stdexcept>

enum class SpotSize { SMALL = 1, MEDIUM = 2, LARGE = 3 };

class Vehicle {
public:
    std::string plate;
    Vehicle(std::string p) : plate(std::move(p)) {}
    virtual ~Vehicle() = default;
    virtual SpotSize size() const = 0;
    virtual double multiplier() const = 0;
};

class Car : public Vehicle {
public:
    using Vehicle::Vehicle;
    SpotSize size() const override { return SpotSize::MEDIUM; }
    double multiplier() const override { return 1.0; }
};

struct Ticket {
    std::string id;
    std::shared_ptr<Vehicle> vehicle;
    int spot_idx;
};

class ParkingLot {
    std::vector<std::pair<SpotSize, std::shared_ptr<Vehicle>>> spots;
    std::unordered_map<std::string, Ticket> tickets;
    double base_rate{20.0};

public:
    ParkingLot(int sm, int md, int lg) {
        for (int i = 0; i < sm; ++i) spots.push_back({SpotSize::SMALL, nullptr});
        for (int i = 0; i < md; ++i) spots.push_back({SpotSize::MEDIUM, nullptr});
        for (int i = 0; i < lg; ++i) spots.push_back({SpotSize::LARGE, nullptr});
    }

    std::string park(std::shared_ptr<Vehicle> v) {
        int best_idx = -1;
        for (size_t i = 0; i < spots.size(); ++i) {
            if (!spots[i].second && spots[i].first >= v->size()) {
                if (best_idx == -1 || spots[i].first < spots[best_idx].first) {
                    best_idx = i;
                    if (spots[i].first == v->size()) break;
                }
            }
        }
        if (best_idx == -1) throw std::runtime_error("Parking lot full!");
        spots[best_idx].second = v;
        std::string tid = "TICK-" + v->plate;
        tickets[tid] = {tid, v, best_idx};
        return tid;
    }

    double unpark(const std::string& tid, double hours = 2.0) {
        auto it = tickets.find(tid);
        if (it == tickets.end()) throw std::runtime_error("Invalid ticket");
        spots[it->second.spot_idx].second = nullptr;
        double fee = hours * base_rate * it->second.vehicle->multiplier();
        tickets.erase(it);
        return fee;
    }
};

int main() {
    ParkingLot lot(1, 1, 1);
    auto car = std::make_shared<Car>("KA-01-1234");
    std::string t = lot.park(car);
    assert(!t.empty());
    assert(lot.unpark(t, 2.0) == 40.0);
    std::cout << "Interview C++ ParkingLot passed!" << std::endl;
    return 0;
}
