# VPOOL — Entity Relationship Diagram

The schema is implemented with SQLAlchemy ORM models (`app/models/`) and maps
to the following relational structure in MySQL.

```mermaid
erDiagram
    USERS ||--o{ VEHICLES : owns
    USERS ||--o{ RIDES : offers
    USERS ||--o{ RIDE_REQUESTS : sends
    USERS ||--o{ BOOKINGS : makes
    VEHICLES ||--o{ RIDES : "used in"
    RIDES ||--o{ RIDE_REQUESTS : receives
    RIDES ||--o{ BOOKINGS : has
    RIDE_REQUESTS ||--o| BOOKINGS : "converts to"

    USERS {
        int id PK
        string name
        string email UK
        string phone UK
        string password_hash
        string organization
        string preferred_time
        string role_preference
        string reset_token
        datetime reset_token_expiry
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    VEHICLES {
        int id PK
        int owner_id FK
        string vehicle_type
        string brand
        string model
        string registration_number UK
        int total_seats
        string color
        datetime created_at
    }

    RIDES {
        int id PK
        int driver_id FK
        int vehicle_id FK
        string pickup_location
        float pickup_lat
        float pickup_lng
        string destination
        float destination_lat
        float destination_lng
        float distance_km
        datetime departure_time
        int total_seats
        int available_seats
        float price_per_seat
        string status
        string notes
        datetime created_at
        datetime updated_at
    }

    RIDE_REQUESTS {
        int id PK
        int ride_id FK
        int passenger_id FK
        int seats_requested
        string pickup_point
        string status
        datetime created_at
        datetime updated_at
    }

    BOOKINGS {
        int id PK
        int ride_id FK
        int passenger_id FK
        int ride_request_id FK
        int seats_booked
        float fare
        string status
        datetime created_at
        datetime updated_at
    }
```

## Relationship notes

- **USERS → VEHICLES** (1:N): a user can register multiple vehicles; each
  vehicle has exactly one owner.
- **USERS → RIDES** (1:N, as driver): a user can offer many rides.
- **VEHICLES → RIDES** (1:N): a vehicle can be used across multiple ride
  postings (at different times).
- **USERS → RIDE_REQUESTS** (1:N, as passenger): a user can send many join
  requests.
- **RIDES → RIDE_REQUESTS** (1:N): a ride can receive requests from many
  passengers.
- **RIDE_REQUESTS → BOOKINGS** (1:0..1): an accepted request produces exactly
  one booking; instant-join bookings have no associated request
  (`ride_request_id` is nullable).
- **RIDES → BOOKINGS** (1:N): a ride can have many confirmed bookings, up to
  its seat capacity.

## Constraints implemented

- `users.email`, `users.phone` — UNIQUE
- `vehicles.registration_number` — UNIQUE
- `ride_requests(ride_id, passenger_id)` — UNIQUE composite (prevents duplicate
  pending requests for the same ride by the same passenger)
- All foreign keys (`driver_id`, `owner_id`, `vehicle_id`, `ride_id`,
  `passenger_id`) reference their parent primary keys with cascading deletes
  configured at the ORM relationship level (`cascade="all, delete-orphan"`)
  where a parent removal should clean up dependents (e.g. deleting a user
  removes their vehicles/rides/requests).
