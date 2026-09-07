"""
Application factory.

Wiring order matters: config is loaded and validated before any
extension initialises, so a misconfigured production deploy dies before
it can bind a port.
"""

import logging
import sys

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import BaseConfig, get_config
from app.extensions import cors, db, jwt, limiter, migrate
from app.utils.errors import ApiError
from app.utils.responses import error_response

API_PREFIX = "/api/v1"


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)

    config: type[BaseConfig] = get_config(config_name)
    app.config.from_object(config)
    config.validate()  

    _configure_logging(app)

    if app.config["BEHIND_PROXY"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    cors.init_app(
        app,
        resources={f"{API_PREFIX}/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=False,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    )

    _register_blueprints(app)
    _register_error_handlers(app)

    app.logger.info("ClinicFlow started in %s mode", app.config["ENV_NAME"])
    return app


def _register_blueprints(app: Flask) -> None:
    from app.routes.health import bp as health_bp

    app.register_blueprint(health_bp, url_prefix=API_PREFIX)


def _configure_logging(app: Flask) -> None:
    """
    Log to stdout so Render captures it. Never log passwords, tokens,
    or patient identifiers — see the logging notes in the README.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
    )
    app.logger.handlers = [handler]
    app.logger.setLevel(logging.DEBUG if app.config["DEBUG"] else logging.INFO)


def _register_error_handlers(app: Flask) -> None:
    """
    Every error path exits through the envelope. Internal detail goes to
    the logs; the client gets a safe, human-readable message.
    """

    @app.errorhandler(ApiError)
    def handle_api_error(exc: ApiError):
        return error_response(exc.message, exc.status_code, exc.errors)

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        messages = {
            404: "The requested resource was not found.",
            405: "That method is not allowed on this endpoint.",
            429: "Too many requests. Please wait and try again.",
        }
        return error_response(
            messages.get(exc.code or 500, exc.description or "Request failed."),
            exc.code or 500,
        )

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):
        app.logger.exception("Unhandled exception: %s", exc)
        db.session.rollback()
        return error_response("Something went wrong. Please try again.", 500)

    @jwt.expired_token_loader
    def handle_expired_token(_header, _payload):
        return jsonify(
            {"success": False, "message": "Your session has expired. Please sign in again."}
        ), 401

    @jwt.invalid_token_loader
    def handle_invalid_token(_reason):
        return jsonify({"success": False, "message": "Invalid authentication token."}), 401

    @jwt.unauthorized_loader
    def handle_missing_token(_reason):
        return jsonify({"success": False, "message": "Authentication required."}), 401
