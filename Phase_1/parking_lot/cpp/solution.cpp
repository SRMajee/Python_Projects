/**
 * Parking Lot Design - Complete Solution with Tests (C++17)
 */

#include <iostream>
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <chrono>
#include <cmath>
#include <cassert>
#include <stdexcept>

enum class SpotSize { SMALL = 1, MEDIUM = 2, LARGE = 3 };

class Vehicle {
protected:
    std::string license_plate;
public:
    Vehicle(std::string plate) : license_plate(std::move(plate)) {}
    virtual ~Vehicle() = default;
    const std::string& get_plate() const { return license_plate; }
    virtual SpotSize get_spot_size() const = 0;
    virtual double get_rate_multiplier() const = 0;
};

class Motorcycle : public Vehicle {
public:
    using Vehicle::Vehicle;
    SpotSize get_spot_size() const override { return SpotSize::SMALL; }
    double get_rate_multiplier() const override { return 0.5; }
};

class Car : public Vehicle {
public:
    using Vehicle::Vehicle;
    SpotSize get_spot_size() const override { return SpotSize::MEDIUM; }
    double get_rate_multiplier() const override { return 1.0; }
};

class Bus : public Vehicle {
public:
    using Vehicle::Vehicle;
    SpotSize get_spot_size() const override { return SpotSize::LARGE; }
    double get_rate_multiplier() const override { return 2.0; }
};

struct Ticket {
    std::string ticket_id;
    int level;
    int spot_id;
    std::shared_ptr<Vehicle> vehicle;
    std::chrono::steady_clock::time_point entry_time;
};

class ParkingSpot {
public:
    int id;
    SpotSize size;
    std::shared_ptr<Vehicle> current_vehicle{nullptr};
    ParkingSpot(int id_, SpotSize size_) : id(id_), size(size_) {}
    bool can_fit(const Vehicle& v) const {
        return current_vehicle == nullptr && static_cast<int>(size) >= static_cast<int>(v.get_spot_size());
    }
};

class ParkingLot {
    std::vector<std::vector<ParkingSpot>> levels;
    std::unordered_map<std::string, Ticket> active_tickets;
    double base_rate_per_hour{20.0};
    int total_spots{0};

public:
    ParkingLot(int num_levels, int small_per_lvl, int med_per_lvl, int large_per_lvl) {
        levels.resize(num_levels);
        for (int l = 0; l < num_levels; ++l) {
            int spot_id = 1;
            for (int i = 0; i < small_per_lvl; ++i) levels[l].emplace_back(spot_id++, SpotSize::SMALL);
            for (int i = 0; i < med_per_lvl; ++i) levels[l].emplace_back(spot_id++, SpotSize::MEDIUM);
            for (int i = 0; i < large_per_lvl; ++i) levels[l].emplace_back(spot_id++, SpotSize::LARGE);
            total_spots += levels[l].size();
        }
    }

    std::string park_vehicle(std::shared_ptr<Vehicle> vehicle) {
        ParkingSpot* best_spot = nullptr;
        int best_level = -1;

        for (size_t l = 0; l < levels.size(); ++l) {
            for (auto& spot : levels[l]) {
                if (spot.can_fit(*vehicle)) {
                    if (!best_spot || spot.size < best_spot->size) {
                        best_spot = &spot;
                        best_level = static_cast<int>(l) + 1;
                        if (best_spot->size == vehicle->get_spot_size()) break;
                    }
                }
            }
            if (best_spot && best_spot->size == vehicle->get_spot_size()) break;
        }

        if (!best_spot) throw std::runtime_error("Parking lot full for vehicle type.");
        best_spot->current_vehicle = vehicle;
        std::string ticket_id = "TICK-" + vehicle->get_plate();
        active_tickets[ticket_id] = Ticket{ticket_id, best_level, best_spot->id, vehicle, std::chrono::steady_clock::now()};
        return ticket_id;
    }

    double unpark_vehicle(const std::string& ticket_id, double simulated_hours = 2.0) {
        auto it = active_tickets.find(ticket_id);
        if (it == active_tickets.end()) throw std::runtime_error("Invalid ticket ID.");

        Ticket t = it->second;
        active_tickets.erase(it);
        levels[t.level - 1][t.spot_id - 1].current_vehicle = nullptr;

        double fee = simulated_hours * base_rate_per_hour * t.vehicle->get_rate_multiplier();
        return std::round(fee * 100.0) / 100.0;
    }
};

int main() {
    ParkingLot lot(1, 1, 1, 1);
    auto car = std::make_shared<Car>("KA-01-1234");
    std::string t = lot.park_vehicle(car);
    assert(!t.empty());

    double fee = lot.unpark_vehicle(t, 2.0);
    assert(fee == 40.0);

    std::cout << "Complete C++ ParkingLot tests passed!" << std::endl;
    return 0;
}
