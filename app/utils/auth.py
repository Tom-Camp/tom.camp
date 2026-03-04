from functools import wraps
from typing import Any, Callable

from flask import abort, request

from app.utils.config import settings


def require_admin(f: Callable) -> Callable:
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        secret = request.headers.get("X-Admin-Secret")
        if not secret or secret != settings.ADMIN_SECRET_KEY:
            abort(401)
        return f(*args, **kwargs)

    return decorated
