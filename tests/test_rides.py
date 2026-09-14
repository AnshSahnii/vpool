"""
Test suite for ride offering, searching, joining, and validation rules.
Run with: pytest tests/
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


def add_vehicle(client):
    resp = client.post("/api/users/me/vehicles", json={
        "vehicle_type": "Car", "brand": "Toyota", "model": "Etios",
        "registration_number": "MH01XX0001", "total_seats": 4
    })
    return resp.get_json()["data"]["id"]


def future_time(hours=3):
    return (datetime.utcnow() + timedelta(hours=hours)).isoformat()


def test_offer_ride_success(client):
    register_and_login(client, "driver1@vpool.com", "9000000001")
    vehicle_id = add_vehicle(client)
    resp = client.post("/api/rides", json={
        "vehicle_id": vehicle_id, "pickup_location": "Point A Location", "destination": "Point B Location",
        "departure_time": future_time(), "available_seats": 2
    })
    assert resp.status_code == 201
    assert resp.get_json()["data"]["available_seats"] == 2


def test_offer_ride_seats_exceed_vehicle_capacity(client):
    register_and_login(client, "driver2@vpool.com", "9000000002")
    vehicle_id = add_vehicle(client)
    resp = client.post("/api/rides", json={
        "vehicle_id": vehicle_id, "pickup_location": "Point A Location", "destination": "Point B Location",
        "departure_time": future_time(), "available_seats": 99
    })
    assert resp.status_code == 422


def test_offer_ride_same_pickup_destination_fails(client):
    register_and_login(client, "driver3@vpool.com", "9000000003")
    vehicle_id = add_vehicle(client)
    resp = client.post("/api/rides", json={
        "vehicle_id": vehicle_id, "pickup_location": "Same Place", "destination": "Same Place",
        "departure_time": future_time(), "available_seats": 2
    })
    assert resp.status_code == 422


def test_join_ride_and_seat_deduction(client):
    register_and_login(client, "driver4@vpool.com", "9000000004")
    vehicle_id = add_vehicle(client)
    ride_resp = client.post("/api/rides", json={
        "vehicle_id": vehicle_id, "pickup_location": "Point A Location", "destination": "Point B Location",
        "departure_time": future_time(), "available_seats": 3
    })
    ride_id = ride_resp.get_json()["data"]["id"]
    client.post("/api/auth/logout")

    register_and_login(client, "passenger1@vpool.com", "9000000005")
    join_resp = client.post(f"/api/rides/{ride_id}/join", json={"seats_booked": 2})
    assert join_resp.status_code == 201

    ride_check = client.get(f"/api/rides/{ride_id}")
    assert ride_check.get_json()["data"]["available_seats"] == 1


def test_join_ride_overbooking_fails(client):
    register_and_login(client, "driver5@vpool.com", "9000000006")
    vehicle_id = add_vehicle(client)
    ride_resp = client.post("/api/rides", json={
        "vehicle_id": vehicle_id, "pickup_location": "Point A Location", "destination": "Point B Location",
        "departure_time": future_time(), "available_seats": 1
    })
    ride_id = ride_resp.get_json()["data"]["id"]
    client.post("/api/auth/logout")

    register_and_login(client, "passenger2@vpool.com", "9000000007")
    resp = client.post(f"/api/rides/{ride_id}/join", json={"seats_booked": 5})
    assert resp.status_code == 422


def test_driver_cannot_join_own_ride(client):
    register_and_login(client, "driver6@vpool.com", "9000000008")
    vehicle_id = add_vehicle(client)
    ride_resp = client.post("/api/rides", json={
        "vehicle_id": vehicle_id, "pickup_location": "Point A Location", "destination": "Point B Location",
        "departure_time": future_time(), "available_seats": 2
    })
    ride_id = ride_resp.get_json()["data"]["id"]
    resp = client.post(f"/api/rides/{ride_id}/join", json={"seats_booked": 1})
    assert resp.status_code == 422


def test_cancel_ride_only_by_owner(client):
    register_and_login(client, "driver7@vpool.com", "9000000009")
    vehicle_id = add_vehicle(client)
    ride_resp = client.post("/api/rides", json={
        "vehicle_id": vehicle_id, "pickup_location": "Point A Location", "destination": "Point B Location",
        "departure_time": future_time(), "available_seats": 2
    })
    ride_id = ride_resp.get_json()["data"]["id"]
    client.post("/api/auth/logout")

    register_and_login(client, "intruder@vpool.com", "9000000010")
    resp = client.delete(f"/api/rides/{ride_id}")
    assert resp.status_code == 403
