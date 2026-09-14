"""
Dashboard routes for drivers and passengers.
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.services import dashboard_service
from app.utils.responses import success_response
from app.utils.decorators import json_endpoint

dashboard_bp = Blueprint("dashboard", __name__)


# ---------------------------------------------------------------------------
# HTML views
# ---------------------------------------------------------------------------
@dashboard_bp.route("/dashboard/driver")
@login_required
def driver_dashboard():
    data = dashboard_service.driver_dashboard_data(current_user)
    return render_template("dashboard/driver_dashboard.html", data=data)


@dashboard_bp.route("/dashboard/passenger")
@login_required
def passenger_dashboard():
    data = dashboard_service.passenger_dashboard_data(current_user)
    return render_template("dashboard/passenger_dashboard.html", data=data)


# ---------------------------------------------------------------------------
# JSON REST API
# ---------------------------------------------------------------------------
@dashboard_bp.route("/api/dashboard/driver", methods=["GET"])
@login_required
@json_endpoint
def api_driver_dashboard():
    return success_response("Driver dashboard fetched.", dashboard_service.driver_dashboard_data(current_user))


@dashboard_bp.route("/api/dashboard/passenger", methods=["GET"])
@login_required
@json_endpoint
def api_passenger_dashboard():
    return success_response("Passenger dashboard fetched.", dashboard_service.passenger_dashboard_data(current_user))
