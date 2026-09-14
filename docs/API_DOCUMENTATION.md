# VPOOL — REST API Documentation

Base URL (local): `http://localhost:5000`

All JSON API endpoints are prefixed with `/api/`. Every response follows this
envelope:

```json
{
  "success": true,
  "message": "Human-readable message",
  "data": { "...": "..." },
  "errors": null
}
```

On failure:

```json
{
  "success": false,
  "message": "Validation failed",
  "data": null,
  "errors": ["Field 'email' is required."]
}
```

Authentication uses **session cookies** (Flask-Login). Log in via
`/api/auth/login` first; the session cookie is then sent automatically with
subsequent requests (`credentials: 'same-origin'` in the browser, or a cookie
jar with `curl -c/-b`).

---

## 1. Authentication — `/api/auth`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | No | Register a new user |
| POST | `/api/auth/login` | No | Log in, starts a session |
| POST | `/api/auth/logout` | Yes | Log out, ends the session |
| POST | `/api/auth/forgot-password` | No | Generate a password reset token |
| POST | `/api/auth/reset-password` | No | Reset password using a token |
| GET | `/api/auth/me` | Yes | Get the current authenticated user |

**POST `/api/auth/register`**
```json
// Request
{
  "name": "Aman Gupta",
  "email": "aman@vpool.com",
  "phone": "9876543210",
  "password": "secret123",
  "organization": "ABC Institute of Technology",
  "preferred_time": "Morning (8-10 AM)",
  "role_preference": "passenger"
}
```
`201 Created` on success. `422` if email/phone already exists or fields are
missing/invalid.

**POST `/api/auth/login`**
```json
{ "email": "aman@vpool.com", "password": "secret123" }
```
`200 OK` with user data on success. `422` on invalid credentials.

**POST `/api/auth/forgot-password`**
```json
{ "email": "aman@vpool.com" }
```
Always returns `200 OK` (never reveals whether the email exists, to prevent
user enumeration). If the account exists, `data.reset_token` is returned
(in this basic/demo implementation — a production system would email it
instead).

**POST `/api/auth/reset-password`**
```json
{ "token": "<reset_token>", "new_password": "newpass123" }
```

---

## 2. Users / Profile — `/api/users`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/users/me` | Yes | Get full profile (incl. vehicles) |
| PUT/PATCH | `/api/users/me` | Yes | Update profile fields |
| POST | `/api/users/me/vehicles` | Yes | Register a new vehicle |
| GET | `/api/users/me/vehicles` | Yes | List my vehicles |

**PUT `/api/users/me`**
```json
{ "name": "Aman K. Gupta", "organization": "XYZ Corp", "preferred_time": "Evening (5-7 PM)" }
```

**POST `/api/users/me/vehicles`**
```json
{
  "vehicle_type": "Car",
  "brand": "Maruti Suzuki",
  "model": "Swift",
  "registration_number": "MH12AB1234",
  "total_seats": 3,
  "color": "White"
}
```
`422` if `registration_number` already exists.

---

## 3. Rides — `/api/rides`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/rides` | Yes | Offer a new ride |
| GET | `/api/rides` | No | Search rides (`?pickup=&destination=&date=&seats=`) |
| GET | `/api/rides/<id>` | No | Get a single ride's details |
| DELETE | `/api/rides/<id>` | Yes (owner) | Cancel a ride |
| GET | `/api/rides/upcoming` | Yes | My upcoming offered rides (as driver) |
| GET | `/api/rides/history` | Yes | My full ride history (as driver) |
| POST | `/api/rides/match` | Yes | Route-matching search (scored results) |

