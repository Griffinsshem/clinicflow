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
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from app.utils.client_ip import client_ip

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()

limiter = Limiter(
    # Keyed on the real visitor, not on Vercel's shared outbound IPs.
    # See app/utils/client_ip.py.
    key_func=client_ip,
    default_limits=[], 
    storage_uri="memory://",
    strategy="fixed-window",
)
