"""
Authentication business logic: registration, login, password reset tokens.
Kept separate from routes so both the HTML views and the JSON API can reuse it.
"""
import secrets
from datetime import datetime, timedelta

from app.extensions import db
from app.models.user import User
from app.utils.validators import (
    ValidationError,
    require_fields,
    validate_email,
    validate_phone,
    validate_password_strength,
)


def register_user(data: dict) -> User:
    require_fields(data, ["name", "email", "phone", "password"])

    name = data["name"].strip()
    email = validate_email(data["email"])
    phone = validate_phone(data["phone"])
    password = validate_password_strength(data["password"])

    # Duplicate user validation
    if User.query.filter_by(email=email).first():
        raise ValidationError("An account with this email already exists.")
    if User.query.filter_by(phone=phone).first():
        raise ValidationError("An account with this phone number already exists.")

    user = User(
        name=name,
        email=email,
        phone=phone,
        organization=data.get("organization", "").strip() or None,
        preferred_time=data.get("preferred_time", "").strip() or None,
        role_preference=data.get("role_preference", "both"),
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(email: str, password: str) -> User:
    require_fields({"email": email, "password": password}, ["email", "password"])
    email = email.strip().lower()

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise ValidationError("Invalid email or password.")
    if not user.is_active:
        raise ValidationError("This account has been deactivated.")
    return user


def create_password_reset_token(email: str) -> str:
    user = User.query.filter_by(email=email.strip().lower()).first()
    if not user:
        # Do not reveal whether the email exists (security best practice)
        return None

    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=30)
    db.session.commit()
    return token


def reset_password_with_token(token: str, new_password: str) -> User:
    require_fields({"token": token, "new_password": new_password}, ["token", "new_password"])
    validate_password_strength(new_password)

    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        raise ValidationError("Invalid or expired reset token.")

    user.set_password(new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.session.commit()
    return user
