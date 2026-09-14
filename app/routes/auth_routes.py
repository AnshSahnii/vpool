"""
Authentication routes.
Serves both traditional HTML form views (for the Bootstrap frontend) and
JSON REST endpoints under /api/auth/* (for programmatic / SPA-style access).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.services import auth_service
from app.utils.validators import ValidationError
from app.utils.responses import success_response, error_response
from app.utils.decorators import json_endpoint

auth_bp = Blueprint("auth", __name__)


# ---------------------------------------------------------------------------
# HTML views
# ---------------------------------------------------------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        try:
            user = auth_service.register_user(request.form.to_dict())
            login_user(user)
            flash("Account created successfully! Welcome to VPOOL.", "success")
            return redirect(url_for("main.index"))
        except ValidationError as e:
            for err in e.errors:
                flash(err, "danger")
    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        try:
            user = auth_service.authenticate_user(
                request.form.get("email", ""), request.form.get("password", "")
            )
            login_user(user, remember=bool(request.form.get("remember")))
            flash(f"Welcome back, {user.name}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.index"))
        except ValidationError as e:
            for err in e.errors:
                flash(err, "danger")
    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "")
        token = auth_service.create_password_reset_token(email)
        # Basic implementation: token is displayed on-screen / logged instead of emailed.
        if token:
            flash(
                f"Password reset token generated. (Demo mode - normally emailed): {token}",
                "info",
            )
            return redirect(url_for("auth.reset_password", token=token))
        flash("If that email exists in our system, a reset link has been generated.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if request.method == "POST":
        try:
            auth_service.reset_password_with_token(token, request.form.get("new_password", ""))
            flash("Password reset successful. Please log in.", "success")
            return redirect(url_for("auth.login"))
        except ValidationError as e:
            for err in e.errors:
                flash(err, "danger")
    return render_template("auth/reset_password.html", token=token)


# ---------------------------------------------------------------------------
# JSON REST API
# ---------------------------------------------------------------------------
@auth_bp.route("/api/auth/register", methods=["POST"])
@json_endpoint
def api_register():
    payload = request.get_json(silent=True) or request.form.to_dict()
    user = auth_service.register_user(payload)
    login_user(user)
    return success_response("User registered successfully.", user.to_dict(), status_code=201)


@auth_bp.route("/api/auth/login", methods=["POST"])
@json_endpoint
def api_login():
    payload = request.get_json(silent=True) or request.form.to_dict()
    user = auth_service.authenticate_user(payload.get("email", ""), payload.get("password", ""))
    login_user(user)
    return success_response("Login successful.", user.to_dict())


@auth_bp.route("/api/auth/logout", methods=["POST"])
@login_required
@json_endpoint
def api_logout():
    logout_user()
    return success_response("Logged out successfully.")


@auth_bp.route("/api/auth/forgot-password", methods=["POST"])
@json_endpoint
def api_forgot_password():
    payload = request.get_json(silent=True) or request.form.to_dict()
    token = auth_service.create_password_reset_token(payload.get("email", ""))
    # Always return 200 without confirming existence (avoids user enumeration)
    data = {"reset_token": token} if token else None
    return success_response("If the email exists, a reset token has been generated.", data)


@auth_bp.route("/api/auth/reset-password", methods=["POST"])
@json_endpoint
def api_reset_password():
    payload = request.get_json(silent=True) or request.form.to_dict()
    auth_service.reset_password_with_token(payload.get("token", ""), payload.get("new_password", ""))
    return success_response("Password has been reset successfully.")


@auth_bp.route("/api/auth/me", methods=["GET"])
@login_required
@json_endpoint
def api_me():
    return success_response("Current user.", current_user.to_dict(include_private=True))
