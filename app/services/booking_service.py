"""
Booking & ride-request business logic.
Two flows are supported:
  1. Instant join: passenger directly books available seats (join_ride).
  2. Request flow: passenger sends a RideRequest, driver accepts/rejects,
     acceptance creates a Booking (request_to_join / respond_to_request).
"""
from app.extensions import db
from app.models.ride import Ride
from app.models.booking import Booking
from app.models.ride_request import RideRequest
from app.services.fare_service import calculate_co2_saved
from app.utils.validators import ValidationError, require_fields, validate_positive_int


def _assert_seat_availability(ride: Ride, seats_wanted: int):
    if ride.status != "scheduled":
        raise ValidationError(f"This ride is '{ride.status}' and cannot accept new bookings.")
    if ride.available_seats < seats_wanted:
        raise ValidationError(
            f"Only {ride.available_seats} seat(s) available, but {seats_wanted} requested."
        )


def _update_pool_progress(ride: Ride, seat_change: int):
    """
    VPOOL 2.0: keep current_passengers and the CO2-saved estimate in sync
    whenever someone joins (seat_change > 0) or cancels (seat_change < 0).
    """
    ride.current_passengers = max(0, ride.current_passengers + seat_change)
    ride.co2_saved_kg = calculate_co2_saved(ride.distance_km, ride.current_passengers)


def join_ride(user, ride_id: int, data: dict) -> Booking:
    ride = Ride.query.get(ride_id)
    if not ride:
        raise LookupError("Ride not found.")
    if ride.driver_id == user.id:
        raise ValidationError("You cannot join your own ride as a passenger.")

    seats = validate_positive_int((data or {}).get("seats_booked", 1), "seats_booked", minimum=1)
    _assert_seat_availability(ride, seats)

    # Booking-conflict validation: passenger cannot double-book the same ride
    existing = Booking.query.filter_by(ride_id=ride.id, passenger_id=user.id, status="confirmed").first()
    if existing:
        raise ValidationError("You already have a confirmed booking on this ride.")

    booking = Booking(
        ride_id=ride.id,
        passenger_id=user.id,
        seats_booked=seats,
        fare=round(ride.price_per_seat * seats, 2),
        status="confirmed",
    )
    ride.available_seats -= seats
    _update_pool_progress(ride, seat_change=seats)
    db.session.add(booking)
    db.session.commit()
    return booking


def cancel_booking(user, booking_id: int) -> Booking:
    booking = Booking.query.get(booking_id)
    if not booking:
        raise LookupError("Booking not found.")
    if booking.passenger_id != user.id:
        raise PermissionError("You can only cancel your own bookings.")
    if booking.status != "confirmed":
        raise ValidationError(f"Booking is already '{booking.status}'.")

    booking.status = "cancelled"
    ride = booking.ride
    if ride and ride.status == "scheduled":
        ride.available_seats = min(ride.total_seats, ride.available_seats + booking.seats_booked)
        _update_pool_progress(ride, seat_change=-booking.seats_booked)
    db.session.commit()
    return booking


def request_to_join(user, ride_id: int, data: dict) -> RideRequest:
    ride = Ride.query.get(ride_id)
    if not ride:
        raise LookupError("Ride not found.")
    if ride.driver_id == user.id:
        raise ValidationError("You cannot request to join your own ride.")

    seats = validate_positive_int((data or {}).get("seats_requested", 1), "seats_requested", minimum=1)
    _assert_seat_availability(ride, seats)

    if RideRequest.query.filter_by(ride_id=ride.id, passenger_id=user.id, status="pending").first():
        raise ValidationError("You already have a pending request for this ride.")

    req = RideRequest(
        ride_id=ride.id,
        passenger_id=user.id,
        seats_requested=seats,
        pickup_point=(data or {}).get("pickup_point", "").strip() or None,
        status="pending",
    )
    db.session.add(req)
    db.session.commit()
    return req


def respond_to_request(driver, request_id: int, accept: bool) -> RideRequest:
    req = RideRequest.query.get(request_id)
    if not req:
        raise LookupError("Ride request not found.")
    ride = req.ride
    if ride.driver_id != driver.id:
        raise PermissionError("Only the ride's driver can respond to this request.")
    if req.status != "pending":
        raise ValidationError(f"Request already '{req.status}'.")

    if accept:
        _assert_seat_availability(ride, req.seats_requested)
        req.status = "accepted"
        booking = Booking(
            ride_id=ride.id,
            passenger_id=req.passenger_id,
            ride_request_id=req.id,
            seats_booked=req.seats_requested,
            fare=round(ride.price_per_seat * req.seats_requested, 2),
            status="confirmed",
        )
        ride.available_seats -= req.seats_requested
        _update_pool_progress(ride, seat_change=req.seats_requested)
        db.session.add(booking)
    else:
        req.status = "rejected"

    db.session.commit()
    return req


def get_passenger_bookings(user, upcoming_only=False):
    query = Booking.query.filter_by(passenger_id=user.id)
    bookings = query.order_by(Booking.created_at.desc()).all()
    if upcoming_only:
        bookings = [b for b in bookings if b.ride and b.status == "confirmed" and b.ride.status == "scheduled"]
    return bookings
