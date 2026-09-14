"""
Fare & Environmental Impact Engine (VPOOL 2.0)
------------------------------------------------
This is intentionally a SIMPLE, formula-based calculator — not a call to a
paid pricing API (Uber/Ola don't offer public pricing APIs). It's meant to
be easy to read and easy to tweak as you learn.

How the market fare is estimated:
    market_fare = base_fare + (distance_km * per_km_rate) + time_of_day_surcharge

How VPOOL's pooled fare is estimated:
    suggested_fare = market_fare * (1 - pool_discount) / passengers_sharing
    (sharing a ride with more people = cheaper per person)

These are simple, transparent formulas on purpose — perfect for a resume
project, and easy to swap out later for a real pricing API if you want to.
"""

# --- Tunable constants (change these numbers any time) ---
BASE_FARE = 30.0          # ₹ flat starting fare, like a cab's base charge
PER_KM_RATE = 12.0        # ₹ per kilometer (rough Ola/Uber economy rate)
PEAK_HOUR_SURCHARGE = 1.25   # 25% extra during rush hours
NIGHT_SURCHARGE = 1.15       # 15% extra late at night
POOL_DISCOUNT = 0.30         # pooled rides are ~30% cheaper than solo market fare

# CO2 emitted per km by an average petrol car (kg) — used for the "savings" estimate
CO2_PER_KM_KG = 0.12


def _time_of_day_multiplier(departure_time):
    """Simple peak/night pricing — no real traffic API needed."""
    hour = departure_time.hour
    if hour in (8, 9, 18, 19):          # typical office rush hours
        return PEAK_HOUR_SURCHARGE
    if hour >= 22 or hour <= 5:          # late night
        return NIGHT_SURCHARGE
    return 1.0


def calculate_fares(distance_km, departure_time, total_seats):
    """
    Returns a dict with market_fare and suggested_fare for a ride.
    `total_seats` = how many passengers the driver is offering (used to
    split the pooled fare — more seats filled means a cheaper fare each).
    """
    distance_km = distance_km or 5.0  # fallback if geocoding didn't resolve

    multiplier = _time_of_day_multiplier(departure_time)
    market_fare = round((BASE_FARE + distance_km * PER_KM_RATE) * multiplier, 2)

    # Sharing the ride with more passengers reduces the price per seat
    passengers_sharing = max(total_seats, 1)
    suggested_fare = round((market_fare * (1 - POOL_DISCOUNT)) / passengers_sharing, 2)

    return {
        "market_fare": market_fare,
        "suggested_fare": suggested_fare,
    }


def calculate_co2_saved(distance_km, passengers_sharing):
    """
    Estimate of CO2 saved by pooling instead of everyone driving separately.
    If 3 people share one car instead of driving 3 separate cars, we "save"
    the emissions of (passengers_sharing - 1) extra car trips.
    """
    if passengers_sharing <= 1:
        return 0.0
    distance_km = distance_km or 5.0  # fallback if geocoding didn't resolve (e.g. no internet access)
    extra_trips_avoided = passengers_sharing - 1
    return round(distance_km * CO2_PER_KM_KG * extra_trips_avoided, 2)
