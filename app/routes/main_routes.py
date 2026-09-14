"""
Main/general routes: landing page and health check.
"""
from flask import Blueprint, render_template
from flask_login import current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html", user=current_user)


@main_bp.route("/api/health")
def health_check():
    return {"status": "ok", "service": "VPOOL API"}, 200