**POST `/api/rides`**
```json
{
  "vehicle_id": 1,
  "pickup_location": "Hinjewadi Phase 1, Pune",
  "destination": "Pune Railway Station",
  "departure_time": "2026-07-20T09:00:00",
  "available_seats": 3,
  "price_per_seat": 80,
  "notes": "AC car"
}
```
Validation performed server-side:
- All required fields present (empty-field validation)
- `pickup_location` ≠ `destination`
- `departure_time` must be in the future
- `available_seats` ≤ vehicle's `total_seats`
- Vehicle must belong to the logged-in user
- Driver cannot have two rides on the same vehicle within 30 minutes of each
  other (booking-conflict validation)

Geocoding (via OpenStreetMap Nominatim) and Haversine distance calculation
run automatically and populate `pickup_lat/lng`, `destination_lat/lng`,
`distance_km`.

**GET `/api/rides?pickup=Kothrud&destination=Hinjewadi&date=2026-07-20&seats=2`**

**POST `/api/rides/match`** — the route matching engine
```json
{
  "pickup_location": "Kothrud, Pune",
  "destination": "Hinjewadi, Pune",
  "departure_time": "2026-07-20T09:00:00",
  "seats_needed": 2,
  "pickup_lat": 18.5074,
  "pickup_lng": 73.8077,
  "destination_lat": 18.5912,
  "destination_lng": 73.7389
}
```
Response:
```json
{
  "success": true,
  "message": "2 matching ride(s) found.",
  "data": [
    {
      "ride": { "...": "full ride object" },
      "score": 1.24,
      "distance_pickup_km": 1.8,
      "distance_destination_km": 0.9,
      "time_diff_minutes": 15.0
    }
  ]
}
```
Lower `score` = better match (weighted distance + time drift).

---

## 4. Bookings & Ride Requests

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/rides/<id>/join` | Yes | Instantly join a ride (books seats directly) |
| DELETE | `/api/bookings/<id>` | Yes (owner) | Cancel a booking |
| GET | `/api/bookings/me` | Yes | My bookings (`?upcoming=true` to filter) |
| POST | `/api/rides/<id>/requests` | Yes | Send a join request (driver-approval flow) |
| POST | `/api/requests/<id>/respond` | Yes (driver) | Accept/reject a request |

**POST `/api/rides/<id>/join`**
```json
{ "seats_booked": 2 }
```
Validation: seat availability, no self-booking, no duplicate confirmed
booking on the same ride by the same passenger.

**POST `/api/requests/<id>/respond`**
```json
{ "accept": true }
```
Accepting creates a `Booking` and deducts seats; rejecting just updates the
request's status.

---

## 5. Dashboards — `/api/dashboard`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/dashboard/driver` | Yes | Offered rides, active bookings, pending requests, earnings |
| GET | `/api/dashboard/passenger` | Yes | Upcoming rides, booking history, ride requests |

---

## 6. Misc

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check — `{"status": "ok"}` |

---

## HTTP status code conventions

| Code | Meaning |
|---|---|
| 200 | Success (GET, update, action) |
| 201 | Resource created (register, offer ride, add vehicle, join ride) |
| 401 | Not authenticated (JSON) — API routes return JSON instead of redirecting |
| 403 | Authenticated but not authorized (e.g. cancelling someone else's ride) |
| 404 | Resource not found |
| 422 | Validation error (see `errors` array for details) |
| 500 | Unexpected server error |

## Example: full curl session

```bash
# Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@vpool.com","phone":"9998887766","password":"secret123"}' \
  -c cookies.txt

# Add a vehicle
curl -X POST http://localhost:5000/api/users/me/vehicles \
  -H "Content-Type: application/json" -b cookies.txt \
  -d '{"vehicle_type":"Car","brand":"Honda","model":"City","registration_number":"MH01ZZ9999","total_seats":4}'

# Offer a ride
curl -X POST http://localhost:5000/api/rides \
  -H "Content-Type: application/json" -b cookies.txt \
  -d '{"vehicle_id":1,"pickup_location":"Baner, Pune","destination":"Airport, Pune","departure_time":"2026-08-01T09:00:00","available_seats":3}'

# Search rides
curl "http://localhost:5000/api/rides?pickup=Baner"
```
