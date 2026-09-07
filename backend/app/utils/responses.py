"""
The single response shape for the whole API.

Success:  {"success": true,  "data": {...}, "meta": {...}}
Failure:  {"success": false, "message": "...", "errors": {"field": "..."}}

Every route returns through these helpers, so the frontend writes one
parser instead of branching per endpoint.
"""

from typing import Any

from flask import jsonify
from flask.wrappers import Response


def success_response(
    data: Any = None,
    message: str | None = None,
    status_code: int = 200,
    meta: dict[str, Any] | None = None,
) -> tuple[Response, int]:
    payload: dict[str, Any] = {"success": True}
    if message is not None:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    if meta is not None:
        payload["meta"] = meta 
    return jsonify(payload), status_code


def error_response(
    message: str,
    status_code: int = 400,
    errors: dict[str, str] | None = None,
) -> tuple[Response, int]:
    payload: dict[str, Any] = {"success": False, "message": message}
    if errors:
        payload["errors"] = errors
    return jsonify(payload), status_code
