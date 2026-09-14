"""
Route matching engine.
Matches a passenger's desired trip (pickup, destination, departure time,
seats needed) against all scheduled rides using:
  1. Text similarity on pickup/destination (falls back to substring match)
  2. Geographic proximity (Haversine distance) when coordinates are available
  3. Departure time window (+/- configurable minutes)
  4. Seat availability

Returns rides ranked by a simple match score (lower distance + tighter
time window = higher score) so the "best" matches surface first.
"""
from datetime import datetime, timedelta

from app.models.ride import Ride
from app.services.geo_service import haversine_distance_km

DEFAULT_TIME_WINDOW_MINUTES = 60
DEFAULT_PROXIMITY_KM = 5.0


def _text_match(a: str, b: str) -> bool:
    if not a or not b:
        return False
    a, b = a.lower().strip(), b.lower().strip()
    return a in b or b in a


def match_rides(pickup_location, destination, departure_time, seats_needed=1,
                 pickup_lat=None, pickup_lng=None, dest_lat=None, dest_lng=None,
                 time_window_minutes=DEFAULT_TIME_WINDOW_MINUTES,
                 proximity_km=DEFAULT_PROXIMITY_KM):
    """
    Core matching algorithm. Returns a list of dicts:
    { "ride": Ride, "score": float, "distance_pickup_km": float|None, "time_diff_minutes": float }
    sorted by best match first.
    """
    if isinstance(departure_time, str):
        departure_time = datetime.fromisoformat(departure_time.replace("Z", ""))

    window_start = departure_time - timedelta(minutes=time_window_minutes)
    window_end = departure_time + timedelta(minutes=time_window_minutes)

    candidates = Ride.query.filter(
        Ride.status == "scheduled",
        Ride.available_seats >= seats_needed,
        Ride.departure_time.between(window_start, window_end),
    ).all()

    results = []
    for ride in candidates:
        # Location matching: prefer geo-distance, fall back to text containment
        pickup_ok, dest_ok = False, False
        pickup_dist_km, dest_dist_km = None, None

        if pickup_lat and pickup_lng and ride.pickup_lat and ride.pickup_lng:
            pickup_dist_km = haversine_distance_km(pickup_lat, pickup_lng, ride.pickup_lat, ride.pickup_lng)
            pickup_ok = pickup_dist_km is not None and pickup_dist_km <= proximity_km
        else:
            pickup_ok = _text_match(pickup_location, ride.pickup_location)

        if dest_lat and dest_lng and ride.destination_lat and ride.destination_lng:
            dest_dist_km = haversine_distance_km(dest_lat, dest_lng, ride.destination_lat, ride.destination_lng)
            dest_ok = dest_dist_km is not None and dest_dist_km <= proximity_km
        else:
            dest_ok = _text_match(destination, ride.destination)

        if not (pickup_ok and dest_ok):
            continue

        time_diff_minutes = abs((ride.departure_time - departure_time).total_seconds()) / 60.0

        # Lower is better: weight distance heavier than time drift
        distance_component = (pickup_dist_km or 0) + (dest_dist_km or 0)
        score = distance_component * 2 + (time_diff_minutes / 60.0)

        results.append({
            "ride": ride,
            "score": round(score, 3),
            "distance_pickup_km": pickup_dist_km,
            "distance_destination_km": dest_dist_km,
            "time_diff_minutes": round(time_diff_minutes, 1),
        })

    results.sort(key=lambda r: r["score"])
    return results
