from datetime import datetime
from app.extensions import db


class RideRequest(db.Model):
    """
    A passenger's request to join a ride. Once approved by the driver
    (or auto-approved, depending on business rule), a Booking is created.
    """
    __tablename__ = "ride_requests"

    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey("rides.id"), nullable=False)
    passenger_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    seats_requested = db.Column(db.Integer, nullable=False, default=1)
    pickup_point = db.Column(db.String(255), nullable=True)

    # pending -> accepted -> rejected -> cancelled
    status = db.Column(db.String(20), default="pending", index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("ride_id", "passenger_id", name="uq_ride_passenger_request"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "ride_id": self.ride_id,
            "passenger_id": self.passenger_id,
            "passenger_name": self.requester.name if self.requester else None,
            "seats_requested": self.seats_requested,
            "pickup_point": self.pickup_point,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<RideRequest ride={self.ride_id} passenger={self.passenger_id} status={self.status}>"
