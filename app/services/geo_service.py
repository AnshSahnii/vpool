"""
Geolocation service.
Uses OpenStreetMap's free Nominatim API for geocoding (no API key required),
with an optional LocationIQ key for higher rate limits. Also provides
Haversine distance calculation between two coordinates (used to estimate
route distance without needing a paid routing API).
"""
import math
import requests
from flask import current_app

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
LOCATIONIQ_URL = "https://us1.locationiq.com/v1/search"


def geocode_location(place_name: str):
    """
    Convert a place name / address into (lat, lng).
    Returns (lat, lng) tuple, or (None, None) if not found / network unavailable.
    This never raises — geocoding is a "best effort" enhancement, not a hard
    requirement for offering/searching rides.
    """
    if not place_name:
        return None, None

    provider = current_app.config.get("GEOCODING_PROVIDER", "nominatim")
    headers = {"User-Agent": "VPOOL-Vehicle-Pooling-App/1.0"}

    try:
        if provider == "locationiq" and current_app.config.get("LOCATIONIQ_API_KEY"):
            params = {
                "key": current_app.config["LOCATIONIQ_API_KEY"],
                "q": place_name,
                "format": "json",
                "limit": 1,
            }
            resp = requests.get(LOCATIONIQ_URL, params=params, headers=headers, timeout=5)
        else:
            params = {"q": place_name, "format": "json", "limit": 1}
            resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=5)

        if resp.status_code == 200 and resp.json():
            result = resp.json()[0]
            return float(result["lat"]), float(result["lon"])
    except (requests.RequestException, ValueError, KeyError, IndexError):
        pass

    return None, None


def haversine_distance_km(lat1, lng1, lat2, lng2):
    """Great-circle distance between two lat/lng points, in kilometers."""
    if None in (lat1, lng1, lat2, lng2):
        return None

    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)
