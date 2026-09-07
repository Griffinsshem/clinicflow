from datetime import timedelta

from flask import Blueprint, current_app, g, request
from flask_jwt_extended import create_access_token

from app.extensions import limiter
from app.models.user import User
from app.schemas.auth import LoginSchema, RegisterSchema
from app.schemas.base import parse_request
from app.services.auth_service import authenticate_user, register_clinic_with_admin
from app.utils.decorators import auth_required
from app.utils.responses import success_response

bp = Blueprint("auth", __name__)


def _issue_token(user: User) -> dict:
    token = create_access_token(
        identity=str(user.id),
        additional_claims={"clinic_id": user.clinic_id, "role": user.role.value},
    )
    expires: timedelta = current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": int(expires.total_seconds()),
        "user": user.to_dict(),
    }


@bp.post("/auth/register")
@limiter.limit("3 per hour")
def register():
    data = parse_request(RegisterSchema, request.get_json(silent=True))

    clinic, user = register_clinic_with_admin(
        clinic_name=data.clinic_name,
        full_name=data.full_name,
        email=data.email,
        password=data.password,
    )

    current_app.logger.info(
        "Clinic registered: clinic_id=%s admin_user_id=%s", clinic.id, user.id
    )

    payload = _issue_token(user)
    payload["clinic"] = clinic.to_dict()
    return success_response(
        data=payload, message="Your clinic account has been created.", status_code=201
    )


@bp.post("/auth/login")
@limiter.limit("5 per minute")
def login():
    data = parse_request(LoginSchema, request.get_json(silent=True))
    user = authenticate_user(email=data.email, password=data.password)

    current_app.logger.info("Login succeeded: user_id=%s", user.id)
    return success_response(data=_issue_token(user), message="Signed in.")


@bp.get("/auth/me")
@auth_required
def me():
    user = g.current_user
    return success_response(
        data={"user": user.to_dict(), "clinic": user.clinic.to_dict()}
    )
