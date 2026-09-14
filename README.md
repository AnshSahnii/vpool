# 🚗 VPOOL — Vehicle Pooling System

A full-stack, production-style **vehicle/ride pooling platform** built for
students and employees to share rides — offer a ride, search for one, get
matched by route, and manage everything from a personal dashboard.

Built as a **backend-focused engineering project** to demonstrate REST API
design, relational database modeling, authentication, and clean layered
architecture with Flask + SQLAlchemy + MySQL.

> 📌 **Status:** Feature-complete demo project. Runs locally with either
> MySQL (production-like) or SQLite (zero-config).

---

## ✨ Features

- **Authentication** — Register, Login, Logout, Forgot/Reset Password,
  Profile management (Flask-Login + hashed passwords)
- **Ride Management** — Offer a ride, search rides, join instantly or via
  request, cancel a ride, view upcoming rides & ride history
- **Route Matching Engine** — Scores candidate rides by pickup/destination
  proximity (Haversine distance), departure time window, and seat
  availability
- **Driver & Passenger Dashboards** — Offered rides, active bookings,
  earnings, pending requests, upcoming rides, booking history
- **GPS / Map Integration** — OpenStreetMap + Leaflet.js map preview with
  pickup/destination markers and estimated distance; browser Geolocation API
  support
- **REST API** — Every feature is available as a clean, versionless JSON API
  under `/api/*`, in addition to server-rendered HTML pages
- **Validation & Error Handling** — Empty-field checks, duplicate-user
  prevention, seat-availability checks, booking-conflict detection, and
  centralized JSON error responses with proper HTTP status codes

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask, Flask-RESTful patterns |
| ORM / DB | SQLAlchemy, MySQL (PyMySQL driver), SQLite (dev fallback) |
| Auth | Flask-Login, Werkzeug password hashing |
| Frontend | HTML5, CSS3, Bootstrap 5, vanilla JavaScript |
| Maps / Geo | OpenStreetMap (Nominatim geocoding), Leaflet.js, browser Geolocation API |
| Testing | pytest |
| Migrations | Flask-Migrate (Alembic) |

---

## 📂 Project Structure

```
vpool/
├── app/
│   ├── __init__.py            # Application factory, blueprint registration, error handlers
│   ├── config.py               # Environment-based configuration
│   ├── extensions.py           # db, login_manager, migrate, cors instances
│   ├── models/                 # SQLAlchemy models: User, Vehicle, Ride, RideRequest, Booking
│   ├── routes/                 # Blueprints: auth, user, ride, booking, dashboard, main
│   ├── services/                # Business logic: auth, ride, booking, matching, geo, dashboard
│   ├── utils/                   # Validators, decorators, standardized JSON responses
│   ├── templates/               # Jinja2 + Bootstrap HTML views
│   └── static/                  # CSS, JS (main.js, map.js, rides.js)
├── docs/                        # Architecture, ER diagram, API docs, setup guide
├── tests/                       # pytest test suite
├── migrations/                  # Flask-Migrate/Alembic migration scripts
├── seed.py                      # Demo data seeder
├── run.py                       # App entrypoint
├── requirements.txt
├── .env.example
└── README.md
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full layered
architecture explanation and diagrams.

---

## 🚀 Quick Start

```bash
git clone https://github.com/<your-username>/vpool.git
cd vpool
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then set USE_SQLITE=true for zero-config startup
python seed.py                # optional: adds demo users/rides
python run.py
```

Visit **http://localhost:5000**. Full walkthrough (including MySQL setup) in
[`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md).

**Demo accounts** (after `python seed.py`), password `password123`:
- `rohan@vpool.com` — driver
- `priya@vpool.com` — driver
- `aman@vpool.com` — passenger

---

## 📖 Documentation

| Doc | Contents |
|---|---|
| [`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md) | Full install & run instructions (MySQL + SQLite) |
| [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md) | Every REST endpoint, request/response examples, status codes |
| [`docs/ER_DIAGRAM.md`](docs/ER_DIAGRAM.md) | Database schema & relationships (Mermaid ER diagram) |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Layered architecture, request lifecycle, matching algorithm |

---

## 🗄️ Database Schema (summary)

```
Users 1───N Vehicles
Users 1───N Rides (as driver)
Vehicles 1───N Rides
Rides 1───N RideRequests
Rides 1───N Bookings
Users 1───N RideRequests (as passenger)
Users 1───N Bookings (as passenger)
RideRequests 1───0..1 Bookings (accepted request → booking)
```


---

## 🔌 REST API (overview)

```
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/auth/forgot-password
POST   /api/auth/reset-password
GET    /api/auth/me

GET    /api/users/me
PUT    /api/users/me
POST   /api/users/me/vehicles
GET    /api/users/me/vehicles

POST   /api/rides                 # offer a ride
GET    /api/rides                 # search rides
GET    /api/rides/<id>
DELETE /api/rides/<id>            # cancel ride
GET    /api/rides/upcoming
GET    /api/rides/history
POST   /api/rides/match           # route matching engine

POST   /api/rides/<id>/join       # instant join
DELETE /api/bookings/<id>         # cancel booking
GET    /api/bookings/me
POST   /api/rides/<id>/requests   # request to join
POST   /api/requests/<id>/respond # driver accepts/rejects

GET    /api/dashboard/driver
GET    /api/dashboard/passenger
GET    /api/health
```

Full request/response examples: [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md).

---

## ✅ Validation & Error Handling

- Empty/missing field checks on every write endpoint
- Duplicate user prevention (unique email & phone)
- Duplicate vehicle registration number prevention
- Seat-availability checks before every booking
- Booking-conflict detection (driver double-booking their vehicle within
  30 minutes; passenger double-booking the same ride)
- Ownership/permission checks (only a ride's driver can cancel it; only a
  booking's passenger can cancel it)
- Centralized error handling — every API error returns
  `{ success, message, data, errors }` with correct HTTP status codes
  (400/401/403/404/422/500); HTML routes flash user-friendly messages instead

---

## 🧪 Testing

```bash
pytest tests/ -v
```

Covers registration/login/validation, ride offering rules (capacity, same
pickup/destination, future-time requirement), booking flows (seat deduction,
overbooking prevention, self-booking prevention), and ownership permission
checks.

---

## 🔮 Future Enhancements

- Real-time ride tracking with WebSockets
- In-app chat between driver and passengers
- Payment gateway integration for fare settlement
- Ratings & reviews for drivers/passengers
- Push notifications (booking confirmations, ride reminders)
- Turn-by-turn routing distance (via OSRM/Google Directions) instead of
  straight-line Haversine distance
- Admin panel for platform moderation
- Recurring ride schedules (e.g. daily office commute)
- Mobile app (React Native) consuming the existing REST API

---

## 📄 License

This project is built for educational/portfolio purposes. Feel free to fork
and adapt it.

---

## 🙋 About this project

VPOOL was built to demonstrate practical backend engineering skills expected
in a Backend Developer internship: REST API design, relational schema
design with proper foreign keys, authentication & authorization, input
validation, layered/service-oriented architecture, and integration with a
free third-party geolocation API — all wired together into a working,
testable full-stack application.
