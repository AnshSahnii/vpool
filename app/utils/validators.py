"""
Reusable input validation helpers used by services/routes.
Keeps validation logic out of route handlers (separation of concerns).
"""
import re
from datetime import datetime

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^\+?[0-9]{10,15}$")


class ValidationError(Exception):
    """Raised when input fails validation. Carries a list of error strings."""
    def __init__(self, errors):
        if isinstance(errors, str):
            errors = [errors]
        self.errors = errors
        super().__init__("; ".join(errors))


def require_fields(data: dict, fields: list):
    """Ensure all listed fields exist and are non-empty (empty-field validation)."""
    missing = []
    for f in fields:
        value = data.get(f) if data else None
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(f)
    if missing:
        raise ValidationError([f"Field '{f}' is required." for f in missing])


def validate_email(email: str):
    if not email or not EMAIL_REGEX.match(email.strip()):
        raise ValidationError("Invalid email address format.")
    return email.strip().lower()


def validate_phone(phone: str):
    if not phone or not PHONE_REGEX.match(phone.strip()):
        raise ValidationError("Invalid phone number. Use 10-15 digits, optional leading +.")
    return phone.strip()


def validate_password_strength(password: str):
    if not password or len(password) < 6:
        raise ValidationError("Password must be at least 6 characters long.")
    return password


def validate_positive_int(value, field_name="value", minimum=1):
    try:
        ivalue = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"'{field_name}' must be an integer.")
    if ivalue < minimum:
        raise ValidationError(f"'{field_name}' must be >= {minimum}.")
    return ivalue


def validate_future_datetime(value, field_name="departure_time"):
    """Accepts ISO-8601 string or datetime; ensures it is in the future."""
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", ""))
        except ValueError:
            raise ValidationError(f"'{field_name}' must be a valid ISO datetime string.")
    if dt <= datetime.utcnow():
        raise ValidationError(f"'{field_name}' must be a future date/time.")
    return dt


def validate_location_string(value, field_name="location"):
    if not value or not str(value).strip() or len(str(value).strip()) < 3:
        raise ValidationError(f"'{field_name}' is invalid or too short.")
    return str(value).strip()
