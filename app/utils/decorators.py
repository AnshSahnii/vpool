"""
Custom decorators for route handlers.
"""
from functools import wraps
from flask import request
from flask_login import current_user
from app.utils.responses import error_response
from app.utils.validators import ValidationError


def json_endpoint(f):
    """
    Wraps an API route to:
    - Catch ValidationError and return a clean 422 response
    - Catch unexpected exceptions and return a clean 500 response
    (Keeps try/except boilerplate out of every route.)
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            return error_response("Validation failed", errors=e.errors, status_code=422)
        except PermissionError as e:
            return error_response(str(e) or "Forbidden", status_code=403)
        except LookupError as e:
            return error_response(str(e) or "Not found", status_code=404)
        except Exception as e:  # noqa: BLE001
            return error_response(f"Internal server error: {str(e)}", status_code=500)
    return wrapper


def login_required_api(f):
    """Like flask_login.login_required but returns JSON 401 instead of redirecting."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return error_response("Authentication required.", status_code=401)
        return f(*args, **kwargs)
    return wrapper
