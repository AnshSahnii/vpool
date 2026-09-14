# VPOOL 2.0 — What's New

This upgrade builds on the original VPOOL project without removing or
breaking anything that already worked. Everything below is intentionally
**simple, formula-based, and readable** — no external paid APIs, no
real-time infrastructure — so it stays approachable if you're still
learning backend development.

## 1. Ride Types: "Ride Now" vs "Scheduled"

Every ride now has a `ride_type` field (`"now"` or `"scheduled"`). Drivers
pick this when offering a ride. It's just a label used for filtering —
no special real-time matching engine was added, keeping it simple.

## 2. Automatic Fare Suggestion (`app/services/fare_service.py`)

Instead of typing a price, drivers can leave "Price per seat" blank and
VPOOL calculates one automatically using a **plain, readable formula**:

```
market_fare = (base_fare + distance_km * per_km_rate) * time_of_day_multiplier
suggested_fare = market_fare * (1 - pool_discount) / seats_shared
```

This is **not** a live call to Uber/Ola's pricing (they don't expose a
public API for that) — it's a transparent formula you can open and tweak
yourself. All the tunable numbers (base fare, per-km rate, discount %) are
constants at the top of the file with comments.

The ride details page shows Market Fare vs VPOOL Fare vs % savings, so
passengers can see why pooling is cheaper.

## 3. Minimum-Passenger Pooling

Drivers can set `min_passengers` when offering a ride (default `1`, meaning
"no waiting required"). The ride details/dashboard pages show:
- ✅ "Pool ready" once enough passengers have joined
- ⏳ "Waiting for pool (X/Y passengers)" until then

This is tracked with a simple `current_passengers` counter on the `Ride`
model, updated whenever someone joins or cancels
(`booking_service._update_pool_progress`). The driver isn't blocked from
starting early — this is just an informational indicator, kept
intentionally simple rather than enforcing a hard rule.

## 4. Fuel Type & Eco-Friendly Filtering

Vehicles now have a `fuel_type` (Petrol/Diesel/CNG/Electric/Hybrid).
Passengers can filter search results by fuel type — useful for finding
eco-friendly rides.

## 5. Environmental Impact (CO₂ Saved)

A simple estimate: if 3 people pool into 1 car instead of driving
separately, we "save" the emissions of 2 avoided car trips:

```
co2_saved_kg = distance_km * CO2_PER_KM_KG * (passengers_sharing - 1)
```

Shown per-ride, and totalled on the passenger dashboard alongside total
money saved.

## What was intentionally left out (and why)

The full "VPOOL 2.0" vision (real-time GPS tracking, Google Maps,
WebSocket live updates, an ML-driven pricing engine benchmarked against
live Uber/Ola APIs, a complete visual redesign, admin analytics) is a
multi-month, multi-person platform effort — not something that belongs in
a single incremental commit, and it would make the codebase much harder to
follow for someone still learning.

If you want to keep growing this project, a sensible next step (once
you're comfortable with what's here) would be:
1. Flask-SocketIO for live ride-status notifications
2. A `RideStop` model for proper multi-passenger pickup sequencing
3. Swapping Leaflet/OpenStreetMap for Google Maps once you have a billing
   key
4. A simple admin blueprint for moderation

Each of those is its own manageable project on top of this one — happy to
build any of them next, one at a time.
