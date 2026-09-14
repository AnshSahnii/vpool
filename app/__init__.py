"""
Application factory for VPOOL - Vehicle Pooling System.
"""
import os
from flask import Flask, render_template

from app.config import config_by_name
from app.extensions import db, login_manager, migrate, cors


def create_app(config_name=None):
    config_name = config_name or os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))

    # --- Init extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # --- Import models so SQLAlchemy is aware of them before create_all() ---
    from app.models import User, Vehicle, Ride, RideRequest, Booking  # noqa: F401

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Register blueprints ---
    from app.routes.main_routes import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.user_routes import user_bp
    from app.routes.ride_routes import ride_bp
    from app.routes.booking_routes import booking_bp
    from app.routes.dashboard_routes import dashboard_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(ride_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(dashboard_bp)

    register_error_handlers(app)

    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        return {"app_name": "VPOOL", "user": current_user}

    return app


def register_error_handlers(app):
    """Central error handling: HTML pages for browser requests, JSON for /api/* requests."""
    from flask import request, jsonify

    def wants_json():
        return request.path.startswith("/api/") or request.accept_mimetypes.best == "application/json"

    @app.errorhandler(404)
    def not_found(e):
        if wants_json():
            return jsonify({"success": False, "message": "Resource not found.", "data": None, "errors": None}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        if wants_json():
            return jsonify({"success": False, "message": "Forbidden.", "data": None, "errors": None}), 403
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(e):
        if wants_json():
            return jsonify({"success": False, "message": "Internal server error.", "data": None, "errors": None}), 500
        return render_template("errors/500.html"), 500
