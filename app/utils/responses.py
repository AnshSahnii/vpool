"""
Standardized JSON API responses so every endpoint returns a predictable shape:
{
  "success": bool,
  "message": str,
  "data": <payload> | null,
  "errors": [ ... ] | null
}
"""
from flask import jsonify


def success_response(message="Success", data=None, status_code=200):
    payload = {"success": True, "message": message, "data": data, "errors": None}
    return jsonify(payload), status_code


def error_response(message="Something went wrong", errors=None, status_code=400):
    payload = {"success": False, "message": message, "data": None, "errors": errors}
    return jsonify(payload), status_code
