"""
Booking & ride-request routes: join ride (instant), request-to-join (driver
approval flow), cancel booking, and driver responses to requests.
"""
from flask import Blueprint, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.services import booking_service
from app.utils.validators import ValidationError
from app.utils.responses import success_response
from app.utils.decorators import json_endpoint

booking_bp = Blueprint("booking", __name__)


# ---------------------------------------------------------------------------
# HTML views
# ---------------------------------------------------------------------------
@booking_bp.route("/rides/<int:ride_id>/join", methods=["POST"])
@login_required
def join_ride_view(ride_id):
    try:
        booking_service.join_ride(current_user, ride_id, request.form.to_dict())
        flash("You have successfully joined the ride!", "success")
    except (ValidationError, PermissionError, LookupError) as e:
        flash(str(e) if not hasattr(e, "errors") else "; ".join(e.errors), "danger")
    return redirect(url_for("ride.ride_details", ride_id=ride_id))


@booking_bp.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking_view(booking_id):
    try:
        booking_service.cancel_booking(current_user, booking_id)
        flash("Booking cancelled.", "info")
    except (ValidationError, PermissionError, LookupError) as e:
        flash(str(e) if not hasattr(e, "errors") else "; ".join(e.errors), "danger")
    return redirect(url_for("dashboard.passenger_dashboard"))


@booking_bp.route("/requests/<int:request_id>/respond", methods=["POST"])
@login_required
def respond_request_view(request_id):
    accept = request.form.get("decision") == "accept"
    try:
        booking_service.respond_to_request(current_user, request_id, accept)
        flash("Request accepted." if accept else "Request rejected.", "success")
    except (ValidationError, PermissionError, LookupError) as e:
        flash(str(e) if not hasattr(e, "errors") else "; ".join(e.errors), "danger")
    return redirect(url_for("dashboard.driver_dashboard"))


# ---------------------------------------------------------------------------
# JSON REST API
# ---------------------------------------------------------------------------
@booking_bp.route("/api/rides/<int:ride_id>/join", methods=["POST"])
@login_required
@json_endpoint
def api_join_ride(ride_id):
    data = request.get_json(silent=True) or request.form.to_dict()
    booking = booking_service.join_ride(current_user, ride_id, data)
    return success_response("Ride joined successfully.", booking.to_dict(), status_code=201)


@booking_bp.route("/api/bookings/<int:booking_id>", methods=["DELETE"])
@login_required
@json_endpoint
def api_cancel_booking(booking_id):
    booking = booking_service.cancel_booking(current_user, booking_id)
    return success_response("Booking cancelled.", booking.to_dict())


@booking_bp.route("/api/bookings/me", methods=["GET"])
@login_required
@json_endpoint
def api_my_bookings():
    upcoming_only = request.args.get("upcoming", "false").lower() == "true"
    bookings = booking_service.get_passenger_bookings(current_user, upcoming_only=upcoming_only)
    return success_response("Bookings fetched.", [b.to_dict() for b in bookings])


@booking_bp.route("/api/rides/<int:ride_id>/requests", methods=["POST"])
@login_required
@json_endpoint
def api_request_to_join(ride_id):
    data = request.get_json(silent=True) or request.form.to_dict()
    req = booking_service.request_to_join(current_user, ride_id, data)
    return success_response("Ride request sent.", req.to_dict(), status_code=201)


@booking_bp.route("/api/requests/<int:request_id>/respond", methods=["POST"])
@login_required
@json_endpoint
def api_respond_to_request(request_id):
    data = request.get_json(silent=True) or request.form.to_dict()
    accept = str(data.get("accept", "false")).lower() == "true"
    req = booking_service.respond_to_request(current_user, request_id, accept)
    return success_response("Request updated.", req.to_dict())
