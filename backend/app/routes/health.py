"""
Liveness and database-connectivity probe.

Deliberately unauthenticated and deliberately uninformative: it reports
whether the database round-trips, never the driver, version, or host.
Render uses this for health checks.
"""

from sqlalchemy import text

from app.extensions import db
from app.utils.responses import success_response

from flask import Blueprint

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        database_ok = True
    except Exception: 
        db.session.rollback()
        database_ok = False

    return success_response(
        data={"status": "ok" if database_ok else "degraded", "database": database_ok},
        status_code=200 if database_ok else 503,
    )
