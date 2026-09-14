"""
VPOOL - Vehicle Pooling System
Application entrypoint. Run with: python run.py
"""
import os
from app import create_app
from app.extensions import db

app = create_app(os.getenv("FLASK_ENV", "development"))


@app.shell_context_processor
def make_shell_context():
    from app.models import User, Vehicle, Ride, RideRequest, Booking
    return {"db": db, "User": User, "Vehicle": Vehicle, "Ride": Ride,
            "RideRequest": RideRequest, "Booking": Booking}


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Creates tablvenv\Scripts\activate  es if they don't exist (dev convenience)
    app.run(debug=app.config.get("DEBUG", True), host="0.0.0.0", port=5000)
