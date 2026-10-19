/**
 * Parking Lot Design - Complete Solution with Tests (Rust)
 */

use std::collections::HashMap;
use std::time::Instant;

#[derive(Debug, PartialEq, Eq, PartialOrd, Ord, Clone, Copy)]
pub enum SpotSize { Small = 1, Medium = 2, Large = 3 }

#[derive(Debug, Clone, Copy)]
pub enum VehicleType { Motorcycle, Car, Bus }

impl VehicleType {
    pub fn required_spot_size(&self) -> SpotSize {
        match self {
            VehicleType::Motorcycle => SpotSize::Small,
            VehicleType::Car => SpotSize::Medium,
            VehicleType::Bus => SpotSize::Large,
        }
    }
    pub fn rate_multiplier(&self) -> f64 {
        match self {
            VehicleType::Motorcycle => 0.5,
            VehicleType::Car => 1.0,
            VehicleType::Bus => 2.0,
        }
    }
}

pub struct Vehicle {
    pub license_plate: String,
    pub vehicle_type: VehicleType,
}

pub struct Ticket {
    pub ticket_id: String,
    pub vehicle_type: VehicleType,
    pub level_idx: usize,
    pub spot_idx: usize,
    pub entry_time: Instant,
}

pub struct ParkingSpot {
    pub id: usize,
    pub size: SpotSize,
    pub is_occupied: bool,
}

pub struct ParkingLot {
    levels: Vec<Vec<ParkingSpot>>,
    active_tickets: HashMap<String, Ticket>,
    base_rate_per_hour: f64,
    total_spots: usize,
}

impl ParkingLot {
    pub fn new(levels: usize, small: usize, medium: usize, large: usize) -> Self {
        let mut all_levels = Vec::new();
        let mut total = 0;
        for _ in 0..levels {
            let mut spots = Vec::new();
            let mut id = 1;
            for _ in 0..small { spots.push(ParkingSpot { id, size: SpotSize::Small, is_occupied: false }); id += 1; }
            for _ in 0..medium { spots.push(ParkingSpot { id, size: SpotSize::Medium, is_occupied: false }); id += 1; }
            for _ in 0..large { spots.push(ParkingSpot { id, size: SpotSize::Large, is_occupied: false }); id += 1; }
            total += spots.len();
            all_levels.push(spots);
        }
        Self {
            levels: all_levels,
            active_tickets: HashMap::new(),
            base_rate_per_hour: 20.0,
            total_spots: total,
        }
    }

    pub fn park_vehicle(&mut self, vehicle: &Vehicle) -> Result<String, &'static str> {
        let req_size = vehicle.vehicle_type.required_spot_size();
        let mut best: Option<(usize, usize, SpotSize)> = None;

        for (l_idx, level) in self.levels.iter().enumerate() {
            for (s_idx, spot) in level.iter().enumerate() {
                if !spot.is_occupied && spot.size >= req_size {
                    match best {
                        None => best = Some((l_idx, s_idx, spot.size)),
                        Some((_, _, b_size)) if spot.size < b_size => {
                            best = Some((l_idx, s_idx, spot.size));
                        }
                        _ => {}
                    }
                    if spot.size == req_size { break; }
                }
            }
            if let Some((_, _, b_size)) = best {
                if b_size == req_size { break; }
            }
        }

        let (l_idx, s_idx, _) = best.ok_or("Parking lot full for vehicle type")?;
        self.levels[l_idx][s_idx].is_occupied = true;

        let ticket_id = format!("TICK-{}", vehicle.license_plate);
        self.active_tickets.insert(
            ticket_id.clone(),
            Ticket {
                ticket_id: ticket_id.clone(),
                vehicle_type: vehicle.vehicle_type,
                level_idx: l_idx,
                spot_idx: s_idx,
                entry_time: Instant::now(),
            },
        );
        Ok(ticket_id)
    }

    pub fn unpark_vehicle(&mut self, ticket_id: &str, simulated_hours: f64) -> Result<f64, &'static str> {
        let ticket = self.active_tickets.remove(ticket_id).ok_or("Invalid ticket ID")?;
        self.levels[ticket.level_idx][ticket.spot_idx].is_occupied = false;
        let fee = simulated_hours * self.base_rate_per_hour * ticket.vehicle_type.rate_multiplier();
        Ok((fee * 100.0).round() / 100.0)
    }
}

fn main() {
    let mut lot = ParkingLot::new(1, 1, 1, 1);
    let car = Vehicle {
        license_plate: "KA-05-9999".to_string(),
        vehicle_type: VehicleType::Car,
    };
    let ticket_id = lot.park_vehicle(&car).unwrap();
    let fee = lot.unpark_vehicle(&ticket_id, 3.0).unwrap();
    assert_eq!(fee, 60.0);
    println!("Complete Rust ParkingLot tests passed!");
}
