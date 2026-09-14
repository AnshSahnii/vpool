"""
Centralized Flask extension instances.
Instantiated here (without an app) and initialized in the app factory
to avoid circular imports across models/routes/services.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
cors = CORS()

login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"


@login_manager.unauthorized_handler
def unauthorized():
    """
    Return JSON 401 for API requests, but redirect to the login page
    for normal browser navigation (HTML views).
    """
    from flask import request, redirect, url_for, jsonify
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "message": "Authentication required.", "data": None, "errors": None}), 401
    return redirect(url_for("auth.login", next=request.path))
