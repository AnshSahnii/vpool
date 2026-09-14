"""
Seeds the database with demo users, vehicles, and rides so the app can be
explored/demoed immediately after setup.

Usage: python seed.py
"""
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models import User, Vehicle, Ride, Booking


def run():
    app = create_app()
    with app.app_context():
        db.create_all()

        if User.query.first():
            print("Database already has data. Skipping seed.")
            return

        # --- Users ---
        driver1 = User(name="Rohan Sharma", email="rohan@vpool.com", phone="9876543210",
                        organization="ABC Institute of Technology", preferred_time="Morning (8-10 AM)",
                        role_preference="driver")
        driver1.set_password("password123")

        driver2 = User(name="Priya Verma", email="priya@vpool.com", phone="9876543211",
                        organization="ABC Institute of Technology", preferred_time="Evening (5-7 PM)",
                        role_preference="both")
        driver2.set_password("password123")

        passenger1 = User(name="Aman Gupta", email="aman@vpool.com", phone="9876543212",
                           organization="ABC Institute of Technology", preferred_time="Morning (8-10 AM)",
                           role_preference="passenger")
        passenger1.set_password("password123")

        db.session.add_all([driver1, driver2, passenger1])
        db.session.commit()

        # --- Vehicles ---
        v1 = Vehicle(owner_id=driver1.id, vehicle_type="Car", brand="Maruti Suzuki", model="Swift",
                      registration_number="MH12AB1234", total_seats=3, color="White", fuel_type="Petrol")
        v2 = Vehicle(owner_id=driver2.id, vehicle_type="Car", brand="Hyundai", model="i20",
                      registration_number="MH14CD5678", total_seats=3, color="Silver", fuel_type="Electric")
        db.session.add_all([v1, v2])
        db.session.commit()

        # --- Rides ---
        r1 = Ride(driver_id=driver1.id, vehicle_id=v1.id, pickup_location="Hinjewadi Phase 1, Pune",
                   destination="Pune Railway Station", departure_time=datetime.utcnow() + timedelta(hours=5),
                   total_seats=3, available_seats=3, price_per_seat=80, status="scheduled",
                   distance_km=18.5, notes="AC car, music on request",
                   ride_type="scheduled", min_passengers=1, market_fare=220, suggested_fare=80)
        r2 = Ride(driver_id=driver2.id, vehicle_id=v2.id, pickup_location="Kothrud, Pune",
                   destination="Hinjewadi Phase 2, Pune", departure_time=datetime.utcnow() + timedelta(hours=8),
                   total_seats=3, available_seats=2, price_per_seat=60, status="scheduled",
                   distance_km=14.2, ride_type="now", min_passengers=2, current_passengers=1,
                   market_fare=180, suggested_fare=60, co2_saved_kg=0)
        db.session.add_all([r1, r2])
        db.session.commit()

        b1 = Booking(ride_id=r2.id, passenger_id=passenger1.id, seats_booked=1, fare=60, status="confirmed")
        db.session.add(b1)
        db.session.commit()

        print("Seed data created successfully!")
        print("Demo accounts (password: password123):")
        print("  Driver:    rohan@vpool.com")
        print("  Driver:    priya@vpool.com")
        print("  Passenger: aman@vpool.com")


if __name__ == "__main__":
    run()
