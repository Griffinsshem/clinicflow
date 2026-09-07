from functools import wraps
from typing import Callable

from flask import g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.extensions import db
from app.models.enums import UserRole
from app.models.user import User
from app.utils.errors import ApiError


def auth_required(fn: Callable) -> Callable:

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()

        identity = get_jwt_identity()
        try:
            user_id = int(identity)
        except (TypeError, ValueError):
            raise ApiError("Invalid authentication token.", 401) from None

        user = db.session.get(User, user_id)
        if user is None:
            raise ApiError("Invalid authentication token.", 401)

        g.current_user = user
        g.clinic_id = user.clinic_id  
        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn: Callable) -> Callable:

    @wraps(fn)
    @auth_required
    def wrapper(*args, **kwargs):
        if g.current_user.role != UserRole.ADMIN:
            raise ApiError("You do not have permission to perform this action.", 403)
        return fn(*args, **kwargs)

    return wrapper
