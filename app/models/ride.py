from datetime import datetime
from app.extensions import db


class Ride(db.Model):
    __tablename__ = "rides"

    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)

    pickup_location = db.Column(db.String(255), nullable=False)
    pickup_lat = db.Column(db.Float, nullable=True)
    pickup_lng = db.Column(db.Float, nullable=True)

    destination = db.Column(db.String(255), nullable=False)
    destination_lat = db.Column(db.Float, nullable=True)
    destination_lng = db.Column(db.Float, nullable=True)

    distance_km = db.Column(db.Float, nullable=True)
    departure_time = db.Column(db.DateTime, nullable=False, index=True)

    total_seats = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    price_per_seat = db.Column(db.Float, default=0.0)

    # --- VPOOL 2.0 additions (kept simple on purpose) ---
    # "now" = instant ride, "scheduled" = planned for later
    ride_type = db.Column(db.String(20), default="scheduled")

    # Pooling: ride can wait until enough passengers join
    min_passengers = db.Column(db.Integer, default=1)  # 1 = no waiting required
    current_passengers = db.Column(db.Integer, default=0)  # counts confirmed bookings' seats

    # Fare engine output (calculated automatically, driver can still override price_per_seat)
    market_fare = db.Column(db.Float, nullable=True)      # what a typical cab app might charge
    suggested_fare = db.Column(db.Float, nullable=True)   # VPOOL's recommended pooled fare

    # Environmental impact estimate (kg of CO2 saved vs everyone driving separately)
    co2_saved_kg = db.Column(db.Float, nullable=True)

    # scheduled -> ongoing -> completed / cancelled
    status = db.Column(db.String(20), default="scheduled", index=True)
    notes = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ride_requests = db.relationship("RideRequest", backref="ride", lazy=True, cascade="all, delete-orphan")
    bookings = db.relationship("Booking", backref="ride", lazy=True, cascade="all, delete-orphan")

    def to_dict(self, include_driver=True):
        data = {
            "id": self.id,
            "driver_id": self.driver_id,
            "vehicle_id": self.vehicle_id,
            "pickup_location": self.pickup_location,
            "pickup_lat": self.pickup_lat,
            "pickup_lng": self.pickup_lng,
            "destination": self.destination,
            "destination_lat": self.destination_lat,
            "destination_lng": self.destination_lng,
            "distance_km": self.distance_km,
            "departure_time": self.departure_time.isoformat() if self.departure_time else None,
            "total_seats": self.total_seats,
            "available_seats": self.available_seats,
            "price_per_seat": self.price_per_seat,
            "ride_type": self.ride_type,
            "min_passengers": self.min_passengers,
            "current_passengers": self.current_passengers,
            "market_fare": self.market_fare,
            "suggested_fare": self.suggested_fare,
            "co2_saved_kg": self.co2_saved_kg,
            "pool_ready": self.current_passengers >= self.min_passengers,
            "status": self.status,
            "notes": self.notes,
        }
        if include_driver and self.driver:
            data["driver"] = {
                "id": self.driver.id,
                "name": self.driver.name,
                "phone": self.driver.phone,
                "organization": self.driver.organization,
            }
        if self.vehicle:
            data["vehicle"] = self.vehicle.to_dict()
        return data

    def __repr__(self):
        return f"<Ride {self.id} {self.pickup_location} -> {self.destination}>"
