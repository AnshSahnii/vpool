from datetime import datetime
from app.extensions import db


class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    vehicle_type = db.Column(db.String(30), nullable=False)  # Car / Bike / Auto
    brand = db.Column(db.String(80), nullable=False)
    model = db.Column(db.String(80), nullable=False)
    registration_number = db.Column(db.String(30), unique=True, nullable=False)
    total_seats = db.Column(db.Integer, nullable=False)  # seats available for passengers
    color = db.Column(db.String(30), nullable=True)

    # VPOOL 2.0: fuel type, used for eco-friendly filtering + CO2 savings estimate
    fuel_type = db.Column(db.String(20), default="Petrol")  # Petrol/Diesel/CNG/Electric/Hybrid

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    rides = db.relationship("Ride", backref="vehicle", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "vehicle_type": self.vehicle_type,
            "brand": self.brand,
            "model": self.model,
            "registration_number": self.registration_number,
            "total_seats": self.total_seats,
            "color": self.color,
            "fuel_type": self.fuel_type,
        }

    def __repr__(self):
        return f"<Vehicle {self.registration_number}>"
