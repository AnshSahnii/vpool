"""
User profile routes: view/edit profile, manage vehicle details.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.services import ride_service
from app.utils.validators import ValidationError, validate_email, validate_phone
from app.utils.responses import success_response
from app.utils.decorators import json_endpoint

user_bp = Blueprint("user", __name__)


# ---------------------------------------------------------------------------
# HTML views
# ---------------------------------------------------------------------------
@user_bp.route("/profile")
@login_required
def profile():
    return render_template("profile/profile.html", user=current_user)


@user_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        try:
            data = request.form.to_dict()
            current_user.name = data.get("name", current_user.name).strip()
            current_user.email = validate_email(data.get("email", current_user.email))
            current_user.phone = validate_phone(data.get("phone", current_user.phone))
            current_user.organization = data.get("organization", "").strip() or None
            current_user.preferred_time = data.get("preferred_time", "").strip() or None
            current_user.role_preference = data.get("role_preference", current_user.role_preference)
            db.session.commit()
            flash("Profile updated successfully.", "success")
            return redirect(url_for("user.profile"))
        except ValidationError as e:
            for err in e.errors:
                flash(err, "danger")
    return render_template("profile/edit_profile.html", user=current_user)


@user_bp.route("/profile/vehicle/add", methods=["GET", "POST"])
@login_required
def add_vehicle():
    if request.method == "POST":
        try:
            ride_service.register_vehicle(current_user, request.form.to_dict())
            flash("Vehicle added successfully.", "success")
            return redirect(url_for("user.profile"))
        except ValidationError as e:
            for err in e.errors:
                flash(err, "danger")
    return render_template("profile/edit_profile.html", user=current_user, show_vehicle_form=True)


# ---------------------------------------------------------------------------
# JSON REST API
# ---------------------------------------------------------------------------
@user_bp.route("/api/users/me", methods=["GET"])
@login_required
@json_endpoint
def api_get_profile():
    return success_response("Profile fetched.", current_user.to_dict(include_private=True))


@user_bp.route("/api/users/me", methods=["PUT", "PATCH"])
@login_required
@json_endpoint
def api_update_profile():
    data = request.get_json(silent=True) or request.form.to_dict()
    if "name" in data and data["name"].strip():
        current_user.name = data["name"].strip()
    if "email" in data and data["email"].strip():
        current_user.email = validate_email(data["email"])
    if "phone" in data and data["phone"].strip():
        current_user.phone = validate_phone(data["phone"])
    if "organization" in data:
        current_user.organization = data.get("organization", "").strip() or None
    if "preferred_time" in data:
        current_user.preferred_time = data.get("preferred_time", "").strip() or None
    if "role_preference" in data:
        current_user.role_preference = data.get("role_preference")

    db.session.commit()
    return success_response("Profile updated.", current_user.to_dict(include_private=True))


@user_bp.route("/api/users/me/vehicles", methods=["POST"])
@login_required
@json_endpoint
def api_add_vehicle():
    data = request.get_json(silent=True) or request.form.to_dict()
    vehicle = ride_service.register_vehicle(current_user, data)
    return success_response("Vehicle registered.", vehicle.to_dict(), status_code=201)


@user_bp.route("/api/users/me/vehicles", methods=["GET"])
@login_required
@json_endpoint
def api_list_vehicles():
    return success_response("Vehicles fetched.", [v.to_dict() for v in current_user.vehicles])
