from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    organization = db.Column(db.String(150), nullable=True)  # College / Organization
    preferred_time = db.Column(db.String(50), nullable=True)  # e.g. "Morning (8-10 AM)"
    role_preference = db.Column(db.String(20), default="both")  # driver / passenger / both

    # Password reset (basic implementation)
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    is_active_flag = db.Column("is_active", db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vehicles = db.relationship("Vehicle", backref="owner", lazy=True, cascade="all, delete-orphan")
    rides_offered = db.relationship("Ride", backref="driver", lazy=True, cascade="all, delete-orphan",
                                     foreign_keys="Ride.driver_id")
    ride_requests = db.relationship("RideRequest", backref="requester", lazy=True, cascade="all, delete-orphan",
                                     foreign_keys="RideRequest.passenger_id")

    # --- Password helpers ---
    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_active(self):
        return self.is_active_flag

    def to_dict(self, include_private=False):
        data = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "organization": self.organization,
            "preferred_time": self.preferred_time,
            "role_preference": self.role_preference,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_private:
            data["vehicles"] = [v.to_dict() for v in self.vehicles]
        return data

    def __repr__(self):
        return f"<User {self.email}>"
