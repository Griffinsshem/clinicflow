"""
Flask extension instances.

These are created unbound (no app) and attached inside create_app().
That split is what makes the app-factory pattern work: models can
`from app.extensions import db` without importing the app, so there
is no import cycle, and tests can build multiple app instances
against different databases.
"""

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[], 
    storage_uri="memory://",
    strategy="fixed-window",
)
