"""
Tests for VPOOL 2.0 additions: automatic fare suggestion, ride_type,
minimum-passenger pooling, and fuel-type filtering.
"""
import pytest
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db as _db


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def register_and_login(client, email, phone):
    client.post("/api/auth/register", json={
        "name": "User " + email, "email": email, "phone": phone, "password": "secret123"
    })
    client.post("/api/auth/login", json={"email": email, "password": "secret123"})


def add_vehicle(client, fuel_type="Petrol"):
    resp = client.post("/api/users/me/vehicles", json={
        "vehicle_type": "Car", "brand": "Toyota", "model": "Etios",
        "registration_number": "MH01YY000" + fuel_type[0], "total_seats": 4, "fuel_type": fuel_type
    })
    return resp.get_json()["data"]["id"]


def future_time(hours=3):
    return (datetime.utcnow() + timedelta(hours=hours)).isoformat()


def test_offer_ride_auto_calculates_fare_when_price_left_blank(client):
    register_and_login(client, "fare1@vpool.com", "9100000001")
    vehicle_id = add_vehicle(client)
    resp = client.post("/api/rides", json={
        "vehicle_id": vehicle_id, "pickup_location": "Point A Location", "destination": "Point B Location",
        "departure_time": future_time(), "available_seats": 3
        # price_per_seat intentionally omitted
    })
    data = resp.get_json()["data"]
    assert resp.status_code == 201
    assert data["market_fare"] is not None
    assert data["suggested_fare"] is not None
    # the auto price should match the suggested fare since none was provided
    assert data["price_per_seat"] == data["suggested_fare"]


def test_offer_ride_respects_custom_price(client):
    register_and_login(client, "fare2@vpool.com", "9100000002")
    vehicle_id = add_vehicle(client)
    resp = client.post("/api/rides", json={
        "vehicle_id": vehicle_id, "pickup_location": "Point A Location", "destination": "Point B Location",
        "departure_time": future_time(), "available_seats": 2, "price_per_seat": 99
    })
    data = resp.get_json()["data"]
    assert data["price_per_seat"] == 99.0
    # market_fare is still calculated for comparison even if driver overrides price
    assert data["market_fare"] is not None


def test_min_passengers_cannot_exceed_available_seats(client):
    register_and_login(client, "fare3@vpool.com", "9100000003")
    vehicle_id = add_vehicle(client)
    resp = client.post("/api/rides", json={
        "vehicle_id": vehicle_id, "pickup_location": "Point A Location", "destination": "Point B Location",
        "departure_time": future_time(), "available_seats": 2, "min_passengers": 5
    })
    assert resp.status_code == 422


def test_pool_ready_flag_updates_as_passengers_join(client):
    register_and_login(client, "fare4@vpool.com", "9100000004")
    vehicle_id = add_vehicle(client)
    ride_resp = client.post("/api/rides", json={
        "vehicle_id": vehicle_id, "pickup_location": "Point A Location", "destination": "Point B Location",
        "departure_time": future_time(), "available_seats": 3, "min_passengers": 2
    })
    ride_id = ride_resp.get_json()["data"]["id"]
    assert ride_resp.get_json()["data"]["pool_ready"] is False
    client.post("/api/auth/logout")

    register_and_login(client, "passenger_fare@vpool.com", "9100000005")
    client.post(f"/api/rides/{ride_id}/join", json={"seats_booked": 2})

    check = client.get(f"/api/rides/{ride_id}")
    ride_data = check.get_json()["data"]
    assert ride_data["current_passengers"] == 2
    assert ride_data["pool_ready"] is True
    assert ride_data["co2_saved_kg"] > 0


def test_search_filters_by_fuel_type(client):
    register_and_login(client, "fare5@vpool.com", "9100000006")
    petrol_vehicle = add_vehicle(client, fuel_type="Petrol")
    electric_vehicle = add_vehicle(client, fuel_type="Electric")

    client.post("/api/rides", json={
        "vehicle_id": petrol_vehicle, "pickup_location": "Green Park Location", "destination": "City Center Location",
        "departure_time": future_time(), "available_seats": 2
    })
    client.post("/api/rides", json={
        "vehicle_id": electric_vehicle, "pickup_location": "Green Park Location", "destination": "City Center Location",
        "departure_time": future_time(hours=4), "available_seats": 2
    })

    resp = client.get("/api/rides?fuel_type=Electric")
    results = resp.get_json()["data"]
    assert len(results) == 1
    assert results[0]["vehicle"]["fuel_type"] == "Electric"
