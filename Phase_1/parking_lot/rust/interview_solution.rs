/**
 * Parking Lot Design - Concise Interview Solution (Rust)
 *
 * 1. Primary Capabilities:
 * - Enum-based type safety for VehicleType and SpotSize with zero overhead.
 * - Best-fit vacant spot lookup algorithm.
 * - Ticket tracking with duration-based fee calculation.
 *
 * 2. Error Handling:
 * - Returns Result<String, &'static str> returning Err("Parking lot full!") on capacity limit.
 * - Returns Result<f64, &'static str> returning Err("Invalid ticket") on unparking.
 *
 * 3. Out Of Scope:
 * - Hardware barrier integration.
 * - Atomic lock-free concurrent reservation.
 */

use std::collections::HashMap;

#[derive(Debug, PartialEq, Eq, PartialOrd, Ord, Clone, Copy)]
pub enum SpotSize { Small = 1, Medium = 2, Large = 3 }

#[derive(Clone, Copy)]
pub enum VehicleType { Motorcycle, Car, Bus }

impl VehicleType {
    pub fn size(&self) -> SpotSize {
        match self { VehicleType::Motorcycle => SpotSize::Small, VehicleType::Car => SpotSize::Medium, VehicleType::Bus => SpotSize::Large }
    }
    pub fn rate_multiplier(&self) -> f64 {
        match self { VehicleType::Motorcycle => 0.5, VehicleType::Car => 1.0, VehicleType::Bus => 2.0 }
    }
}

pub struct ParkingLot {
    spots: Vec<(SpotSize, bool)>, // (Size, is_occupied)
    tickets: HashMap<String, (VehicleType, usize)>, // ticket_id -> (type, spot_idx)
    base_rate: f64,
}

impl ParkingLot {
    pub fn new(sm: usize, md: usize, lg: usize) -> Self {
        let mut spots = Vec::new();
        for _ in 0..sm { spots.push((SpotSize::Small, false)); }
        for _ in 0..md { spots.push((SpotSize::Medium, false)); }
        for _ in 0..lg { spots.push((SpotSize::Large, false)); }
        Self { spots, tickets: HashMap::new(), base_rate: 20.0 }
    }

    pub fn park(&mut self, plate: &str, v_type: VehicleType) -> Result<String, &'static str> {
        let req = v_type.size();
        let mut best_idx = None;

        for (idx, &(size, occ)) in self.spots.iter().enumerate() {
            if !occ && size >= req {
                match best_idx {
                    None => best_idx = Some(idx),
                    Some(b) if size < self.spots[b].0 => best_idx = Some(idx),
                    _ => {}
                }
                if size == req { break; }
            }
        }

        let idx = best_idx.ok_or("Parking lot full!")?;
        self.spots[idx].1 = true;
        let tid = format!("TICK-{}", plate);
        self.tickets.insert(tid.clone(), (v_type, idx));
        Ok(tid)
    }

    pub fn unpark(&mut self, tid: &str, hours: f64) -> Result<f64, &'static str> {
        let (v_type, idx) = self.tickets.remove(tid).ok_or("Invalid ticket")?;
        self.spots[idx].1 = false;
        Ok(hours * self.base_rate * v_type.rate_multiplier())
    }
}

fn main() {
    let mut lot = ParkingLot::new(1, 1, 1);
    let tid = lot.park("KA-01-1234", VehicleType::Car).unwrap();
    let fee = lot.unpark(&tid, 2.0).unwrap();
    assert_eq!(fee, 40.0);
    println!("Interview Rust ParkingLot passed!");
}
