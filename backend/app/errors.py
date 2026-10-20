"""Domain errors, mapped to HTTP responses in the routes (see python-backend skill)."""


class DatabaseCheckError(Exception):
    """Raised by the /ready database checker when a check cannot produce a result.

    The checker wraps any failure here (connection refused, unexpected error), so the
    app can map it to HTTP 503 and a readiness probe never sees a 500. The caller's
    message is kept untouched.
    """
