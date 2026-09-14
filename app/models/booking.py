from datetime import datetime
from app.extensions import db


class Booking(db.Model):
    """
    A confirmed seat reservation on a ride. Created once a RideRequest
    is accepted (or directly, for instant-join rides).
    """
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey("rides.id"), nullable=False)
    passenger_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    ride_request_id = db.Column(db.Integer, db.ForeignKey("ride_requests.id"), nullable=True)

    seats_booked = db.Column(db.Integer, nullable=False, default=1)
    fare = db.Column(db.Float, default=0.0)

    # confirmed -> cancelled -> completed
    status = db.Column(db.String(20), default="confirmed", index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    passenger = db.relationship("User", backref="bookings", foreign_keys=[passenger_id])

    def to_dict(self):
        return {
            "id": self.id,
            "ride_id": self.ride_id,
            "passenger_id": self.passenger_id,
            "passenger_name": self.passenger.name if self.passenger else None,
            "seats_booked": self.seats_booked,
            "fare": self.fare,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ride": self.ride.to_dict(include_driver=True) if self.ride else None,
        }

    def __repr__(self):
        return f"<Booking ride={self.ride_id} passenger={self.passenger_id} status={self.status}>"
