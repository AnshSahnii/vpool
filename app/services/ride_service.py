"""
Ride management business logic: offering rides, vehicle registration,
cancelling rides, and fetching ride histories/upcoming rides.
"""
from datetime import datetime

from app.extensions import db
from app.models.ride import Ride
from app.models.vehicle import Vehicle
from app.models.booking import Booking
from app.services.geo_service import geocode_location, haversine_distance_km
from app.services.fare_service import calculate_fares
from app.utils.validators import (
    ValidationError,
    require_fields,
    validate_positive_int,
    validate_future_datetime,
    validate_location_string,
)


def register_vehicle(user, data: dict) -> Vehicle:
    require_fields(data, ["vehicle_type", "brand", "model", "registration_number", "total_seats"])
    seats = validate_positive_int(data["total_seats"], "total_seats", minimum=1)

    reg_number = data["registration_number"].strip().upper()
    if Vehicle.query.filter_by(registration_number=reg_number).first():
        raise ValidationError("A vehicle with this registration number is already registered.")

    vehicle = Vehicle(
        owner_id=user.id,
        vehicle_type=data["vehicle_type"].strip(),
        brand=data["brand"].strip(),
        model=data["model"].strip(),
        registration_number=reg_number,
        total_seats=seats,
        color=data.get("color", "").strip() or None,
        fuel_type=data.get("fuel_type", "Petrol").strip() or "Petrol",
    )
    db.session.add(vehicle)
    db.session.commit()
    return vehicle


def offer_ride(user, data: dict) -> Ride:
    require_fields(data, ["vehicle_id", "pickup_location", "destination", "departure_time", "available_seats"])

    vehicle = Vehicle.query.get(int(data["vehicle_id"]))
    if not vehicle or vehicle.owner_id != user.id:
        raise ValidationError("Invalid vehicle. You can only offer rides using your own registered vehicle.")

    pickup = validate_location_string(data["pickup_location"], "pickup_location")
    destination = validate_location_string(data["destination"], "destination")
    if pickup.lower() == destination.lower():
        raise ValidationError("Pickup location and destination cannot be the same.")

    departure_time = validate_future_datetime(data["departure_time"], "departure_time")
    seats = validate_positive_int(data["available_seats"], "available_seats", minimum=1)

    if seats > vehicle.total_seats:
        raise ValidationError(
            f"available_seats ({seats}) cannot exceed the vehicle's total capacity ({vehicle.total_seats})."
        )

    # Booking-conflict validation: same driver, overlapping departure window (+/- 30 min) on same vehicle
    conflict = Ride.query.filter(
        Ride.driver_id == user.id,
        Ride.vehicle_id == vehicle.id,
        Ride.status == "scheduled",
    ).all()
    for existing in conflict:
        delta = abs((existing.departure_time - departure_time).total_seconds())
        if delta < 30 * 60:
            raise ValidationError(
                "You already have a ride scheduled within 30 minutes of this departure time."
            )

    pickup_lat, pickup_lng = geocode_location(pickup)
    dest_lat, dest_lng = geocode_location(destination)
    distance_km = haversine_distance_km(pickup_lat, pickup_lng, dest_lat, dest_lng)

    # --- VPOOL 2.0: ride type + minimum-passenger pooling ---
    ride_type = data.get("ride_type", "scheduled")
    if ride_type not in ("now", "scheduled"):
        ride_type = "scheduled"

    min_passengers = validate_positive_int(data.get("min_passengers", 1) or 1, "min_passengers", minimum=1)
    if min_passengers > seats:
        raise ValidationError("min_passengers cannot be greater than available_seats.")

    # --- VPOOL 2.0: automatic fare suggestion (simple formula, see fare_service.py) ---
    fares = calculate_fares(distance_km, departure_time, seats)

    # If the driver didn't type a custom price, use our suggested fare automatically
    price_per_seat = data.get("price_per_seat")
    if price_per_seat is None or str(price_per_seat).strip() == "":
        price_per_seat = fares["suggested_fare"]
    else:
        price_per_seat = float(price_per_seat)

    ride = Ride(
        driver_id=user.id,
        vehicle_id=vehicle.id,
        pickup_location=pickup,
        pickup_lat=pickup_lat,
        pickup_lng=pickup_lng,
        destination=destination,
        destination_lat=dest_lat,
        destination_lng=dest_lng,
        distance_km=distance_km,
        departure_time=departure_time,
        total_seats=seats,
        available_seats=seats,
        price_per_seat=price_per_seat,
        ride_type=ride_type,
        min_passengers=min_passengers,
        current_passengers=0,
        market_fare=fares["market_fare"],
        suggested_fare=fares["suggested_fare"],
        notes=data.get("notes", "").strip() or None,
        status="scheduled",
    )
    db.session.add(ride)
    db.session.commit()
    return ride


def cancel_ride(user, ride_id: int) -> Ride:
    ride = Ride.query.get(ride_id)
    if not ride:
        raise LookupError("Ride not found.")
    if ride.driver_id != user.id:
        raise PermissionError("Only the driver who offered this ride can cancel it.")
    if ride.status == "cancelled":
        raise ValidationError("Ride is already cancelled.")
    if ride.status == "completed":
        raise ValidationError("Cannot cancel a completed ride.")

    ride.status = "cancelled"
    # Cascade-cancel active bookings so passengers see accurate state
    for booking in ride.bookings:
        if booking.status == "confirmed":
            booking.status = "cancelled"
    db.session.commit()
    return ride


def get_upcoming_rides_for_driver(user):
    return (
        Ride.query.filter(
            Ride.driver_id == user.id,
            Ride.status == "scheduled",
            Ride.departure_time >= datetime.utcnow(),
        )
        .order_by(Ride.departure_time.asc())
        .all()
    )


def get_ride_history_for_driver(user):
    return (
        Ride.query.filter(Ride.driver_id == user.id)
        .order_by(Ride.departure_time.desc())
        .all()
    )


def search_rides(pickup=None, destination=None, date=None, min_seats=1, fuel_type=None, ride_type=None):
    """
    Basic search filter used by the search endpoint; fine matching by
    proximity/time-window is handled in matching_service.match_rides.
    """
    query = Ride.query.filter(Ride.status == "scheduled", Ride.available_seats >= int(min_seats or 1))

    if pickup:
        query = query.filter(Ride.pickup_location.ilike(f"%{pickup}%"))
    if destination:
        query = query.filter(Ride.destination.ilike(f"%{destination}%"))
    if ride_type:
        query = query.filter(Ride.ride_type == ride_type)
    if fuel_type:
        # Join to Vehicle so passengers can filter for eco-friendly rides (Electric/CNG/Hybrid)
        query = query.join(Vehicle, Ride.vehicle_id == Vehicle.id).filter(Vehicle.fuel_type == fuel_type)
    if date:
        try:
            day = datetime.fromisoformat(str(date))
            start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            query = query.filter(Ride.departure_time.between(start, end))
        except ValueError:
            pass

    return query.order_by(Ride.departure_time.asc()).all()
