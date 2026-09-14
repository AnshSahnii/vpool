# VPOOL — Setup Guide

This guide covers local setup for development/demo purposes, using either
MySQL (production-like) or SQLite (zero-config, fastest for evaluation).

## Prerequisites

- Python 3.10+
- pip
- MySQL Server 8.x (optional — SQLite fallback available)
- Git

## 1. Clone & create a virtual environment

```bash
git clone https://github.com/<your-username>/vpool.git
cd vpool
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

### Option A — Quick start with SQLite (no MySQL needed)
```env
USE_SQLITE=true
SECRET_KEY=any-random-string
```

### Option B — MySQL (recommended for the "real" experience)
1. Create the database and a user:
   ```sql
   CREATE DATABASE vpool_db CHARACTER SET utf8mb4;
   CREATE USER 'vpool_user'@'localhost' IDENTIFIED BY 'vpool_pass';
   GRANT ALL PRIVILEGES ON vpool_db.* TO 'vpool_user'@'localhost';
   FLUSH PRIVILEGES;
   ```
2. Set in `.env`:
   ```env
   USE_SQLITE=false
   DATABASE_URL=mysql+pymysql://vpool_user:vpool_pass@localhost:3306/vpool_db
   SECRET_KEY=any-random-string
   ```

## 4. Initialize the database

Tables are created automatically the first time you run the app (via
`db.create_all()` in `run.py`), or explicitly:

```bash
python -c "from app import create_app; from app.extensions import db; app = create_app(); \
app.app_context().push(); db.create_all()"
```

For schema migrations going forward (recommended once the schema stabilizes):
```bash
flask db init      # first time only
flask db migrate -m "Initial schema"
flask db upgrade
```

## 5. (Optional) Seed demo data

```bash
python seed.py
```
Creates 2 drivers, 1 passenger, 2 vehicles, 2 rides, and 1 booking.
Demo login: `rohan@vpool.com` / `priya@vpool.com` / `aman@vpool.com`,
password `password123` for all.

## 6. Run the application

```bash
python run.py
```
Visit **http://localhost:5000**

Or with Gunicorn (production-style):
```bash
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

## 7. Run tests

```bash
pytest tests/ -v
```

## 8. Geocoding / Maps configuration (optional)

By default, VPOOL uses **OpenStreetMap's Nominatim API** for geocoding —
completely free, no API key required. Ride maps render with **Leaflet.js**
and OSM tiles (also free, no key required).

If you want higher rate limits, sign up for a free
[LocationIQ](https://locationiq.com) key and set:
```env
GEOCODING_PROVIDER=locationiq
LOCATIONIQ_API_KEY=your_key_here
```

To use Google Maps instead, swap the tile layer URL in
`app/static/js/map.js` and the geocoding call in
`app/services/geo_service.py` for the Google Maps Geocoding API (requires a
billing-enabled Google Cloud API key).

## Troubleshooting

| Issue | Fix |
|---|---|
| `ModuleNotFoundError: PyMySQL` | `pip install -r requirements.txt` again |
| `Access denied for user 'vpool_user'` | Recheck the `GRANT` statement and password in `.env` |
| Port 5000 already in use | `python run.py` then change `app.run(port=5001)` in `run.py`, or kill the process using port 5000 |
| Geocoding returns null lat/lng | Nominatim usage policy limits request rate; the app degrades gracefully (text-based search/matching still works without coordinates) |
