"""
Domain-level exception raised by services and routes.

Services stay ignorant of Flask: they raise ApiError, and a single
handler in create_app() converts it into the response envelope. This
keeps business logic testable without a request context and stops
error-shaping logic being copy-pasted across route files.
"""


class ApiError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        errors: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors
