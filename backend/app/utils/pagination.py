from typing import Any

from sqlalchemy import Select, func, select

from app.extensions import db

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def parse_pagination(args: dict[str, Any]) -> tuple[int, int]:
    try:
        page = max(1, int(args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1

    try:
        limit = int(args.get("limit", DEFAULT_LIMIT))
    except (TypeError, ValueError):
        limit = DEFAULT_LIMIT

    limit = max(1, min(limit, MAX_LIMIT))
    return page, limit


def escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def paginate(stmt: Select, page: int, limit: int) -> tuple[list, dict]:
    total = db.session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.session.scalars(stmt.limit(limit).offset((page - 1) * limit)).all()

    return list(rows), {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit if total else 0,
    }
