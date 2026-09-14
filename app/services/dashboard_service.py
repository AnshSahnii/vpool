"""
Aggregates data for the Driver and Passenger dashboards.
"""
from datetime import datetime

from app.models.ride import Ride
from app.models.booking import Booking
from app.models.ride_request import RideRequest


def driver_dashboard_data(user):
    offered_rides = Ride.query.filter_by(driver_id=user.id).order_by(Ride.departure_time.desc()).all()
    active_rides = [r for r in offered_rides if r.status == "scheduled"]
    completed_rides = [r for r in offered_rides if r.status == "completed"]

    pending_requests = (
        RideRequest.query.join(Ride, RideRequest.ride_id == Ride.id)
        .filter(Ride.driver_id == user.id, RideRequest.status == "pending")
        .all()
    )

    active_bookings = []
    for r in active_rides:
        active_bookings.extend([b for b in r.bookings if b.status == "confirmed"])

    total_earnings = sum(
        b.fare for r in offered_rides for b in r.bookings if b.status in ("confirmed", "completed")
    )

    return {
        "offered_rides": [r.to_dict(include_driver=False) for r in offered_rides],
        "active_rides_count": len(active_rides),
        "completed_rides_count": len(completed_rides),
        "pending_requests": [req.to_dict() for req in pending_requests],
        "active_bookings_count": len(active_bookings),
        "total_earnings": round(total_earnings, 2),
    }


def passenger_dashboard_data(user):
    bookings = Booking.query.filter_by(passenger_id=user.id).order_by(Booking.created_at.desc()).all()
    upcoming = [
        b for b in bookings
        if b.status == "confirmed" and b.ride and b.ride.status == "scheduled"
        and b.ride.departure_time >= datetime.utcnow()
    ]
    history = [b for b in bookings if b.ride and (b.ride.status in ("completed", "cancelled") or b.status == "cancelled")]

    my_requests = RideRequest.query.filter_by(passenger_id=user.id).order_by(RideRequest.created_at.desc()).all()

    # VPOOL 2.0: simple "impact" totals — how much this passenger has saved by pooling
    confirmed_bookings = [b for b in bookings if b.status in ("confirmed", "completed")]
    total_money_saved = 0.0
    total_co2_saved = 0.0
    for b in confirmed_bookings:
        if b.ride and b.ride.market_fare:
            total_money_saved += max(0.0, (b.ride.market_fare - b.fare))
        if b.ride and b.ride.co2_saved_kg:
            # split the ride's total CO2 saving across passengers proportional to seats booked
            total_co2_saved += b.ride.co2_saved_kg

    return {
        "upcoming_rides": [b.to_dict() for b in upcoming],
        "booking_history": [b.to_dict() for b in history],
        "ride_requests": [r.to_dict() for r in my_requests],
        "total_bookings": len(bookings),
        "total_money_saved": round(total_money_saved, 2),
        "total_co2_saved_kg": round(total_co2_saved, 2),
    }
