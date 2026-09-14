"""
Ride management routes: offer ride, search ride, cancel ride,
view upcoming rides, ride history, and route-matching.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app.models.ride import Ride
from app.services import ride_service, matching_service
from app.utils.validators import ValidationError
from app.utils.responses import success_response
from app.utils.decorators import json_endpoint

ride_bp = Blueprint("ride", __name__)


# ---------------------------------------------------------------------------
# HTML views
# ---------------------------------------------------------------------------
@ride_bp.route("/rides/offer", methods=["GET", "POST"])
@login_required
def offer_ride():
    if request.method == "POST":
        try:
            ride = ride_service.offer_ride(current_user, request.form.to_dict())
            flash("Ride offered successfully!", "success")
            return redirect(url_for("ride.ride_details", ride_id=ride.id))
        except ValidationError as e:
            for err in e.errors:
                flash(err, "danger")
    return render_template("rides/offer_ride.html", user=current_user)


@ride_bp.route("/rides/search", methods=["GET"])
@login_required
def search_ride():
    pickup = request.args.get("pickup", "")
    destination = request.args.get("destination", "")
    date = request.args.get("date", "")
    fuel_type = request.args.get("fuel_type", "")
    ride_type = request.args.get("ride_type", "")
    results = []
    if pickup or destination:
        results = ride_service.search_rides(pickup=pickup, destination=destination, date=date,
                                             fuel_type=fuel_type or None, ride_type=ride_type or None)
    return render_template("rides/search_ride.html", results=results, pickup=pickup,
                            destination=destination, date=date, fuel_type=fuel_type, ride_type=ride_type)


@ride_bp.route("/rides/<int:ride_id>")
@login_required
def ride_details(ride_id):
    ride = Ride.query.get_or_404(ride_id)
    return render_template("rides/ride_details.html", ride=ride)


@ride_bp.route("/rides/<int:ride_id>/cancel", methods=["POST"])
@login_required
def cancel_ride_view(ride_id):
    try:
        ride_service.cancel_ride(current_user, ride_id)
        flash("Ride cancelled.", "info")
    except (ValidationError, PermissionError, LookupError) as e:
        flash(str(e) if not hasattr(e, "errors") else "; ".join(e.errors), "danger")
    return redirect(url_for("dashboard.driver_dashboard"))


# ---------------------------------------------------------------------------
# JSON REST API
# ---------------------------------------------------------------------------
@ride_bp.route("/api/rides", methods=["POST"])
@login_required
@json_endpoint
def api_offer_ride():
    data = request.get_json(silent=True) or request.form.to_dict()
    ride = ride_service.offer_ride(current_user, data)
    return success_response("Ride offered successfully.", ride.to_dict(), status_code=201)


@ride_bp.route("/api/rides", methods=["GET"])
@json_endpoint
def api_search_rides():
    results = ride_service.search_rides(
        pickup=request.args.get("pickup"),
        destination=request.args.get("destination"),
        date=request.args.get("date"),
        min_seats=request.args.get("seats", 1),
        fuel_type=request.args.get("fuel_type"),
        ride_type=request.args.get("ride_type"),
    )
    return success_response("Rides fetched.", [r.to_dict() for r in results])


@ride_bp.route("/api/rides/<int:ride_id>", methods=["GET"])
@json_endpoint
def api_get_ride(ride_id):
    ride = Ride.query.get(ride_id)
    if not ride:
        raise LookupError("Ride not found.")
    return success_response("Ride fetched.", ride.to_dict())


@ride_bp.route("/api/rides/<int:ride_id>", methods=["DELETE"])
@login_required
@json_endpoint
def api_cancel_ride(ride_id):
    ride = ride_service.cancel_ride(current_user, ride_id)
    return success_response("Ride cancelled.", ride.to_dict())


@ride_bp.route("/api/rides/upcoming", methods=["GET"])
@login_required
@json_endpoint
def api_upcoming_rides():
    rides = ride_service.get_upcoming_rides_for_driver(current_user)
    return success_response("Upcoming rides fetched.", [r.to_dict() for r in rides])


@ride_bp.route("/api/rides/history", methods=["GET"])
@login_required
@json_endpoint
def api_ride_history():
    rides = ride_service.get_ride_history_for_driver(current_user)
    return success_response("Ride history fetched.", [r.to_dict() for r in rides])


@ride_bp.route("/api/rides/match", methods=["POST"])
@login_required
@json_endpoint
def api_match_rides():
    """
    Route matching endpoint: given a passenger's desired pickup, destination,
    and departure time, returns scored/ranked candidate rides.
    """
    data = request.get_json(silent=True) or request.form.to_dict()
    from app.utils.validators import require_fields, validate_future_datetime, validate_location_string

    require_fields(data, ["pickup_location", "destination", "departure_time"])
    pickup = validate_location_string(data["pickup_location"], "pickup_location")
    destination = validate_location_string(data["destination"], "destination")
    departure_time = validate_future_datetime(data["departure_time"], "departure_time")

    matches = matching_service.match_rides(
        pickup_location=pickup,
        destination=destination,
        departure_time=departure_time,
        seats_needed=int(data.get("seats_needed", 1)),
        pickup_lat=data.get("pickup_lat"),
        pickup_lng=data.get("pickup_lng"),
        dest_lat=data.get("destination_lat"),
        dest_lng=data.get("destination_lng"),
    )

    payload = [
        {
            "ride": m["ride"].to_dict(),
            "score": m["score"],
            "distance_pickup_km": m["distance_pickup_km"],
            "distance_destination_km": m["distance_destination_km"],
            "time_diff_minutes": m["time_diff_minutes"],
        }
        for m in matches
    ]
    return success_response(f"{len(payload)} matching ride(s) found.", payload)
